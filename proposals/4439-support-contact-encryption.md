# MSC4439: Encryption key URIs in `/.well-known/matrix/support`

The [`/.well-known/matrix/support`] endpoint provides an [`email_address`] property for reaching server contacts,
including those intended for sensitive security disclosures (the `m.role.security` role). [RFC9116] \(commonly known
as `security.txt`\) serves a similar purpose and defines an `Encryption` field (&sect;2.5.4) allowing operators to
advertise a key URI for encrypted communication with security researchers.

This proposal adds a similar `pgp_key` field to the [`Contact`] entry on [`/.well-known/matrix/support`], enabling
homeserver operators to indicate a key that senders may use when communicating sensitive information over email or
other insecure channels.

## Proposal

A new optional property `pgp_key` (unstable prefix: `dev.zirco.msc4439.pgp_key`) is added to the [`Contact`]
response from [`/.well-known/matrix/support`]. This field indicates a PGP key that may be used for encrypted
communication to that particular contact. If the field is used, the `email_address` field SHOULD also be present.

The value of this field MUST be a URI pointing to a location where the key may be retrieved. Raw key material MUST
NOT appear as the value of this field. As with [RFC9116], it is always the responsibility of the sender to ensure they
trust the key provided.

Example of an OpenPGP key available from a web URI:

```
{
    "contacts": [
        {
            "email_address": "logan@zirco.dev",
            "pgp_key": "https://zirco.dev/pgp/logn.pub",
            "role": "m.role.admin"
        }
    ]
}
```

Other URI schemes other than `https` may also be used, common examples include, but are not limited to:
- `openpgp4fpr:67FAAA655DBD691E7957E0951594E544D8F8F21E` (key fingerprint)
- `dns:HASH._openpgpkey.zirco.dev?type=OPENPGPKEY` (`OPENPGPKEY` DNS record) ([RFC7929])

## Potential issues

None identified.

## Alternatives

Sensitive communications may instead be conducted over Matrix, where E2EE is native. However, some researchers prefer
or mandate out-of-band channels, which this MSC accommodates.

## Unstable prefix

While this proposal is unstable, `pgp_key` should be referred to as `dev.zirco.msc4439.pgp_key`.

  [`/.well-known/matrix/support`]: https://spec.matrix.org/unstable/client-server-api/#getwell-knownmatrixsupport
  [`email_address`]: https://spec.matrix.org/unstable/client-server-api/#getwell-knownmatrixsupport_response-200_contact
  [`Contact`]: https://spec.matrix.org/unstable/client-server-api/#getwell-knownmatrixsupport_response-200_contact
  [RFC9116]: https://www.rfc-editor.org/info/rfc9116
  [RFC7929]: https://www.rfc-editor.org/info/rfc7929
