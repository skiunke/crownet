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

#pragma once

#include "../../mobility/IPositionHistoryProvider.h"
#include "inet/mobility/base/MobilityBase.h"
#include "rover/applications/common/AidBaseApp.h"
#include "rover/common/ItsPdu_m.h"

namespace rover {

class VruAid : public AidBaseApp {
 public:
  VruAid();
  virtual ~VruAid();

 protected:
  IPositionHistoryProvider* mobilityModule = nullptr;

 protected:
  virtual void initialize(int stage) override;
  virtual FsmState fsmAppMain(cMessage* msg) override;
  virtual void socketDataArrived(AidSocket* socket, Packet* packet) override;
  virtual Coord getCurrentLocation();

  virtual void setAppRequirements() override;
  virtual void setAppCapabilities() override;

  // VAM
};
}  // namespace rover
