# MSC1731: Mechanism for redirecting to an alternative server during SSO login

This proposal sets out an alternative solution to the problem described in
[MSC1730](https://github.com/matrix-org/matrix-doc/pull/1730): that of needing
to redirect to an alternative homserver during login.

This proposal suggests a mechanism which is less general than that in MSC1730,
in that it works only with the `m.login.sso` login flow for web-based
single-sign-on. However, it is simpler in some respects.

## Proposal

### Background

The `m.login.sso` flow (which is defined by
[MSC1721](https://github.com/matrix-org/matrix-doc/pull/1721) is essentially as
follows:

1. Client sends `GET /_matrix/client/r0/login` to the server to establish the
   permitted flows. `m.login.sso` is among those listed.

2. The user selects a "log in with single-sign-on" option.

3. In web-based clients, the "log in with single-sign-on" option is a link to
   `/_matrix/client/r0/login/sso/redirect?redirectUrl=<redirect_url>`, where
   `<redirect_url>` is a link back to the client which will be used later.

   In non-web-based clients, the client opens a web view on the above page,
   setting `<redirect_url>` to a URL which it can intercept.

4. The server returns a redirect to the single-sign-on system, having arranged
   that when the single-sign-on completes, it will redirect back to an endpoint
   on the server with the authentication results.

5. The server then redirects back to the original `<redirect_url>`, with the
   addition of a `loginToken` query parameter.

6. The client then uses the `loginToken` as a parameter in a call to `POST
   /_matrix/client/r0/login`, with `type: m.login.token`. This returns the
   access token, as for a normal password login.

### Proposed changes

As well as returning a `loginToken` at step 5 above, we could add a
`homeserver` parameter. Clients would then add `/_matrix/client/...` to this
URL to form valid C-S endpoints for step 6 and onwards.

A corollary is that we would need to extend the [fallback login
mechanism](https://matrix.org/docs/spec/client_server/r0.4.0.html#login-fallback)
to add a second parameter to the `window.onLogin` callback, giving the value of
the `homeserver` field.
