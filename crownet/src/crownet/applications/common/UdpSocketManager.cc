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

#include "crownet/applications/common/UdpSocketManager.h"
#include "crownet/applications/common/AppCommon_m.h"
#include "inet/networklayer/common/L3Address.h"
#include "inet/networklayer/common/L3AddressResolver.h"

namespace  crownet {
Define_Module(UdpSocketManager);

UdpSocketManager::UdpSocketManager() {
    // TODO Auto-generated constructor stub

}

UdpSocketManager::~UdpSocketManager() {
    // TODO Auto-generated destructor stub
}

void UdpSocketManager::initSocket() {
    socket.setOutputGate(gate("toStack"));
    const char *localAddress = par("localAddress");
    socket.bind(
        *localAddress ? L3AddressResolver().resolve(localAddress) : L3Address(),
        localPort);

    // socketOptions
    int timeToLive = par("timeToLive");
    if (timeToLive != -1) socket.setTimeToLive(timeToLive);

    int dscp = par("dscp");
    if (dscp != -1) socket.setDscp(dscp);

    int tos = par("tos");
    if (tos != -1) socket.setTos(tos);

    const char *multicastInterface = par("multicastInterface");
    if (multicastInterface[0]) {
      IInterfaceTable *ift =
          getModuleFromPar<IInterfaceTable>(par("interfaceTableModule"), this);
      NetworkInterface *ie = ift->findInterfaceByName(multicastInterface);
      if (!ie)
        throw cRuntimeError(
            "Wrong multicastInterface setting: no interface named \"%s\"",
            multicastInterface);
      socket.setMulticastOutputInterface(ie->getInterfaceId());
    }

    bool receiveBroadcast = par("receiveBroadcast");
    if (receiveBroadcast) socket.setBroadcast(true);

    bool joinLocalMulticastGroups = par("joinLocalMulticastGroups");
    if (joinLocalMulticastGroups) {
      MulticastGroupList mgl =
          getModuleFromPar<IInterfaceTable>(par("interfaceTableModule"), this)
              ->collectMulticastGroups();
      socket.joinLocalMulticastGroups(mgl);
    }
    socket.setCallback(this);
}

ISocket &UdpSocketManager::getSocket() { return socket; }

// UdpSocket::ICallback
void UdpSocketManager::socketDataArrived(UdpSocket *socket, Packet *packet) {
  send(packet, gate("toApp"));
}

void UdpSocketManager::socketErrorArrived(UdpSocket *socket, Indication *indication) {
  EV_WARN << "Ignoring UDP error report " << indication->getName() << endl;
  // todo handle socketError
  delete indication;
}

void UdpSocketManager::socketClosed(UdpSocket *socket) {
  if (operationalState == State::STOPPING_OPERATION) {
    startActiveOperationExtraTimeOrFinish(par("stopOperationExtraTime"));
  }
  // todo inform app logiv of socketClosed
}
}

