# MSC4044: Enforcing user ID grammar in rooms

The specification presently allows for a "historical" grammar for user IDs, described
[here](https://spec.matrix.org/v1.7/appendices/#historical-user-ids) and clarified by
[PR #1506](https://github.com/matrix-org/matrix-spec/pull/1506). The use of this historical
character set has allowed for "weird" and generally not-great user IDs to appear in the wild,
causing a variety of issues for software projects.

This proposal uses a future room version to strictly use the
[non-historical grammar](https://spec.matrix.org/v1.7/appendices/#user-identifiers) for user IDs,
preventing historical IDs from joining and participating in those room versions.

Matrix does not currently specify a way for a user with a historical ID to fix their user ID,
however it is envisioned that account portability will exist around the time of this MSC's
acceptance to provide an escape route. This is discussed in further detail in the "Potential Issues"
section.

## Proposal

In a future room version, the [non-historical grammar](https://spec.matrix.org/v1.7/appendices/#user-identifiers)
for user IDs is strictly enforced on all places a user ID can appear in an event. For example, the
`sender` of all events and `state_key` of `m.room.member` MUST match the grammar. All user IDs which
use the historical grammar, by any definition, are considered non-compliant.

By making this change in a room version, non-compliant user IDs are slowly removed from the public
federation. Several rooms will naturally upgrade to a room version which includes this MSC's change
after it becomes available in servers, and eventually the specification will update the
[recommended default room version](https://spec.matrix.org/v1.7/rooms/#complete-list-of-room-versions)
to include this MSC's change as well to affect new room creation.

In short, this MSC starts a multi-year process to formally phase out non-compliant user IDs as new
(and existing through upgrades) rooms use a room version which bans such user IDs.

## Potential issues

Though the intention of this MSC is to deliberately prevent non-compliant user IDs from appearing
in rooms, there are real users which are affected. The author is of the opinion that wildly non-compliant
user IDs (such as those using obscure unicode codepoints) should expect to be unable to participate,
however it is unfair to expect the same for users which innocently used capital letters in their
localparts. For example, `@Alice:example.org` should be provided a path to fix their user ID so they
can continue participating in conversations, without having to create a whole new account.

It is expected that Matrix accepts an MSC to support "account portability", giving users the option
of cross-server and local account transfers. A user could initiate a transfer to fix their user ID
to be compliant with the specification and thus allow them to join rooms employing this MSC's change.

If account portability supports it, a server could additionally self-initiate a transfer to fix
simple casing conflicts (ie: migrate `@Alice:example.org` to `@alice:example.org`). Servers are not
advised to "merge" accounts nor are they advised to manually fix "weird" user IDs on behalf of the
users. Instead, they should wait for a user-initiated transfer. For example, if `@Alice` and `@alice`
are both registered when the server wants to fix casing of its user IDs, the server *should not*
attempt to merge the two accounts nor should `@Alice` become `@alice2`. The user should be given
the opportunity to select a new (non-conflicting) localpart at their convenience.

Clients can additionally detect when the logged in account has a non-compliant user ID and prompt
them to self-initiate a transfer, provided the server supports such a transfer.

Account portability in Matrix is, as of writing, progressing under the pseudo IDs project. Prior
art for such MSCs include:

* [MSC1228: Removing MXIDs from events](https://github.com/matrix-org/matrix-spec-proposals/pull/1228)
* [MSC2787: Portable Identities](https://github.com/matrix-org/matrix-spec-proposals/pull/2787)
* [MSC3839: Primary-identity-as-key](https://github.com/matrix-org/matrix-spec-proposals/pull/3839)
* [MSC4014: Pseudonymous Identities](https://github.com/matrix-org/matrix-spec-proposals/pull/4014)

The general idea is that by breaking the association of user IDs with events, it becomes possible for
the user ID to change without affecting the events themselves. In the interim, MSCs like this one
help limit the ability for non-compliant IDs to spread (and provide a useful way for association-breaking
MSCs to only support compliant IDs).

## Alternatives

We don't do this, or hope that pseudo IDs fix the problem.

## Security considerations

This MSC improves the security posture of the protocol by reducing the likelihood of strange characters
appearing in user IDs.

## Unstable prefix

This MSC can be implemented in a room version identified as `org.matrix.msc4044`. A future MSC will
be required to incorporate this MSC into a stable room version.

## Dependencies

As of writing, this MSC is required by the Spec Core Team's documents/proposals within the MIMI working
group at the IETF.
