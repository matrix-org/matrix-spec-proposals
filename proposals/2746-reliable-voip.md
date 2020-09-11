# MSC2746: Improved Signalling for 1:1 VoIP

Matrix has basic support for signalling 1:1 WebRTC calls, but has a number of shortcomings:

 * If several devices try to answer the same call, there is no way for them to determine clearly
   that the caller has set up the call with a different device, and no way for the caller to
   determine which candidate events map to which answer.
 * Hangup reasons are often incorrect.
 * There is confusion and no clear guidance on how clients should determine whether an incoming
   invite is stale or not.
 * There is no support for renegotiation of SDP, for changing ICE candidates / hold/resume
   functionality, etc.
 * There is no distinction between rejecting a call and ending it, which means that in trying
   to reject a call, a client can inadvertantly cause a call that has been sucessfully set up
   on a different device to be hung up.

## Proposal
### Change the `version` field in all VoIP events to `1`
This will be used to determine whether determine whether devices support this new version of the protocol.
If clients see events with `version` other than `0` or `1`, they should treat these the same as if they had
`version` == `1`.

### Add `invitee` field to `m.call.invite`
This allows for the following use cases:
 * Placing a call to a specifc user in a room where other users are also present.
 * Placing a call to oneself.

The field should be added for all invites where the target is a specific user. Invites without an `invitee`
field are defined to be intended for any member of the room other than the sender of the event. Clients
should consider an incoming call if they see a non-expired invite event where the `invitee` field is either
absent or equal to their user's Matrix ID, however they should evaluate whether or not to ring based on their
user's trust relationship with the caller, eg. ignoring call invites from users in public rooms that they have
no other connection with. As a starting point, it is suggested that clients ring for any call invite from a user
that they have a direct message room with. It is strongly recommended that when clients do not ring for an
incoming call invite, they still display the invite in the room and annotate that it was ignored.

### Add `party_id` to all VoIP events
Whenever a client first participates in a new call, it generates a `party_id` for itself to use for the
duration of the call. This needs to be long enough that the chance of a collision between multiple devices
both generating an answer at the same time generating the same party ID is vanishingly small: 8 uppercase +
lowercase alphanumeric characters is recommended. Parties in the call are identified by the tuple of
`(user_id, party_id)`.

The client  adds a `party_id` field containing this ID alongside the `user_id` field to all VoIP events it sends on the
call. Clients use this to identify remote echo of their own events, since a user may now call themselves,
they can no longer ignore events from their own user. This field also identifies different answers sent
by different clients to an invite, and matches `m.call.candidate` events to their respective answer/invite.

A client implementation may choose to use the device ID used in end-to-end cryptography for this purpose,
or it may choose, for example, to use a different one for each call to avoid lekaing information on which
devices were used in a call (in an unencrypted room) or if a single device (ie. access token were used to
send signalling for more than one call party.

### Introduce `m.call.select_answer`
This event is sent by the caller's client once it has chosen an answer. Its
`selected_party_id` field indicates the answer it's chosen (and has `call_id`
and its own `party_id` too). If the callee's client sees a `select_answer` for an answer
with party ID other than the one it sent, it ends the call and informs the user the call
was answered elsewhere. It does not send any events. Media can start flowing
before this event is seen or even sent.  Clients that implement previous
versions of this specification will ignore this event and behave as they did
before.

Example:
```
{
    "type": "m.call.select_answer",
    "content": {
        "call_id": "12345",
        "party_id": "67890",
        "selected_party_id": "111213",
    },
}
```

### Introduce `m.call.reject`

 * If the `m.call.invite` event has `version` `1`, a client wishing to reject the call
   sends an `m.call.reject` event. This rejects the call on all devices, but if the calling
   device sees an accept, it disregards the reject event and carries on. The reject has a
   `party_id` just like an answer, and the caller sends a `select_answer` for it just like an
   answer. If the other client that had already sent an answer sees the caller select the
   reject response instead of its answer, it ends the call.
 * If the `m.call.invite` event has `version` `0`, the callee sends an `m.call.hangup` event before.

Example:
```
{
    "type": "m.call.reject",
    "content" : {
        "version": 1,
        "call_id": "12345",
        "party_id": "67890",
    }
}
```

If the calling user chooses to end the call before setup is complete, the client sends `m.call.hangup`
as previously.

### Clarify what actions a client may take in response to an invite
The client may:
 * Attempt to accept the call by sending an answer
 * Actively reject the call everywhere: reject the call as per above, which will stop the call from
   ringing on all the user's devices and the caller's client will inform them that the user has
   rejected their call.
 * Ignore the call: send no events, but stop alerting the user about the call. The user's other
   devices will continue to ring, and the caller's device will continue to indicate that the call
   is ringing, and will time the call out in the normal way if no other device responds.

### Introduce more reason codes to `m.call.hangup`
 * `ice_timeout`: The connection failed after some media was exchanged (as opposed to current
   `ice_failed` which means no media connection could be established). Note that, in the case of
   an ICE renegotiation, a client should be sure to send `ice_timeout` rather than `ice_failed` if
   media had previously been received successfully, even if the ICE renegotiation itself failed.
 * `user_hangup`: Clients must now send this code when the user chooses to end the call, although
   for backwards compatability, a clients should treat an absence of the `reason` field as
   `user_hangup`.
 * `user_media_failed`: The client was unable to start capturing media in such a way as it is unable
   to continue the call.
 * `unknown_error`: Some other failure occurred that meant the client was unable to continue the call
   rather than the user choosing to end it.

### Introduce `m.call.negotiate`
This introduces SDP negotiation semantics for media pause, hold/resume, ICE restarts and voice/video
call up/downgrading. Clients should implement & honour hold functionality as per WebRTC's
recommendation: https://www.w3.org/TR/webrtc/#hold-functionality

