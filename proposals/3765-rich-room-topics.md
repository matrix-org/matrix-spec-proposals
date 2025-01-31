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

Drawing from extensible events as described in [MSC1767], a new content
block `m.topic` is defined, which wraps an `m.text` content block that
allows representing the room topic in different mime types. In current
room versions, this content block is added to the content of [`m.room.topic`]
events as shown below[^1].

```json5
{
  "type": "m.room.topic",
  "state_key": "",
  "content": {
    "m.topic": {
      "m.text": [ {
        "mimetype": "text/html",
        "body": "All about <b>pizza</b> | <a href=\"https://recipes.pizza.net\">Recipes</a>"
      }, {
        "body": "All about **pizza** | [Recipes](https://recipes.pizza.net)"
      }]
    },
    "topic": "All about **pizza** | [Recipes](https://recipes.pizza.net)"
  },
  ...
}
```

In line with [MSC1767], clients should render the first mime type in the
array that they understand. Further details of how `m.text` works may
be found in [MSC1767] and are not repeated here.

The wrapping `m.topic` content block is similar to `m.caption` for file
uploads as defined in [MSC3551]. It avoids clients accidentally rendering
the topic as a room message. ([MSC1767] specifies that unknown events with
an `m.text` content block should be rendered as a regular room message, and
while [MSC1767] had explicitly excluded state events from being treated as 
extensible, this is being changed with [MSC4252].) The extra content block, therefore, allows putting
a fallback representation that is actually designated for the timeline
into a separate `content['m.text']` field. In addition, the `m.topic` content
block also serves as a good place for additional fields to be added by
other MSCs in the future.

It is recommended that clients always include a plain text variant within `m.text` when
sending `m.room.topic` events. This prevents bad UX in situations where a plain
text topic is sufficient such as the public rooms directory.

Additionally, clients should duplicate the plain text topic into the existing
`topic` field for backwards compatibility with clients that don't support
`m.topic` yet. This also helps prevent inconsistencies since such clients
are likely to delete the `m.topic` content block when updating `m.room.topic`
themselves.

In order to prevent formatting abuse in room topics, clients are
encouraged to limit the length of topics during both entry and display,
for instance, by capping the number of displayed lines. Additionally,
clients should ignore things like headings and enumerations (or format them
as regular text). A future MSC may introduce a mechanism to capture extended
multiline details that are not suitable for room topics in a separate field
or event type.

On the server side, any logic that currently operates on the `topic` field is
updated to use the `m.topic` content block instead:

- In [`/_matrix/client/v3/createRoom`], the `topic` parameter should cause `m.room.topic`
  to be written with a `text/plain` mimetype in `m.topic`. If at the same time an
  `m.room.topic` event is supplied in `initial_state`, it is overwritten entirely.
  A future MSC may generalize the `topic` parameter to allow specifying other mime
  types without `initial_state`.
- In [`GET /_matrix/client/v3/publicRooms`], [`GET /_matrix/federation/v1/publicRooms`]
  and their `POST` siblings, the `topic` response field should be read from the
  `text/plain` mimetype of `m.topic` if it exists or omitted otherwise.
  A plain text topic is sufficient here because this data is commonly
  only displayed to users that are *not* a member of the room yet. These
  users don't commonly have the same need for rich room topics as users
  who already reside in the room. A future MSC may update these endpoints
  to support rich text topics.
- The same logic is applied to [`/_matrix/client/v1/rooms/{roomId}/hierarchy`]
  and [`/_matrix/federation/v1/hierarchy/{roomId}`].
- In [server side search], the `room_events` category is expanded to search
  over the `m.text` content block of `m.room.topic` events.

## Potential issues

None.

## Alternatives

The combination of `format` and `formatted_body` currently utilised to
enable HTML in `m.room.message` events could be generalised to
`m.room.topic` events. However, this would only allow for a single
format in addition to plain text and is a weaker form of reuse than
described in the introductory section of [MSC1767].

## Security considerations

Allowing HTML in room topics is subject to the same security
considerations that apply to HTML in room messages. In particular,
topics are already included in the content that clients should [sanitise]
for unsafe HTML.

## Unstable prefix

While this MSC is not considered stable, `m.topic` should be referred to
as `org.matrix.msc3765.topic`.

[^1]: A future MSC may discuss how to adopt the `m.topic` content block in
      new room versions which support extensible events.

[plain text]: https://spec.matrix.org/v1.12/client-server-api/#mroomtopic
[MSC1767]: https://github.com/matrix-org/matrix-spec-proposals/pull/1767
[MSC4252]: https://github.com/matrix-org/matrix-spec-proposals/pull/4252
[sanitise]: https://spec.matrix.org/v1.12/client-server-api/#security-considerations
[server side search]: https://spec.matrix.org/v1.12/client-server-api/#server-side-search
[`m.room.topic`]: https://spec.matrix.org/v1.12/client-server-api/#mroomtopic
[`/_matrix/client/v1/rooms/{roomId}/hierarchy`]: https://spec.matrix.org/v1.12/client-server-api/#get_matrixclientv1roomsroomidhierarchy
[`/_matrix/client/v3/createRoom`]: https://spec.matrix.org/v1.12/client-server-api/#post_matrixclientv3createroom
[`/_matrix/federation/v1/hierarchy/{roomId}`]: https://spec.matrix.org/v1.12/server-server-api/#get_matrixfederationv1hierarchyroomid
[`GET /_matrix/client/v3/publicRooms`]: https://spec.matrix.org/v1.12/client-server-api/#get_matrixclientv3publicrooms
[`GET /_matrix/federation/v1/publicRooms`]: https://spec.matrix.org/v1.12/server-server-api/#get_matrixfederationv1publicrooms
