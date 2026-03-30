# MSC4441: Encrypted User Profile Annotations via Account Data

Many platforms, such as Discord, provide a capability for a user to leave personal "notes" on a user's profile. Matrix,
however, has no similar functionality that can be shared between clients. This proposal builds User Profile Annotations,
a method of storing personal context on other users' profiles. This is made possible using a new `m.profile_annotations`
Account Data event, allowing the storage of free text (and other annotations) for a user's reference.

The framework introduced within this MSC builds upon [Extensible Events][MSC1767] and provides room for future extension
into other forms of user context, such as contact labels or custom nickname overrides. The content stored within these
annotations is also encrypted using an account secret scoped specifically for account data.

## Proposal

### Plaintext `m.profile_annotations`

A new event, `m.profile_annotations`, is stored in [`account_data`][account_data]. The `content` of this event is a JSON
mapping between MXIDs (user or room IDs) and annotations stored on that user/room. Within a user, the `m.text`
property represents a text annotation ("note") on that user. It follows the text format as defined in [MSC1767][MSC1767].

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

### Account Data Key (ADK)

A new secret, `m.account_data.key` is stored in [SSSS][SSSS]. This secret is 256 bits of cryptographic random data used
as the secret in HKDF when encrypting profile annotations (and potentially, in the future, other forms of account data).

`m.account_data.key`:

```json
{
    "encrypted": {
        "key_id_1": {
            "ciphertext": "...",
            // ... other properties according to key_id_1's algorithm
        }
    }
}
```

### Encrypted `m.profile_annotations`

Using the ADK bytes introduced above, contents of `m.profile_annotations` can be encrypted using
[`m.secret_storage.v1.aes-hmac-sha2`][SS_crypto]. The info property of the HKDF is the value `m.profile_annotations`,
an ASCII `/`, concatenated with the MXID of the user it represents (e.g. `m.profile_annotations/@logn:zirco.dev`.

This encryption is applied individually to the Canonical JSON contents of each user's annotation. It MAY be mixed
alongside plaintext data. An example of the event `content` follows:

`m.profile_annotations`:
```json
{
    "@logn:zirco.dev": {
        "encrypted": {
            "iv": "...",
            "ciphertext": "...",
            "mac": "..."
        }
    }
}
```

## Potential issues

#### SSSS availability
Many users have not enabled SSSS. This would potentially require a client to either fall back to plain text or force a
user to set up SSSS to use encrypted annotations (not desired). Alternatively the ADK could be stored on the client.

#### Concurrent writes
Account data is last-write-wins. The usage of one key representing all users may lead to a data race in rare scenarios
(although this tradeoff was accepted to keep the behavior similar to existing state like `m.direct`).

## Alternatives

#### Store annotations as a new API endpoint
Rather than using `account_data`, a new dedicated endpoint for annotations would be created. Rejected because it
requires substantial serverside changes for a simple interop.

#### Encrypt the entire event as one blob
Rejected because encrypting each user's data individually allows for finer grained control, alongside providing
compatibility to users with no SSSS.

#### Eliminate the ADK and simply use the SSSS master
Using the SSSS master would require re-encrypting notes and potentially change how users may interface with client
access to this information. Introducing a new key, potentially usable in the future for more information, is far
simpler.

## Security considerations

- The SSSS model does not provide forward secrecy in the case of key compromise.
- Plaintext fallback may not be immediately obvious to clients.

## Trust and Safety considerations

Profile annotations are the property of one singular user and are never shared with others by the server. Still, a
server does not gain any moderation visibility into the content potentially being hosted and accessible to their users.

Because these are never transmitted, there should be no method for an annotated user to be harmed.

## Future extensibility

In the future, this MSC may be built on to implement nickname or avatar overrides, general user tagging functionalities,
etc.

## Unstable prefix

Before this MSC is accepted, implementations should use the unstable `account_data` events:

| Stable identifier       | Purpose                                  | Unstable identifier                     |
| ----------------------- | ---------------------------------------- | --------------------------------------- |
| `m.profile_annotations` | Storage of User Profile Annotations      | `dev.zirco.msc4441.profile_annotations` |
| `m.account_data.key`    | ADK secret storage for encrypted content | `dev.zirco.msc4441.account_data.key`    |

## Dependencies

None.

  [MSC1767]: https://github.com/matrix-org/matrix-spec-proposals/pull/1767
  [account_data]: https://spec.matrix.org/v1.18/client-server-api/#client-config
  [SSSS]: https://spec.matrix.org/v1.18/client-server-api/#secrets
  [SS_crypto]: https://spec.matrix.org/v1.18/client-server-api/#msecret_storagev1aes-hmac-sha2-1
