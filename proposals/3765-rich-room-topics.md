# MSC3765: Rich text in room topics

## Problem

Topics are a central piece of room meta data and usually made easily
accessible to room members in clients. As a result, room administrators
often extend the use of topics to collect helpful peripheral information
that is related to the room’s purpose. Most commonly these are links to
external resources. At the moment, topics are limited to [plain text]
which, depending on the number and length of URLs and other content,
easily gets inconvenient to consume and calls for richer text formatting
options.

## Proposal

Drawing from extensible events as described in [MSC1767],
`m.room.topic` is formally deprecated and replaced with a new `m.topic`
event type. The latter contains an `m.markup` content block representing
the room topic in different mime types.

``` json5
{
    "type": "m.topic",
    "state_key": "",
    "content": {
        "m.markup": [{
            "mimetype": "text/html",
            "body": "All about <b>pizza</b> | <a href=\"https://recipes.pizza.net\">Recipes</a>"
        }, {
            "mimetype": "text/plain",
            "body": "All about **pizza** | [Recipes](https://recipes.pizza.net)"
        }],
    },
    ...
}
```

Details of how `m.markup` works may be found in [MSC1767] and are not
repeated here.

While the content of `m.topic` is currently identical to `m.message`, a
dedicated event type allows the two to diverge in the future.

A change to `/_matrix/client/v3/createRoom` is not necessary. The
endpoint has a plain text `topic` parameter but also allows to specify a
full `m.topic` event in `initial_state`.

Room topics also occur as part of the `PublicRoomsChunk` object in the
responses of `/_matrix/client/v3/publicRooms` and
`/_matrix/client/v1/rooms/{roomId}/hierarchy`. The topic can be kept
plain text here because this data should commonly only be displayed to
users that are *not* a member of the room yet. These users will not have
the same need for rich room topics as users who are inside the room.

## Transition

The same transition mechanism as in [MSC1767] is proposed. In
particular, this means a new room version N is introduced. Starting from
N clients are not permitted to send `m.room.topic` events anymore and
MUST treat `m.room.topic` as an invalid event type. Instead the new
`m.topic` event type is to be used.

Similarly, servers use the `m.topic` event type instead of
`m.room.topic` when creating rooms with a room version greater or equal
to N.

Specific care should be taken when rooms are upgraded via
[`/rooms/{roomId}/upgrade`]. If the new room version is greater or
equal to N, an existing `m.room.topic` event in the old room

``` json5
{
    "type": "m.room.topic",
    "state_key": "",
    "content": {
        "topic": "All about pizza"
    },
    ...
}
```

should be migrated to an `m.topic` event with a single plain-text markup
in the new room

``` json5
{
    "type": "m.topic",
    "state_key": "",
    "content": {
        "m.markup": [{
            "mimetype": "text/plain",
            "body": "All about pizza"
        }],
    },
    ...
}
```

## Potential issues

None.

## Alternatives

The combination of `format` and `formatted_body` currently utilised to
enable HTML in `m.room.message` events could be generalised to
`m.topic` events. However, this would only allow for a single
format in addition to plain text and is a weaker form of reuse than
described in the introductory section of [MSC1767].

## Security considerations

Allowing HTML in room topics is subject to the same security
considerations that apply to HTML in room messages.

## Unstable prefix

While this MSC is not considered stable, `m.topic` should be referred to
as `org.matrix.msc3765.topic`.

## Dependencies

- [MSC1767]

  [plain text]: https://spec.matrix.org/v1.2/client-server-api/#mroomtopic
  [MSC1767]: https://github.com/matrix-org/matrix-spec-proposals/pull/1767
  [`/rooms/{roomId}/upgrade`]: https://spec.matrix.org/v1.5/client-server-api/#post_matrixclientv3roomsroomidupgrade
