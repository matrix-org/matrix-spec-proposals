# MSC3677: Rich text in room topics

## Problem

Topics are a central piece of room meta data and usually made easily
accessible to room members in clients. As a result, room administrators
often extend the use of topics to collect helpful peripheral information
that is related to the room’s purpose. Most commonly these are links to
external resources. At the moment, topics are limitted to [plain text]
which, depending on the number and length of URLs and other content,
easily gets inconvenient to consume and calls for richer text formatting
options.

## Proposal

To enrich `m.room.topic` events, we build upon extensible events as
defined in [MSC1767] and define a new `m.topic` event in `content`.
The latter contains a list of renderings in the same format that
[MSC1767] uses for `m.message` events.

``` json
{
    "type": "m.room.topic",
    "state_key": "",
    "content": {
        "m.topic": [{
            "mimetype": "text/html", // optional, default text/plain
            "body": "All about <b>pizza</b> | <a href=\"https://recipes.pizza.net\">Recipes</a>"
        }, {
            "mimetype": "text/plain",
            "body": "All about **pizza** | [Recipes](https://recipes.pizza.net)"
        }],
    },
    ...
}
```

A change to `/_matrix/client/v3/createRoom` is not necessary. The
endpoint has a plain text `topic` parameter but also allows to specify a
full `m.room.topic` event in `initial_state`.

Room topics also occur as part of the `PublicRoomsChunk` object in the
responses of `/_matrix/client/v3/publicRooms` and
`/_matrix/client/v1/rooms/{roomId}/hierarchy`. The topic can be kept
plain text here because this data should commonly only be displayed to
users that are *not* a member of the room yet. These users will not have
the same need for rich room topics as users who are inside the room.

## Transition

Similar to [MSC1767] a time-constrained transition period is proposed.
Upon being included in a released version of the specification, the
following happens:

-   The `topic` field in the content of `m.room.topic` events is
    deprecated
-   Clients continue to include `topic` in outgoing events as a fallback
-   Clients prefer the new `m.topic` format in events which include it
-   A 1 year timer begins for clients to implement the above conditions
    -   This can be shortened if the ecosystem adopts the format sooner
    -   After the (potentially shortened) timer, an MSC is introduced to
        remove the deprecated `topic` field. Once accepted under the
        relevant process, clients stop including the field in outgoing
        events.

## Potential issues

None.

## Alternatives

The combination of `format` and `formatted_body` currently utilised to
enable HTML in `m.room.message` events could be generalised to
`m.room.topic` events. However, this would only allow for a single
format in addition to plain text and is a weaker form of reuse as
described in the introductory section of [MSC1767].

## Security considerations

Allowing HTML in room topics is subject to the same security
considerations that apply to HTML in room messages.

## Unstable prefix

While this MSC is not considered stable, implementations should apply
the behaviours of this MSC on top of room version 9 as
org.matrix.msc3677.

-   `m.topic` should be referred to as `org.matrix.msc3677.topic` until
    this MSC lands

## Dependencies

-   [MSC1767]

  [plain text]: https://spec.matrix.org/v1.2/client-server-api/#mroomtopic
  [MSC1767]: https://github.com/matrix-org/matrix-spec-proposals/pull/1767
