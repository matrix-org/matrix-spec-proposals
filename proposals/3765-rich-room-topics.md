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

It is recommended that clients always include a plain text variant when
sending `m.topic` events. This prevents bad UX in situations where a plain
text topic is sufficient such as the public rooms directory.

In order to prevent formatting abuse in room topics, clients are
encouraged to limit the length of topics to at most two lines. Additionally,
clients should ignore things like headings and enumerations (or format them
as regular text). A future MSC may introduce a mechanism to capture extended
multiline details that are not suitable for room topics in a separate field
or event type.

On the server side, any logic that currently operates on `m.room.topic` is
updated to use `m.topic` instead.

In [`/_matrix/client/v3/createRoom`], the `topic` parameter causes `m.topic`
to be written with a `text/plain` mimetype. If an `m.topic` event is supplied
in `initial_state`, the `topic` parameter overwrites its `text/plain` mimetype
but retains any other mimetypes.

In [`GET /_matrix/client/v3/publicRooms`], [`GET /_matrix/federation/v1/publicRooms`]
and their `POST` siblings, the `topic` response field is read from the
`text/plain` mimetype of `m.topic` if it exists or omitted otherwise.
A plain text topic is sufficient here because this data is commonly
only displayed to users that are *not* a member of the room yet. These
users don't have the same need for rich room topics as users who already
reside in the room.

The same logic is applied to [`/_matrix/client/v1/rooms/{roomId}/hierarchy`]
and [`/_matrix/federation/v1/hierarchy/{roomId}`].

In [server side search], the `room_events` category is expanded to search
over the `text/plain` mimetype in `m.topic`.

Finally, `m.topic` is also added to the events that are recommended for
inclusion in [stripped state].

## Transition

As this MSC replaces `m.room.topic` for an extensible alternative,
clients and servers are expected to treat `m.room.topic` as invalid in
extensible event-supporting room versions. Similarly, `m.topic` cannot
be used in non-extensible-supporting room versions.

It is recommended that servers replicate `m.room.topic` to `m.topic`
with a plain text mimetype and vice versa when [upgrading] between room
versions that do and don't support extensible events.

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
considerations that apply to HTML in room messages. In particular,
topics are already included in the content that clients should [sanitise]
for unsafe HTML.

## Other notes

Normally extensible events would only be permitted in a specific
room version. However, to facilitate adoption, clients MAY include
the `m.topic` content block in `m.room.topic` events in room
versions that don't support extensible events. They must, however,
take care to always duplicate the plain text mimetype into the
normal `topic` field, too. This ensures compatibility for clients
and servers that don't support this proposal. Since such clients
are likely to delete the `m.topic` content block when updating
`m.room.topic` themselves, it also helps prevent inconsistencies.

## Unstable prefix

While this MSC is not considered stable, `m.topic` should be referred to
as `org.matrix.msc3765.topic`. Note that extensible events and content
blocks might have their own prefixing requirements.

## Dependencies

- [MSC1767]

[plain text]: https://spec.matrix.org/v1.12/client-server-api/#mroomtopic
[MSC1767]: https://github.com/matrix-org/matrix-spec-proposals/pull/1767
[MSC3551]: https://github.com/matrix-org/matrix-spec-proposals/pull/3551
[sanitise]: https://spec.matrix.org/v1.12/client-server-api/#security-considerations
[server side search]: https://spec.matrix.org/v1.12/client-server-api/#server-side-search
[stripped state]: https://spec.matrix.org/v1.12/client-server-api/#stripped-state
[upgrading]: https://spec.matrix.org/v1.12/client-server-api/#room-upgrades
[`/_matrix/client/v1/rooms/{roomId}/hierarchy`]: https://spec.matrix.org/v1.12/client-server-api/#get_matrixclientv1roomsroomidhierarchy
[`/_matrix/client/v3/createRoom`]: https://spec.matrix.org/v1.12/client-server-api/#post_matrixclientv3createroom
[`/_matrix/federation/v1/hierarchy/{roomId}`]: https://spec.matrix.org/v1.12/server-server-api/#get_matrixfederationv1hierarchyroomid
[`GET /_matrix/client/v3/publicRooms`]: https://spec.matrix.org/v1.12/client-server-api/#get_matrixclientv3publicrooms
[`GET /_matrix/federation/v1/publicRooms`]: https://spec.matrix.org/v1.12/server-server-api/#get_matrixfederationv1publicrooms
