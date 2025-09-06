# MSC4317: Signed profile data

[MSC4133] introduced the ability to store custom data beyond `avatar_url` and `displayname` in user
profiles. In some cases home servers might want to manage certain profile data. In a corporate
setup, for instance, some employee data such as a person's role, location or telephone number might
be sourced from a central HR system. The spec doesn't forbid managed profile properties and
[MSC4133] allows users to understand which properties they can modify through the `m.profile_fields`
capability. There is, however, no way to tell which properties are managed in *another* user's
profile, especially when they're on a different home server. In environments where a user's trust
into home servers is larger than their trust into other users this prevents users from identifying
impersonation attacks.

This proposal aims to resolve this shortcoming by introducing a scheme for cryptographically binding
profile data to an externally verifiable entity via the mechanism introduced in [MSC4316].

## Proposal

In conjunction with [MSC4316], a new profile property `m.signed` is introduced which is an object
with the following mandatory properties:

- `user_id`: The account's user identifier.
- `signatures`: Signatures of the `m.signed` value as per the current [signing specification].

Any other properties in `m.signed` are optional and extend the data under signature.

``` json5
{
  "avatar_url": "mxc://...",
  ...
  "m.signed": {
    "displayname": "Alice Liddell",
    "role": "Head of Culture & People",
    "telephone": "+1 (555) 555-1234",
    ...
    "user_id": "@alice:matrix.org",
    "signatures": {
      "external": {
        // External X.509 signature
        "x509:$FINGERPRINT_BASE64": "$SIGNATURE"
      }
    }
  }
}
```

Clients MAY check the signed data and present it to the user during the semi-automated verification
process introduced in [MSC4316]. In doing so, clients MUST ensure that the contained `user_id`
matches the account the profile is from and that the profile data and the key to be verified have
been signed by the same certificate.

Since keys are not profile data and this proposal is not meant to be used without [MSC4316], the
signing certificate is not repeated in the profile. Instead, clients can retrieve the certificate
from [`/_matrix/client/v3/keys/query`], provided that the server publishes it there.

Similar to [MSC4316], this proposal doesn't define how signed data is added to a user's profile as
this is assumed to be an administrator task. It is expected that home servers will offer suitable
admin APIs to facilitate this task.

## Potential issues

Properties under `m.signed` can conflict with top-level profile properties.

``` json5
{
  "displayname": "Alice Liddell",
  ...
  "m.signed": {
    "displayname": "Not actually Alice Liddell",
    ...
    "user_id": "@alice:matrix.org",
    "signatures": {
      "external": {
        // External X.509 signature
        "x509:$FINGERPRINT_BASE64": "$SIGNATURE"
      }
    }
  }
}
```

Clients SHOULD prefer the signed data if they are able to validate the signature. If they cannot
validate the signature, they cannot establish any proof of the signed data's authenticity and SHOULD
prefer the top-lvel properties regardless of whether there is any collision.

Additionally, current clients won't know how to interpret signed profile data. For backwards
compatibility home servers MAY, therefore, duplicate properties from `m.signed` to the top level.

## Alternatives

Rather than signing the key and profile data separately, they could be combined in an X.509
certificate (or more generally a signature document). There is, however, no canonical place in
Matrix to store something that is both a key and a profile.

Carrying the above idea further, the certificate could remain on the owning client to be shared only
during device verification via a new verification method akin to [QR-code verification]. This,
however, requires both clients to be online simultaneously, making (semi-)automated verification as
introduced in [MSC4316] impossible. Additionally, it only marginally improves the security concern
of leaking signed data because any client that received the certificate during verification would
still store it locally to be able to present the data to their user again upon request.

## Security considerations

If signed profile data is leaked during a security breach, the authenticity of the data can be
verified by anyone which prevents deniability.

## Unstable prefix

While this MSC is not considered stable, `m.signed` should be referred to as
`de.gematik.msc4317.signed`. Elements inherited from [MSC4316] have their own prefixing
requirements.

## Dependencies

This proposal depends on [MSC4316].

  [MSC4133]: https://github.com/matrix-org/matrix-spec-proposals/pull/4133
  [MSC4316]: https://github.com/matrix-org/matrix-spec-proposals/pull/4316
  [signing specification]: https://spec.matrix.org/v1.15/appendices/#signing-json
  [`/_matrix/client/v3/keys/query`]: https://spec.matrix.org/v1.15/client-server-api/#post_matrixclientv3keysquery
  [QR-code verification]: https://spec.matrix.org/v1.15/client-server-api/#qr-codes
