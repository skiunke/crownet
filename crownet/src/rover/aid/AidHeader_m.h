//
// Generated file, do not edit! Created by nedtool 5.6 from rover/aid/AidHeader.msg.
//

#ifndef __ROVER_AIDHEADER_M_H
#define __ROVER_AIDHEADER_M_H

#if defined(__clang__)
#  pragma clang diagnostic ignored "-Wreserved-id-macro"
#endif
#include <omnetpp.h>

// nedtool version check
#define MSGC_VERSION 0x0506
#if (MSGC_VERSION!=OMNETPP_VERSION)
#    error Version mismatch! Probably this file was generated by an earlier version of nedtool: 'make clean' should help.
#endif

// dll export symbol
#ifndef ROVER_API
#  if defined(ROVER_EXPORT)
#    define ROVER_API  OPP_DLLEXPORT
#  elif defined(ROVER_IMPORT)
#    define ROVER_API  OPP_DLLIMPORT
#  else
#    define ROVER_API
#  endif
#endif


namespace rover {

class AidHeader;
} // namespace rover

#include "inet/common/INETDefs_m.h" // import inet.common.INETDefs

#include "inet/common/packet/chunk/Chunk_m.h" // import inet.common.packet.chunk.Chunk


namespace rover {

/**
 * Class generated from <tt>rover/aid/AidHeader.msg:22</tt> by nedtool.
 * <pre>
 * class AidHeader extends inet::FieldsChunk
 * {
 * }
 * </pre>
 */
class ROVER_API AidHeader : public ::inet::FieldsChunk
{
  protected:

  private:
    void copy(const AidHeader& other);

  protected:
    // protected and unimplemented operator==(), to prevent accidental usage
    bool operator==(const AidHeader&);

  public:
    AidHeader();
    AidHeader(const AidHeader& other);
    virtual ~AidHeader();
    AidHeader& operator=(const AidHeader& other);
    virtual AidHeader *dup() const override {return new AidHeader(*this);}
    virtual void parsimPack(omnetpp::cCommBuffer *b) const override;
    virtual void parsimUnpack(omnetpp::cCommBuffer *b) override;

    // field getter/setter methods

    public:
    virtual std::string str() const override;
};

inline void doParsimPacking(omnetpp::cCommBuffer *b, const AidHeader& obj) {obj.parsimPack(b);}
inline void doParsimUnpacking(omnetpp::cCommBuffer *b, AidHeader& obj) {obj.parsimUnpack(b);}

} // namespace rover

#endif // ifndef __ROVER_AIDHEADER_M_H

