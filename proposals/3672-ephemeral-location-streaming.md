# MSC3672 - Sharing ephemeral streams of location data

## Problem

[MSC3489](https://github.com/matrix-org/matrix-doc/blob/matthew/location-streaming/proposals/3489-location-streaming.md) 
focuses on streaming persistent location data for applications that require
historical knowledge. 

We also need the ability to share this data in a non-persistent way for cases in 
which privacy is a concern, like user locations.

## Proposal

This MSC adds the ability to publish short-lived location beacons through the 
the use of custom Ephemeral Data Units (EDUs) by building on top of [MSC2476](https://github.com/ananace/matrix-doc/blob/user-defined-edus/proposals/2477-user-defined-ephemeral-events.md).

In order to do so we will start by introducing a new boolean property on 
`m.beacon_info` called `live` which will mark the start of an user's 
intent to share ephemeral location information.

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
`m.beacon` with the same location payload as defined in [MSC3489](https://github.com/matrix-org/matrix-doc/blob/matthew/location-streaming/proposals/3489-location-streaming.md).


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

E2E encryption for EDUs isn't currently defined but as we're dealing with 
privacy sensitive data we propose to wrap them inside the standard encryption
envelope:

```json5
{
    "algorithm": "m.megolm.v1.aes-sha2",
    "sender_key": "<sender_curve25519_key>",
    "device_id": "<sender_device_id>",
    "session_id": "<outbound_group_session_id>",
    "ciphertext": "<encrypted_payload_base_64>"
}
```

in which the `ciphertext` will contain the `m.beacon` payload defined above and
which will be sent to `rooms/{roomId}/ephemeral/m.room.encrypted/{txnId}`

The Megolm keys required to decrypt this EDU should be shared over Olm just like
regular encrypted timeline events.

## Alternatives

Alternatively, we could negotiate a WebRTC data channel using [MSC3401](https://github.com/matrix-org/matrix-doc/blob/matthew/group-voip/proposals/3401-group-voip.md) and stream low-latency geospatial data over the 
participating devices in the room. However it would be useful to support plain 
HTTP like the rest of Matrix and requiring a WebRTC stack is prohibitively 
complicated for simple clients (e.g. basic IOT devices reporting spatial telemetry).

## Unstable prefix

 * `m.beacon_info.*` should be referred to as `org.matrix.msc3489.beacon_info.*` until this MSC lands.
 * `m.beacon` should be referred to as `org.matrix.msc3489.beacon` until this MSC lands.
 * `m.location` should be referred to as `org.matrix.msc3488.location.*` until MSC3488 lands.
 * `m.ts` should be referred to as `org.matrix.msc3488.ts.*` until MSC3488 lands.
 * `m.asset` should be referred to as `org.matrix.msc3488.asset.*` until MSC3488 lands.