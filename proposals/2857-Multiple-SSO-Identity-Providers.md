# MSC2857: Multiple SSO Identity Providers

Matrix already has generic SSO support, but it does not yield the best user experience especially for
instances which wish to offer multiple identity providers. This MSC provides a simple and fully
backwards compatible way to extend the current spec which would allow clients to give users options
like `Continue with Google` and `Continue with Github` side-by-side.


## Proposal

Currently, Matrix supports `m.login.sso`, `m.login.token` and `/login/sso/redirect` for clients to
pass their user to the configured Identity provider and for them to come back with something which
is exchangeable for a Matrix access token. This flow offers no insight to the user as to what
Identity providers are available. It allows clients to offer a super generic `Sign in with SSO`
button only.

By augmenting the `m.login.sso` flow discovery definition to include metadata on the supported IDPs
the client can show a button for each of the supported providers, yielding a much more usable
experience. This would look like this:

```json
{
    "flows": [
        {
            "type": "m.login.sso",
            "identity_providers": [
                {
                    "id": "google",
                    "name": "Google",
                    "icon": "mxc://..."
                },
                {
                    "id": "github",
                    "name": "Github",
                    "icon": "mxc://..."
                }
            ]
        },
        {
            "type": "m.login.token"
        }
    ]
}
```

A new endpoint would be needed to support redirecting directly to one of the IDPs:

`GET /_matrix/client/r0/login/sso/redirect/{idp_id}`

This would behave identically to the existing endpoint without the last argument
except would allow the server to forward the user directly to the correct IDP.

For the case of User Interactive Auth the server would just give the appropriate
identity provider as an option, that being the same as the user used to login with.

For the case of backwards compatibility the existing endpoint should remain,
and if the server supports multiple SSO IDPs it should offer the user a page
which lets them choose between the available IDP options as a fallback.


## Potential issues

None discovered at this time


## Alternatives

An alternative to the whole approach would be to allow `m.login.sso.$idp` but this forces
treating an opaque identifier as hierarchical and offers worse backwards compatibility.

An alternative to the proposed backwards compatibility plan where the server offers a
fallback page which fills the gap and lets the user choose which SSO IDP they need is
for the server to deterministically always pick one, maybe the first option and let
old clients only auth via that one but that means potentially locking users out of their
accounts.


## Security considerations

This could potentially aid phishing attacks by bad homeservers, where if the app says
`Continue with Google` and then they are taken to a page which is styled to look like
the Google login page they might be a tiny bit more susceptible to being phished as opposed
as to when they click a more generic `Sign in with SSO` button, but this attack was possible
anyhow using a different vector of a controlled Element/client instance which modifies
the text.


## Unstable prefix

Whilst in development use `msc2857.identity_providers` for the flow discovery and `/unstable`
for the new endpoints.

