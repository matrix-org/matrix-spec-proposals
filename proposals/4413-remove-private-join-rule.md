# MSC4413: Remove `private` join_rule

## Problem

Back in the darkest beginnings of Matrix, we conjectured that Matrix rooms might benefit from a `private`
join_rule, which meant that no new users would be able to join a given room (even if invited):
 * https://github.com/matrix-org/synapse-ancient/commit/53153c77b

This was never fully implemented by Synapse (particularly the `may_join` concept, which was eventually
overtaken by the `restricted` join_rule).

Meanwhile, `private` made it into the spec as a restricted keyword (presumably to reflect that some
implementations might have been using it anyway, or perhaps to speculatively reserve it for future use):
 * https://github.com/matrix-org/matrix-spec-proposals/commit/9d7f2baf5

This was then updated to be "reserved without implementation. No significant meaning." while specifying
restricted rooms:
 * https://github.com/matrix-org/matrix-spec-proposals/commit/6c4aabd05

This is unhelpful, because:
 * Rooms with unrecognised join_rules are treated with 'private' semantics anyway (i.e. nobody can join them,
   even if invited) - see https://github.com/matrix-org/matrix-spec/issues/657
 * It is *very* easy to mistake `private` for `invite` join_rule and introduce relatively subtle
   bugs when configuring join_rules - see https://github.com/ruma/ruma/issues/2354, and both Element X iOS
   and Element X Android incorrectly setting `private` join_rules at the time of writing.
 * In practice, we're not aware of anyone ever deliberating using the `private` join_rule, either clientside
   or serverside.
 * Rooms already have too many ways in which they can be 'public' or 'private' around various different axises;
   this eliminates one of the possible flavours of confusion.

## Proposal

We remove `private` from the spec entirely as of the next room version.

This means that it will not be explicitly "reserved" per se, but given join_rules doesn't allow extensible
identifiers, all strings are reserved there anyway.

This then means that libraries like Ruma can then remove `private` from their join_rules enum and avoid future
confusion.

Meanwhile, if there are any clients out there relying on `private` semantics, then they will still work
(given unrecognised strings in a join_rule are treated as private anyway)

## Potential issues

If we were to change the default behaviour of join_rules with unrecognised string to not be 'private' semantics,
then we'd break anyone relying on the historical implicit behaviour of `private`. So if we ever do that, we might
need to reintroduce `private` as a keyword.

## Alternatives

Alternatively, we could actually make `private`'s intended semantics explicit at this point already:
"No other users are allowed to join the room, even if invited".  However this is redundant, given the
current auth rules, and opens us up to folks getting `private` and `invite` mixed up in future.

## Security considerations

See Potential Issues.

## Unstable prefix

None

## Dependencies

None