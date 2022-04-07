# MSC3672 - Sharing ephemeral streams of location data

## Problem

[MSC3489](https://github.com/matrix-org/matrix-doc/pull/3489) 
focuses on streaming persistent location data for applications that require
historical knowledge. 

While that's perfect for situations in which long term storage of the data is a 
non-issue and implied (e.g. flight paths, strava style exercises, fleet 
tracking), there are also cases in doing so is undesirable for either privacy 
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

We will start by introducing `m.beacon_info` as a new state event type; the event shape originally taken from [MSC3489](https://github.com/matrix-org/matrix-doc/pull/3489), but with some slight tweaks.

The `state_key` of this state event must be send to the sender's MXID. As per [event auth rules](https://spec.matrix.org/v1.2/rooms/v9/#authorization-rules), this restricts the state event to only be editable by the sender.

**`m.beacon_info` state event `content` field definitions**

| key | type | value | description | Required |
| ---- | ----| ----- | ----------- | -------- |
| `timeout` | int | A positive number of milliseconds | The maximum length of the location sharing session, relative to `m.ts`. | yes
| `description` | string | Optional descriptive text | A human-readable description of the live location sharing session. | no |
| `live` | bool | true | A boolean describing whether the location sharing session is currently active. Also denotes this session as ephemeral. | yes
| `m.ts` | int | [Unix timestamp](https://en.wikipedia.org/wiki/Unix_time) | The timestamp of when the location sharing session was started by the sender. | yes
| `m.asset` | dict | A dictionary (see below) | Describes the object being tracked. From [MSC3488](https://github.com/matrix-org/matrix-spec-proposals/pull/3488). | yes

TODO: This design does not currently allow for a user to have multiple live location sharing sessions active simultaneously. Incorporating either [MSC3671](https://github.com/matrix-org/matrix-spec-proposals/pull/3671) or [MSC3757](https://github.com/matrix-org/matrix-spec-proposals/pull/3757) will help here.

TODO: Is `m.ts` really needed on `m.beacon_info`? Or can we just simply use `origin_server_ts`?

**`m.asset` dictionary definition**

| key | type | value | description | required |
| ---- | --- | ----- | ----------- | -------- |
| `type` | string | `m.self`  | A string identifying the asset being tracked, as defined by [MSC3488](https://github.com/matrix-org/matrix-spec-proposals/pull/3488). `m.self` means this session tracks the sender's location. | yes |


A full example of the `m.beacon_info` state event:

```json5
{
    "type": "m.beacon_info",
    "state_key": "@stefan:matrix.org",
    "content": {
        "timeout": 600000,
        "description": "Stefan's live location",
        "live": true,
        "m.ts": 1436829458432,
        "m.asset": {
            "type": "m.self"
        }
    },
    "origin_server_ts": 1436829458474,
    "event_id": "$abcd:domain",
    "room_id": "!1234:domain"
}
```

Subsequently clients will start sending beacon data EDUs to the new 
`rooms/{roomId}/ephemeral/{eventType}/{txnId}` endpoint where `eventType` equals 
`m.beacon` with the following payload.

**`m.beacon` ephemeral event `content` field definitions**

| key | type | value | description | Required |
| ---- | ----| ----- | ----------- | -------- |
| `m.relates_to` | dictionary | Event reference, defined in [MSC2674](https://github.com/matrix-org/matrix-spec-proposals/pull/2674) | A reference to the state event defining a live location share that this location update is related to. | yes
| `m.location` | dictionary | An extensible event containing location data, defined in [MSC3267](https://github.com/matrix-org/matrix-spec-proposals/pull/3267) | The asset's location, and an optional description | yes |
| `m.ts` | int | [Unix timestamp](https://en.wikipedia.org/wiki/Unix_time) | The optional timestamp of when the location was recorded. If missing, clients should use `origin_server_ts`. | no

An full example of a `m.beacon` EDU as received by a client:

```json5
{
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
    },
    "type": "m.beacon",
    "sender": "@stefan:matrix.org",
    "origin_server_ts": 1636829518182
}
```

If multiple live beacons exist, clients have the option of either aggregating
all available location EDUs into one render or just those referencing a particular 
`m.beacon_info` state event.

When the user decides they would like to stop sharing their live location the 
original `m.beacon_info`'s `live` property should be set to `false`.

## Security considerations

End-to-end encryption for ephemeral data units isn't currently available, but a 
mechanism for achieving that is defined separately in [MSC3673](https://github.com/matrix-org/matrix-doc/pull/3673). This would prevent location data from being readable by homeservers participating in the room.

Likewise, end-to-end encryption for state events could be provided by [MSC3414](https://github.com/matrix-org/matrix-spec-proposals/pull/3414). This would hide the metadata that a user has started or stopped sharing their location from being known to the homeservers participating in the room.


## Alternatives

Alternatively, we could negotiate a WebRTC data channel using [MSC3401](https://github.com/matrix-org/matrix-doc/pull/3401) 
and stream low-latency geospatial data over the participating devices in the 
room. However it would be useful to support plain HTTP like the rest of Matrix 
and requiring a WebRTC stack is prohibitively complicated for simple clients 
(e.g. basic IOT devices reporting spatial telemetry).

Another alternative is to use to-device events but that comes with disadvantages
of its own as they're 1:1, single message per transaction and not intended for 
conversational data.

## Dependencies

This proposal relies on the following MSCs:

* [MSC2477: User-defined ephemeral events in rooms](https://github.com/matrix-org/matrix-doc/pull/2477)
* [MSC3488: Extending events with location data](https://github.com/matrix-org/matrix-spec-proposals/pull/3488)

## Unstable prefix

Until this MSC is merged, the following unstable prefixes should be used:

 * `m.beacon_info` should be referred to as `org.matrix.msc3672.beacon_info`
 * `m.beacon` should be referred to as `org.matrix.msc3672.beacon`

 Until [MSC3488](https://github.com/matrix-org/matrix-spec-proposals/pull/3488) is merged, the following unstable prefix should be used:

 * `m.location` should be referred to as `org.matrix.msc3488.location`
 * `m.ts` should be referred to as `org.matrix.msc3488.ts`
 * `m.asset` should be referred to as `org.matrix.msc3488.asset`