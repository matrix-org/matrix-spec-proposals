# MSC3488 - m.location: Extending events with location data

## Problem

We need a standard way to share location data about events in Matrix. Use
cases include sharing freeform static location info, sharing live-updating
location data of assets, associating location data with IOT telemetry, etc.

The spec currently has the concept of an `m.location` `msgtype` on
`m.room.message` events, but this is very limiting as it only applies to
sharing location as an instant message.  Instead, we'd like to leverage
extensible events (MSC1767) to associate location data with any kind of
event.

## Proposal

We introduce `m.location` as an extensible event type: a key which can be
placed in the `content` of any event to associate a location object with the
other data (if any) in that event.  Clients which are location-aware may
let the user view events containing `m.location` on a map.

This is intended to eventually replace the `m.location` msgtype (although this
MSC doesn't obsolete it)

The `m.location` object must contain a `uri` field with a standard RFC5870
`geo:` URI.  It may also contain an optional `description` field, giving a
free-form label that should be used to label this location on a map. This is
not to be confused with fallback text representations of the event, which are
given by `m.text` or `m.html` as per MSC1767.  The description field is also
not intended to include semantic descriptions of the location (e.g. the
details of a calendar invite), which should be stored in their respective
extensible event types when available.

XXX: should description be localised?

```json
        "m.location": {
            "uri": "geo:51.5008,0.1247;u=35",
            "description": "Our destination",
        },
```

If sharing the location of an object, one would add another subtype (e.g. a
hypothetical `m.asset` type) to give the object a type and ID.

If sharing time-sensitive data, one would add another subtype (e.g. a
hypothetical `m.ts` type) to spell out the exact time that the data in the
event refers to (milliseconds since the UNIX epoch)

If `m.location` is used as the event type itself, it describes a contextless
static location, suitable for "drop a pin on a map" style use cases.

Example for sharing a static location:

```json
{
    "type": "m.location",
    "content": {
        "m.location": {
            "uri": "geo:51.5008,0.1247;u=35",
            "description": "Matthew's whereabouts",
        },
        "m.ts": 1636829458432,
        "m.text": "Matthew was at geo:51.5008,0.1247;u=35 as of Sat Nov 13 18:50:58 2021"
    }
}
```

## Alternatives

We could use GeoJSON (RFC7946) to describe the location.  However, it doesn't
support the concept of uncertainty, and is designed more for sharing map
annotations than location sharing. It would look something like this if we
used it:

```json
        "m.geo": {
            "type": "Point", 
            "coordinates": [30.0, 10.0]
        }
```

Another design choice is to represent static shared locations as a normal room
event rather than a state event.  The reason we've chosen non-state events is
so that the data is subject to normal history visibility: it's very much a
transient event. Just because I temporarily mention a location to someone
doesn't mean I want it pinned in the room state forever more.  On the other
hand, it means that streaming location data (where you do want to keep track
of the current location in room state) ends up being a different shape, which
could be a little surprising.

## Security considerations

Geographic location data is high risk from a privacy perspective.
Clients should remind users to be careful where they send location data,
and encourage them to do so in end-to-end encrypted rooms, given the
very real risk of real-world abuse from location data.

## Unstable prefix

`m.location` used as a event type and extensible event field name should be
referred to as `org.matrix.msc3488.location` until this MSC lands.
`m.ts` should be referred to as `org.matrix.msc3488.ts` until this MSC lands.