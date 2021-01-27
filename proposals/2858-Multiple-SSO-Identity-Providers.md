# MSC2858: Multiple SSO Identity Providers

Matrix already has generic SSO support, but it does not yield the best user experience especially for
instances which wish to offer multiple identity providers (IdPs). This MSC provides a simple and fully
backwards compatible way to extend the current spec which would allow clients to give users options
like `Continue with Google` and `Continue with Github` side-by-side.

Currently, Matrix supports `m.login.sso`, `m.login.token` and `/login/sso/redirect` for clients to
pass their user to the configured Identity provider and for them to come back with something which
is exchangeable for a Matrix access token. This flow offers no insight to the user as to what
Identity providers are available: clients can offer only a very generic `Sign in with SSO`
button. With the currently possible solutions and workarounds the experience is far from great
and user's have to blindly click `Sign in with SSO` without any clue as to what's hiding on the other
side of the door. Some users will definitely not be familiar with `SSO` but will be with the concept of
"Continue with Google" or similar.

## Proposal

We extend the [login
flow](https://matrix.org/docs/spec/client_server/r0.6.1#login) to allow clients
to choose an SSO Identity provider before control is handed over to the server.

### Extensions to login flow discovery

The response to [`GET /_matrix/client/r0/login`](https://matrix.org/docs/spec/client_server/r0.6.1#get-matrix-client-r0-login)
is extended to **optionally** include an `identity_providers` property for
flows whose type `m.login.sso`. This would look like this:

```json
{
    "flows": [
        {
            "type": "m.login.sso",
            "identity_providers": [
                {
                    "id": "google",
                    "name": "Google",
                    "icon": "mxc://...",
                    "brand": "org.matrix.google"
                },
                {
                    "id": "github",
                    "name": "Github",
                    "icon": "mxc://...",
                    "brand": "org.matrix.github"
                }
            ]
        },
        {
            "type": "m.login.token"
        }
    ]
}
```

The value of the `identity_providers` property is a list, each entry consisting
of an object with the following fields:

 * The `id` field is **required**. It is an opaque string chosen by the
   homeserver implementation, and uniquely identifies the identity provider on
   that server. Clients should not infer any semantic meaning from the
   identifier. The identifier should be between 1 and 255 characters in length,
   and should consist of the characters matching unreserved URI characters as
   defined in [RFC3986](http://www.ietf.org/rfc/rfc3986.txt):

   ```
   ALPHA  DIGIT  "-" / "." / "_" / "~"
   ```

 * The `name` field is **required**. It should be a human readable string
   intended for printing by the client. No explicit length limit or grammar is
   specified.

 * The `icon` field is **optional**. It should point to an icon representing
   the IdP.  If present then it must be an MXC URI to an image resource.

 * The `brand` field is **optional**. It allows the client to style the login
   button to suit a particular brand. It should be a string matching the
   "Common namespaced identifier grammar" as defined in
   [MSC2758](https://github.com/matrix-org/matrix-doc/pull/2758).

   Initially the following identifiers are specified:
    * `org.matrix.gitlab`
    * `org.matrix.github`
    * `org.matrix.apple`
    * `org.matrix.google`
    * `org.matrix.facebook`
    * `org.matrix.twitter`

   Server implementations are free to add additional brands, though they should
   be mindful of clients which do not recognise any given brand.

   Clients are free to implement any set of brands they wish, including all or
   any of the above, but are expected to apply a sensible unbranded fallback
   for any brand they do not recognise/support.


### Extend the `/login/sso/redirect` endpoint

A new endpoint is added to support redirecting directly to one of the IdPs:

`GET /_matrix/client/r0/login/sso/redirect/{idp_id}`

This would behave identically to the existing endpoint without the last argument
except would allow the server to forward the user directly to the correct IdP.

For the case of backwards compatibility the existing endpoint is to remain,
and if the server supports multiple SSO IdPs it should offer the user a page
which lets them choose between the available IdP options as a fallback.

### Notes on user-interactive auth

For the case of User Interactive Auth the server would just give the standard
SSO flow option without any `identity_providers` as there is no method for
a client to choose an IdP within that flow at this time nor is it as
essential.

## Potential issues

None discovered at this time


## Alternatives

An alternative to the whole approach would be to allow `m.login.sso.$idp` but this forces
treating an opaque identifier as hierarchical and offers worse backwards compatibility.

An alternative to the proposed backwards compatibility plan where the server offers a
fallback page which fills the gap and lets the user choose which SSO IdP they need is
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

Whilst in development use `org.matrix.msc2858.identity_providers` for the flow discovery and `/_matrix/client/unstable/org.matrix.msc2858/login/sso/redirect/{idp_id}`
for the new endpoints.
