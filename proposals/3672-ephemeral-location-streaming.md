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

**`m.beacon_info` state event definition**

| type | key | value | description | Required |
| ---- | ----| ----- | ----------- | -------- |
| string | `type` | `m.beacon_info` | This state event defines a single location sharing session. | yes |
| string | `state_key` | The sender's MXID | As per [event auth rules](https://spec.matrix.org/v1.2/rooms/v9/#authorization-rules), this restricts the state event to only be editable by the sender. | yes |
| dict | `content->m.beacon_info` | An `m.beacon_info` dictionary (see below) | This defines the current state of the live location sharing session. | yes |
| int | `m.ts` | [Unix timestamp](https://en.wikipedia.org/wiki/Unix_time) | The timestamp of when the location sharing session was started by the sender. | yes
| dict | `m.asset` | A dictionary (see below) | Describes the object being tracked. From [MSC3488](https://github.com/matrix-org/matrix-spec-proposals/pull/3488). | yes

TODO: This design does not currently allow for a user to have multiple live location sharing sessions active simultaneously. Incorporating either [MSC3671](https://github.com/matrix-org/matrix-spec-proposals/pull/3671) or [MSC3757](https://github.com/matrix-org/matrix-spec-proposals/pull/3757) will help here.

**`m.beacon_info` dictionary definition**

| type | key | value | description | required |
| ---- | --- | ----- | ----------- | -------- |
| int | `timeout` | A positive number of milliseconds | The maximum length of the location sharing session, relative to a `m.ts`. | yes
| string | `description` | Optional descriptive text | A human-readable description of the live location sharing session. | no |
| bool | `live` | true | A boolean describing whether the location sharing session is currently active. Also denotes this session as ephemeral. | yes

TODO: `m.beacon_info` being used in two contexts is confusing.

**`m.asset` dictionary definition**

| type | key | value | description | required |
| ---- | --- | ----- | ----------- | -------- |
| string | `type` | `m.self`  | A string identifying the asset being tracked, as defined by [MSC3488](https://github.com/matrix-org/matrix-spec-proposals/pull/3488). `m.self` means this session tracks the sender's location. | yes |


A full example of the `m.beacon_info` state event:

```json5
{
    "type": "m.beacon_info",
    "state_key": "@stefan:matrix.org",
    "content": {
        "m.beacon_info": {
            "timeout": 600000,
            "description": "Stefan's live location",
            "live": true
        },
        "m.ts": 1436829458432,
        "m.asset": {
            "type": "m.self"
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

## Dependencies

This proposal relies on the following MSCs:

* [MSC2477: User-defined ephemeral events in rooms](https://github.com/matrix-org/matrix-doc/pull/2477)
* [MSC3488: Extending events with location data](https://github.com/matrix-org/matrix-spec-proposals/pull/3488)

## Unstable prefix

Until this MSC is merged, the following unstable prefixes should be used:

 * Any instance of `m.beacon_info` should be referred to as `org.matrix.msc3672.beacon_info`
 * `m.beacon` should be referred to as `org.matrix.msc3672.beacon`

 Until [MSC3488](https://github.com/matrix-org/matrix-spec-proposals/pull/3488) is merged, the following unstable prefix should be used:

 * `m.location` should be referred to as `org.matrix.msc3488.location`
 * `m.ts` should be referred to as `org.matrix.msc3488.ts`
 * `m.asset` should be referred to as `org.matrix.msc3488.asset`