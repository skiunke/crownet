/*
 * RoVerCore.cc
 *
 *  Created on: Aug 6, 2020
 *      Author: sts
 */
#include "VadereCore.h"

#include <inet/common/ModuleAccess.h>
#include <omnetpp/checkandcast.h>
#include <traci/SubscriptionManager.h>

#include "rover/artery/traci/VadereLauchner.h"
#include "rover/artery/traci/VadereSubscriptionManager.h"

using namespace traci;
using namespace omnetpp;

namespace {
const simsignal_t initSignal = cComponent::registerSignal("traci.init");
const simsignal_t stepSignal = cComponent::registerSignal("traci.step");
const simsignal_t closeSignal = cComponent::registerSignal("traci.close");
}  // namespace

namespace rover {

Define_Module(VadereCore);

void VadereCore::handleMessage(omnetpp::cMessage* msg) {
  if (msg == m_updateEvent) {
    // mobility provider is ahead dt = updateInterval
    // needed to interpolate between NOW(=simTime()) and NOW+updateInterval
    simtime_t targetTime = simTime() + m_updateInterval;
    m_traci->simulationStep(targetTime.dbl());
    if (m_subscriptions) {
      m_subscriptions->step();
    }
    emit(stepSignal, simTime());

    if (!m_stopping) {
      scheduleAt(simTime() + m_updateInterval, m_updateEvent);
    }
  } else if (msg == m_connectEvent) {
    m_traci->connect(m_launcher->launch());
    auto traciLauchner = omnetpp::check_and_cast<VadereLauchner*>(m_launcher);
    {  // scope of raw pointer
      auto tmp_vadereLiteApi =
          omnetpp::check_and_cast<VadereLiteApi*>(m_lite.get());
      auto tmp_vadereAPI = omnetpp::check_and_cast<VadereApi*>(m_traci.get());
      traciLauchner->initializeServer(tmp_vadereLiteApi, tmp_vadereAPI);
    }
    checkVersion();
    syncTime();
    emit(initSignal, simTime());
    m_updateInterval = Time{m_traci->simulation.getDeltaT()};
    scheduleAt(simTime() + m_updateInterval, m_updateEvent);
  }
}

VadereLiteApi* VadereCore::getVadereLiteAPI() {
  return omnetpp::check_and_cast<VadereLiteApi*>(m_lite.get());
}

} /* namespace rover */
