# MSC1692: Terms of service at registration

At registration, homeservers may wish to require the user to accept a given set of policy documents,
such as a terms of service and privacy policy. There may be many different types of documents, all of
which are versioned and presented in (potentially) multiple languages.

This proposal covers requiring users to accept the list of documents during registration. Future
improvements could include informing the user *after* registration that a document has changed, which
has been spun out to [MSC3012](https://github.com/matrix-org/matrix-spec-proposals/pull/3012).

## Proposal

The [User-Interactive Authentication](https://spec.matrix.org/v1.9/client-server-api/#user-interactive-authentication-api)
API (UIA) is currently used during registration to create a new account. In future, it is expected
that OIDC will be used instead, which can include support for this MSC's principles without needing
to change the Matrix specification itself. As a measure until OIDC is here though, this MSC exists
to fill the need.

A new `m.login.terms` authentication type is introduced, allowing servers to include it in registration
flows if it desires. Servers which do not require policy acceptance at registration are not required
to support this flow.

The parameters for the new authentication type look like the following:

```json
{
    "policies": {
        "terms_of_service": {
            "version": "1.2",
            "en": {
                "name": "Terms of Service",
                "url": "https://example.org/somewhere/terms-1.2-en.html"
            },
            "fr": {
                "name": "Conditions d'utilisation",
                "url": "https://example.org/somewhere/terms-1.2-fr.html"
            }
        },
        "privacy_policy": {
            "version": "1.2",
            "en": {
                "name": "Privacy Policy",
                "url": "https://example.org/somewhere/privacy-1.2-en.html"
            },
            "fr": {
                "name": "Politique de confidentialité",
                "url": "https://example.org/somewhere/privacy-1.2-fr.html"
            }
        }
    }
}
```

Each key under `policies` is a "Policy ID", and defined by the server. They are an opaque identifier
(described later in this proposal). Each policy object associated with the policy ID has a required
`version` as a convenience to the client, and is another opaque identifier. All other keys are language
codes to represent the same document. The client picks the language which best suits the user.

Language codes *should* be formatted as per [Section 2.2 of RFC 5646](https://datatracker.ietf.org/doc/html/rfc5646#section-2.2),
noting that some implementation *may* use an underscore instead of dash. For example, `en_US` instead
of `en-US`. This recommendation is to ensure maximum compatibility with existing conventions around
language choices in (Matrix) clients.

`name` and `url` for each policy document are required, and are arbitrary strings with no maximum
length. `url` *must* be a valid URI with scheme `https://` or `http://`. Insecure HTTP is discouraged.

If a client encounters an invalid parameter, registration should stop with an error presented to the
user.

To complete the stage, accepting *all* of the listed documents, the client submits an empty `auth`
dict. The client *should* present the user with a checkbox to accept each policy, including a link
to the provided `url`, or otherwise rely on [fallback auth](https://spec.matrix.org/v1.9/client-server-api/#fallback).

The server is expected to track which document versions it presented to the user during registration,
if applicable.

### Opaque identifier

This definition is inherited from [MSC1597](https://github.com/matrix-org/matrix-spec-proposals/pull/1597).

> Opaque IDs must be strings consisting entirely of the characters
> `[0-9a-zA-Z._~-]`. Their length must not exceed 255 characters and they must
> not be empty.

## Unstable prefix

Regrettably, this MSC was implemented with *stable* identifiers before an unstable identifiers process
was established. Implementation has existed in some capacity since 2018: https://github.com/matrix-org/synapse/pull/4004

Noting that the modern MSC process forbids such behaviour, new implementations should use the stable
`m.login.terms` identifier regardless of MSC status. If the MSC changes in a breaking way, a new
identifier *must* be chosen, and *must* include a proper unstable prefix.
