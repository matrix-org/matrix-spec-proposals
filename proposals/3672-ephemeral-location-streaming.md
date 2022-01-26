# MSC3672 - Sharing ephemeral streams of location data

## Problem

[MSC3489](https://github.com/matrix-org/matrix-doc/pull/3489) 
focuses on streaming persistent location data for applications that require
historical knowledge. 

While that's perfect for situations in which long term storage of the data is a 
non-issue and implied (e.g. flight paths, strava style exercises, fleet 
tracking), there are also cases in doing so is undersirable for either privacy 
or performance reasons.

Sharing user live location updates is one of the cases in which privacy is 
paramount and where we need the ability to share data in a safe and 
non-persistent fashion.

## Proposal

This MSC adds the ability to publish short-lived location beacons through the 
the use of custom Ephemeral Data Units (EDUs) by building on top of [MSC2477](https://github.com/matrix-org/matrix-doc/pull/2477).

Ephemeral data units (EDUs) are Matrix's default mechanism for broadcasting 
short-lived data to a group of users and with the advent of user-defined ones 
they perfectly fit live location sharing. 
They are intended to be non-persistent, not take part in a room's history and 
are currently used for typing notifications, event receipts, and presence 
updates. As an extra precaution they can also be encrypted as defined in [MSC3673](https://github.com/matrix-org/matrix-doc/pull/3673).

We will start by introducing a new boolean property on `m.beacon_info` called 
`live` which will mark the start of an user's intent to share ephemeral location 
information.

```json5
{
    "type": "m.beacon_info.@stefan:matrix.org",
    "state_key": "@stefan:matrix.org",
    "content": {
        "m.beacon_info": {
            "description": "Stefan's live location",
            "timeout": 600000, // how long from the last event until we consider the beacon inactive in milliseconds
            "live": true // this is a live location beacon
        },
        "m.ts": 1436829458432, // creation timestamp of the beacon on the client
        "m.asset": {
            "type": "m.self.live" // live user location tracking
        }
    }
}
```

We define this new property in order to allow clients to distinguish between 
share types without potentially overwriting static ones.

Multiple live beacons on the same timeline have the option of either aggregating
all available location EDUs or just the ones referencing a particular 
`beacon_info`.

Subsequently clients will start sending beacon data EDUs to the new 
`rooms/{roomId}/ephemeral/{eventType}/{txnId}` endpoint where `eventType` equals 
`m.beacon` with the same location payload as defined in [MSC3489](https://github.com/matrix-org/matrix-doc/pull/3489).


```json5
{
    "m.relates_to": { // from MSC2674: https://github.com/matrix-org/matrix-doc/pull/2674
        "rel_type": "m.reference", // from MSC3267: https://github.com/matrix-org/matrix-doc/pull/3267
        "event_id": "$beacon_info"
    },
    "m.location": {
        "uri": "geo:51.5008,0.1247;u=35",
        "description": "Arbitrary beacon information"
    },
    "m.ts": 1636829458432,
}
```

These will reach clients through `/sync`s `ephemeral` dictionary with the same 
payload but with the addition of a `sender` which the clients can aggregate user 
locations on.

When the user decides they would like to stop sharing their live location the 
original `m.beacon_info`'s `live` property should be set to `false`.

## Encryption

End to end encryption for ephemeral data units isn't currently available but a 
mechanism for achieving that is defined separately in [MSC3673](https://github.com/matrix-org/matrix-doc/pull/3673)

## Alternatives

Alternatively, we could negotiate a WebRTC data channel using [MSC3401](https://github.com/matrix-org/matrix-doc/pull/3401) 
and stream low-latency geospatial data over the participating devices in the 
room. However it would be useful to support plain HTTP like the rest of Matrix 
and requiring a WebRTC stack is prohibitively complicated for simple clients 
(e.g. basic IOT devices reporting spatial telemetry).

Another alternative is to use to-device events but that comes with disadvantages
of its own as they're 1:1, single message per transaction and not intended for 
conversational data.

## Unstable prefix

 * `m.beacon_info.*` should be referred to as `org.matrix.msc3489.beacon_info.*` until this MSC lands.
 * `m.beacon` should be referred to as `org.matrix.msc3489.beacon` until this MSC lands.
 * `m.location` should be referred to as `org.matrix.msc3488.location.*` until MSC3488 lands.
 * `m.ts` should be referred to as `org.matrix.msc3488.ts.*` until MSC3488 lands.
 * `m.asset` should be referred to as `org.matrix.msc3488.asset.*` until MSC3488 lands.