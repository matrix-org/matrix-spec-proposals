# MSC4143: MatrixRTC

This MSC defines the modules with which the matrix real time system is build.

The MatrixRTC specification is separated into different modules.

- The MatrixRTC room state that defines the state of the real time application.\
  It is the source of truth for:
  - Who is part of a session
  - Who is connected via what technology/backend
  - Metadata per device used by other participants to decide whether the streams
    from this source are of interest / need to be subscribed.
- The RTC backend.
  - It defines how to connect the participating peers.
  - Livekit is the standard for this as of writing.
  - Defines how to connect to a server/other peers, how to update the connection,
    how to subscribe to different streams...
  - Another planned backend is a full mesh implementation based on MSC3401.
- The RTCSession types (application) have their own per application spec.
  - Calls can be done with an application of type `m.call` see (TODO: link call msc)
  - The application defines all the details of the RTC experience:
    - How to interpret the metadata of the member events.
    - What streams to connect to.
    - What data in which format to sent over the RTC channels.

This MSC will focus on the matrix room state which can be seen as the most high
level signalling of a call:

## Proposal

Each RTC session is made out of a collection of `m.rtc.member` events.
Each `m.rtc.member` event defines the application type: `application`
and a `call_id`. And is stored in a state event of type `m.rtc.member`.
The first element of the state key is the `userId` and the second the `deviceId`.
(see [this proposal for state keys](https://github.com/matrix-org/matrix-spec-proposals/pull/3757#issuecomment-2099010555)
for context about second/first state key.)

### The MatrixRTC room state

Everything required for working MatrixRTC
(current session, sessions history, join/leave events, ...) only
require one event type.

A complete `m.rtc.member` state event looks like this:

```json
// event type: "m.rtc.member"
// event key: ["@user:matrix.domain", "DEVICEID"]
{
  "application": "m.my_session_type",
  "call_id": "",
  "device_id": "DEVICEID",
  "created_ts": Time | undefined,
  "focus_active": {...FOCUS_A},
  "foci_preferred": [
    {...FOCUS_1},
    {...FOCUS_2}
  ]
}
```

> [!NOTE]  
> This relies on [MSC3757](https://github.com/matrix-org/matrix-spec-proposals/pull/3757).
> We need to have one state event per device, hence multiple "non-overwritable" state
> events per user.
>
> More specifically this uses the approach outlined in this [comment](https://github.com/matrix-org/matrix-spec-proposals/pull/3757#issuecomment-2099010555).

This gives us the information, that user: `@user:matrix.domain` with device `DEVICEID`
is part of an RTCSession of type `m.call` in the scope/sub-session `""` (empty
string as call id) connected over `FOCUS_A`. This is all information that is needed
for another room member to detect the running session and join it.

We include the device_id in the member content to not rely on the exact format of the state key.
In case [MSC3757](https://github.com/matrix-org/matrix-spec-proposals/pull/3757) is used it would not
be the second element of the state key array.

`created_ts` is an optional property that caches the time of creation. It is not required
for an event that, has not yet been updated, there the `origin_server_ts` is used.

> [!NOTE]
> We introduce `created_ts()` as the notation for `created_ts ?? origin_server_ts`

Once the event gets updated the origin_server_ts needs to be copied into the `created_ts` field.
An existing `created_ts` field implies that this is a state event updating the current session
and a missing `created_ts` field implies that it is a join state event.
All membership events that belong to one member session can be grouped with the index
`created_ts()`+`device_id`. This is why the `m.rtc.member` events deliberately do NOT include a `membership_id`.

Other then the membership sessions, there is **no event** to represent a rtc session (containing all members).
This event would include shared information where it is not trivial to decide who has authority over it.
Instead the session is a computed value based on `m.rtc.member` events.
The list of events with the same `application` and `m.call_id` represent one session.
This array allows to compute fields like participant count, start time ...

Sending an empty `m.rtc.member` event represents a leave action.
Sending a well formatted `m.rtc.member` represents a join action.

Based on the value of `application`, the event might include additional parameters
required to provide additional session parameters.

> A thirdRoom like experience could include the information of an approximate position
> on the map, so that clients can omit connecting to participants that are not in their
> area of interest.

#### Historic sessions

Since there is no singe entry for a historic session (because of the owner ship discussion),
historic sessions need to be computed and most likely cached on the client.

Each state event can either mark a join or leave:

- join: `prev_state.application != current_state.application` &&
  `prev_state.m.call_id != current_state.m.call_id` &&
  `current_state.application != undefined`
  (where an empty `m.rtc.member` event would imply `state.application == undefined`)
- leave: `prev_state.application != current_state.application` &&
  `prev_state.m.call_id != current_state.m.call_id` &&
  `current_state.application == undefined`

Based on this one can find user sessions. (The range between a join and a leave
event) of specific times.
The collection of all overlapping user sessions with the same `call_id` and
`application` define one MatrixRTC history event.

### The RTC backend

`foci_active` and `foci_preferred` are used to communicate

- how a user is connected to the session (`foci_active`)
- what connection method this user knows about would like to connect with.

The only enforced parameter of a `foci_preferred` or `foci_active` is `type`.
Based on the focus type a different amount of parameters might be needed to,
communicate how to connect to other users.
`foci_preferred` and `foci_active` can have different parameters so that it is,
possible to use a combination of the two to figure our that everyone is connected
with each other.

Only users with the same type can connect in one session. If a frontend does
not support the used type they cannot connect.

Each focus type will get its own MSC in which the detailed procedure to get from
the foci information to working webRTC connections to the streams of all the
participants is explained.

- [`livekit`](www.example.com) TODO: create `livekit` focus MSC and add link here.
- [`full_mesh`](https://github.com/matrix-org/matrix-spec-proposals/pull/3401)
  TODO: create `full-mesh` focus MSC based on[MSC3401](https://github.com/matrix-org/matrix-spec-proposals/pull/3401)
  and add link here.

#### Sourcing `foci_preferred`

At some point participants have to decide/propose which focus they use.
Based on the focus type and usecase choosing a `foci_preferred` can be different.
If possible these guidelines should be obeyed:

- If there is a relation between the `focus_active` and a preferred focus (`type: livekit` is an example for this)
  it is recommended to copy _the preferred focus that relates to the current `focus_active`_ of other participants to the start of the `foci_preferred` array of the member event.
  (The exact definition of: _the preferred focus that relates to the current `focus_active`_ is part of the specification for each focus type. For `full_mesh` for example there is no such thing as: _the preferred focus that relates to the current `focus_active`_ )
- Homeservers can proposes `preferred_foci` via the well known. An array of preferred foci is provided behind the well known key `m.rtc_foci`. This is defined in [MSC4158](https://github.com/matrix-org/matrix-spec-proposals/pull/4158). They are related and it is recommended to also read [MSC4158](https://github.com/matrix-org/matrix-spec-proposals/pull/4158) with this MSC.
  Those proposals from **your own** homeserver should come next in the `foci_preferred` list of the member event.
- Clients also have the option to configure a preferred foci even though this is not recommended (see below).
  Those come last in the list.

The rational for those guidelines are as following:

- It is always desired to have as little focus switches as possible.
  That is why the highest priority is to prefer the focus that is already in use
- MatrixRTC is designed around the same culture that makes matrix possible:
  A large amount of infrastructure in form of homeservers is provided by the users.
  For MatrixRTC the same is thea goal. To achieve a stable and healthy ecosystem
  rtc infrastructure should be thought of as a part of a homeserver. It is very similar
  to a turn server: mostly traffic and little cpu load.
  To not end up in a world where each user is only using one central SFU but where the traffic
  is split over multiple SFU's it is important that we leverage the SFU distribution on the
  homeserver distribution.
  For this reason the second guideline is to lookup the prefferred foci from the homeserver well_known
- Looking up the prefferred foci from a client is toxic to a federated system. If the majority of users
  decide to use the same client all of the users will use one Focus. This destroys the passive security mechanism, that each instance is not an interesting attack vector since it is only a fraction of the network.
  Additionally it will result in poor performance if every user on matrix would use the same Focus.
  There are cases where this is acceptable:
  - Transitioning to MatrixRTC. Here it might be beneficial to have a client that has a fallback Focus
    so calls also work with homeservers not supporting it.
  - For testing purposes where a different Focus should be tested but one does not want to touch the .well_known
  - For custom deployments that benefit from having the Focus configuration on a per client basis instead of per homeserver.

### The RTCSession types (application)

Each session type might have its own specification in how the different streams
are interpreted and even what focus type to use. This makes this proposal extremely
flexible. A Jitsi conference could be added by introducing a new `application`
and a new focus type and would be MatrixRTC compatible. It would not be compatible
with applications that do not use the Jitsi focus but clients would know that there
is an ongoing session of unknown type and unknown focus and could display/represent
this in the user interface.

To make it easy for clients to support different RTC session types, the recommended
approach is to provide a matrix widget for each session type, so that client developers
can use the widget as the first implementation if they want to support this RTC
session type.

Each application should get its own MSC in which the all the additional
fields are explained and how the communication with the possible foci is
defined:

- [`m.call`](www.example.com) TODO: create `m.call` MSC and add link here.

## Potential issues

## Alternatives

## Security considerations

## Unstable prefix

The state events and the well_known key introduced in this MSC use the unstable prefix
`org.matrix.msc4143.` instead of `m.` as used in the text.

Possible values inside the `m.rtc.member` event (like `m.call`) will use a prefix defined in the
related PR (TODO create and link `m.call` application type PR)
