# MSC3401: Native Group VoIP signalling

## Problem

VoIP signalling in Matrix is currently conducted via timeline events in a 1:1 room.
This has some limitations, especially if you try to broaden the approach to multiparty VoIP calls:

 * VoIP signalling can generate a lot of events as candidates are incrementally discovered, and for rapid call setup these need to be relayed as rapidly as possible.
   * Putting these into the room timeline means that if the client has a gappy sync, for VoIP to be reliable it will need to go back and fill in the gap before it can process any VoIP events, slowing things down badly.
   * Timeline events are (currently) subject to harsh rate limiting, as they are assumed to be a spam vector.
 * VoIP signalling leaks IP addresses.  There is no reason to keep these around for posterity, and they should only be exposed to the devices which care about them.
 * Candidates are ephemeral data, and there is no reason to keep them around for posterity - they're just clogging up the DAG.

Meanwhile we have no native signalling for group calls at all, forcing you to instead embed a separate system such as Jitsi, which has its own dependencies and doesn't directly leverage any of Matrix's encryption, decentralisation, access control or data model.

## Proposal

This proposal provides a signalling framework using to-device messages which can be applied to native Matrix 1:1 calls, full-mesh calls, SFU calls, cascaded SFU calls and in future MCU calls, and hybrid SFU/MCU approaches. It replaces the early flawed sketch at [MSC2359](https://github.com/matrix-org/matrix-doc/pull/2359).

This does not immediately replace the current 1:1 call signalling, but may in future provide a migration path to unified signalling for 1:1 and group calls.

Diagramatically, this looks like:

1:1:
```
          A -------- B
```

Full mesh between clients
```
          A -------- B
           \       /
            \     /
             \   /
              \ /
               C
```

SFU (aka Focus):
```
          A __    __ B
              \  /   
               F 
               | 
               |
               C

Where F is an SFU focus
```

Cascaded decentralised SFU:
```
     A1 --.           .-- B1
     A2 ---Fa ----- Fb--- B2
           \       /
            \     /
             \   /
              \ /
               Fc
              |  |
             C1  C2

Where Fa, Fb and Fc are SFU foci, one per homeserver, each with two clients.
```

### m.call state event

The user who wants to initiate a call sends a `m.call` state event into the room to inform the room participants that a call is happening in the room. This effectively becomes the placeholder event in the timeline which clients would use to display the call in their scrollback (including duration and termination reason using `m.terminated`). Its body has the following fields:

 * `m.intent` to describe the intended UX for handling the call.  One of:
     * `m.ring` if the call is meant to cause the room participants devices to ring (e.g. 1:1 call or group call)
     * `m.prompt` is the call should be presented as a conference call which users in the room are prompted to connect to
     * `m.room` if the call should be presented as a voice/video channel in which the user is immediately immersed on selecting the room.
 * `m.type` to say whether the initial type of call is voice only (`m.voice`) or video (`m.video`).  This signals the intent of the user when placing the call to the participants (i.e. "i want to have a voice call with you" or "i want to have a video call with you") and warns the receiver whether they may be expected to view video or not, and provide suitable initial UX for displaying that type of call... even if it later gets upgraded to a video call.
 * `m.terminated` if this event indicates that the call in question has finished, including the reason why. (A voice/video room will never terminate.) (do we need a duration, or can we figure that out from the previous state event?).  
 * `m.name` as an optional human-visible label for the call (e.g. "Conference call").
 * `m.foci` as an optional list of recommended SFUs that the call initiator can recommend to users who do not want to use their own SFU (because they don't have one, or because they would be the only person on their SFU for their call, and so choose to connect direct to save bandwidth).
 * The State key is a unique ID for that call. (We can't use the event ID, given `m.type` and `m.terminated` is mutable).  If there are multiple non-terminated conf ID state events in the room, the client should display the most recently edited event.

For instance:

```jsonc
{
    "type": "m.call",
    "state_key": "cvsiu2893",
    "content": {
        "m.intent": "m.room",
        "m.type": "m.voice",
        "m.name": "Voice room",
        "m.foci": [
            "@sfu-lon:matrix.org",
            "@sfu-nyc:matrix.org",
        ],
    }
}
```

We mandate at most one call per room at any given point to avoid UX nightmares - if you want the user to participate in multiple parallel calls, you should simply create multiple rooms, each with one call.

### Call participation

Users who want to participate in the call declare this by publishing a `m.call.member` state event using their matrix ID as the state key (thus ensuring other users cannot edit it).  The event contains a timestamp named `m.expires_ts` describing when this data should be considered stale, and an array `m.calls` of objects describing which calls the user is participating in within that room.  This array must contain one item (for now).

When sending an `m.call.member` event, clients should choose a reasonable value for `m.expires_ts` in case they go offline unexpectedly. If the user stays connected for longer than this time, the client must actively update the state event with a new expiration timestamp.

`m.call.member` state events must be ignored if the `m.expires_ts` field indicates they have expired, or if their user's `m.room.member` event's membership field is not `join`.

The fields within the item in the `m.calls` contents are:

 * `m.call_id` - the ID of the conference the user is claiming to participate in.  If this doesn't match an unterminated `m.call` event, it should be ignored.
 * `m.foci` - Optionally, if the user wants to be contacted via an SFU rather than called directly (either 1:1 or full mesh), the user can also specify the SFUs their client(s) are connecting to.
 * `m.devices` - The list of the member's active devices in the call. A member may join from one or more devices at a time, but they may not have two active sessions from the same device. Each device contains the following properties:
   * `device_id` - The device id to use for to-device messages when establishing a call
   * `session_id` - A unique identifier used for resolving duplicate sessions from a given device. When the `session_id` field changes from an incoming `m.call.member` event, any existing calls from this device in this call should be terminated. `session_id` should be generated once per client session on application load.
   * `feeds` - Contains an array of feeds the member is sharing and the opponent member may reference when setting up their WebRTC connection.
     * `purpose` - Either `m.usermedia` or `m.screenshare` otherwise the feed should be ignored.

For instance:

```jsonc
{
    "type": "m.call.member",
    "state_key": "@matthew:matrix.org",
    "content": {
        "m.calls": [
            {
                "m.call_id": "cvsiu2893",
                "m.foci": [
                    "@sfu-lon:matrix.org",
                    "@sfu-nyc:matrix.org",
                ],
                "m.devices": [
                    {
                        "device_id": "ASDUHDGFYUW", // Used to target to-device messages
                        "session_id": "GHKJFKLJLJ", // Used to resolve duplicate calls from a device
                        "feeds": [
                            {
                                "purpose": "m.usermedia",
                                "id": "qegwy64121wqw", // WebRTC MediaStream id
                                "tracks": [
                                    {
                                        "kind": "audio",
                                        "id": "zvhjiwqsx", // WebRTC MediaStreamTrack id
                                        "label": "Sennheiser Mic",
                                        "settings": { // WebRTC MediaTrackSettings object
                                            "channelCount": 2,
                                            "sampleRate": 48000,
                                            "m.maxbr": 32000, // Matrix-specific extension to advertise the max bitrate of this track
                                        }
                                    },
                                    {
                                        "kind": "video",
                                        "id": "zbhsbdhzs",
                                        "label": "Logitech Webcam",
                                        "settings": {
                                            "width": 1280,
                                            "height": 720,
                                            "facingMode": "user",
                                            "frameRate": 30.0,
                                            "m.maxbr": 512000,
                                        }
                                    },
                                ],
                            },
                            {
                                "purpose": "m.screenshare",
                                "id": "suigv372y8378",
                                "tracks": [
                                    {
                                        "kind": "video",
                                        "id": "xbhsbdhzs",
                                        "label": "My Screenshare",
                                        "settings": {
                                            "width": 3072,
                                            "height": 1920,
                                            "cursor": "moving",
                                            "displaySurface": "monitor",
                                            "frameRate": 30.0,
                                            "m.maxbr": 768000,
                                        }
                                    },
                                ]
                            }
                        ]
                    }
                ]
            }
        ],
        "m.expires_ts":  1654616071686
    }
}
```

This builds on MSC #3077, which describes streams in `m.call.*` events via a `sdp_stream_metadata` field, but providing the full set of information needed for all devices in the room to know what feeds are available in the group call without having to independently discover them from the SFU.

** TODO: Add tracks field **
** TODO: Add bitrate/format fields **

Clients should do their best to ensure that calls in `m.call.member` state are removed when the member leaves the call. However, there will be cases where the device loses network connectivity, power, the application is forced closed, or it crashes. If the `m.call.member` state has stale device data the call setup will fail. Clients should re-attempt invites up to 3 times before giving up on calling a member.

### Call setup

Call setup then uses the normal `m.call.*` events, except they are sent over to-device messages to the relevant devices (encrypted via Olm).  This means:

 * When initiating a 1:1 call, the `m.call.invite` is sent to the devices listed in `m.call.member` event's `m.devices` array using the `device_id` field.
 * `m.call.*` events sent via to-device messages should also include the following properties in their content:
   * `conf_id` - The group call id listed in `m.call`
   * `dest_session_id` - The recipient's session id. Incoming messages with a `dest_session_id` that doesn't match your current session id should be discarded.
 * In addition to the fields above `m.call.invite` events sent via to-device messages should include the following properties  :
   * `device_id` - The message sender's device id. Used by the opponent member to send response to-device signalling messages even if the `m.call.member` event has not been received yet.
   * `sender_session_id` - Like the `device_id` the `sender_session_id` is used by the opponent member to filter out messages unrelated to the sender's session even if the `m.call.member` event has not been received yet.
 * For 1:1 calls, we might want to let the to-device messages flow and cause the client to ring even before the `m.call` event propagates, to minimise latency.  Therefore we'll need to include an `m.intent` on the `m.call.invite` too.
 * When initiating a group call, we need to decide which devices to actually talk to.
     * If the client has no SFU configured, we try to use the `m.foci` in the `m.call` event.
         * If there are multiple `m.foci`, we select the closest one based on latency, e.g. by trying to connect to all of them simultaneously and discarding all but the first call to answer.
         * If there are no `m.foci` in the `m.call` event, then we look at which foci in `m.call.member` that are already in use by existing participants, and select the most common one.  (If the foci is overloaded it can reject us and we should then try the next most populous one, etc).
         * If there are no `m.foci` in the `m.call.member`, then we connect full mesh.
         * If subsequently `m.foci` are introduced into the conference, then we should transfer the call to them (effectively doing a 1:1->group call upgrade).
     * If the client does have an SFU configured, then we decide whether to use it. 
         * If other conf participants are already using it, then we use it.
         * If there are other users from our homeserver in the conference, then we use it (as presumably they should be using it too)
         * If there are no other `m.foci` (either in the `m.call` or in the participant state) then we use it.
         * Otherwise, we save bandwidth on our SFU by not cascading and instead behaving as if we had no SFU configured.
 * We do not recommend that users utilise an SFU to hide behind for privacy, but instead use a TURN server, only providing relay candidates, rather than consuming SFU resources and unnecessarily mandating the presence of an SFU.

TODO: spec how clients discover their homeserver's preferred SFU foci

Originally this proposal suggested that foci should be identified by their `(user_id, device_id)` rather than just their user_id, in order to ensure convergence on the same device.  In practice, this is unnecessary complication if we make it the SFU implementor's problem to ensure that either only one device is logged in per SFU user - or instead you cluster the SFU devices together for the same user.  It's important to note that when calling an SFU you should call `*` devices.

### SFU control

SFUs are Selective Forwarding Units - a server which forwarding WebRTC streams between peers (which could be clients or SFUs or both).  To make use of them effectively, peers need to be able to tell the SFU which streams they want to receive, and the SFU must tell the peers which streams it wants to be sent.  We also need a way of telling SFUs which other SFUs to connect ("cascade") to.

The client does this by establishing an optional datachannel connection to the SFU using normal `m.call.invite`, in order to perform low-latency signalling to rapidly select streams.

To select a stream over this channel, the peer sends:

```jsonc
{
    "op": "select",
    "conf_id": "cvsiu2893",
    "start": [
        { "stream_id": "qegwy64121wqw", "track_id": "zbhsbdhwe" }
        { "stream_id": "qegwy64121wqw", "track_id": "zbhsbdhzs" }
    ],
    "stop": [
        { "stream_id": "suigv372y8378", "track_id": "xbhsbdhzs" }
    ]    
}
```

All streams are sent within a single media session (rather than us having multiple sessions or calls), and there is no difference between a peer sending simulcast streams from a webcam versus two SFUs trunking together.

If no DC is established, then 1:1 calls should send all streams without prompting, and SFUs should send no streams by default.

If you are using your SFU in a call, it will need to know how to connect to other SFUs present in order to participate in the fullmesh of SFU traffic (if any).  One option here is for SFUs to act as an AS and sniff the `m.call.member` traffic of their associated server, and automatically call any other `m.foci` which appear.  (They don't need to make outbound calls to clients, as clients always dial in).  Otherwise, we could consider an `"op": "connect"` command sent by clients, but then you have the problem of deciding which client(s) are responsible for reminding the SFU to connect to other SFUs.  Much better to trust the server.

Also, in order to authenticate that only legitimate users are allowed to subscribe to a given conf_id on an SFU, it would make sense for the SFU to act as an AS and sniff the `m.call` events on their associated server, and only act on to-device `m.call.*` events which come from a user who is confirmed to be in the room for that `m.call`.  (In practice, if the conf is E2EE then it's of limited use to connect to the SFU without having the keys to decrypt the traffic, but this feature is desirable for non-E2EE confs and to stop bandwidth DoS)

XXX: define how these DC messages muxes with other traffic, and consider what message encoding to actually use.

TODO: spell out how this works with active speaker detection & associated signalling

## Example Diagrams

**Legend**

| Arrow Style | Description |
|-------------|-------------|
| Solid | [State Event](https://spec.matrix.org/latest/client-server-api/#types-of-room-events) |
| Dashed | [Event (sent as to-device message)](https://spec.matrix.org/latest/client-server-api/#send-to-device-messaging) |


### Basic Call

```mermaid
sequenceDiagram
    autonumber
    participant Alice
    participant Room
    participant Bob
    Alice->>Room: m.call
    Alice->>Room: m.call.member
    Bob->>Room: m.call.member
    Alice-->>Bob: m.call.invite
    Alice-->>Bob: m.call.candidates
    Alice-->>Bob: m.call.candidates
    Bob-->>Alice: m.call.answer
    Bob-->>Alice: m.call.candidates
    Alice-->>Bob: m.call.select_answer
```

## Encryption

We get E2EE for 1:1 and full mesh calls automatically in this model.

However, when SFUs are on the media path, the SFU will necessarily terminate the SRTP traffic from the peer, breaking E2EE.  To address this, we apply an additional end-to-end layer of encryption to the media using [WebRTC Encoded Transform](https://github.com/w3c/webrtc-encoded-transform/blob/main/explainer.md) (formerly Insertable Streams) via [SFrame](https://datatracker.ietf.org/doc/draft-omara-sframe/).

In order to provide PFS, The symmetric key used for these stream from a given participating device is a megolm key. Unlike a normal megolm key, this is shared via `m.room_key` over Olm to the devices participating in the conference including an `m.call_id` and `m.room_id` field on the key to correlate it to the conference traffic, rather than using the `session_id` event field to correlate (given the encrypted traffic is SRTP rather than events, and we don't want to have to send fake events from all senders every time the megolm session is replaced).

The megolm key is ratcheted forward for every SFrame, and shared with new participants at the current index via `m.room_key` over Olm as per above.  When participants leave, a new megolm session is created and shared with all participants over Olm.  The new session is only used once all participants have received it.

## Potential issues

To-device messages are point-to-point between servers, whereas today's `m.call.*` messages can transitively traverse servers via the room DAG, thus working around federation problems.  In practice if you are relying on that behaviour, you're already in a bad place.

The SFUs participating in a conference end up in a full mesh.  Rather than inventing our own spanning-tree system for SFUs however, we should fix it for Matrix as a whole (as is happening in the LB work) and use a Pinecone tree or similar to decide what better-than-full-mesh topology to use.  In practice, full mesh cascade between SFUs is probably not that bad (especially if SFUs only request the streams over the trunk their clients care about) - and on aggregate will be less obnoxious than all the clients hitting a single SFU.

SFrame mandates its own ratchet currently which is almost the same as megolm but not quite.  Switching it out for megolm seems reasonable right now (at least until MLS comes along)

## Alternatives

There are many many different ways to do this.  The main other alternative considered was not to use state events to track membership, but instead gossip it via either to-device or DC messages between participants.  This fell apart however due to trust: you effectively end up reinventing large parts of Matrix layered on top of to-device or DC.  So you might as well publish and distribute the participation data in the DAG rather than reinvent the wheel.

Another option is to treat 1:1 (and full mesh) entirely differently to SFU based calling rather than trying to unify them.  Also, it's debatable whether supporting full mesh is useful at all.  In the end, it feels like unifying 1:1 and SFU calling is for the best though, as it then gives you the ability to trivially upgrade 1:1 calls to group calls and vice versa, and avoids maintaining two separate hunks of spec.  It also forces 1:1 calls to take multi-stream calls seriously, which is useful for more exotic capture devices (stereo cameras; 3D cameras; surround sound; audio fields etc).

An alternative to to-device messages is to use DMs.  You still risk gappy sync problems though due to lots of traffic, as well as the hassle of creating DMs and requiring canonical DMs to set up the calls.  It does make debugging easier though, rather than having to track encrypted ephemeral to-device msgs.

## Security considerations

State events are not encrypted currently, and so this leaks that a call is happening, and who is participating in it, and from which devices.

Malicious users could try to DoS SFUs by specifying them as their foci.

SFrame E2EE may go horribly wrong if we can't send the new megolm session fast enough to all the participants when a participant leave (and meanwhile if we keep using the old session, we're technically leaking call media to the parted participant until we manage to rotate).

Need to ensure there's no scope for media forwarding loops through SFUs.

Malicious users in a room could try to sabotage a conference by overwriting the `m.call` state event of the current ongoing call.

Too many foci will chew bandwidth due to fullmesh between them.  In the worst case, if every use is on their own HS and picks a different foci, it degenerates to a fullmesh call (just serverside rather than clientside).  Hopefully this shouldn't happen as you will converge on using a single SFU with the most clients, but need to check how this works in practice.

## Unstable prefix

| stable event type | unstable event type |
|-------------------|---------------------|
| m.call            | org.matrix.msc3401.call |
| m.call.member     | org.matrix.msc3401.call.member |
