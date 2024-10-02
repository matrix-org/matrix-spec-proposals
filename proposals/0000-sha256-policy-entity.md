# MSC0000: Hashed moderation policy entities

Currently, moderation policies describe the entity they are targeting
by including a literal identifier in the `entity` field.

This is problematic for multiple reasons.

#### Propagating abuse

The literal entities can propagate abuse. For example,
if the user
`@i.hate.example.com:example.com` is banned, then the
mxid will be embded in the policy.

Additionally, users have been known to embed or masquerade URLs
into their mxids.

#### Identifying users before encountering them

Policies can be used as an address book to identify problematic users
who have not been encountered by

For example, if `@yarrgh:example.com` is banned for `piracy`,
then it is obvious that `@yarrgh:example.com` could be a pirate.
Even if the reason was not provided with the policy.

## Proposal

We therefore propose a new field `hashes` to the top level of all
moderation policy events.
Embedded within this, we propose a simple `sha256` entity hash field.

```json
{
  "type": "m.policy.rule.user",
  "content": {
    "hashes": {
      "sha256": "VPqwbUV7mMMkOVto3kPwsNXXiALMs7VCKWh3OeqqjGs="
    },
	"recommendation": "m.takedown",
  }
}
```

In this example, when a moderation tool encounters a new user, or a
new policy, the tool will calculate the base64 encoded sha256
of their full mxid `@yarrgh:example.com` to
match against policies that provide an associated hash.


## Potential issues

None noted.

## Alternatives

None considered.

## Security considerations

### Dictionary attack

It's important for policy curators to understand that this proposal
does not prevent published hashes from being reversed.  The mechanism
that allows moderators to reveal banned users (by encountering them in
their community) is effectively a dicationary attack against the
policy list. This is how the proposal works by design. But this means
that a third party that collects a sufficient amount of data on the
Matrix ecosystem can reverse the hashes in the same way that a
moderator can, in order to publish their own version of the list in
clear text.

It's important to note that the hashes are only there for obscuration
purposes, to provide an indirect means to address entities. In order
to hide abuse embeded directly within the identifiers.  If attackers
have to go elsewhere to view the list or go through extensive data
collection to reveal all the hashes, then this is a secondary success.


## Unstable prefix

*If a proposal is implemented before it is included in the spec, then implementers must ensure that the
implementation is compatible with the final version that lands in the spec. This generally means that
experimental implementations should use `/unstable` endpoints, and use vendor prefixes where necessary.
For more information, see [MSC2324](https://github.com/matrix-org/matrix-doc/pull/2324). This section
should be used to document things such as what endpoints and names are being used while the feature is
in development, the name of the unstable feature flag to use to detect support for the feature, or what
migration steps are needed to switch to newer versions of the proposal.*

## Dependencies

- While not a dependency, the example shows the `m.takedown`
  recommendation, which is described in MSC0000 where is it FIXME
  AAAAAAAAAAa.
