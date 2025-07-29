# MSC4143: MatrixRTC

MatrixRTC is short for Matrix real time communication.
This MSC defines the modules with which the Matrix real time system is built.

MatrixRTC specifies how a real time session is described in a room and how matrix users can connect to
a session.

The MatrixRTC specification is separated into different modules:


- The MatrixRTC room state that defines the state of the real time session.\
  It is the source of truth for:
  - Who is part of a session
  - Who is connected via what technology/backend
  - Metadata per device used by other participants to decide whether the streams
    from this source are of interest / need to be subscribed.
- The MatrixRTC backend.
  - Allows for multiple backend implementations to be used.
  - It defines how to discover the available backend(s).
  - It defines how to connect the participating peers.
  - Defines how to connect to a server/other peers, how to update the connection,
    how to subscribe to different streams...
  - A proposal utilising LiveKit is the standard for this as of writing.
  - Another planned backend is a full mesh implementation based on [MSC3401](https://github.com/matrix-org/matrix-spec-proposals/pull/3401).
- The MatrixRTC application.
  - Each application type can have it's own spec.
  - Voice and video conferencing can be done with an application of type `m.call`
  - The application defines all the details of the RTC experience:
    - How to interpret the metadata of the member events.
    - What streams to connect to.
    - What data in which format to sent over the RTC channels.
    - What MatrixRTC backends are supported.
- End-to-end encryption of media streams

This MSC will focus on the Matrix room state which is responsible for the high
level signalling of a RTC session:

## Proposal

Each RTC session is made out of a collection of `m.rtc.member` room state events.
Each `m.rtc.member` event defines who (the `member`) is a participant of which session (the `session`).

### The MatrixRTC room state

All data related to a MatrixRTC session
(current session, sessions history, join/leave events, ...) only
requires one event type.

(current session, sessions history, join/leave events, ...) only
require one event type:.

We use a set of `m.rtc.member` (one for each participant) state events to represent a session.

based on the content a `m.rtc.member` state event can either represent a connected or a disconnected member.

#### Joining a session

Sending a well-formed `m.rtc.member` event that describes a connected state for a state key that is not yet used or contains a disconnected `m.rtc.member` event represents a join action. 

The fields are as follows:

- `member` required object - describes the participant of the RTC session:
  - `id` required string - a unique identifier for this session membership as defined above. Recommended to be a UUID. It can be reused if the user leaves and rejoins the session.
  It should be unique across all devices of the user. TODO: define grammar
  - `device_id` required string - the Matrix device ID of the device that is joining the session. This is used when sending
    [to-device messages](https://spec.matrix.org/v1.11/client-server-api/#send-to-device-messaging).
  - `user_id` required string - the Matrix user ID of the user that is joining the session. This is needed as we cannot rely
    on the owner of state event as it might have been modified by an admin or similar.
- `session` required object - an object that is used to uniquely identify this session across RTC member events
of the Matrix room:
  - `application` required string - a recognised application type. e.g. `m.call` as linked below
  - additional fields as defined by the application type
- `created_ts` - timestamp in milliseconds since UNIX epoch.
  - this should **not** be present the first time that the `m.rtc.member` event is sent.
  - if the `m.rtc.member` event is sent again, the `created_ts` should be populated with the `origin_server_ts`
    that was given to the previous version of the state event.
- `focus_active` required Focus object - specifies the algorithm that defines how to choose a Focus for this member. See below for details.
- `foci_preferred` required array of Focus objects - specifies the input data for this algorithm contributed by this member. See below for details.

Additional fields may be added depending on the application type.

A full `m.rtc.member` state event for a joined member looks like this:

```json5
// event type: "m.rtc.member"
// state key: see next section for definition
{
  "session": {
    "application": "m.call"
    // further fields for the application
  },
  "member": {
    "id": "xyzABCDEF10123",
    "device_id": "DEVICEID",
    "user_id": "@user:matrix.domain"
  },
  "created_ts": Time | undefined,
  "focus_active": {...FOCUS_A},
  "foci_preferred": [
    {...FOCUS_1},
    {...FOCUS_2}
  ]
}
```

This gives us the information, that user: `@user:matrix.domain` with member ID `DEVICEID_m:call_123456789`
is part of a session identified by `{}` using application of type `m.call` connected over `FOCUS_A`.
This is sufficient information for another room member to detect the running session and join it.

`created_ts` is an optional property that caches the time of creation. It is not required
for an event that, has not yet been updated, there the `origin_server_ts` is used.

> [!NOTE]
> We introduce `created_ts()` as the notation for `created_ts ?? origin_server_ts`

Once the event gets updated the `origin_server_ts` needs to be copied into the `created_ts` field.
An existing `created_ts` field implies that this is a state event updating the current session
and a missing `created_ts` field implies that it is a join state event.
All membership events that belong to one member session can be grouped with the index
`created_ts()`+`state_key`. This is why the `m.rtc.member` events deliberately do NOT include something akin to a `membership_id`.

Other then the membership sessions, there is **no event** to represent a RTC session (containing all members).
This event would include shared information where it is not trivial to decide who has authority over it.
Instead the session is a computed value based on `m.rtc.member` events.
The list of events with the same `session` content represent one session.
This array allows to compute fields like participant count, start time etc.

Based on the value of `application`, the event might include additional parameters
to provide additional session parameters.

> A [Third Room](https://thirdroom.io) like experience could include the information of an approximate position
> on the map, so that clients can omit connecting to participants that are not in their
> area of interest.

#### State key for `m.rtc.member`

The state key is generated from the `member` field of the `m.rtc.member` event.

We want to choose a state key that is compatible with whichever state protection proposal is accepted to ensure that
users cannot modify one another's sessions.

For [MSC3757](https://github.com/matrix-org/matrix-spec-proposals/pull/3757) we generate the state key by
concatenating the following strings:

- the Matrix ID of the user
- an `_` (underscore)
- the `member`.`id` field

For example with a `member`.`id` of `xyzABCDEF10123` for user `@user:matrix.domain` the state key would be `@user:matrix.domain_xyzABCDEF10123`.

For a client parsing the state key we would treat anything before the first `_` as the Matrix ID of the user
and anything after as the `member`.`id` field.

#### Leaving a session

Sending an empty `m.rtc.member` event represents a leave action. The state key must be the same as boefore

There is an optional `leave_reason` field that can be used to provide a reason for leaving the session:

- `leave_reason` optional string - one of: `lost_connection`

An example of leaving a session where the user explicitly disconnects:

```json5
// event type: "m.rtc.member"
// state key: "@user:matrix.domain_xyzABCDEF10123"
{
}
```

The client should use the `prev_content` field of the [room state event](https://spec.matrix.org/v1.11/client-server-api/#room-event-format)
to determine the details of the leave event.

For example:

```json5
// event type: "m.rtc.member"
// state key: "@user:matrix.domain_xyzABCDEF10123"
{
  "content": {
    "leave_reason": "lost_connection"
  },
  "prev_content": {
    "session": {
      "application": "m.call",
      "call_id": ""
    },
    "member": {
      "id": "xyzABCDEF10123",
      "device_id": "DEVICEID",
      "user_id": "@user:matrix.domain"
    },
    "created_ts": 123456,
    "focus_active": {...FOCUS_A},
    "foci_preferred": [
      {...FOCUS_1},
      {...FOCUS_2}
    ]
  }
}
```

#### Reliability requirements for the room state

Room state is a very well suited place to store the data for a MatrixRTC session.
It allows:

- The client to determine current ongoing sessions without loading history for every room.
  Or doing additional work other then the sync loop that needs to run anyways.
- The client can compute/access data of past sessions without any additional redundant data.
- Sessions (start/end/participant count) are federated and there is not redundant data storage that
  could result in conflicts, or can get out of sync. The room state events are part of the DAG and this
  is solved like any other Persistent Data Unit (PDU) in Matrix.

However, a challenging circumstance with using the room state to represent a session is
the disconnection behaviour. If the client disconnects from a call because of a network issue,
an application crash or a user forcefully quitting the client, the room state cannot be updated anymore.
The client is required to leave by sending a new empty state which cannot happen once connection is lost.

If the state is not updated correctly we end up with a room state that is not
correctly representing the current RTC session state. Historic and current MatrixRTC session data would be broken.

For an acceptable solution, the following requirements need to be taken into consideration:

- Room state is set to empty if the client looses connection. (A heartbeat like system is desired)
- The best source of truth for a call participation is a working connection to the SFU.
  It is desired that the disconnect of the member on the SFU gets propagated to the room state.
- It should be possible to updated the room state without the client being online.
- All this should be compatible when Matrix uses cryptographic identities.

[MSC4140](https://github.com/matrix-org/matrix-spec-proposals/pull/4140) proposes a concept to
delay the leave events until one of the leave conditions (heartbeat or SFU disconnect) occur
and fulfil all of the these requirements.

A MatrixRTC client has to first send/schedule the following delayed leave event:

```json5
// event type: "m.rtc.member"
// state key: "@user:matrix.domain_xyzABCDEF10123"
{
  "leave_reason": "lost_connection"
}
```

only after that the actual state event can be sent, so that we guarantee that the state will be empty eventually.
The `leave_reason` is added so clients can be more verbal about why a user disconnected from a call.
It allows to communicate with other participants in a session if the user has disconnected intentionally or lost connection.

#### Session history

Since there is no single entry for a historic session (because of the ownership discussion),
historic sessions need to be computed and most likely cached on the client.

Each state event can either mark a join or leave:

- join: `prev_state.session != current_state.session` &&
  `current_state.session != undefined`
  (where an empty `m.rtc.member` event would imply `state.session == undefined`)
- leave: `prev_state.session != current_state.session` &&
  `current_state.session == undefined`

Based on this one can find user sessions. (The range between a join and a leave
event) of specific times.
The collection of all overlapping user sessions with the same `session` contents
define one MatrixRTC history event.

### The RTC backend

Backend **infrastructure** in this context can be anything that can serve as the backend for a
MatrixRTC session. In most cases this is a SFU. But also a full mesh implementation could
be an infrastructure. Not all kind of infrastructure require a way of sourcing a backend resource
(e.g. full-mesh). In this MSC we only refer to infrastructure where it is necessary to have access to additional
data to participate in the MatrixRTC session.

The backend is referred to as a Focus or as Foci in plural.

Note that these backends are independent of the application (e.g. `m.call`) being used in the session.

A Focus is represented as a JSON object with one mandatory field:

- `type` required string: The type of the Focus as defined by an RTC backend..

Additional fields will be present depending on `type`.

Only users with the same type can connect in one session. If a frontend does
not support the used type they cannot connect.

Each Focus type will get its own MSC in which the detailed procedure to get from
the foci information to working WebRTC connections to the streams of all the
participants is explained.

Foci are represented in three places:

- `focus_active` of `m.rtc.member` state event - specifies the algorithm that defines how to choose a Focus for this member.
- `foci_preferred` of `m.rtc.member` state event- specifies the input data for this algorithm contributed by this member.
- `m.rtc_foci` of the `.well-known/matrix/client` - specifies the list of available Foci for the homeserver.

The `focus_active` algorithm needs to be designed so that all participants converge to the same SFU/Focus.

The following Focus `type` values are defined:

- `livekit` - a backend using the [LiveKit](https://livekit.io/) SFU as described in
  [MSC4195](https://github.com/matrix-org/matrix-spec-proposals/pull/4195).
- `full_mesh` - a backend using a full-mesh approach based on [MSC3401](https://github.com/matrix-org/matrix-spec-proposals/pull/3401).

#### Choosing the value of `foci_preferred` for the `m.rtc.member` state event

At some point session participants have to decide/propose which Focus they will use.

Based on the Focus type and application choosing the method by which the contents of the `foci_preferred` field on the `m.rtc.member`
can be different.

There are three guidelines which should be obeyed by a client  when building the `foci_preferred` list:

1. It is always desired to have as few Focus switches as possible.

If there are other participants on the session (i.e. other `m.rtc.member` events) the client should calculate what the Focus it should connect to
based on the `m.rtc.member` events for the existing participants.
This should happen reactively on each `m.rtc.member` state event change.
Each MatrixRTC frontend is responsible that it can deal with focus switches based on changing state gracefully. It is part of the design of MatrixRTC and a requirement for a eventually consistent distributed system.

The calculated Focus should then be present at the start of the `foci_preferred` list.

2. The client should lookup the suggested foci from the homeserver `.well-known/matrix/client` as defined below.

MatrixRTC is designed around the same culture that makes Matrix possible: A large amount of infrastructure in the form of homeservers is provided by the users.

To achieve a stable and healthy ecosystem backend RTC infrastructure should be thought of as a part of a homeserver.

It is very similar to a TURN server: mostly traffic and little CPU load.

To not end up in a world where each user is only using one central SFU but where the traffic
is split over multiple SFU's it is important that we leverage the SFU distribution on the
homeserver federation.

These proposals from **your own** homeserver should come next in the `foci_preferred` list of the member event.

3. Clients should not use a hard-coded Focus.

Looking up the preferred Foci from a client is toxic to a federated system. If the majority of users
decide to use the same client all of the users will use one Focus. This destroys the passive security mechanism, that
each instance is not an interesting attack vector since it is only a fraction of the network.
Additionally it will result in poor performance if every user on Matrix would use the same Focus.

However, there are cases where this is acceptable:

- Transitioning to MatrixRTC. Here it might be beneficial to have a client that has a fallback Focus
  so calls also work with homeservers not supporting it.
- For testing purposes where a different Focus should be tested but one does not want to touch the .well-known
- For custom deployments that benefit from having the Focus configuration on a per client basis instead of per homeserver.

Therefore, if a client does use a hard-coded Focus it should come last in the `foci_preferred` list.

#### Discovery of Foci using `.well-known/matrix/client`

> [!NOTE]
> Backend **infrastructure** in this context can be anything that can serve as the backend for a
> MatrixRTC session. In most cases this is a SFU. But also a full mesh implementation could
> be an infrastructure. Not all kind of infrastructure require a way of sourcing a backend resource
> (e.g. full-mesh). In this MSC we only refer to infrastructure where it is necessary to have access to additional
> data to participate in the MatrixRTC session.

We use a `m.rtc_foci` key in the homeserver `.well-known/matrix/client` that can be used to expose
a sorted (by priority) list of Focus description objects.

For example in generic form:

```json5
{
  "m.rtc_foci": [
    {
      "type": "some-focus-type",
      "additional-type-specific-field": "https://my_focus.domain",
      "another-additional-type-specific-field": ["with", "Array", "type"]
    }
  ]
}
```

Or a concrete example for a `livekit` Focus:

```json5
{
  "m.rtc_foci": [
    {
      "type":"livekit",
      "livekit_service_url":"https://livekit-jwt.call.element.io"
    }
  ]
}
```

### The RTC application types

Each application type might have its own specification in how the different streams
are interpreted and even what Focus type to use. This makes this proposal extremely
flexible. A Jitsi conference could be added by introducing a new `application`
and a new Focus type and would be MatrixRTC compatible. It would not be compatible
with applications that do not use the Jitsi Focus but clients would know that there
is an ongoing session of unknown type and unknown Focus and could display/represent
this in the user interface.

To make it easy for clients to support different application types, the recommended
approach is to provide a Matrix widget for each application type. This way the
client developers can use the widget as the first implementation if they want to
support this RTC application type.

Each application should get its own MSC in which the all the additional
fields are explained and how the communication with the possible foci is
defined:

- `m.call` - voice and video conferencing described by [MSC4196](https://github.com/matrix-org/matrix-spec-proposals/pull/4196).

#### Interoperability between applications

There is a use-case in which a `m.call` app might want to participate in a session of type (application) `custom-call-with-more-features`. A native mobile matrix client might support `m.call` and is at hand to join the feature rich application/session.

There could be fallback mechanisms but the most flexible approach is to treat it per application type. If it makes sense for an application type to fully conform to `m.call` a client that can connect to an `m.call` RTC session (application) could claim that it is also compatible with `custom-call-with-more-features` . It is than the job of the `custom-call-with-more-features` session type (application) to define some kind of feature list so that it can tell if users are joining with an m.call client or a dedicated `custom-call-with-more-features` client.

### End-to-end encryption of media streams

We define how the key material is shared between the participants of the call to facilitate end-to-end encryption of the media streams.

Calls started in non-encrypted room will be non-encrypted. Calls started in encrypted rooms will be encrypted.

The backend (e.g. LiveKit) MSC defines how the key material is actually used. E.g. The RTC client will generate a random 256 key material, then the application
can use this input material to generate the needed secrets (by stretching/HKDF as see fit).

#### Per-participant sender key

A participant can share it's chosen key with other participants by sending Matrix [to-device messaging](https://spec.matrix.org/v1.11/client-server-api/#send-to-device-messaging) to the other participants.

The key is sent as an event of type `m.rtc.encryption_keys` as an encrypted to-device message.

The device ID that is being sent to is the `member`.`device_id` from the `m.rtc.member` events.

The event contains the following fields:

- `session` required object: The contents of the `session` from the `m.rtc.member` event.
- `member` required object: The contents of the `member` from the corresponding `m.rtc.member` event.
- `keys` required array of objects: The sender keys to be distributed to the participant:
  - `key` required string: The base64 encoded key material.
  - `index` required int: The index of the key to distinguish it from other keys. This must be a between 0 and 255 inclusive.
    In some implementations of MatrixRTC this may correspond to the `keyID` field of the WebRTC [SFrame](https://www.w3.org/TR/webrtc-encoded-transform/#sframe) header.
  - `invalidates_key_index` optional int: The index of the key that is invalidated by this key. If this is set, the application should invalidate the key identified
    by `invalidates_key_index` once it receives a frame with the new `index`. This is to protect against an exfiltrated key being used to forge frames.
  - `invalidates_after_ms` optional int: The number of milliseconds after the key identified by `invalidates_key_index` is invalidated by this key even if no frames
    are received. Again, this is to protect against an exfiltrated key being used to forge frames.

Depending on the RTC application, additional fields may be added to this event.

An example to-device event:

```json5
// event type: "m.rtc.encryption_keys"
{
    "session": {
      "application": "m.call",
      "call_id": "",
      "scope": "m.room"
    },
    "member": {
      "id": "xyzABCDEF10123",
      "device_id": "DEVICEID",
      "user_id": "@user:matrix.domain"
    },
    "room_id": "!roomid:matrix.domain",
    "keys": [
        {
            "index": 10,
            "key": "base64encodedkey",
            "invalidates_key_index": 9,
            "invalidates_after_ms": 5000
        },
    ],
}
```

On receipt of the `m.rtc.encryption_keys` event the application can associate the received key with the RTC session by matching the `session` and `member` contents with the corresponding `m.rtc.member` event.

When the application joins the session it should send the key to all the existing participants.

To ensure forward secrecy and post compromise security, the key material should be rotated (i.e. a new key generated) when a participant joins or leaves the session.

Key rotation is done as follows:

- the sending application generates the new key material for the participant.
- the sending application sends the new key material to all the participants with a new `index` value and `invalidates_key_index` set to the current `index`.
- the receiving application stores the new key material for the specified `index`.
- the sending application continues to use the old/current key to encrypt media.
- the sending application waits for a period of time. The default should be 3 seconds.
 It is possible to overwrite this on a per application basis in case an application has specific requirements on security or wants to minimize missed stream data.
 Also negotiation approaches can be defined where the RTC application uses data channels to communicate if everyone has received the next key.
- the sending application starts to use the new key to encrypt media.
- the receiving application invalidates the existing key with the `invalidates_key_index` value.

### Discovery/negotiation of application types

Problem: If a user wants to make a call to a user or room, then which call/application options should the client present to the user?

This should also take account of non-MatrixRTC calling: legacy 1:1 VoIP, room state widget for Jitsi.

TODO: write up notes.

## Potential issues

## Alternatives

### One state event per user

[MSC3401](https://github.com/matrix-org/matrix-spec-proposals/pull/3401) proposed to have one state event per user with that state event containing an array of memberships.

This introduces two problems:

- potential inconsistency where one user device overwrites the state of another device during a concurrent update.
- when handling client disconnects the MSC3757 proposal could not be used as you would not know what the correct
  state is at the time of the disconnect.

### One state event per device

This would mean not using `member`.`id` in the state key anymore. Race conditions can be solved by the client which would need to manage multiple sessions at once.

### A separate system not associated with Matrix accounts

This MSC proposes to combine the MatrixRTC backend infrastructure with the homeserver.
Other sources where the backend could be sourced from are:

- A separate system not associated with Matrix accounts.
  (you would need a Matrix account + a "LiveKit provider" account for example)
- The client could bring its own backend link.
- A centralized solution.

The centralized solution would not fit to Matrix. A separate system would match the distributed
nature of Matrix but would not match the user experience goals for MatrixRTC calls.

The client defining the SFU that is used, is the current solution. This causes the issue, that clients
in general are less distributed than homeservers. There is only a limited set of clients that a large
percentage of users use.
Using this as the source for the infrastructure would result in just a handful of very large infrastructure
hosts.
This is harder to scale and it is harder to justify who is covering the costs. (For Matrix homeservers, this
is an already solved problem where there are individuals, communities and institutions that have their own individual
solutions and answers for how and why they provide the infrastructure.)

### `m.rtc.encryption_keys` room event

Earlier iterations of this MSC used an encrypted `m.rtc.encryption_keys` room event to distribute the per-participant sender keys.

Whilst reducing traffic by only needing to send one event per participant, this approach does not allow for perfect forward secrecy
as the keys are stored in the room history.

The encrypted content of the `m.rtc.encryption_keys` event was as follows:

```json5
{
    "session": {
      "application": "m.call",
      "call_id": ""
    },
    "member": {
      "id": "xyzABCDEF10123",
      "device_id": "DEVICEID",
      "user_id": "@user:matrix.domain"
    }.
    "keys": [
        {
            "index": 0,
            "key": "base64encodedkey"
        },
    ],
}
```

## Security considerations

### Discoverability of infrastructure

The `.well-known/matrix/client` is publicly readable, hence everyone can read and know
about the infrastructure which could lead to resource "stealing".
Each infrastructure however has their own authentication mechanism defined in the infrastructure specification.
Those mechanisms for instance can use a service to interact with the homeserver and based on that decide to allow users
to use the infrastructure.

This is defined in the respective infrastructure MSC.

### Forward secrecy for end-to-end encryption of media streams

The considerations to ensure forward secrecy are described in the [End-to-end encryption of media streams](#end-to-end-encryption-of-media-streams)
section above.

### End-to-end media encryption key rotation lag

The proposed key rotation semantics does mean that a participant could continue to decrypt media that was sent in the three seconds after
leaving the session.

## Unstable prefix

Use `org.matrix.msc3401.call.member` as the state event type in place of `m.rtc.member`.

For discovery via `.well-known/matrix/client` the prefix `org.matrix.msc4158.rtc_foci` is used in place of `m.rtc_foci`.

Use `io.element.call.encryption_keys` in place of the `m.rtc.encryption_keys` room event and to-device event types.

## Dependencies

This proposal depends on
[MSC3757: Restricting who can overwrite a state event](https://github.com/matrix-org/matrix-spec-proposals/pull/3757)
to provide access control for the decentralised management of call membership state. However, an alternative such
as [MSC3779: "Owned" State Events](https://github.com/matrix-org/matrix-spec-proposals/pull/3779) could be used instead with
some adaptations.

This proposal also depends on [MSC4140: Cancellable delayed events](https://github.com/matrix-org/matrix-spec-proposals/pull/4140)
to provide a mechanism for clients to ensure that they can update the room state even if they lose connection.
