# MSC4303: Disallowing non-compliant user IDs in rooms

The specification presently allows for a "historical" grammar for user IDs, described
[here](https://spec.matrix.org/v1.15/appendices/#historical-user-ids). The use of this historical
character set has allowed for "weird" and generally not-great user IDs to appear in the wild,
causing a variety of issues for software projects.

The historical grammar can be split into two classes:

1. printable ASCII (U+0021 to U+007E), aka. historical-but-compliant
2. arbitrary unicode and blank localparts, aka. non-compliant

This proposal uses a future room version to prohibit the second class, while still allowing the first.
Users with non-ASCII user IDs will not be able to join or participate in those room versions.

This proposal does not cover room ID grammar, as that will be handled by another MSC,
such as [MSC4051](https://github.com/matrix-org/matrix-spec-proposals/pull/4051).

## Proposal

In a future room version, the historical-but-compliant grammar for user IDs is strictly enforced on
all places a user ID can appear in an event.

* The `sender` of all events.
* The `state_key` of `m.room.member` events.
* The `join_authorised_via_users_server` field in `m.room.member` events.
* Keys of the `users` object in `m.room.power_levels`.

User IDs in the new room version must only consist of ASCII characters between U+0021 and U+007E
and the localpart must not be empty.

By making this change in a room version, non-compliant user IDs are slowly removed from the public
federation. Several rooms will naturally upgrade to a room version which includes this MSC's change
after it becomes available in servers, and eventually the specification will update the
[recommended default room version](https://spec.matrix.org/v1.15/rooms/#complete-list-of-room-versions)
to include this MSC's change as well to affect new room creation.

In short, this MSC starts a multi-year process to formally phase out non-compliant user IDs as new
(and existing through upgrades) rooms use a room version which bans such user IDs.

## Potential issues

Unlike [MSC4044](https://github.com/matrix-org/matrix-spec-proposals/pull/4044), this MSC does
not define all historical user IDs as non-compliant. Therefore, real users who registered historical
user IDs should not be affected. Only accounts registered by modified servers will be prohibited
from participating in new rooms. Additionally, the existing spec already recommends servers drop
traffic from such non-compliant user IDs outside of rooms (e.g. in to-device events), which means
such users may already not be able to participate in encrypted rooms.

## Alternatives

[MSC4044](https://github.com/matrix-org/matrix-spec-proposals/pull/4044)

We don't do this, or hope that pseudo IDs fix the problem.

## Security considerations

This MSC improves the security posture of the protocol by reducing the likelihood of strange characters
appearing in user IDs.

## Unstable prefix

This MSC can be implemented in a room version identified as `fi.mau.msc4303` building on top of
room version 11. A future MSC will be required to incorporate this MSC into a stable room version.

## Dependencies

None.
