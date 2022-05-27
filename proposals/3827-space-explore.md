# MSC3827: Filtering of `/publicRooms` by room type

[MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772) defines Spaces as
rooms with `type` of `m.space`. One of the most requested features for Spaces is
to have [a way to to discover
them](https://github.com/vector-im/element-web/issues/17264). To solve this
issue, this MSC proposes a mechanism for filtering the response of
`/publicRooms` by room type.

## Proposal

This MSC proposes adding a `room_type` filter to the `/publicRooms` endpoint.
The value of `room_type` is an array of room types - possible values of the
`type` field in the `m.room.create` state event - which should be returned.

An example request could look like this:

```HTTP
POST /_matrix/client/v3/publicRooms
{
    "filter": {
        "room_type": ["m.space"]
    },
    "limit": 10
}
```

the response then also includes a `room_type` field, so that clients can show
the room type metadata.

```json
{
    "chunk": [{
        "avatar_url": "mxc://bleecker.street/CHEDDARandBRIE",
        "guest_can_join": false,
        "join_rule": "public",
        "name": "CHEESE",
        "num_joined_members": 37,
        "room_id": "!ol19s:bleecker.street",
        "topic": "Tasty tasty cheese",
        "world_readable": true,
        "room_type": "m.space"
    }],
    "next_batch": "p190q",
    "prev_batch": "p1902",
    "total_room_count_estimate": 115
}

```

## Alternatives

### Using a special endpoint

A special endpoint for spaces and other room types could be used. Then each new
room type would require a special MSC and there would be no way to filter by
custom room types. Filtering by multiple types would be impossible.

### Replacing the room directory with a server-wide space

[A matrix-spec issue](https://github.com/matrix-org/matrix-spec/issues/830)
suggests replacing the room directory with a server-wide space; while this
solution certainly has benefits, it would require a lot of changes both on the
client and the server side.

## Unstable prefix

While this MSC is not considered stable, implementations should use
`org.matrix.msc3827` as a namespace.

|Release    |Development                   |
|-----------|------------------------------|
|`room_type`|`org.matrix.msc3827.room_type`|
