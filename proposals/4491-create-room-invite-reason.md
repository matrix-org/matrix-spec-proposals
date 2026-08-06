# MSC4491: Invite reasons in room creation

[`POST /_matrix/client/v3/createRoom`][spec-createRoom] allows you to specify a list of user IDs to
invite (via `invite`). It further allows you to mark these invites as "direct", via `is_direct`,
indicating to the recipient(s) that this room is intended to be a DM room. However, there is
currently no mechanism within which to specify an invitation *reason*, which can leave recipients
confused as to why they received an invite, and may lead them to mistake the invite for spam.

However, this `is_direct` flag [cannot be set after room creation][spec-is_direct-sb], without
manually sending the invite membership state event (see [Alternatives](#alternatives)).
This means that inviting a recipient after the room is created (in order to include a `reason`)
will not tell the recipient that the invite is to a direct message, which again results in confusion
and poor UX[^gomuks#731].

[spec-createRoom]: https://spec.matrix.org/v1.18/client-server-api/#post_matrixclientv3createroom
[spec-is_direct-sb]: https://spec.matrix.org/v1.18/client-server-api/#server-behaviour-16
[^gomuks#731]: See the demo video in <https://github.com/gomuks/gomuks/pull/731>

## Proposal

This proposal introduces a new optional field in the `/createRoom` payload: `invite_reason`.

`invite_reason` is an optional string that, if provided, should be the `reason` included
in each `m.room.member` invite state event sent by the server resulting from the `invite` array.
If the field is empty or omitted, no reason is attached to the implied invites.

An example of this in practice could be a client informing a user why they are being invited to a
DM ahead of time, or a client upgrading a room attaching a "this room was upgraded" so members
aren't surprised by a random invite to a room they may not have used in a long time.

Another use-case could be safety related: clients may opt to reject any invites that lack a reason,
especially from users they do not share a room with or have no non-public mutual rooms with. This
would also open the possibility for a future extension to [invite blocking][spec-invite-blocking].

[spec-invite-blocking]: https://spec.matrix.org/v1.18/client-server-api/#invite-permission

## Potential issues

`/createRoom` is already a complex endpoint, and this proposal adds yet another (albeit minor)
feature to it. A future proposal may wish to tackle the complexity of `/createRoom`.

`invite_reason` is unencrypted - inconsiderate UI choices may result in the user believing their
invitation reasons are also encrypted (especially when creating DMs). Clients should take additional
precautions to ensure users are aware that their invitations will not be encrypted, perhaps with a
red shield in the input box, or some other familiar mechanism.

### Abuse

Unsolicited invites are a known abuse vector in Matrix, with ongoing efforts to reduce the area.
As such, concerns regarding abuse are explicitly called out here:

A malicious actor could use this to distribute invite spam with abusive reasons even faster than
prior to this proposal if the homeserver does not implement sufficient rate-limiting technologies on
room-creation invites. Prior, actors would be limited either by the rate-limit applied to the
individual invite endpoint, or at least by the rate at which they could create individual requests.

Server implementations MAY also wish to refuse to create rooms where an invite reason is too long
or otherwise is flagged by a spam filter in order to prevent malicious users mass-distributing
abusive messages in invite reasons. Implementations may already have implemented this on the
[invite endpoint][spec-invite], although this is not explicitly specified behaviour.

[spec-versions]: https://spec.matrix.org/v1.18/client-server-api/#get_matrixclientversions

## Alternatives

* [`POST /_matrix/client/v3/rooms/{roomId}/invite`][spec-invite] could be modified to accept
  `is_direct` as a body parameter, but this might allow clients to incorrectly mark rooms as direct
  and indirect when issuing an invite, and preventing that would require the server tracks the flag
  for the room (at which point, the server might as well issue the invites anyway).

* Sending the `m.room.member` state event manually has also been considered, but the author deemed
  this non-idiomatic, and also relies upon the server supporting creating (typically federated)
  invites on-the-fly while handling new events, which is not guaranteed behaviour.

* A new endpoint that replaces `invite` with a new mapping, which would allow
  `is_direct` and/or `reason` to be supplied atomically, may be worth consideration, but would
  require an endpoint version bump, has more complex implementation shapes, and is otherwise
  something the author is not interested in pursuing unless there is expressed interest in this
  more demanding change.

[spec-invite]: https://spec.matrix.org/v1.18/client-server-api/#post_matrixclientv3roomsroomidinvite

## Security considerations

None.

## Unstable prefix

`uk.timedout.msc4491` should be used as a prefix for the new fields until this proposal is stable.

| Stable | Unstable |
| ------ | -------- |
| `invite_reason` | `uk.timedout.msc4491.invite_reason` |

`uk.timedout.msc4491.create_room_invite_reasons` SHOULD be present in the `unstable_features` of
[`GET /_matrix/client/versions`][spec-versions] until this proposal is merged, to indicate
unstable support for the new fields.

This proposal is intended to be backwards compatible and thus does not need to bump any versions.

## Dependencies

None.
