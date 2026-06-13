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
and poor UI[^gomuks#731].

[spec-createRoom]: https://spec.matrix.org/v1.18/client-server-api/#post_matrixclientv3createroom
[spec-is_direct-sb]: https://spec.matrix.org/v1.18/client-server-api/#server-behaviour-16
[^gomuks#731]: See the demo video in <https://github.com/gomuks/gomuks/pull/731>

## Proposal

This proposal introduces two new optional fields in the `/createRoom` payload: `invite_reasons` and
`invite_reason`.

`invite_reason` is an optional string that, if provided, should be the default `reason` included
in each `m.room.member` invite state event sent by the server resulting from the `invite` array.

`invite_reasons` is an optional mapping of `{user_id: string}`.
Each key should be a user ID that is already present in `invite`.
The value of each key should be the `reason` to set in each invite dispatched as a result of
`invite`.

Or, as a nicely presented table:

| Key              | Type                | Description |
| ---------------- | ------------------- | ----------- |
| `invite_reason`  | `string` (optional) | The default invite reason to include in any implied `m.room.member` events. |
| `invite_reasons` | `{string: string}` (optional) | Individual `reason`s to include in specific implied `m.room.member` events. |

Clients SHOULD NOT include user IDs in `invite_reasons` that are not in `invite`, and SHOULD NOT
make the value of any `invite_reasons` entry the same as `invite_reason`. Servers MUST ignore any
entries which appear in `invite_reasons` that do not also appear in `invite`.

For each user ID in `invite`:

1. If a user ID appears in `invite_reasons`, the value provided in that mapping should be used as
   the `reason` field, even if it is empty (which is akin to removing the reason for that specific
   invite, in which case the server may omit the reason field entirely).
2. If `invite_reason` is provided AND not empty, that value should populate the reason field.
3. Otherwise, no reason is attached to the invite.

An example usage of this two-field mechanism may be:

1. A client wishes to invite everyone in a
   predecessor room after an upgrade. It can include every joined member in `invite`, and provide
   `{"invite_reason": "This room was replaced, please join the new one."}`. Then, every user who
   receives an invite to that room knows exactly why they were invited, and is more likely to
   accept.
2. A client wishes to start a DM with a user, and would like to provide them with a reason before
   inviting them. In this case, if there's only one user to invite to the DM, `invite_reason`
   *could* suitably be used, but the client may instead opt to omit `invite_reason` and explicitly
   name the user in `invite_reasons`: `{"invite_reasons": {"@alice:example.com": "Hi Alice!"}}`.
3. A client wishes to start a group with a few users and wishes to preemptively explain why they
   were invited (via `invite_reason`), but modify the reason for
   certain members(via `invite_reasons`).

Another use-case could be safety related: clients may opt to reject any invites that lack a reason,
especially from users they do not share a room with or have no non-public mutual rooms with. This
would also open the possibility for a future extension to [invite blocking][spec-invite-blocking].

[spec-invite-blocking]: https://spec.matrix.org/v1.18/client-server-api/#invite-permission

## Potential issues

Servers which do not understand these new parameters will not be able to include reasons, which may
result in users unexpectedly issuing invites on room creation which lack a reason. To alleviate
this, clients MAY check [`GET /_matrix/clients/versions`][spec-versions] for an applicable spec
version (if merged), or the unstable prefix in [Unstable prefix](#unstable-prefix), before
presenting the user with a UI to include an invite reason when creating a room.

[spec-versions]: https://spec.matrix.org/v1.18/client-server-api/#get_matrixclientversions

## Alternatives

[`POST /_matrix/client/v3/rooms/{roomId}/invite`][spec-invite] could be modified to accept
`is_direct` as a body parameter, but this might allow clients to incorrectly mark rooms as direct
and indirect when issuing an invite, and preventing that would require the server tracks the flag
for the room (at which point, the server might as well issue the invites anyway).

Sending the `m.room.member` state event manually has also been considered, but the author deemed
this non-idiomatic, and also relies upon the server supporting creating (typically federated)
invites on-the-fly while handling new events, which is not guaranteed behaviour.

## Security considerations

A malicious actor could use this to distribute invite spam with abusive reasons even faster than
prior to this proposal if the homeserver does not implement sufficient rate-limiting technologies on
room-creation invites. Prior, actors would be limited either by the rate-limit applied to the
individual invite endpoint, or at least by the rate at which they could create individual requests.

## Unstable prefix

`uk.timedout.msc4491` should be used as a prefix for the new fields until this proposal is stable.

| Stable | Unstable |
| ------ | -------- |
| `invite_reason` | `uk.timedout.msc4491.invite_reason` |
| `invite_reasons` | `uk.timedout.msc4491.invite_reasons` |

`uk.timedout.msc4491.create_room_invite_reasons` SHOULD be present in the `unstable_features` of
[`GET /_matrix/client/versions`][spec-versions] until this proposal is merged, to indicate
unstable support for the new fields.

This proposal is intended to be backwards compatible and thus does not need to bump any versions.

## Dependencies

None.
