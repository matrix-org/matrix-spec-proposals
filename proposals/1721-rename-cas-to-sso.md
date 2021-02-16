# MSC1721: Rename `m.login.cas` to `m.login.sso`

The Matrix Client-Server spec includes a [section on client login using Central
Authentication Service
(CAS)](https://matrix.org/docs/spec/client_server/r0.4.0.html#cas-based-client-login).

The spec currently fails to mention it, but this process is triggered when [`GET
/login`](https://matrix.org/docs/spec/client_server/r0.4.0.html#get-matrix-client-r0-login)
returns a flow type of `m.login.cas`.

Nothing in this flow is specific to CAS - it is equally applicable for other
web-based single-sign-on processes, such as SAML.

Accordingly, we should rename `cas` to `sso`.

## Proposal

1. `m.login.sso` should be defined as a valid login type for return from `GET
   /login`. (We should probably mention `m.login.cas` in the spec while we are
   there.)

2. When a client wishes to use the SSO login type, it should redirect to
   `/_matrix/client/r0/login/sso/redirect` (instead of
   `/_matrix/client/r0/login/cas/redirect`).

3. Servers should treat `/_matrix/client/r0/login/sso/redirect` identically to
   `/_matrix/client/r0/login/cas/redirect`: they should issue a redirect to
   their configured single-sign-on system.

4. Servers which support `m.login.sso` should make sure they update their [login
   fallback page](https://matrix.org/docs/spec/client_server/r0.4.0.html#login-fallback)
   to understand the new login type.
