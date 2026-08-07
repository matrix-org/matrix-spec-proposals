# MSC4220: Local call rejection (m.call.reject_locally)

## Problem

MSC2746 added the concept of explicitly rejecting a ringing call across all devices (`m.call.reject`) as opposed to
terminating a call which may be already ongoing (`m.call.hangup`).

However, we have no way for a specific device to say that it is unable to accept the currently ringing call.
Use cases include:

 * Automatically rejecting the call on a given device because that device can't support the call protocol (e.g. MatrixRTC),
   and so giving the caller a way to be warned that the reason the callee might not answer is because they don't speak
   the right protocol.
 * Letting users stop their local device ringing, but leave the call ringing other devices on the account (e.g. in case
   a different person can pick them up)

## Proposal

Introduce a new call signalling event called `m.call.reject_locally`, which has a `reason` field which allows the device
to state why it's unable to accept a given call.  It uses the same other fields as `m.call.reject`. For instance:

```json5
{
  "call_id": "abcdefg1234", // Required: The ID of the call this event relates to.
  "party_id": "ASHGCGYUWE", // Required: This identifies the party that sent this event.
  "version": "1", // this would be part of v1 calling, given it's not a breaking change but an addition
  "reason": "needs_matrixrtc"
}
```

Possible reason codes are:

 * `unimplemented` - a generic way to say that this device can't accept the call because it has no legacy VoIP stack.
 * `unsupported_protocol` - a generic way to say that this device can't accept the call because it has an unspecified different VoIP staack.
 * `needs_matrixrtc` - indicates that this device requires MatrixRTC (MSC4143) to receive calls.
 * `unwanted` - a generic way to say that the user manually rejected the call, but only on that local device.

Calling devices SHOULD warn the user if a callee device returns `needs_matrixrtc` that the call should be attempted via
MatrixRTC instead, or `unsupported_protocol` that "the user may not be able to answer on their current Matrix client".

Other reasons MAY be ignored by the caller, given they are not actionable.

While we're at it, we should fix the spec to clarify that `m.call.hangup` should not be used to reject v1 calls, as
that's what `m.call.reject` is for.  Currently the spec is ambiguous and says `m.call.hangup` "can be sent either once
the call has has been established or before to abort the call." which is true, but not how v1 calls are meant to work.

## Potential issues

1. It feels wrong to be writing MSCs against the legacy VoIP calling system while MatrixRTC is the future.  However, this
is effectively a migratory step towards MatrixRTC, so it's justifiable.

2. If none of the callee's devices can support legacy VoIP, we really shouldn't try to set up the call in the first place -
or failing that, if they all local-reject the call, the call should be rejected outright as if the callee sent an
`m.call.reject`.  However, this means tracking capabilities of the callee's devices, which is an additional level of
complexity with dependency on extensible events, so has been descoped for now.

(We might also want to reject the call if no devices are sufficiently online to even acknowledge the invite - if we had an
invite acknowledgement event like a SIP 180).

3. Does this give legacy clients a way of rejecting MatrixRTC calls that they can't answer?  It's not clear from MSC4143 how
much `m.call.*` etc is actually being used for MatrixRTC calls these days.  Whatever, surely legacy clients need a way
to warn MatrixRTC clients that they won't be able to answer their calls...

## Alternatives

1. Implement capability negotiation to tell up front whether a callee will be able to accept a call up front. For
instance, advertising supported call protocol version in extensible profiles would be a way to tell which protocol a
given user wants to be called via.

2. Ideally we wouldn't need this at all, as MatrixRTC would provide backwards compatibility with legacy calling
(similar to a SIP<->MatrixRTC bridge, one could dial into MatrixRTC calls via legacy Matrix calling too).  But this
doesn't exist yet, hence this workaround.

3. Clients which can support both legacy & matrixrtc calling (e.g. Element Web) could place both call types running
simultaneously, avoiding the need for warnings about unsupported protocols.  However, clients which only speak legacy
calling (e.g. classic Element iOS/Android) would still benefit from theis MSC.

## Security considerations

The rejection leaks which devices the user is currently active on, and their capabilities.

## Unstable prefix

`m.call.reject_locally` is `org.matrix.mscXXXX.call.reject_locally` until ready.

## Dependencies

Given this MSC involves `needs_matrixrtc` it has a soft dependency on MSC4143.
