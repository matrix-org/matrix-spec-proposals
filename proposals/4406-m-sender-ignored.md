# MSC4406: `M_SENDER_IGNORED` error code

Matrix has a concept called "ignoring", which allows users to request that events from a sender
are hidden from them. This typically involves the server no longer sending new events from the
sender through sync, and history pagination omitting the sender's events (excluding state events),
and invites not being sent to the user's clients.

Some servers, like Synapse and conduwuit, go a step further with this, and refuse to provide events
from ignored senders via `GET /_matrix/client/v3/rooms/{roomId}/events/{eventId}` [^synapse][^conduwuit]. While
this is, on the surface, a desirable behaviour (it prevents clients rendering ignored events that
get replied to by an unignored user), it causes clients to render messages like
"unable to load event" or "reply to unknown event". This is incredibly jarring in public rooms where
there is active conversation.

One of the issues with this approach is that *clients don't know why they can't see the event*.
This proposal introduces a supplementary error code for this specific scenario, `M_SENDER_IGNORED`,
which will allow clients to determine why an event is unavailable to it.

[^synapse]: https://github.com/element-hq/synapse/blob/a0e6a05/synapse/visibility.py#L186
[^conduwuit]: https://forgejo.ellis.link/continuwuation/continuwuity/src/commit/d8311a5/src/api/client/room/event.rs#L32-L34

## Proposal

This proposal amends [Section 10.26.3: Ignoring Users: Server Behaviour][spec1] to clarify
that servers MUST NOT serve ignored events via the following endpoints by returning
`404 / M_SENDER_IGNORED` if the event at `eventId` has an ignored `sender`:

* [`/_matrix/client/v3/events/{eventId}`][getevent]
* [`/_matrix/client/v3/rooms/{roomId}/event/{eventId}`][getroomevent]
* [`/_matrix/client/v3/rooms/{roomId}/context/{eventId}`][context]
* [`/_matrix/client/v1/rooms/{roomId}/relations/{eventId}`][relations]
* [`/_matrix/client/v1/rooms/{roomId}/relations/{eventId}/{relType}`][relations2]
* [`/_matrix/client/v1/rooms/{roomId}/relations/{eventId}/{relType}/{eventType}`][relations3]

Errors with `M_SENDER_IGNORED` SHOULD include a `sender` property in their error response, like so:

```json
{
    "errcode": "M_SENDER_IGNORED",
    "error": "You have ignored the user that sent this event",
    "sender": "@user:example.org"
}
```

This will allow clients to know which user was ignored, which may allow them to present a button
to un-ignore the relevant user, or otherwise provider richer information to the user.

Endpoints that return multiple, potentially unrelated events, should instead filter out events
from ignored senders, as if they simply didn't exist. Per the current specification, should state
events be a required part of the endpoint's context (e.g. sync's `state`), those event should
remain in the results.

* [`/_matrix/client/v3/sync`][sync]
* [`/_matrix/client/v3/events`][events]
* [`/_matrix/client/v3/search`][search]
* [`/_matrix/client/v3/rooms/{roomId}/messages`][messages]
* [`/_matrix/client/v1/rooms/{roomId}/timestamp_to_event`][timestamp_to_event]
* [`/_matrix/client/v3/rooms/{roomId}/initialSync`][initial_sync]
* [`/_matrix/client/v3/rooms/{roomId}/context/{eventId}`][context]
* [`/_matrix/client/v1/rooms/{roomId}/relations/{eventId}`][relations]
* [`/_matrix/client/v1/rooms/{roomId}/relations/{eventId}/{relType}`][relations2]
* [`/_matrix/client/v1/rooms/{roomId}/relations/{eventId}/{relType}/{eventType}`][relations3]

Future endpoints that deal with returning event data should take these same ignore behaviours into
account.

[spec1]: https://spec.matrix.org/v1.17/client-server-api/#server-behaviour-16
[getevent]: https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv3events
[getroomevent]: https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv3events
[context]: https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv3roomsroomidcontexteventid
[relations]: https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv1roomsroomidrelationseventid
[relations2]: https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv1roomsroomidrelationseventidreltype
[relations3]: https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv1roomsroomidrelationseventidreltypeeventtype
[sync]: https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv3sync
[events]: https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv3events
[search]: https://spec.matrix.org/v1.17/client-server-api/#post_matrixclientv3search
[messages]: https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv3roomsroomidmessages
[timestamp_to_event]: https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv1roomsroomidtimestamp_to_event
[initial_sync]: https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv3roomsroomidinitialsync

## Potential issues

This proposal makes no effort to tackle the issue presented by ignoring users while being a
community moderator. While the error code revealing who is ignored may allow moderators to
temporarily un-ignore users for the purposes of moderation, it still prevents the calling user
from being able to see the events in question.

## Alternatives

None.

## Security considerations

None.

## Unstable prefix

| Unstable | Stable |
| -------- | ------ |
| `M_SENDER_IGNORED` | `uk.timedout.msc4406.sender_ignored` |

## Dependencies

None
