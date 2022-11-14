# MSC3787: Allowing knocks to restricted rooms

[Join rules](https://spec.matrix.org/v1.1/client-server-api/#mroomjoin_rules) define what conditions
a user must meet in order to, well, join a room. With the current setup it is impossible to have more
than one rule active at a time, which makes it difficult to allow anyone from room X to join, but also
join if their knock was accepted. The room would instead have to choose which condition it favoured.

Though generic approaches to allow arbitrary mixing of join rules are possible, such as those noted
in [MSC3613](https://github.com/matrix-org/matrix-spec-proposals/pull/3613) and
[MSC3386](https://github.com/matrix-org/matrix-spec-proposals/pull/3386), this proposal aims to fill
an immediate gap where rooms cannot allow knocks and also other join conditions through `restricted`
join rules. This is done by introducing yet another join rule, per the discussion on MSC3613 (which
was rejected in favour of the stop-gap approach described by this MSC).

Alternative MSCs, such as [MSC3386](https://github.com/matrix-org/matrix-spec-proposals/pull/3386),
seek to redesign the join rules structure entirely. This proposal is intended to fill a notable gap
while more complex MSCs work out their specifics.

## Proposal

In a new room version, we introduce a new `join_rule` for the
[`m.room.join_rules`](https://spec.matrix.org/v1.2/client-server-api/#mroomjoin_rules) event. This
new join rule would be called `knock_restricted` and inherit all of the behaviour of `knock` and
`restricted` - whichever of the two join rules is satisfied first allows a prospective member to
join. For example, a user can simply knock on the room (exactly as if the room was set up as `knock`
only), or if they met the `allow` conditions in the join rules then they could join without invite
(exactly as if the room was set up as `restricted` only).

The effect on the [authorization rules](https://spec.matrix.org/v1.2/rooms/v9/#authorization-rules)
is as follows:

* Rule 4.3.5 (handling of `m.room.member` joins) gets amended to say "If `join_rule` is `restricted`
  or `knock_restricted`:"
* Rule 4.7.1 (handling of `m.room.member` knocks) gets amended to say "If the `join_rule` is anything
  other than `knock` or `knock_restricted`, reject."

No other changes are required within the specification. Implementations might need to modify their
checks to ensure they appropriately look up the `allow` key of an `m.room.join_rules` event when the
`join_rule` is `restricted` *or* `knock_restricted` though.

## Potential issues

As a point of bikeshed, the name `knock_restricted` is not perfect. Alternative naming is possible,
however the author points the reader to the introduction where this MSC is outlined as a stop-gap
solution pending proper/formal addressing of the problem statement.

Clients will also need special rendering for this join rule. Such a user interface might be:

```
This room is:
[ ] Public
[x] Private

Join rules (disabled when Public):
[x] Allow members of `#space:example.org` to join
[x] Allow knocking
```

## Alternatives

[MSC3613](https://github.com/matrix-org/matrix-spec-proposals/pull/3613) is an obvious candidate
given it paved the path for this MSC. Ultimately, MSC3613 was rejected on not technical grounds but
rather pragmatic grounds: while we could support a system of mixing different join rules, the current
set of join rules don't make sense to mix outside of `knock`+`restricted`. So, we introduce a new
join rule for the exactly one useful case of mixing join rules.

[MSC3386](https://github.com/matrix-org/matrix-doc/pull/3386) and similar ideas favour a complete
rebuild of the join rules system. While a potentially great change for Matrix, it doesn't feel proper
for the short term.

## Security considerations

This MSC does not introduce too many new topics, so is not at risk of the same security considerations
which would normally accompany a new join rule. At best, this MSC makes it possible for a room to be
"less private" because of allowing knocks and other join conditions in the same room, however the rooms
using this setup will be doing so deliberately.

## Unstable prefix

Implementations of this MSC should use `org.matrix.msc3787` for the room version, using room version 9
for all other behaviours of the room.

## Dependencies

No relevant dependencies.
