# MSC3489 - m.beacon: Sharing streams of location data with history

## MSC TODO

- [ ] Timestamps are ms
- [ ] Refer to related MSCs in a references section
    - [ ] related: EDU-based live location
    - [ ] related: 3488 - static location
    - [ ] nice to have: deleting state events
    - [ ] semi-needed: the 2 state_key ones
    - [ ] relates_to https://github.com/matrix-org/matrix-spec-proposals/pull/2674
    - [ ] m.reference https://github.com/matrix-org/matrix-spec-proposals/pull/3267
- [ ] Update EDU-equivalent one to say it's identical to this except blah
- [ ] Clarify how to stop sharing - make a new event
- [ ] Update JSON to be what we want
- [ ] Clarify beacon/beacon_info naming
- [ ] Section on permissions: what we can do now, what the right solution is

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
[MSC3672](https://github.com/matrix-org/matrix-doc/pull/3672)

## Proposal

This MSC adds the ability to publish real-time location beacons to Matrix by
building on [MSC3488](https://github.com/matrix-org/matrix-doc/pull/3488),
which allows sharing of single static locations via the `m.location` event
type.

We introduce two types of event to describe beacons:

* **`m.beacon_info`**: a single state event containing metadata about this
  beacon (e.g. how long it will remain live).

* **``m.beacon`**: multiple message events containing the actual locations at
  various times. All of the `m.beacon`s refer to the original `m.beacon_info`.

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
([MSC3488](https://github.com/matrix-org/matrix-doc/pull/3488)).

`live` should be true when a user starts sharing location.

`m.ts` is the time when location sharing started, in milliseconds since the
epoch.

`timeout` is the length of time in milliseconds that the location will be live.
So the location will stop being shared at `m.ts` + `timeout` milliseconds since
the epoch.

`m.asset` identifies the type of asset being tracked as per
[MSC3488](https://github.com/matrix-org/matrix-doc/pull/3488).

#### `state_key` of `m.beacon_info`

The `state_key` of the `m.beacon_info` identifies the beacon. It must start
with the mxid of the sender, and if it contains more characters, the first
character after the mxid must be underscore, to match
[MSC3757](https://github.com/matrix-org/matrix-doc/pull/3757) and
[MSC3779](https://github.com/matrix-org/matrix-doc/pull/3779).

If `state_key` exactly equals the sender's mxid, then the current Matrix spec
prevents anyone else from overwriting the state from this event. If `state_key`
contains further characters, that protection will not apply until
[MSC3757](https://github.com/matrix-org/matrix-doc/pull/3757) (some equivalent
mechanism) is available.

Obviously, if the `state_key` equals the sender's mxid, each user can only
share a single beacon in each room at any time. We recommend that clients work
in this mode until
[MSC3757](https://github.com/matrix-org/matrix-doc/pull/3757) is available.

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

We recommend clients do not use this style of `state_key` until
[MSC3757](https://github.com/matrix-org/matrix-doc/pull/3757) is available.

## `m.beacon` - "I am here"

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
            "event_id": "$beacon_info"
        },
        "m.location": {
            "uri": "geo:51.5008,0.1247;u=35",
            "description": "Arbitrary beacon information"
        },
        "m.ts": 1636829458432,
    }
}
```

`m.relates_to` is a reference relationship ([MSC3267](https://github.com/matrix-org/matrix-spec-proposals/pull/3267)).  The `event_id` is the ID of the `m.beacon_info` event emitted when the user started this live share.

`m.location` is identical to the `m.location` section of the `m.location` event
type in [MSC3488](https://github.com/matrix-org/matrix-doc/pull/3488). As such,
it must contain a `uri` field with an RFC5870 `geo:` URI. It can contain an
optional `description` field to provide user-facing updates e.g. the current
address of this location.

`m.ts` is the time in milliseconds since the epoch when the location was measured.

## Permission to share location



## Encryption

Location data should be stored end-to-end encrypted for obvious data privacy
reasons - given the beacon data is stored as simple events that will be automatic.

## Alternatives

Initially this MSC considered storing location data in a separate state event but
that had multiple downsides:
* No encryption without MSC3414
* Difficult access to historical data, timeline pagination required
* State resolution thrasing on every location update. By storing a state event for every location datapoint, 
we put significant load on servers' state management implementations.  Current implementations
may not handle this well.


Storing the location data as references as opposed to in a state event has multiple advantages:
* Location data is easily encrypted (no dependency on MSC3414)
* Doesn't thrash state resolution by storing new location points every time they change
* Paginated history easily accessible through the `relations` endpoint. If history is not wanted, then one can use
data retention policies(e.g. exploding messages) to ensure it does not
accumulate unnecessarily.
* Allows other users to request data from a beacon




Another option would be using ephemeral data units to broadcast location updates but they
do come with downsides of their own:
* they are not persisted and cannot provide historical data
* there's no per-room API for them
* they are not end to end encrypted
However, a privacy-preserving "never store these" approach is still desirable, hence [MSC3672](https://github.com/matrix-org/matrix-doc/pull/3672)

Alternatively, we could behave like MSC3401 and announce users' beacons in
`m.beacon_info.*` (similar to MSC3401's `m.call`), and then send location
data via to-device messages to interested devices.
 * Pros:
   * Doesn't thrash state resolution by storing new location points every time they change
   * Gets you easy E2EE automatically
 * Cons:
   * designs out historical geo-data use cases
   * means you are reinventing the pubsub fan-out routing you get for free with Matrix events
   * means you have to reinvent decentralised ACLs to check that the subscribing users are valid
   * means new joiners to a room won't even be able to see the most recent location for someone
   * MSC1763 data retention lets us control the historical data anyway.

Alternatively, we could send location data as normal E2EE messages. However,
clients would have to back-paginate in an unbounded fashion to confidently
say what the various beacons are doing rather than simply fishing it out of
room state.

Alternatively, we could negotiate a WebRTC data channel using MSC3401 and
stream low-latency geospatial data over the participating devices in the room.
This doesn't give us historical data, however, and requiring a WebRTC stack
is prohibitively complicated for simple clients (e.g. basic IOT devices
reporting spatial telemetry).

We could include velocity data as well as displacement data here(especially as
the W3C geolocation API provides it); this has been left for a future MSC in
the interests of avoiding scope creep.

## Security considerations

Location data is high risk for real-world abuse, especially if stored
unencrypted or persisted. The same security considerations apply as for
`m.location` data in general.

## Unstable prefix

 * `m.beacon_info.*` should be referred to as `org.matrix.msc3489.beacon_info.*` until this MSC lands.
 * `m.beacon` should be referred to as `org.matrix.msc3489.beacon` until this MSC lands.
 * `m.location` should be referred to as `org.matrix.msc3488.location.*` until MSC3488 lands.
 * `m.ts` should be referred to as `org.matrix.msc3488.ts.*` until MSC3488 lands.
 * `m.asset` should be referred to as `org.matrix.msc3488.asset.*` until MSC3488 lands.
