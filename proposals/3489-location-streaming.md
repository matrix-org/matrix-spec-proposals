# MSC3489 - m.beacon: Sharing streams of location data with history

## Problem

A common communication feature is sharing live location data with other users.
Use cases include helping users find each other and asset tracking. Matrix
doesn't currently provide a way of doing this.

Therefore, we'd like to provide a way for users to efficiently advertise the
time-limited real-time location of themselves or arbitrary assets to other
users in a room - while by default preserving the history of the location
data in the room by storing it as relational timeline events.

The rationale for persisting location data is to support the use cases of:

* Publishing things like Strava-style exercise data
* Bridging to things like ADS-B sources for sharing plane flight path data.
* Logistics use cases where you want to track where your fleet of
  vehicles/ships has been, or the packages within them
* Supporting scenarios where you're trying to rendezvous with someone/something
  which will be aided by seeing their historical whereabouts (e.g.
  search-and-rescue operations; enhanced Find-my-iPhone style use cases).

For purely ephemeral location sharing, see
[MSC3672](https://github.com/matrix-org/matrix-spec-proposals/pull/3672).

## Proposal

This MSC adds the ability to publish real-time location beacons to Matrix by
building on
[MSC3488](https://github.com/matrix-org/matrix-spec-proposals/pull/3488),
which allows sharing of single static locations via the `m.location` event
type.

We introduce two types of event to describe beacons:

* **`m.beacon_info`**: a single state event containing metadata about this
  beacon (e.g. how long it will remain live).

* **`m.beacon`**: multiple message events containing the actual locations at
  various times. All of the `m.beacon` events refer to the original
  `m.beacon_info`.

### `m.beacon_info` - "I am going to share live location"

An example `m.beacon_info` event is:

```json5
{
  "type": "m.beacon_info",
  "state_key": "@matthew:matrix.org",
  "content": {
    "description": "The Matthew Tracker",
    "live": true,
    "m.ts": 1436829458432,
    "timeout": 86400000,
    "m.asset": { "type": "m.self" }
  }
}
```

`description` is the same as an `m.location` description
([MSC3488](https://github.com/matrix-org/matrix-spec-proposals/pull/3488)).

`live` should be true when a user starts sharing location.

`m.ts` is the time when location sharing started, in milliseconds since the
epoch.

`timeout` is the length of time in milliseconds that the location will be live.
So the location will stop being shared at `m.ts` + `timeout` milliseconds since
the epoch.

`m.asset` identifies the type of asset being tracked as per
[MSC3488](https://github.com/matrix-org/matrix-spec-proposals/pull/3488).

#### `state_key` of `m.beacon_info`

The `state_key` of the `m.beacon_info` identifies the beacon. It must start
with the mxid of the sender, and if it contains more characters, the first
character after the mxid must be underscore, to match
[MSC3757](https://github.com/matrix-org/matrix-spec-proposals/pull/3757) and
[MSC3779](https://github.com/matrix-org/matrix-spec-proposals/pull/3779).

If `state_key` exactly equals the sender's mxid, then the current Matrix spec
prevents anyone else from overwriting the state from this event. Until
`state_key`
[MSC3757](https://github.com/matrix-org/matrix-spec-proposals/pull/3757) (or
some equivalent mechanism) lands, `state_key` will not be allowed to contain
further characters. After it lands, adding underscore and further characters
will allow one user to create multiple beacons.

Obviously, if the `state_key` always equals the sender's mxid, each user can
only share a single beacon in each room at any time. We recommend that clients
work in this mode until
[MSC3757](https://github.com/matrix-org/matrix-spec-proposals/pull/3757) is
available.

To allow multiple beacons per user (e.g. one per device), we use a `state_key`
of mxid plus underscore, and an identifier. For example:

```json5
{
  "type": "m.beacon_info",
  "state_key": "@matthew:matrix.org_46583241",  // inspired by MSC3757
  "content": {
    "description": "Matthew's other phone",
    "live": true,
    "m.ts": 1436829458432,
    "timeout": 86400000,
    "m.asset": { "type": "m.self" }
  }
}
```

This style of `state_key` will not work (is not allowed) until
[MSC3757](https://github.com/matrix-org/matrix-spec-proposals/pull/3757) is
available.

### `m.beacon` - "I am here"

The actual location data is sent in `m.beacon` events, which have a reference
relationship to the original `m.beacon_info` event.

`m.beacon` events should be sent at a variable rate which is meaningful for
the use case for the asset being tracked. This rate should not be more
frequent than sending an event every 2 seconds. If the asset is not moving,
the location should still be refreshed on a regular basis to convey that
information - e.g. every 30 seconds.

An example `m.beacon` event is:

```json5
{
  "type": "m.beacon",
  "sender": "@matthew:matrix.org",
  "content": {
    "m.relates_to": {
      "rel_type": "m.reference",
      "event_id": "$beacon_info_event_id"
    },
    "m.location": {
      "uri": "geo:51.5008,0.1247;u=35",
      "description": "Arbitrary beacon information"
    },
    "m.ts": 1636829458432,
  }
}
```

`m.relates_to` is a reference relationship
([MSC3267](https://github.com/matrix-org/matrix-spec-proposals/pull/3267)).
The `event_id` is the ID of the `m.beacon_info` event emitted when the user
started this live share.

`m.location` is identical to the `m.location` section of the `m.location` event
type in [MSC3488](https://github.com/matrix-org/matrix-spec-proposals/pull/3488). As such,
it must contain a `uri` field with an RFC5870 `geo:` URI. It can contain an
optional `description` field to provide user-facing updates e.g. the current
address of this location.

`m.ts` is the time in milliseconds since the epoch when the location was
measured.

### Stopping sharing

To stop sharing, the client should emit an additional `m.beacon_info`
event that is identical to the first, except with `live: false`.

The client that initiated a share should stop sharing if:

* the timeout on a live share has expired, or
* the user requested to stop sharing, or
* the user revoked permissions on their device to share location.

For example:

```json5
{
  "type": "m.beacon_info",
  "state_key": "@matthew:matrix.org_46583241",
  "content": {
    "description": "Matthew's other phone",
    "live": false,  // Stop sharing
    "m.ts": 1436829458432,
    "timeout": 86400000,
    "m.asset": { "type": "m.self" }
  }
}
```

### Deciding which shared locations are live

A location share is "live" if the sender is currently sharing their location.

Client apps will often want to  determine two related but different pieces of
information about the shares in a room:

1. Which location shares are live
2. How to display a single location share event (e.g. in a timeline)

#### Which locations shares are live

To determine who is currently sharing their location in a room, clients should
examine the room state for events of type `m.beacon_info`.

For each `m.beacon_info` event in the room state, it is live if:

* `live` is `true`, and
* `m.ts + timeout < now_ts` where `now_ts` is the current time in milliseconds
  since the epoch.

Otherwise it is not live.

#### How to display a single location share event

For clients with timelines, we expect that a map or similar will appear in the
timeline whenever a `m.beacon_info` event with `live: true` is sent, and
related `m.beacon` events will cause that map to update. Stopping sharing
(sending a `m.beacon_info` event with `live: false`) might not create any new
visible item in the timeline.

For a map on a timeline associated with an initial `m.beacon_info`, to
determine whether that map is "live", clients should:

* look in the room state for an `m.beacon_info` event with the same
  `state_key`, and
* follow the rules in the previous section ("Which location shares are live").

### Redacting shared locations

Because location information is private, it is vital that people are able to
delete information that they no longer want to reveal, or that was
inadvertently posted to the wrong room.

We expect that clients will provide a single UI element that redacts all events
for a live sharing session. This includes the original `m.beacon_info` event,
all `m.beacon` events related to it, and any additional `m.beacon_info` event
sent to stop sharing.

Redaction should be done in the normal way, using the `redact` API as specified
in section
[7.9 Redactions](https://spec.matrix.org/v1.2/client-server-api/#redactions) of
the Client-Server API. (See also
[MSC2244: Mass redactions](https://github.com/matrix-org/matrix-spec-proposals/pull/2244).)

## Permission to share location

Since the `m.beacon_info` event is a state event, users who wish to share their
live location will need permission to send state events. By default, users with
power level 50 are able to send state events.

To allow all users to send `m.beacon_info` events, the room's power levels
should be set to something like this:

```json5
{
  "state_key": "",
  "type": "m.room.power_levels",
  "content": {
    "events": {
      "m.beacon_info": 0,
      ...
    },
    ...
  },
  ...
}
```

This can be done during room creation, or later by sending a new
`m.room.power_levels` state event.

[MSC3779](https://github.com/matrix-org/matrix-spec-proposals/pull/3779) is intended to
make it easier to send this kind of state event, and the `state_key`s in this
proposal are deliberately designed to take advantage of MSC3779 if it is
standardised. If MSC3779 is available, users with permission to send message
events will automatically have permission to share their live location, because
the `state_key` matches the pattern required to be an "owned" state event.

## Alternatives

### Storing location in room state

Initially this MSC considered storing location data in a separate state event
but that had multiple downsides:

* No encryption without
  [MSC3414](https://github.com/matrix-org/matrix-spec-proposals/pull/3414).
* Difficult access to historical data, timeline pagination required.
* State resolution thrashing on every location update. By storing a state event
  for every location datapoint, we put significant load on servers' state
  management implementations. Current implementations may not handle this
  well.

Storing the location data as references as opposed to in a state event has
multiple advantages:

* Location data is easily encrypted (no dependency on
  [MSC3414](https://github.com/matrix-org/matrix-spec-proposals/pull/3414)).
* Doesn't thrash state resolution by storing new location points every time
  they change.
* Paginated history easily accessible through the `relations` endpoint. If
  history is not wanted, then one can use data retention policies (e.g.
  exploding messages) to ensure it does not accumulate unnecessarily.
* Allows other users to request data from a beacon.

### Sending location data using ephemeral data units (EDUs)

This proposal covers use cases where location data needs to be preserved
in the room timeline. In cases where this is not required, better privacy
may be obtained by sending the `m.beacon` events as EDUs.

See [MSC3672](https://github.com/matrix-org/matrix-spec-proposals/pull/3672)
for this approach. Note that it depends on user-defined EDUs
([MSC2477](https://github.com/matrix-org/matrix-spec-proposals/pull/2477/))
and encrypted EDUs
([MSC3673](https://github.com/matrix-org/matrix-spec-proposals/pull/3673)).

### To-device messages

We could behave like
[MSC3401](https://github.com/matrix-org/matrix-spec-proposals/pull/3401) and
send location data via to-device messages to interested devices.

 * Pros:
   * Doesn't thrash state resolution by storing new location points every time
     they change
   * Gets you easy E2EE automatically
 * Cons:
   * designs out historical geo-data use cases
   * means you are reinventing the pubsub fan-out routing you get for free with
     Matrix events
   * means you have to reinvent decentralised ACLs to check that the
     subscribing users are valid
   * means new joiners to a room won't even be able to see the most recent
     location for someone
   * MSC1763 data retention lets us control the historical data anyway.

Alternatively, we could negotiate a WebRTC data channel using MSC3401 and
stream low-latency geospatial data over the participating devices in the room.
This doesn't give us historical data, however, and requiring a WebRTC stack
is prohibitively complicated for simple clients (e.g. basic IOT devices
reporting spatial telemetry).

### One state event per user

(As suggested by @deepbluev7)

To reduce the problem of state bloat (too many state events with different keys) and avoid the need for permission changes on state events, we could post a single state event per user, which contained a list of all the currently-shared location events, and the location events could be normal timeline events, which are updated using message edits (with `m.replace`).

Advantages:

* Backwards compatible with static location sharing ([MSC3488](https://github.com/matrix-org/matrix-spec-proposals/pull/3488)) - clients that did not understand live location sharing but did understand static would see the location changing over time due to the edits.
* Only one state event per user - less state bloat.
* No need for changes to the rules about who can modify state events (but still requires the ability for unprivileged users to create a state event with `state_key` equal to their mxid).

Disadvantages

* Potential race where multiple clients update the same state event at the same time, and one overwrites the other.
* Location events need to be fetched from the timeline before they can be used.
* Potential confusion - a live location is semantically different from a static location that has been edited.

### No state events

We could send location data as normal E2EE messages, with no state events
involved. However, clients would have to back-paginate in an unbounded fashion
to confidently say what the various beacons are doing rather than simply
fishing it out of room state.

### Including velocity

We could include velocity data as well as displacement data here (especially as
the W3C geolocation API provides it); this has been left for a future MSC in
the interests of avoiding scope creep.

## Security considerations

Location data is high risk for real-world abuse, especially if stored
unencrypted or persisted. The same security considerations apply as for
`m.location` data in general.

Normally, locations should only be shared in encrypted rooms, meaning that they
are transferred and stored end-to-end encrypted automatically.

Clients will probably want to warn users when they request to share location in
an unencrypted room.

See "Redacting shared locations" above for information about deleting shared
location data.

## Unstable prefix

Until this MSC lands, the following unstable prefixes should be used:

 * `m.beacon_info` -> `org.matrix.msc3672.beacon_info`
 * `m.beacon` -> `org.matrix.msc3672.beacon`

(Note: these prefixes are shared with MSC3672. If this MSC lands first, MSC3672
can be updated to use stable prefixes.)

Until MSC3488 lands, the following unstable prefixes should be used:

 * `m.location` -> `org.matrix.msc3488.location`
 * `m.ts` -> `org.matrix.msc3488.ts`
 * `m.asset` -> `org.matrix.msc3488.asset`

Examples of the events with unstable prefixes:

```json5
{
  "content": {
    "description": "Kylie's live location",
    "live": true,
    "org.matrix.msc3488.asset": { "type": "m.self" },
    "org.matrix.msc3488.ts": 651066205621,
    "timeout": 3600000
  },
  "room_id": "!dypRwVXIkJkTAACHPd:element.io",
  "sender": "@kylie:example.com",
  "state_key": "@kylie:example.com",
  "type": "org.matrix.msc3672.beacon_info",
  "event_id": "$TlS7h0NHzBdZIccsSspF5CMpQE8YMT0stRern0nXscI"
}

```

```json5
{
  "content": {
    "m.relates_to": {
      "event_id": "$TlS7h0NHzBdZIccsSspF5CMpQE8YMT0stRern0nXscI",
      "rel_type": "m.reference"
    },
    "org.matrix.msc3488.location": {
      "uri": "geo:8.95752746197222,12.494122581370175;u=10"
    },
    "org.matrix.msc3488.ts": 651066206460
  },
  "room_id": "!dypRwVXIkJkTAACHPd:element.io",
  "sender": "@kylie:example.com",
  "type": "org.matrix.msc3672.beacon",
  "event_id": "$75FtAIdg9wRTdACcgq4yetaInKlKQKhExYAwMc-qW3Q"
}
```

## Related MSCs

### Dependencies

* [MSC3267](https://github.com/matrix-org/matrix-spec-proposals/pull/3267):
  *Reference relations*. This MSC uses `rel_type: m.reference` from MSC3267,
  which in turn builds on
  [MSC2674](https://github.com/matrix-org/matrix-spec-proposals/pull/2674):
  Event Relationships (which has landed).

* [MSC3488](https://github.com/matrix-org/matrix-spec-proposals/pull/3488):
  *Extending events with location data*. This MSC re-uses the `m.location`
  object from MSC3488.

### MSCs that will enhance this one

* [MSC3779](https://github.com/matrix-org/matrix-spec-proposals/pull/3779):
  *"Owned" State Events*. If MSC3779 lands, normal users will be able to share
  their live location without special room permissions.

* [MSC3757](https://github.com/matrix-org/matrix-spec-proposals/pull/3757):
  *Restricting who can overwrite a state event*. If MSC3757 lands, it will be
  possible for users to share multiple live locations with variable `state_keys`
  without fear that other users can overwrite their `m.beacon_info`.

### Related

* [MSC3672](https://github.com/matrix-org/matrix-spec-proposals/pull/3672):
  *Sharing ephemeral streams of location data*. Equivalent of this MSC, but
  using ephemeral events, for greater privacy but reduced historical
  functionality.

## Implementations

Element (Web, Android and iOS) implementations based on this MSC are underway
in April 2022, and feedback from those implementations has been incorporated
into updates of this document.