If both the invite event and the accepted answer event have `version` equal to `1`, either party may
send `m.call.negotiate` with an `sdp` field to offer new SDP to the other party. This event has
`call_id` with the ID of the call and `party_id` equal to the client's party ID for that call.
The caller ignores any negotiate events with `party_id` not equal to the `party_id` of the
answer it accepted. Clients should use the `party_id` field to ignore the remote echo of their
own negotiate events.

This has a `lifetime` field as in `m.call.invite`, after which the sender of the negotiate event
should consider the negotiation failed (timed out) and the recipient should ignore it.

Example:
```
{
    "type": "m.call.negotiate",
    "content": {
        "call_id": "12345",
        "party_id": "67890",
        "sdp": "[some sdp]",
        "lifetime": 10000,
    }
}
```

### Designate one party as 'polite'
In line with WebRTC perfect negotiation (https://w3c.github.io/webrtc-pc/#perfect-negotiation-example)
we introduce rules to establish which party is polite. By default, the callee is the polite party.
In a glare situation, if the client receives an invite whilst preparing to send one, it becomes the callee
and therefore becomes the polite party. If an invite is received after the client has sent one, the
party whose invite had the lexicographically greater call ID becomes the polite party.

### Add explicit recommendations for call event liveness.
`m.call.invite` contains a `lifetime` field that indicates how long the offer is valid for. When
a client receives an invite, it should use the `age` field of the event plus the time since it
received the event from the homeserver to determine whether the invite is still valid. If the
invite is still valid *and will remain valid for long enough for the user to accept the call*,
it should signal an incoming call. The amount of time allowed for the user to accept the call may
vary between clients, for example, it may be longer on a locked mobile device than on an unlocked
desktop device.

The client should only signal an incoming call in a given room once it has completed processing the
entire sync response and, for encrypted rooms, attempted to decrypt all encrypted events in the
sync response for that room. This ensures that if the sync response contains subsequent events that
indicate the call has been hung up, rejected, or answered elsewhere, the client does not signal it.

If on startup, after processing locally stored events, the client determines that there is an invite
that is still valid, it should still signal it but only after it has completed a sync from the homeserver.

### Introduce recommendations for batching of ICE candidates
Clients should aim to send a small number of candidate events, with guidelines:
 * ICE candidates which can be discovered immediately or almost immediately in the invite/answer
   event itself (eg. host candidates). If server reflexive or relay candiates can be gathered in
   a sufficiently short period of time, these should be sent here too. A delay of around 200ms is
   suggested as a starting point.
 * The client should then allow some time for further candidates to be gathered in order to batch them,
   rather than sending each candidate as it arrives. A starting point of 2 seconds after sending the
   invite or 500ms after sending the answer is suggested as starting point (since a delay is natural
   anyway after the invite whilst the client waits for the user to accept it).

### Add DTMF
Add that Matrix clients can send DTMF as specified by WebRTC. The WebRTC standard as of August
2020 does not support receiving DTMF but a Matrix client can receive and interpret the DTMF sent
in the RTP payload.

### Deprecate `type` in `m.call.invite` and `m.call.answer`
These are redundant: clients should continue to send them but must not require
them to be present on events they receive.

### Specify exact grammar for VoIP IDs
`call_id`s and the newly introduced `party_id` are explicitly defined to be up to 32 characters
from the set of `A-Z` `a-z` `0-9` `.-_`.

## Potential issues
 * The ability to call yourself makes the protocol a little more complex for clients to implement,
   and is somewhat of a special case. However, some of the necessary additions are also required for
   other features so this MSC elects to make it possible.
 * Clients must make a decision on whether to ring for any given call: defining this in the spec
   would be cumbersome and would limit clients' ability to use reputation-based systems for this
   decision in the future. However, having a call ring on one client and not the other because one
   had categorised it as a junk call and not the other would be confusing for the user.

## Alternatives
 * We could define that the ID of a call is implcitly the event IDs of the invite event rather than
   having a specific `call_id` field. This would mean that a client would be unable to know the ID of
   a call before the remote echo of the invite came back, which could complicate implementations.
   There is probably no compelling reason to change this.
 * `m.call.select_answer` was chosen such that its name reflect the intention of the event. `m.call.ack`
   is more succinct and mirrors SIP, but this MSC opts for the more descriptive name.
 * This MSC elects to allow invites without an `invitee` field to mean a call for anyone in the room.
   This could be useful for hunt group style semantics where an incoming call causes many different
   users' phones to ring and any one of them may pick up the call. This does mean clients will need
   to not blindly ring for any call invites in any room, since this would make unsolicited calls in
   easy in public rooms. We could opt to leave this out, or make it more explicit with a specific value
   for the `invitee` field.
 * `party_id` is one of many potential solutions: callees could add `answer_id`s to their events and
   callers could be identified by the lack of an `answer_id`. An explicit field on every event may be
   easier to comprehend, less error-prone and clearer in the backwards-compatibility scenario.
 * We could make `party_id`s more prescriptive, eg. the caller could always have a `party_id` of the
  empty string, the word `caller` or equal to the `call_id`, which may make debugging simpler.

## Security considerations
 * IP addresses remain in the room in candidates, as they did in the previous version of the spec.
   This is not ideal, but alternatives were either sending candidates over to-device messages
   (would slow down call setup because a target device would have to be established before sending
   candidates) or redacting them afterwards (the volume of events sent during calls can already
   cause rate limiting issues and this would exacerbate this).
 * Clients must take care to not ring for any call, as per the 'alternatives' section.
