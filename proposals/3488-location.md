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

The `m.location` object must contain a `uri` field with a standard RFC5870 `geo:` URI.

It may also contain an optional `description` field, giving a
free-form label that should be used to label this location on a map. This is
not to be confused with fallback text representations of the event, which are
given by `m.text` or `m.html` as per MSC1767.  The description field is also
not intended to include semantic descriptions of the location (e.g. the
details of a calendar invite), which should be stored in their respective
extensible event types when available.

XXX: should description be localised?

`m.location` can also contain an optional `zoom_level` field to specify the 
displayed area size on client mapping libraries.
Possible values range from 0 to 20 based on the definitions from 
[OpenStreetMap here](https://wiki.openstreetmap.org/wiki/Zoom_levels) and it
would be the client's responsibility to map them to values a particular library
uses, if different. The client is also free to completely ignore it and decide
the zoom level through other means.

```json5
"m.location": {
    "uri": "geo:51.5008,0.1247;u=35",
    "description": "Our destination",
    "zoom_level": 15,
}
```

In order to differentiate between user tracking and other objects we also
introduce a new subtype called `m.asset` to give the object a type and ID.

`m.asset` defines a generic asset that can be used for location tracking 
but also in other places like inventories, geofencing, checkins/checkouts etc.
It should contain a mandatory namespaced `type` key defining what particular 
asset is being referred to. 
For the purposes of user location tracking `m.self` should be used in order to
avoid duplicating the mxid.

If `m.asset` is missing from the location's content the client should render it 
as `m.self` as that will be the most common use case. 
Otherwise, if it's not missing but the type is invalid or unknown the client 
should attempt to render it as a generic location. 
Clients should be able to distinguish between `m.self` and explicit assets for
this feature to be correctly implemented as interpreting everything as `m.self`
is unwanted.


If sharing time-sensitive data, one would add another subtype (e.g. a
hypothetical `m.ts` type) to spell out the exact time that the data in the
event refers to (milliseconds since the UNIX epoch)

If `m.location` is used as the event type itself, it describes a contextless
static location, suitable for "drop a pin on a map" style use cases.

Example for sharing a static location:

```json5
{
    "type": "m.location",
    "content": {
        "m.location": {
            "uri": "geo:51.5008,0.1247;u=35",
            "description": "Matthew's whereabouts",
        },
        "m.asset": {
            "type": "m.self" // the type of asset being tracked
        },
        "m.ts": 1636829458432,
        "m.text": "Matthew was at geo:51.5008,0.1247;u=35 as of Sat Nov 13 18:50:58 2021"
    }
}
```

## Migration from the `m.location` msgtype

Historically in Matrix, static locations have been shared via the `m.location`
msgtype in `m.room.message`. Until that API is deprecated from the spec,
clients should share static locations in a backwards-compatible way by mixing
in the `m.location` extensible event type from this MSC into the old-style
`m.room.message`.  During this migratory phase, this necessarily duplicates the
relevant data.  If both fields are present, clients that speak MSC3488 should
favour the contents of the MSC3488 fields over the legacy `geo_uri` field.

```json5
{
    "type": "m.room.message",
    "content": {
        "body": "Matthew was at geo:51.5008,0.1247;u=35 as of Sat Nov 13 18:50:58 2021",
        "msgtype": "m.location",
        "geo_uri": "geo:51.5008,0.1247;u=35",
        "m.location": {
            "uri": "geo:51.5008,0.1247;u=35",
            "description": "Matthew's whereabouts",
        },
        "m.asset": {
            "type": "m.self" // the type of asset being tracked
        },
        "m.text": "Matthew was at geo:51.5008,0.1247;u=35 as of Sat Nov 13 18:50:58 2021",
        "m.ts": 1636829458432,
    }
}
```

This means that clients which do not yet implement MSC3488 will be able to
correctly handle the location share. In future, an MSC will be written to
officially deprecate the `m.location` msgtype from the spec, at which point
clients should start sending `m.location` event types instead.  Clients should
grandfather in the old `m.location` msgtype format for posterity in order to
display old events; this is unavoidable (similar to HTML being doomed to display
blink tags until the end of days).

## Alternatives

We could use GeoJSON (RFC7946) to describe the location.  However, it doesn't
support the concept of uncertainty, and is designed more for sharing map
annotations than location sharing. It would look something like this if we
used it:

```json5
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

All points from https://www.w3.org/TR/geolocation/#security apply.

## Well-known configuration

Homeservers should be allowed to define a custom tile server to use. For that 
we introduce a new key in `.well-known` called `m.tile_server` which should 
contain a `map_style_url` pointing to the desired map style `json`.

Clients should read the `.well-known` and reconfigure accordingly, with values
coming from it taking precedence over base configuration.

```json5
{
    "m.tile_server": { 
        "map_style_url": "https://www.example.com/style.json"
    },
    
    
    "m.homeserver": {
        "base_url": "https://matrix-client.matrix.org"
    },
    "m.identity_server": {
        "base_url": "https://vector.im"
    }
}
```

## Unstable prefix

 * `m.location` used as a event type and extensible event field name should be
referred to as `org.matrix.msc3488.location` until this MSC lands.
 * `m.ts` should be referred to as `org.matrix.msc3488.ts` until this MSC lands.
 * `m.asset` should be referred to as `org.matrix.msc3488.asset` until this MSC lands.
 * `m.tile_server` should be referred to as `org.matrix.msc3488.tile_server` until this MSC lands.
