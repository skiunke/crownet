//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Lesser General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Lesser General Public License for more details.
//
// You should have received a copy of the GNU Lesser General Public License
// along with this program.  If not, see http://www.gnu.org/licenses/.
//

#include "rover/common/positionMap/GlobalDensityMap.h"

#include <inet/common/ModuleAccess.h>
#include <inet/mobility/contract/IMobility.h>
#include <omnetpp/checkandcast.h>
#include <memory>
#include "artery/application/Middleware.h"
#include "artery/application/MovingNodeDataProvider.h"
#include "artery/utility/Identity.h"
#include "rover/dcd/regularGrid/RegularCellVisitors.h"
#include "rover/dcd/regularGrid/RegularDcdMapPrinter.h"

namespace {
const simsignal_t traciInit = cComponent::registerSignal("traci.init");
}  // namespace

namespace rover {

Define_Module(GlobalDensityMap);

const simsignal_t GlobalDensityMap::registerMap =
    cComponent::registerSignal("RegisterDensityMap");
const simsignal_t GlobalDensityMap::removeMap =
    cComponent::registerSignal("RemoveDensityMap");

GlobalDensityMap::~GlobalDensityMap() {
  if (updateTimer) cancelAndDelete(updateTimer);
}

void GlobalDensityMap::initialize() {
  getSystemModule()->subscribe(registerMap, this);
  getSystemModule()->subscribe(removeMap, this);
  getSystemModule()->subscribe(traciInit, this);
}

void GlobalDensityMap::finish() {
  getSystemModule()->unsubscribe(registerMap, this);
  getSystemModule()->unsubscribe(removeMap, this);
  getSystemModule()->unsubscribe(traciInit, this);
}

void GlobalDensityMap::receiveSignal(omnetpp::cComponent *source,
                                     omnetpp::simsignal_t signalId,
                                     omnetpp::cObject *obj,
                                     omnetpp::cObject *details) {
  if (signalId == registerMap) {
    auto mapHandler = check_and_cast<GridHandler *>(obj);
    dezentralMaps[mapHandler->getMap()->getOwnerId()] = mapHandler;
    EV_DEBUG << "register DensityMap for node: "
             << mapHandler->getMap()->getOwnerId();

  } else if (signalId == removeMap) {
    auto mapHandler = check_and_cast<GridHandler *>(obj);
    dezentralMaps.erase(mapHandler->getMap()->getOwnerId());
    EV_DEBUG << "remove DensityMap for node: "
             << mapHandler->getMap()->getOwnerId();
  }
}
void GlobalDensityMap::receiveSignal(cComponent *source, simsignal_t signalID,
                                     const SimTime &t, cObject *details) {
  if (signalID == traciInit) {
    // 1) setup map
    converter = inet::getModuleFromPar<OsgCoordConverter>(
                    par("coordConverterModule"), this, true)
                    ->getConverter();
    nodeManager = inet::getModuleFromPar<traci::NodeManager>(
        par("traciNodeManager"), this, true);

    std::pair<int, int> gridDim;
    double gridSize = par("gridSize").doubleValue();
    gridDim.first = floor(converter->getBoundaryWidth() / gridSize);
    gridDim.second = floor(converter->getBoundaryWidth() / gridSize);
    RegularDcdMapFactory f{std::make_pair(gridSize, gridSize), gridDim};

    dcdMapGlobal = f.create_shared_ptr(IntIdentifer(-1));  // global

    // 2) setup writer.
    FileWriterBuilder fBuilder{};
    fBuilder.addMetadata("IDXCOL", 3);
    fBuilder.addMetadata("XSIZE", converter->getBoundaryWidth());
    fBuilder.addMetadata("YSIZE", converter->getBoundaryHeight());
    fBuilder.addMetadata("CELLSIZE", par("gridSize").doubleValue());
    fBuilder.addMetadata<std::string>(
        "MAP_TYPE",
        "global");  // The global density map is the ground
                    // truth. No algorihm needed.
    fBuilder.addMetadata("NODE_ID", dcdMapGlobal->getOwnerId().value());
    fBuilder.addPath("global");

    fileWriter.reset(fBuilder.build(
        std::make_shared<RegularDcdMapGlobalPrinter>(dcdMapGlobal.get())));
    fileWriter->writeHeader();
  }
}

void GlobalDensityMap::initialize(int stage) {
  cSimpleModule::initialize(stage);
  if (stage == INITSTAGE_LOCAL) {
    std::string x = par("coordConverterModule").stdstringValue();
  } else if (stage == INITSTAGE_APPLICATION_LAYER) {
    m_middelwareModule = par("middelwareModule").stdstringValue();

    updateTimer = new cMessage("GlobalDensityMapTimer");
    updateInterval = par("updateInterval").doubleValue();
    if (updateInterval > 0) {
      scheduleAt(simTime() + updateInterval, updateTimer);
    }
  }
}

void GlobalDensityMap::handleMessage(cMessage *msg) {
  if (msg->isSelfMessage()) {
    // 1) update maps
    updateMaps();

    // 2) write to file
    writeMaps();

    // 3) reschedule
    scheduleAt(simTime() + updateInterval, msg);
  } else {
    delete msg;
  }
}

void GlobalDensityMap::visitNode(const std::string &traciNodeId,
                                 omnetpp::cModule *mod) {
  // access middelware for position

  auto middleware = check_and_cast<artery::Middleware *>(
      mod->getModuleByPath(m_middelwareModule.c_str()));

  // convert to traci 2D position
  const auto &pos = middleware->getFacilities()
                        .getConst<artery::MovingNodeDataProvider>()
                        .position();
  const auto &posInet = converter->position_cast_traci(pos);

  // visitNode is called for *all* nodes thus this 'local' map of the global
  // module represents the global (ground truth) of the simulation.
  dcdMapGlobal->incrementLocal(posInet, mod->getId(), simTime());
}

/**
 * update global and decentralized maps together to get the same time stamp.
 */
void GlobalDensityMap::updateMaps() {
  // update global map. (Visit all nodes managed by traci)
  // only update once for given simtime_t
  if (lastUpdate >= simTime()) {
    return;
  }
  lastUpdate = simTime();

  // global map needs reset (not clear)
  dcdMapGlobal->visitCells(ResetVisitor{lastUpdate});
  dcdMapGlobal->clearNeighborhood();
  nodeManager->visit(this);

  // update each decentralized map
  for (auto &handler : dezentralMaps) {
    handler.second->updateLocalMap();
    handler.second->computeValues();
  }
}

void GlobalDensityMap::writeMaps() {
  fileWriter->writeData();

  // write decentralized maps
  for (auto &handler : dezentralMaps) {
    handler.second->writeMap();
  }
}

}  // namespace rover
