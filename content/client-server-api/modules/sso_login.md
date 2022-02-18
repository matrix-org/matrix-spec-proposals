---
type: module
---

### SSO client login/authentication

Single Sign-On (SSO) is a generic term which refers to protocols which
allow users to log into applications via a single web-based
authentication portal. Examples include OpenID Connect, "Central
Authentication Service" (CAS) and SAML.

This module allows a Matrix homeserver to delegate user authentication
to an external authentication server supporting one of these protocols.
In this process, there are three systems involved:

-   A Matrix client, using the APIs defined this specification, which
    is seeking to authenticate a user to a Matrix homeserver.
-   A Matrix homeserver, implementing the APIs defined in this
    specification, but which is delegating user authentication to the
    authentication server.
-   An "authentication server", which is responsible for
    authenticating the user.

This specification is concerned only with communication between the
Matrix client and the homeserver, and is independent of the SSO protocol
used to communicate with the authentication server. Different Matrix
homeserver implementations might support different SSO protocols.

Clients and homeservers implementing the SSO flow will need to consider
both [login](#login) and [user-interactive authentication](#user-interactive-authentication-api). The flow is
similar in both cases, but there are slight differences.

Typically, SSO systems require a single "callback" URI to be configured
at the authentication server. Once the user is authenticated, their
browser is redirected to that URI. It is up to the Matrix homeserver
implementation to implement a suitable endpoint. For example, for CAS
authentication the homeserver should provide a means for the
administrator to configure where the CAS server is and the REST
endpoints which consume the ticket.

Homeservers may optionally expose multiple possible SSO options for
the user to pursue, typically in the form of several "log in with $provider"
buttons. These are known as "identity providers" (IdPs).

#### Client login via SSO

An overview of the process is as follows:

1.  The Matrix client calls [`GET /login`](/client-server-api/#get_matrixclientv3login) to find the supported login
    types, and the homeserver includes a flow with
    `"type": "m.login.sso"` in the response.
2.  To initiate the `m.login.sso` login type, the Matrix client
    instructs the user's browser to navigate to the
    [`/login/sso/redirect`](/client-server-api/#get_matrixclientv3loginssoredirect) endpoint on the user's homeserver.
    Note that this may be the IdP-dependent version of the endpoint if the
    user has selected one of the `identity_providers` from the flow.
3.  The homeserver responds with an HTTP redirect to the SSO user
    interface, which the browser follows.
4.  The authentication server and the homeserver interact to verify the
    user's identity and other authentication information, potentially
    using a number of redirects.
5.  The browser is directed to the `redirectUrl` provided by the client
    with a `loginToken` query parameter for the client to log in with.
6.  The client exchanges the login token for an access token by calling
    the [`/login`](/client-server-api/#post_matrixclientv3login) endpoint with a `type` of `m.login.token`.

For native applications, typically steps 1 to 4 are carried out by
opening an embedded web view.

These steps are illustrated as follows:

```
    Matrix Client                        Matrix Homeserver      Auth Server
        |                                       |                   |
        |-------------(0) GET /login----------->|                   |
        |<-------------login types--------------|                   |
        |                                       |                   |
        |   Webview                             |                   |
        |      |                                |                   |
        |----->|                                |                   |
        |      |--(1) GET /login/sso/redirect-->|                   |
        |      |<---------(2) 302---------------|                   |
        |      |                                |                   |
        |      |<========(3) Authentication process================>|
        |      |                                |                   |
        |      |<--(4) redirect to redirectUrl--|                   |
        |<-----|                                |                   |
        |                                       |                   |
        |---(5) POST /login with login token--->|                   |
        |<-------------access token-------------|                   |
```

{{% boxes/note %}}
In the older [r0.4.0
version](https://matrix.org/docs/spec/client_server/r0.4.0.html#cas-based-client-login)
of this specification it was possible to authenticate via CAS when the
homeserver provides a `m.login.cas` login flow. This specification
deprecates the use of `m.login.cas` to instead prefer `m.login.sso`,
which is the same process with the only change being which redirect
endpoint to use: for `m.login.cas`, use `/cas/redirect` and for
`m.login.sso` use `/sso/redirect` (described below). The endpoints are
otherwise the same.
{{% /boxes/note %}}

{{% definition path="api/client-server/definitions/sso_login_flow" %}}

##### Client behaviour

The client starts the process by instructing the browser to navigate to
[`/login/sso/redirect`](/client-server-api/#get_matrixclientv3loginssoredirect)
(or [`/login/sso/redirect/{idpId}`](/client-server-api/#get_matrixclientv3loginssoredirectidpid)
when using one of the `identity_providers`)
with an appropriate `redirectUrl`. Once
authentication is successful, the browser will be redirected to that
`redirectUrl`.

{{% http-api spec="client-server" api="sso_login_redirect" %}}

###### Security considerations

1.  CSRF attacks via manipulation of parameters on the `redirectUrl`

    Clients should validate any requests to the `redirectUrl`. In
    particular, it may be possible for attackers to falsify any query
    parameters, leading to cross-site request forgery (CSRF) attacks.

    For example, consider a web-based client at
    `https://client.example.com`, which wants to initiate SSO login on
    the homeserver at `server.example.org`. It does this by storing the
    homeserver name in a query parameter for the `redirectUrl`: it
    redirects to
    `https://server.example.org/login/sso/redirect?redirectUrl=https://client.example.com?hs=server.example.org`.

    An attacker could trick a victim into following a link to
    `https://server.example.org/login/sso/redirect?redirectUrl=https://client.example.com?hs=evil.com`,
    which would result in the client sending a login token for the
    victim's account to the attacker-controlled site `evil.com`.

    To guard against this, clients MUST NOT store state (such as the
    address of the homeserver being logged into) anywhere it can be
    modified by external processes.

    Instead, the state could be stored in
    [localStorage](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage)
    or in a cookie.

2.  For added security, clients SHOULD include a unique identifier in
    the `redirectUrl` and reject any callbacks that do not contain a
    recognised identifier, to guard against unsolicited login attempts
    and replay attacks.

##### Server behaviour

Servers should note that `identity_providers` are optional, and older clients
might not interpret the value correctly. In these cases, the client will use
the generic `/redirect` endpoint instead of the `/redirect/{idpId}` endpoint.

###### Redirecting to the Authentication server

The server should handle
`/_matrix/client/v3/login/sso/redirect` as follows:

1.  It should build a suitable request for the SSO system.
2.  It should store enough state that the flow can be securely resumed
    after the SSO process completes. One way to do this is by storing a
    cookie which is stored in the user's browser, by adding a
    `Set-Cookie` header to the response.
3.  It should redirect the user's browser to the SSO login page with the
    appropriate parameters.

See also the "Security considerations" below.

###### Handling the callback from the Authentication server

Note that there will normally be a single callback URI which is used for
both login and user-interactive authentication: it is up to the
homeserver implementation to distinguish which is taking place.

The homeserver should validate the response from the SSO system: this
may require additional calls to the authentication server, and/or may
require checking a signature on the response.

The homeserver then proceeds as follows:

1.  The homeserver MUST map the user details received from the
    authentication server to a valid [Matrix user
    identifier](/appendices#user-identifiers). The guidance in
    [Mapping from other character
    sets](/appendices#mapping-from-other-character-sets) may be
    useful.
2.  If the generated user identifier represents a new user, it should be
    registered as a new user.
3.  The homeserver should generate a short-term login token. This is an
    opaque token, suitable for use with the `m.login.token` type of the
    [`/login`](/client-server-api/#post_matrixclientv3login) API. The lifetime of this token SHOULD be limited to
    around five seconds.
4.  The homeserver adds a query parameter of `loginToken`, with the
    value of the generated login token, to the `redirectUrl` given in
    the `/_matrix/client/v3/login/sso/redirect`
    request. (Note: `redirectURL` may or may not include existing query
    parameters. If it already includes one or more `loginToken`
    parameters, they should be removed before adding the new one.)
5.  The homeserver redirects the user's browser to the URI thus built.

##### Security considerations

1.  Homeservers should ensure that login tokens are not sent to
    malicious clients.

    For example, consider a homeserver at `server.example.org`. An
    attacker tricks a victim into following a link to
    `https://server.example.org/login/sso/redirect?redirectUrl=https://evil.com`,
    resulting in a login token being sent to the attacker-controlled
    site `evil.com`. This is a form of cross-site request forgery
    (CSRF).

    To mitigate this, Homeservers SHOULD confirm with the user that they
    are happy to grant access to their matrix account to the site named
    in the `redirectUrl`. This can be done either *before* redirecting
    to the SSO login page when handling the
    `/_matrix/client/v3/login/sso/redirect`
    endpoint, or *after* login when handling the callback from the
    authentication server. (If the check is performed before
    redirecting, it is particularly important that the homeserver guards
    against unsolicited authentication attempts as below).

    It may be appropriate to whitelist a set of known-trusted client
    URLs in this process. In particular, the homeserver's own [login
    fallback](#login-fallback) implementation could be excluded.

2.  For added security, homeservers SHOULD guard against unsolicited
    authentication attempts by tracking pending requests. One way to do
    this is to set a cookie when handling
    `/_matrix/client/v3/login/sso/redirect`, which
    is checked and cleared when handling the callback from the
    authentication server.

#### SSO during User-Interactive Authentication

[User-interactive authentication](#user-interactive-authentication-api) is used by client-server endpoints
which require additional confirmation of the user's identity (beyond
holding an access token). Typically this means that the user must
re-enter their password, but for homeservers which delegate to an SSO
server, this means redirecting to the authentication server during
user-interactive auth.

The implementation of this is based on the [Fallback](#fallback) mechanism for
user-interactive auth.

#### Client behaviour

Clients do not need to take any particular additional steps beyond
ensuring that the fallback mechanism has been implemented, and treating
the `m.login.sso` authentication type the same as any other unknown type
(i.e. they should open a browser window for
`/_matrix/client/v3/auth/m.login.sso/fallback/web?session=<session_id>`.
Once the flow has completed, the client retries the request with the
session only.)

#### Server behaviour

##### Redirecting to the Authentication server

The server should handle
`/_matrix/client/v3/auth/m.login.sso/fallback/web`
in much the same way as
`/_matrix/client/v3/login/sso/redirect`, which is to
say:

1.  It should build a suitable request for the SSO system.
2.  It should store enough state that the flow can be securely resumed
    after the SSO process completes. One way to do this is by storing a
    cookie which is stored in the user's browser, by adding a
    `Set-Cookie` header to the response.
3.  It should redirect the user's browser to the SSO login page with the
    appropriate parameters.

See also the "Security considerations" below.

###### Handling the callback from the Authentication server

Note that there will normally be a single callback URI which is used for
both login and user-interactive authentication: it is up to the
homeserver implementation to distinguish which is taking place.

The homeserver should validate the response from the SSO system: this
may require additional calls to the authentication server, and/or may
require checking a signature on the response.

The homeserver then returns the [user-interactive authentication
fallback completion](#fallback) page to the user's browser.

###### Security considerations

1.  Confirming the operation

    The homeserver SHOULD confirm that the user is happy for the
    operation to go ahead. The goal of the user-interactive
    authentication operation is to guard against a compromised
    `access_token` being used to take over the user's account. Simply
    redirecting the user to the SSO system is insufficient, since they
    may not realise what is being asked of them, or the SSO system may
    even confirm the authentication automatically.

    For example, the homeserver might serve a page with words to the
    effect of:

    > A client is trying to remove a device from your account. To
    > confirm this action, re-authenticate with single sign-on. If you
    > did not expect this, your account may be compromised!

    This confirmation could take place before redirecting to the SSO
    authentication page (when handling the
    `/_matrix/client/v3/auth/m.login.sso/fallback/web`
    endpoint), or *after* authentication when handling the callback from
    the authentication server. (If the check is performed before
    redirecting, it is particularly important that the homeserver guards
    against unsolicited authentication attempts as below).

2.  For added security, homeservers SHOULD guard against unsolicited
    authentication attempts by tracking pending requests. One way to do
    this is to set a cookie when handling
    `/_matrix/client/v3/auth/m.login.sso/fallback/web`,
    which is checked and cleared when handling the callback from the
    authentication server.
