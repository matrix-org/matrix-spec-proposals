# MSC3173: Expose stripped state events to any potential joiner

It can be useful to view the partial state of a room before joining to allow a user
to know *what* they're joining. For example, it improves the user experience to
show the user the room name and avatar before joining.

It is already allowed to partially view the room state without being joined to
the room in some situations:

* If the room has `history_visibility: world_readable`, then anyone can inspect
  it (by calling `/state` on it).
* Rooms in the [room directory](https://matrix.org/docs/spec/client_server/latest#get-matrix-client-r0-publicrooms)
  expose some of their state publicly.
* [Invited users](https://matrix.org/docs/spec/server_server/r0.1.4#put-matrix-federation-v2-invite-roomid-eventid)
  and [knocking users](https://github.com/matrix-org/matrix-doc/pull/2403)
  receive stripped state events to display metadata to users.

This MSC proposes allowing the stripped state events that are currently available
to invited and knocking users to any user who could potentially join a room. It
also consolidates the recommendation on which events to include as stripped state
for potential joiners and provides a way to query for the stripped state directly.

This will allow for improved future use cases, such as:

* Improved user experience for more complicated access controls (e.g.
  [MSC3083](https://github.com/matrix-org/matrix-doc/pull/3083)).
* Showing a room preview on platforms when peeking fails (using for clients as
  well as matrix.to).
* Joining by alias (e.g. as in Element) could show a room preview.

## Background

When creating an invite it is [currently recommended](https://matrix.org/docs/spec/server_server/r0.1.4#put-matrix-federation-v2-invite-roomid-eventid)
to include stripped state events which are useful for displaying the invite to a user:

> An optional list of simplified events to help the receiver of the invite identify
> the room. The recommended events to include are the join rules, canonical alias,
> avatar, and name of the room.

The invited user receives these [stripped state events](https://spec.matrix.org/unstable/client-server-api/#get_matrixclientr0sync)
as part of the `/sync` response:

> The state of a room that the user has been invited to. These state events may
> only have the `sender`, `type`, `state_key` and `content` keys present. These
> events do not replace any state that the client already has for the room, for
> example if the client has archived the room.

These are sent as part of the [`unsigned` content of the `m.room.member` event](https://spec.matrix.org/unstable/client-server-api/#mroommember)
containing the invite.

[MSC2403: Add "knock" feature](https://github.com/matrix-org/matrix-doc/pull/2403)
extends this concept to also include the stripped state events in the `/sync` response
for knocking users:

> It is proposed to add a fourth possible key to rooms, called `knock`. Its value
> is a mapping from room ID to room information. The room information is a mapping
> from a key `knock_state` to another mapping with key events being a list of
> `StrippedStateEvent`.

It is also provides an extended rationale of why this is useful:

> These stripped state events contain information about the room, most notably the
> room's name and avatar. A client will need this information to show a nice
> representation of pending knocked rooms. The recommended events to include are the
> join rules, canonical alias, avatar, name and encryption state of the room, rather
> than all room state. This behaviour matches the information sent to remote
> homeservers when remote users are invited to a room.

[MSC1772: Spaces](https://github.com/matrix-org/matrix-doc/pull/1772) additionally
recommends including the `m.room.create` event as one of the stripped state events:

> Join rules, invites and 3PID invites work as for a normal room, with the exception
> that `invite_state` sent along with invites should be amended to include the
> `m.room.create` event, to allow clients to discern whether an invite is to a
> space-room or not.

## Proposal

This proposal includes a few aspects which are dealt with separately:

1. Generalizing when a user is allowed to view the stripped state of a room.
2. A consistent definition of stripped state and a recommendation for which
   events to include in the stripped state.
3. Providing a dedicated API for accessing the stripped state of the room.

### Accessing the stripped state of a room

Any user who is able to join a room shall be allowed to have access the stripped
state events of that room. Additionally, any user who could access the state of
a room may access the stripped state of a room, as it is a strict subset of
information.

Potential ways that a user might be able to join a room include, but are not
limited to, the following mechanisms:

* A room that has `join_rules` set to `public` or `knock`.
* A room that the user is in possession of an invite to (regardless of the `join_rules`).

Future MSCs might include additional mechanism for a user to join a room and
should consider this MSC, for example:

* [MSC3083: Restricting room membership based on space membership](https://github.com/matrix-org/matrix-doc/pull/3083)
  proposes allowing users to join a room based on their membership in a space (as defined in
  [MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772)).

### Stripped state definitions and recommended events

It is also proposed to create a single definition of what the stripped state of
a room is and for what events should be included in the stripped state to be
potential joiners.

The stripped state of a room is a list of simplified state events to help a
potential joiner identify the room. These state events may only have the
`sender`, `type`, `state_key` and `content` keys present. These events do not
replace any state that the client already has for the room, for example if the
client has archived the room.

It is recommended (although not required<sup id="a0">[0](#f0)</sup>) that
homeserver implementations include the following events as part of the stripped
state of a room:

* Create event (`m.room.create`)<sup id="a1">[1](#f1)</sup>
* Join rules (`m.room.join_rules`)
* Canonical alias (`m.room.canonical_alias`)
* Room avatar (`m.room.avatar`)
* Room name (`m.room.name`)
* Encryption information (`m.room.encryption`)<sup id="a2">[2](#f2)</sup>
* Room topic (`m.room.topic`)<sup id="a3">[3](#f3)</sup>

### Stripped state API

#### Client-server API

`GET /_matrix/client/r0/rooms/{roomIdOrAlias}/stripped_state`

A dedicated API is provided to query for the stripped state of a room. As
described above, any potential joiner may access the stripped state of a room
(and in the case of a room with `history_visibility: world_readable` -- anyone
may access the stripped state, as it is a strict subset of the state).

This API is rate-limited and does not require authentication.

The request format follows [the `/state` endpoint](https://matrix.org/docs/spec/client_server/latest#get-matrix-client-r0-rooms-roomid-state),
but with the addition of handling a `server_name` query parameter (as
specified for [the `/join/{roomIdOrAlias}` endpoint](https://matrix.org/docs/spec/client_server/latest#post-matrix-client-r0-join-roomidoralias)).

The response body includes an array of `StrippedState`, as
[described in the `/sync` response](https://matrix.org/docs/spec/client_server/latest#get-matrix-client-r0-sync).

If the homeserver does not know the state of the requested room it should use
the corresponding federation API to request the stripped state from another
homeserver.

TODO

##### Example request:

`GET /_matrix/client/r0/rooms/%21636q39766251%3Aexample.com/stripped_state HTTP/1.1`

##### Responses:

###### Status code 200:

The current stripped state of the room

```json
[
  {
    "content": {
      "join_rule": "public"
    },
    "type": "m.room.join_rules",
    "sender": "@example:example.org",
    "state_key": ""
  },
  {
    "content": {
      "creator": "@example:example.org",
      "room_version": "1",
      "m.federate": true,
      "predecessor": {
        "event_id": "$something:example.org",
        "room_id": "!oldroom:example.org"
      }
    },
    "type": "m.room.create",
    "sender": "@example:example.org",
    "state_key": ""
  }
]
```

Note that this is the same example as [the `/state` endpoint](https://matrix.org/docs/spec/client_server/latest#get-matrix-client-r0-rooms-roomid-state),
but limited to what would be returned as stripped state.

###### Status code 403:

You are not a member of the room, a potential joiner, and the room is not publicly viewable.

#### Server-server API

`GET /_matrix/federation/v1/stripped_state/{roomId}`

Retrieve the stripped state of a room, this is essentially identical to the
client-server API, but will not reach out over federation.

Path parameters:

* `roomId` - **Required.** The room ID to get state for.

Response format:

* `stripped_state` - `[StrippedState]` A list of simplified events to help identify the room.

The form of `StrippedState` is as defined in
[the `/invite/{roomId}/{eventId}` endpoint](https://matrix.org/docs/spec/server_server/latest#put-matrix-federation-v2-invite-roomid-eventid).

The stripped state should be returned to the requesting server if the host has
a potential joiner, e.g. if the room has `join_rules` set to `public` or any
user on the request server is in possession of an invite to the room. The
requesting server is responsible for filtering the returned data to the client.

## Potential issues

This is a generalization of current behavior and shouldn't introduce any new issues.

## Alternatives

A different approach to this would be to separately specify each situation in which
a user is allowed to see stripped state events, as we do currently for invites and
knocking.

## Security considerations

This would allow for invisibly accessing the stripped state of a room with `public`
or `knock` join rules.

In the case of a public room, if the room has `history_visibility` set to `world_readable`
then this is no change. Otherwise, it is trivial to access the state of the room
by joining, but currently users in the room would know that the join occurred.
Additionally, this information is already provided by the room directory (if
the room is listed there).

Similarly, in the case of knocking, a user is able to trivially access the
stripped state of the room by knocking, but users in the room would know that
the knock occurred.

This does not seem to be weakening the security expectations of either join rule.

## Future extensions

### Revisions to the room directory

A future MSC could include additional information from the stripped state events
in the [room directory](https://matrix.org/docs/spec/client_server/latest#get-matrix-client-r0-publicrooms).
The main missing piece seems to be the encryption information, but there may also
be other pieces of information to include.

### Additional ways to join a room

[MSC3083](https://github.com/matrix-org/matrix-doc/pull/3083) leverages this to
expose the information available in stripped state events via the spaces summary
for potential joiners due to membership in a space.

## Unstable prefix

| Stable Endpoint | Unstable Endpoint |
|---|---|
| `/_matrix/client/r0/rooms/{roomIdOrAlias}/stripped_state` | `/_matrix/client/unstable/org.matrix.msc3173/rooms/{roomIdOrAlias}/stripped_state` |
| `/_matrix/federation/v1/stripped_state/{roomId}` | `/_matrix/federation/unstable/org.matrix.msc3173/stripped_state/{roomId}` |

## Footnotes

<a id="f0"/>[0]: Privacy conscious deployments may wish to limit the metadata
available to users who are not in a room as the trade-off against user experience.
There seems to be no reason to not allow this. [↩](#a0)

<a id="f1"/>[1]: As updated in [MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772). [↩](#a1)

<a id="f2"/>[2]: The encryption information (`m.room.encryption`) is already sent
from Synapse and generally seems useful for  a user to know before joining a room.
[↩](#a2)

<a id="f3"/>[3]: The room topic (`m.room.topic`) is included as part of the
[room directory](https://matrix.org/docs/spec/client_server/latest#get-matrix-client-r0-publicrooms)
response for public rooms. It is also planned to be included as part of [MSC2946](https://github.com/matrix-org/matrix-doc/pull/2946)
in the spaces summary response. [↩](#a3)
