# MSC4205: Hashed moderation policy entities

Currently, moderation policies describe the entity they are targeting
by including a literal identifier in the `entity` field.

This is problematic for multiple reasons.

#### Propagating abuse

The literal entities can propagate abuse. For example,
if the user
`@i.hate.example.com:example.com` is banned, then the
mxid will be embedded in the policy.

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
their community) is effectively a dictionary attack against the
policy list. This is how the proposal works by design. But this means
that a third party that collects a sufficient amount of data on the
Matrix ecosystem can reverse the hashes in the same way that a
moderator can, in order to publish their own version of the list in
clear text.

It's important to note that the hashes are only there for obscuration
purposes, to provide an indirect means to address entities. In order
to hide abuse embedded directly within the identifiers.  If attackers
have to go elsewhere to view the list or go through extensive data
collection to reveal all the hashes, then this is a secondary success.


## Unstable prefix

`org.matrix.msc4205.hashes` -> `hashes`

## Dependencies

- While not a dependency, the example shows the `m.takedown`
  recommendation, which is described in [MSC4204 `m.takedown`
  moderation policy
  recommendation](https://github.com/matrix-org/matrix-spec-proposals/pull/4204).
