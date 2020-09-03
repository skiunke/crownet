/*
 * GridDensityMap.cc
 *
 *  Created on: Aug 25, 2020
 *      Author: sts
 */

#include "GridDensityMap.h"

namespace rover {

DensityMeasure::DensityMeasure() : IEntry<omnetpp::simtime_t>() {}
DensityMeasure::DensityMeasure(int count, omnetpp::simtime_t& measurement_time,
                               omnetpp::simtime_t& received_time)
    : IEntry<omnetpp::simtime_t>(count, measurement_time, received_time) {}

std::string DensityMeasure::delimWith(std::string delimiter) const {
  std::stringstream out;
  out << count << delimiter << measurement_time.dbl() << delimiter
      << received_time.dbl();
  return out.str();
}

std::ostream& operator<<(std::ostream& os, const DensityMeasure& obj) {
  os << "Count: " << obj.count
     << "| measurement_time:" << obj.measurement_time.dbl()
     << "| received_time: " << obj.received_time.dbl()
     << "| valid: " << obj.valid();
  return os;
}

} /* namespace rover */
