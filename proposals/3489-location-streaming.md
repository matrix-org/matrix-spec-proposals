# MSC3489 - m.beacon: Sharing streams of location data

## Problem

A common communication feature is sharing live location data with other users.
Use cases include helping users find each other and asset tracking. Matrix
doesn't currently provide a way of doing this.

Therefore, we'd like to provide a way for users to efficiently advertise the
time-limited real-time location of themselves or arbitrary assets to other
users in a room.

## Proposal

This MSC adds the ability to publish real-time location beacons to Matrix by
building on MSC3488 (m.location: Extending events with location data).

We introduce two types of state events to describe beacons: the first contains
the metadata about the beacons advertised by a given user: `m.beacon_info.*`.
As Matrix doesn't yet have a way to stop other users overwriting an event
other than setting its state_key to be the owner's mxid, we work around this
by letting the final part of the event type be a unique ID for the beacon.
(Ideally we would put the unique ID as its `state_key` and flip a bit on the
event to indicate that it can only ever be written by its owner - we may get
this via MSC3414 encrypted state events).

This lets us track an arbitrary number of beacons per user, and avoids becaon
metadata being duplicated as location data is shared.

An example `m.beacon_info.*` event is:

```json
{
    "type": "m.beacon_info.self",
    "state_key": "@matthew:matrix.org",
    "content": {
        "m.beacon_info": {
            "description": "The Matthew Tracker", // same as an `m.location` description
            "created": 1436829458432, // creation timestamp of the beacon on the client.
            "lifetime": 86400000, // how long the beacon will publish for in milliseconds
        }
    }
}
```

Separately, we have the actual location data from the beacon in question
stored in `m.beacon.*` state events.  Storing the data as state events
ensures that the current location of a given beacon is trivial to determine
(rather than the client having to back-paginate history).  It also gives us
location history where desirable.  If history is not wanted, then one can use
data retention policies(e.g. exploding messages) to ensure it does not
accumulate unnecessarily.

`m.beacon.*` events should be sent every 2 seconds while the location of
the asset is moving.  If the asset is not moving, it should be refreshed
every 30 seconds.

An example `m.beacon.*` event is:

```json
{
    "type": "m.beacon.self",
    "state_key": "@matthew:matrix.org",
    "content": {
        "m.location": {
            "uri": "geo:51.5008,0.1247;u=35",
        },
        "m.ts": 1636829458432,
    }
}
```

The special ID `self` is used to indicate that the beacon describes the
primary asset associated with that mxid (e.g. the whereabouts of its human
user).

## Encryption

Location data should be stored end-to-end encrypted for obvious data privacy
reasons - given the beacon data is stored in state events, this should be
achieved by MSC3414.

## Problems

By storing a state event for every location datapoint, we put significant
load on servers' state management implementations.  Current implementations
may not handle this well.  However, semantically, state events provide the
behaviour we need (easy access to current value; persistent state within
a room), hence adopting them for this.

## Alternatives

We could behave like MSC3401 and broadcast and announce users' beacons in
`m.beacon_info.*` (similar to MSC3401's `m.calls`), and then send location
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

Alternatively, we could sell location data as normal E2EE messages. However,
clients would have to back-paginate in an unbounded fashion to confidently
say what the various beacons are doing rather than simply fishing it out of
room state.

Alternatively, we could negotiate a WebRTC data channel using MSC3401 and
stream low-latency geospatial data over the participating devices in the room.
This doesn't give us historical data, however, and requiring a WebRTC stack
is prohibitively complicated for simple clients (e.g. basic IOT devices
reporting spatial telemetry).

## Security considerations

Location data is high risk for real-world abuse, especially if stored
unencrypted or persisted. The same security considerations apply as for
`m.location` data in general.

## Unstable prefix

`m.beacon_info.*` should be referred to as `org.matrix.msc3489.beacon_info.*` until this MSC lands.
`m.beacon.*` should be referred to as `org.matrix.msc3489.beacon.*` until this MSC lands.
`m.location` should be referred to as `org.matrix.msc3488.location.*` until MSC3488 lands.
`m.ts` should be referred to as `org.matrix.msc3488.ts.*` until MSC3488 lands.
