# MSC4266: Policies in `/.well-known/matrix/support`

Matrix supports collecting policy consent from users during [account
registration]. There is, however, no API allowing clients to retrieve the
policies again at a later point. This requires the user to manually store them
upon registration to be able to refer to them again.

Furthermore, some policies, such as the privacy policy, might be relevant for
users of other homeservers. Again, these users' clients have no way to
programmatically retrieve the server's policies.

The present proposal addresses this situation by publishing the policies in the
server's support document under [`/.well-known/matrix/support`].

## Proposal

A new optional property `policies` is added to the response of
[`/.well-known/matrix/support`]. The format is the same one used during
[registration][account registration].

``` json5
{
  "contacts": [ ... ],
  "support_page": ...,
  "policies": {
    "privacy_policy": {
      "en": {
        "name": "Privacy Policy",
        "url": "https://example.org/somewhere/privacy-1.2-en.html"
      },
      "fr": {
        "name": "Politique de confidentialité",
        "url": "https://example.org/somewhere/privacy-1.2-fr.html"
      },
      "version": "1.2"
    },
    "terms_of_service": {
      "en": {
        "name": "Terms of Service",
        "url": "https://example.org/somewhere/terms-1.2-en.html"
      },
      "fr": {
        "name": "Conditions d'utilisation",
        "url": "https://example.org/somewhere/terms-1.2-fr.html"
      },
      "version": "1.2"
    }
  }
}
```

If the request is authenticated, the server SHOULD respond with the latest
version of the policies that the user consented to.

## Potential issues

None.

## Alternatives

It might be debatable whether policies represent "support" information. Instead
of repurposing the support document, the policies could also be made available
via a dedicated endpoint.

Instead of querying the server, the client could store the policies in the
user's account data. If [encrypted] this would prevent the server from tampering
with the policies the user has consented to. This would, however, not allow
external users to retrieve the policies.

## Security considerations

The server could fake the terms and respond with a version that is different
from the one the user consented to.

## Unstable prefix

While this proposal is unstable `policies` should be referred to as
`org.matrix.msc4266.policies`.

  [account registration]: https://spec.matrix.org/v1.13/client-server-api/#terms-of-service-at-registration
  [`/.well-known/matrix/support`]: https://spec.matrix.org/v1.13/client-server-api/#getwell-knownmatrixsupport
  [encrypted]: https://spec.matrix.org/v1.13/client-server-api/#secret-storage
