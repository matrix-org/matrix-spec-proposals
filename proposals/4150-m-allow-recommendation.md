# MSC4150: `m.allow` recommendation for moderation policy lists

The [moderation policy lists module] provides data structures to build rule-based moderation features
for Matrix. Each rule in a policy list has a so called recommendation which describes an action to be
taken when the rule matches against a certain subject.

At the time of writing, the only supported recommendation is [`m.ban`]. This is sufficient for building
block-list moderation tools where every entity is permitted by default and only those entities that match
to rules are denied.

With only a single recommendation, however, it's not possible to _also_ support allow-list systems where
every entity is denied by default and only those entities that match to rules are permitted. This is
prominently evidenced by the fact that existing moderation tools such as [Mjolnir] and [Draupnir] use a
custom `org.matrix.mjolnir.allow` recommendation[^1][^2] to provide both block-list and allow-list semantics[^3].

The proposal at hand attempts to close this gap by standardizing an `m.allow` recommendation.


## Proposal

A new recommendation `m.allow` is introduced. When this recommendation is used, the entities affected by
the rule should be allowed for participation where possible. As with `m.ban`, the enforcement is deliberately
left as an implementation detail. The existing [suggestions] for `m.ban` could simply be inverted, however.


## Potential issues

When both `m.ban` and `m.allow` recommendations are used in the same policy list, confusion could arise if
two rules with opposing recommendations match against an entity. Given that the spec doesn't currently
impose _any_ logic for how policy lists are to be interpreted, it could well leave this question as an
implementation detail, too.

However, if a resolution is indeed desired, the spec could mandate that `m.ban` rules override `m.allow`
rules but not the other way around. This matches both [Mjolnir's implementation] and the way
[server access control lists] are evaluated.


## Alternatives

None that the author could think of.


## Security considerations

None on top of what's already [listed] in the spec.


## Unstable prefix

Until this proposal is accepted into the spec, implementations should refer to `m.allow` as
`org.matrix.mjolnir.allow`.


## Dependencies

None.


[^1]: https://github.com/matrix-org/mjolnir/blob/5e35efd1dbc0097a7c19bed2831a1308a29d7be7/src/models/ListRule.ts#L63
[^2]: https://github.com/Gnuxie/matrix-protection-suite/blob/7fbf691f87056e01de7175b5322b25a901311409/src/PolicyList/PolicyRule.ts#L33
[^3]: A concrete use case that requires both block-list and allow-list semantics can be found in the
      Gematik messenger specification for the healthcare sector in Germany. The latter currently depends
      on a custom state event to control invite permissions:
      https://github.com/gematik/api-ti-messenger/blob/9b9f21b87949e778de85dbbc19e25f53495871e2/src/schema/permissionConfig.json

[`m.ban`]: https://spec.matrix.org/v1.10/client-server-api/#mban-recommendation
[listed]: https://spec.matrix.org/v1.10/client-server-api/#security-considerations-16
[Draupnir]: https://github.com/the-draupnir-project/Draupnir
[Mjolnir]: https://github.com/matrix-org/mjolnir
[Mjolnir's implementation]: https://github.com/matrix-org/mjolnir/blob/5e35efd1dbc0097a7c19bed2831a1308a29d7be7/src/models/AccessControlUnit.ts#L266
[moderation policy lists module]: https://spec.matrix.org/v1.10/client-server-api/#moderation-policy-lists
[server access control lists]: https://spec.matrix.org/v1.10/client-server-api/#mroomserver_acl
[suggestions]: https://spec.matrix.org/v1.10/client-server-api/#mban-recommendation
