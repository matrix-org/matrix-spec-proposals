# MSC4271: Recommended `enabled`-ness for default push rules

Homeservers are required to deploy a set of [predefined push rules] into user
accounts. For one thing, the specification covers the sheer existence of these
predefined rules. This is sensible as a means to preventing clients from
inventing their own set of default rules.

Additionally, however, the specification also prescribes the initial value of
each rule's `enabled` field. While the default `enabled`-ness is adequate for
the majority of use cases, fixating the values in the spec prevents
customisation for more specialised usage scenarios. As an example, a server may
want to disable `.m.rule.suppress_notices` by default because it uses server
notices for time critical or otherwise important notifications.

The proposal at hand, retains the definition of default push rules while
granting server admins freedom in deciding on their initial `enabled` settings.

## Proposal

Servers MUST deploy the [predefined push rules] into user accounts. They SHOULD
use the `enabled` values as currently defined in the spec but MAY pick different
values based on their specific use cases and user base.

## Potential issues

None.

## Alternatives

The requirement to apply the default `enabled` values could be downgraded
further to "CAN use". However, given that these values currently are a hard
requirement and that their adequateness is widely accepted, there is no
necessity for further flexibility.

As a more radical change, the deployment of predefined rules could be made
entirely optional. It is, however, [probable] that existing clients assume the
existence of these rules. Thus, removing them could lead to major compatibility
issues. Additionally, if clients cannot rely on the existence of standard rules,
they might clash over creating their own set of standard rules.

## Security considerations

None.

## Unstable prefix

None.

## Dependencies

None.

  [predefined push rules]: https://spec.matrix.org/v1.13/client-server-api/#predefined-rules
  [probable]: https://github.com/matrix-org/synapse/issues/9325#issuecomment-1285895341
