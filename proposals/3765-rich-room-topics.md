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

Drawing from extensible events as described in [MSC1767], `m.room.topic`
is prohibited in room versions that support extensible events and replaced
with a new `m.topic` event type. The latter contains a new content block
`m.topic` which wraps an `m.text` content block that allows representing
the room topic in different mime types.

``` json5
{
  "type": "m.topic",
  "state_key": "",
  "content": {
    "m.topic": {
      "m.text": [{
          "body": "All about **pizza** | [Recipes](https://recipes.pizza.net)"
      }, {
          "mimetype": "text/html",
          "body": "All about <b>pizza</b> | <a href=\"https://recipes.pizza.net\">Recipes</a>"
      }]
    }
  },
  ...
}
```

Details of how `m.text` works may be found in [MSC1767] and are not
repeated here.

The wrapping `m.topic` content block is similar to `m.caption` for file
uploads as defined in [MSC3551]. It avoids clients accidentally rendering
the topic state event as a room message.

In order to prevent formatting abuse in room topics, clients are
encouraged to limit the length of topics to at most two lines. Additionally,
clients should ignore things like headings and enumerations (or format them
as regular text). A future MSC may introduce a mechanism to capture extended
multiline details that are not suitable for room topics in a separate field
or event type.

A change to [`/_matrix/client/v3/createRoom`] is not necessary. The
endpoint has a plain text `topic` parameter but also allows to specify a
full `m.topic` event in `initial_state`.

Room topics also occur as part of the `PublicRoomsChunk` object in the
responses of [`/_matrix/client/v3/publicRooms`] and
[`/_matrix/client/v1/rooms/{roomId}/hierarchy`]. The topic can be kept
plain text here because this data should commonly only be displayed to
users that are *not* a member of the room yet. These users will not have
the same need for rich room topics as users who are inside the room. If
no plain text topic exists, home servers should return an empty topic
string from these end points. Since this will inevitably lead to bad UX,
client implementations are encouraged to always include a plain text
variant when sending `m.topic` events.

## Transition

As this MSC replaces `m.room.topic` for an extensible alternative,
clients and servers are expected to treat `m.room.topic` as invalid in
extensible event-supporting room versions.

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

[plain text]: https://spec.matrix.org/v1.12/client-server-api/#mroomtopic
[MSC1767]: https://github.com/matrix-org/matrix-spec-proposals/pull/1767
[MSC3551]: https://github.com/matrix-org/matrix-spec-proposals/pull/3551
[`/_matrix/client/v1/rooms/{roomId}/hierarchy`]: https://spec.matrix.org/v1.12/client-server-api/#get_matrixclientv1roomsroomidhierarchy
[`/_matrix/client/v3/createRoom`]: https://spec.matrix.org/v1.12/client-server-api/#post_matrixclientv3createroom
[`/_matrix/client/v3/publicRooms`]: https://spec.matrix.org/v1.12/client-server-api/#get_matrixclientv3publicrooms
