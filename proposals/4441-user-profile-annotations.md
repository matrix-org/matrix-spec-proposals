# MSC4441: User Profile Annotations ("Profile Notes")

Many platforms, such as Discord, provide a capability for a user to leave personal "notes" on a user's profile. Matrix,
however, has no similar functionality that can be shared between different clients. This proposal builds User Profile
Annotations, a method for storing personal metadata on user profiles.

## Proposal

This proposal introduces a new `m.profile_annotations` Account Data entry, allowing the storage of free text (and other
future annotations) on users. The framework introduced within this MSC provides room for future extension into other
forms of user context, such as contact labels and custom nickname overrides.

### `m.profile_annotations`

A new value, `m.profile_annotations`, is stored in [`account_data`][]. The `content` MUST
be a mapping between valid user MXIDs and annotations stored on that user. Within a user, the `m.text` property
represents a textual annotation ("note") on that user, with the object holding an ordered array as defined by [MSC1767][].

Clients MUST ignore and **preserve** unknown fields within profile annotations.

`m.profile_annotations`:

```json
{
    "@logn:zirco.dev": {
        "m.text": [
            { "body": "<i>Hello world</i>", "mimetype": "text/html" },
            { "body": "Hello world" }
        ]
    }
}
```

## Potential issues

### Concurrent writes
Account data is last-write-wins. The usage of one account data entry representing all users may lead to a data race in
rare scenarios (although this tradeoff was accepted to keep the behavior similar to existing state like `m.direct`).
In the future, other proposals may provide atomic write capabilities, which this proposal will benefit from.

### Information exposure
Because account data is not encrypted, the server administrator has access to information contained within users' defined
annotations. In the future, [MSC4483][] or a similar mechanism can allow for account data encryption to protect this
information. Clients may wish to tell users notes are not encrypted.

## Alternatives

### Store annotations as a new API endpoint
Rather than using `account_data`, a new dedicated endpoint for annotations would be created. Rejected because it
requires substantial serverside changes, this MSC aims to be entirely clintside.

## Trust and Safety considerations

Profile annotations are the property of one singular user and are never shared with others by the server. Still, a
server does not gain any moderation visibility into the content potentially being hosted and accessible to their users.
Because the content is scoped to only a singular user, this is acceptable.

## Future extensibility

In the future, this MSC may be built on to implement nickname or avatar overrides, general user tagging functionalities,
etc.

## Unstable prefix

Before this MSC is accepted, implementations should use the unstable `account_data` events:

| Stable identifier        | Purpose                                  | Unstable identifier                      |
| ------------------------ | ---------------------------------------- | ---------------------------------------- |
| `m.profile_annotations`  | Storage of User Profile Annotations      | `dev.zirco.msc4441.profile_annotations`  |

## Dependencies

None.

[MSC1767]: https://github.com/matrix-org/matrix-spec-proposals/pull/1767
[MSC4483]: https://github.com/matrix-org/matrix-spec-proposals/pull/4483
[`account_data`]: https://spec.matrix.org/v1.18/client-server-api/#client-config
