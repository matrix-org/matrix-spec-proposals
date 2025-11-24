# MSC3635: Early Media for VoIP

In PSTN and SIP calls, media can be sent between callee and caller before the callee has accepted
the call. This allows for things like ringback tones and announcements.

## Context
Early Media is already a well-established concept in SIP. Traditionally, it relies on the
decoupling of the offer and answer from the INVITE and OK messages, instead allowing the
answer to be sent in other responses to the INVITE
(https://datatracker.ietf.org/doc/html/rfc3261#page-80). This simply allows the same media
channel to be established earlier in the lifetime of the call.

This method of exchanging ealry media is known as the Gateway Model. However,
[RFC3960](https://datatracker.ietf.org/doc/html/rfc3960) details how this is, "seriously
limited in the presence of forking", leading to media clipping. Since Matrix is fundamentally
multi-device and multi-user, these issues may be even more prevalent.

Furthermore, [RFC3959](https://datatracker.ietf.org/doc/html/rfc3959) explains that application
servers may not be able to produce an answer for the UAS due to end-to-end encryption. Since all
WebRTC calls use DTLS, we would expect this problem to occur in Matrix calls.

Moreover, the gateway model assumes that if, having started to receive early media from one
endpoint, another endpoint then answers, the UAC can simply switch streams and play the media
stream from the endpoint that answered. In WebRTC, this would mean supplying a different answer
from the one originally supplied and switching to a new offer from a different peer with a
different DTLS fingerprint. This may be viable using the 'pranswer' Session Description Type,
although may be considered somewhat of an edge case.

[RFC3960](https://datatracker.ietf.org/doc/html/rfc3960) proposes the Application Server model
for SIP early media to address these problems, and strongly recommends it for most situations.
This essentially establishes separate media sessions for each early media session and the main
media session by using multipart bodies for SIP message to send multiple session descriptions
per SIP message. This allows the media sessions to be distinct, solving the above problems.
However, it adds significant complexity and the gateway model is still widely used in practice.

## Proposal

This MSC proposes to allow early media in a manner similar to the gateway model above. We do this
by allowing an `m.call.negotiate` event to be sent by the callee before `m.call.answer`. The `type`
field MUST be set to `pranswer`. The caller should ignore `m.call.negotiate` events of any other
type before the `m.call.answer`. Clients using WebRTC compatible APIs should simply be able to
pass this SDP object into `setRemoteDescription` as-is. In fact, if clients do not explicitly
discard `m.call.negotiate` before an `m.call.answer`, they may already inadvertently support this
MSC.

The the same call is later answered with an `m.call.answer` event, the caller's client passes the
answer SDP to the WebRTC API just as before: it may do so since the previous SDP was of type
`pranswer` (https://datatracker.ietf.org/doc/html/rfc8829#section-5.6).

If the call is not successfully set up, the caller destroys the early media stream. The process of
tearing down the PeerConnection will do this anyway.

If a different device answers, the caller's client still passes the answer SDP to the WebRTC API as
before: this will cause the connection to the device that sent the pranswer to be aborted and
the connection restarted with the new device.

If the caller's client receives `pranswer` negotiate events from multiple callee devices, it selects
one arbitrarily (ie. most likely the first) and ignores the others.

Callee clients cannot assume that caller clients support this MSC and therefore must not assume
that the `pranswer` SDP has been processed (however if they see the ICE connection state change to
`connected`, they will know that it has).

It is suggested that the `pranswer` SDP be essentially the same as the `answer` SDP, therefore
for a normal, bidirectional media call, the `pranswer` would negotiate `sendrecv` media. This
means the media stream is started and ready to go as soon as the callee answers. It is, of course,
vital that the callee's client does not play the incoming audio or send any media not explicitly
intended to be early media (eg. keeps the user's micprophone muted) until the user has accepted the
call. Likewise it is generally advised for the caller's client to keep the user's outbound media
muted until the call is answered since users are likely to assume they cannot be heard, although
sometimes early media is used to gather information from callers (eg. PINs for calling cards):
this would generally be DTMF, but this may require exceptions to this rule.

It is strongly advised to use this only in setups where the callee is a single device and the only
user receiving the call, eg. when the callee is a PSTN gateway or similar. It is not intended for
use on regular clients due to the number of different devices that could potentially send `pranswer`s.

## Alternatives

This MSC opts for the simpler 'gateway model' despite the fact that some of some of its limitations
may be more of an issue in the Matrix protocol. The reasons for this are:

 * For interfacing with SIP, we would likely need to support this anyway since this is still quite
   commonly used.
 * It allows for a great deal of functionality with very little overhead, even if it may not be perfect.
   In many scenarios (eg. bridging) there is only one callee device and so one class of problems will
   never manifest.
 * This does not rule out an approach more like the Application Server method in the future, if necessary.
 * It is a very natural fit for the existing WebRTC `pranswer` semantics.

An alternative would be a proposal negotiating separate media sessions for each early media session and
the 'real' media session by the callee making a separate offer to the caller using different events types.

## Security considerations

Any client sending a `pranswer` should obviously bear in mind that this will reveal the device is online.
For this reason (and others, above) it is not advised for end-user clients to send `pranswer`s.

There are also obvious privacy concerns about establishing media sessions before a call is answered
if not done so carefully. Advice for handling this is given in the proposal section.

In the best case, this only allows a callee to send media to a callee without the caller's client UI
saying that the call is answered. This could still be somewhat surprising to an unsuspecting caller.

## Dependencies
Depends on [MSC2746](https://github.com/matrix-org/matrix-doc/pull/2746).
