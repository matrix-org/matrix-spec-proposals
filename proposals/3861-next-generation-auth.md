# MSC3861: Next-generation auth for Matrix, based on OAuth 2.0/OIDC

The goal of this MSC is to propose a new set of authentication APIs for Matrix, based on the OAuth 2.0 and OpenID Connect (OIDC) specifications.
To understand this proposal, it is important to lay out the reasoning behind it.

## Rationale

Matrix currently uses a [custom protocol for authentication](https://spec.matrix.org/v1.13/client-server-api/#client-authentication), one that hasn't been significantly updated in many years.
This leads to two main problems:

 1. The custom protocol does not follow best practices, nor does it use the collective experience of other authentication protocols.
 2. While relatively generic, the custom protocol does not currently support many desired features that users and organizations actually want.

These points could be addressed by iterating on the current protocol; however, using the industry standard OAuth 2.0 allows us to benefit from its experience without having to build a competing (relatively generic) authentication protocol.
We also will benefit more easily from any further enhancements or best practice recommendations of OAuth 2.0.

## Background and motivation

This section expands on the benefits of moving to OAuth 2.0.
It is purely informative and not part of the actual proposal.
The proposal itself is high-level, and the technical implications are split into separate, more focused MSCs.

### Current paradigm

The Matrix Client-Server API currently has endpoints for [authenticating][spec-auth] and [managing][spec-account] users.
This API design is focused on displaying authentication UI as native controls within the Matrix client.
It is meant to offer multiple server-defined, multi-staged authentication flows, which the client then uses to build a native UI.

[spec-auth]: https://spec.matrix.org/v1.13/client-server-api/#client-authentication
[spec-account]: https://spec.matrix.org/v1.13/client-server-api/#account-registration-and-management

As an example, on the Matrix.org homeserver, the user registration flow is gated behind three stages:

1. A CAPTCHA challenge
1. An agreement to the terms of service
1. An email verification

On paper, this lets clients implement their own UI for authentication, but in practice, the dynamic nature of the flows makes it difficult to implement a streamlined UI.
Moreover, the fact that those stages are displayed on client-driven UI, and not on a homeserver-specific domain, makes them insecure, impossible to design, or behave poorly in terms of user experience.

A few issues can be highlighted from this particular example:

- When setting up a CAPTCHA challenge, CAPTCHA services expect the challenge to be served from a specific domain. Because the client can be on any domain, [Synapse currently advises disabling host verification](https://element-hq.github.io/synapse/latest/CAPTCHA_SETUP.html#getting-api-keys).
  When this option is disabled, the CAPTCHA service expects the server to verify the domain of the challenge, which is not possible.
- The agreement to the terms of service can be completely ignored by the client, as it only requires the client to send a request with no specific data to validate it.
  This means the server has to trust the goodwill of the client to make sure the user agrees to the terms of service.
- The current design of the email verification flow has a confusing user experience.
  The link sent to the user by email leads to a screen where the user is prompted to return to their client.
  A better approach would be to send a one-time code by email, which avoids one extra context switch and can sometimes be automatically filled by the operating system.
- Because the password field is displayed by the client, any system password manager will save the password as associated with the client domain.
  This means that if the user chooses to use a different client, they will have to manually find the password in their password manager, as the password will not be associated with the _service_, i.e., the homeserver domain.

**Note**: Many of these points could be improved with individual improvements to each of those stages, and multiple MSCs already exist to address some of them.

### Benefits of authenticating end-users through a web browser

Rather than trying to fix the existing flows, this MSC proposes an alternative approach to authentication.
Authenticating end-users through a web browser is a well-established approach for many applications and would help solve most of the UI quirks mentioned above.
Though, some applications may wish to retain browser-less authentication, which this proposal supports thanks to the inherited authentication specifications.

The general idea is simple: to authenticate a user, the client redirects the user to a URL provided by the homeserver to complete the authentication flow and then to redirect the user back to the client.

This allows the homeserver to implement an authentication (and registration) flow tailored to its requirements.
A public service with open registration like Matrix.org could have secure CAPTCHA prompts, email verification, and terms of service agreements, with both password-based and social-based authentication.
A private service could have SSO-based authentication with specific 2FA requirements.

Using the homeserver's domain name in the authentication flow unlocks new kinds of authentication mechanisms and enhances the user experience of existing flows.
WebAuthn credentials/Passkeys, as well as client certificate-based authentication, are all bound to the domain they are registered on, making them impractical if the client is directly authenticating the end user.
Password managers will also function better if the credentials are bound to the homeserver domain instead of the client itself.

This makes it possible to design widely different authentication flows for different homeservers, without having to cross an API boundary.
Implementers of said flows can focus on the specifics of their deployment without worrying about defining the right API between the client and the homeserver.

Bouncing between the client and the browser may lead to user confusion, especially on operating systems with limited window management capabilities.
Mobile operating systems such as iOS and Android provide a way to embed a secure browser view within an application ([`ASWebAuthenticationSession`](https://developer.apple.com/documentation/authenticationservices/aswebauthenticationsession) on iOS, [Custom Tabs](https://developer.android.com/develop/ui/views/layout/webapps/overview-of-android-custom-tabs) on Android).
In those cases the host application cannot control or monitor what is happening within the embedded browser view, but that view shares the same context as the system-wide browser.

### Concealing the user's credentials

Another benefit of authenticating outside the client is that the client never has the user's full credentials.
This has two important implications:

- The client can't store the user's credentials, and thus can't use them to gain access without the user's consent.
- The user can use different clients without worrying about revealing their account credentials to unknown parties. Only their homeserver ever interacts with their credentials.

With the current authentication paradigm, sensitive account operations, such as changing passwords or deactivating the account, are protected with authentication steps where the client must present the user's credentials.

With the current state of the ecosystem, in a password-based account, this means sending the user's password again: nothing prevents the client from storing the password on the initial login and using it to perform these actions.
To put that in perspective, this means that if a user on the matrix.org homeserver tries to log in on a new client they want to try out, this client would be able to completely lock them out of their account by logging out other sessions and changing their password without additional confirmation from the user.

This also effectively widens the attack surface for credential theft, as both the client and the homeserver currently have access to the user's credentials.

Making it mandatory for the client to go through the system browser to authenticate means there is a part of the login flow that the client can't skip and doesn't have control over.
The user has to give their explicit consent during that part of the flow, with no way for the client to bypass it.

This opens up the possibility of giving more restrictive access to the user's account.
It would open up Matrix to a new class of clients with only partial access to the user's account.

**Note**: This does not change the level of trust that the user places in their homeserver. Their E2EE keys are still controlled by the client and never exposed to the homeserver, keeping the content of their events secret from the homeserver.

### Limitations of the existing [`m.login.sso`] flow

The Matrix Client-Server API already has an existing browser-based authentication flow.
The [`m.login.sso`] flow is effectively used as a single-staged flow, which works as follows:

1. The client redirects to the homeserver to start the authentication
1. The homeserver authenticates the user
1. It redirects back to the client with a single-use "login token"
1. The client exchanges that "login token" to get an access token

This flow design is very similar to the industry-standard OAuth 2.0 authorization code flow as described in [RFC 6749](https://tools.ietf.org/html/rfc6749#section-4.1). However, [`m.login.sso`] is relatively simple and does not incorporate many of the security features commonly found in OAuth 2.0 flows.

- There is no protection to ensure the client at the end of the flow is the same as the one that started it.
- Because of this, clients using custom URI schemes as redirect URLs are vulnerable to interception by other applications.
- The login token is passed to the client in the query parameters of the redirect URL, which can be visible to the server hosting a web-based client.
- The homeserver has limited metadata about the client, only the redirect URL. This makes it hard to display relevant information about the client to the user during the flow.
- There is no way for the server to return an error message to the client.
- There is no built-in way to keep state throughout the flow, making it hard for the client to distinguish multiple concurrent flows, and potentially leaking the "login token" to the wrong homeserver.

### OAuth 2.0 and OpenID Connect as building blocks

Quoting the [specification](https://spec.matrix.org/v1.13/#introduction-to-the-matrix-apis):

> Matrix is a set of open APIs for open-federated Instant Messaging (IM), Voice over IP (VoIP) and Internet of Things (IoT) communication, designed to create and support a new global real-time communication ecosystem. The intention is to provide an **open decentralised pubsub layer for the internet for securely persisting and publishing/subscribing JSON objects**.

Fundamentally, Matrix does not set out to be an authentication protocol.
The ecosystem needs authentication to work, but it is not core to the mission.

This MSC essentially proposes building on top of well-established authentication protocols, defined by OAuth 2.0 RFCs and OpenID Connect specifications.

[OAuth 2.0](https://oauth.net/2/) is a framework for building authorization systems, defined across multiple RFCs by the IETF.
[OpenID Connect](https://openid.net/connect/) is an effort by the OpenID Foundation to standardize on top of OAuth 2.0.

This set of MSCs is an attempt to build on top of these existing specifications, defining what clients and homeservers must implement to comply with the Matrix specification.

### Beyond browser-based authentication

This MSC intentionally does not cover the use of alternative authorization flows that don't rely on a web browser, for automation or other purposes.
This does not mean that the Matrix ecosystem should not embrace such flows, but it is rather an attempt to keep this proposal focused on making this a good default flow for most users, ensuring it is treated as a first-class citizen in the ecosystem.

The goal is to set a new widely-adopted base for authentication in the Matrix ecosystem, eventually replacing the current custom authentication protocol.
Solving Matrix-specific problems with this new base could benefit the wider ecosystem of decentralized protocols, rather than staying confined to Matrix.

### Why not 'just use OpenID Connect'?

OpenID Connect does a good job at standardizing on top of OAuth 2.0, and it covers most things happening between the client and the server for authentication.
It is a great fit for connecting identity providers to other pieces of software, and this is already what homeservers do with the [`m.login.sso`] flow.

Knowing that, it might seem like fully adopting OpenID Connect would facilitate the use of off-the-shelf identity providers for Matrix homeservers.
However, in practice, OpenID Connect does not cover continuous exchanges between the application and the identity providers: there is no well-supported standard to signal new sessions, new users, session endings, user deactivation, etc., from the identity provider to the application.
Matrix fundamentally needs those signals, as the state of devices (and, to some extent, users) is propagated to other servers through room memberships and cryptographic devices.
Moreover, most identity providers are designed to provide service to a fixed set of applications, which does not fit the Matrix ecosystem, where users can use any number of different clients.

This means that backfitting Matrix-specific concepts on top of OpenID Connect would be a bad idea, especially as one important goal of this proposal is to keep the current authentication paradigm working for some time.

**Note**: an earlier version of this MSC focused on 'delegating' authentication to an identity provider, but it showed its limitations and added much confusion over the intent of the proposal.

### Keeping the ecosystem open

One common critique of OAuth 2.0 and OpenID Connect is that they are widely used in contexts where the service provider controls which clients are allowed to interact with the service.
This usually implies a contractual relationship between the service provider and the client, typically through a developer program, where the client must comply with the service provider's terms of service.

This has been a notorious problem with [OAuth 2.0 in email protocols][thunderbird-oauth2], where email clients are forced to register their applications with each email provider, giving the email provider the right to reject any application.

This proposal aims to mitigate this problem by defining a way for clients to dynamically register themselves with the homeserver.

[thunderbird-oauth2]: https://wiki.mozilla.org/Thunderbird:Autoconfiguration:ConfigFileFormat#OAuth2

## Proposal

This proposal introduces a new set of authentication APIs for Matrix, based on OAuth 2.0 and OpenID Connect (OIDC) specifications.

As a first step, it introduces those APIs as alternatives to the existing authentication mechanisms -- in particular [`/_matrix/client/v3/login`] and [User-Interactive Authentication](https://spec.matrix.org/v1.13/client-server-api/#user-interactive-authentication-api) (UIA).
It does not attempt to cover all use cases of the existing APIs at this point.
The long-term goal is to deprecate the existing account management APIs and UIA-protected endpoints, providing alternatives where necessary.
This deprecation is not done in this MSC.

While not directly part of this proposal, it paves the way for providing only partial access to the user's account.
Therefore, the specification should begin including the scope required to access each endpoint in its description.

### Core authentication flow

To cover the most common use case of authenticating an end-user, the following MSCs are necessary:

- [MSC2964: Usage of OAuth 2.0 authorization code grant and refresh token grant][MSC2964] describes how the main authentication flow works
- [MSC2965: OAuth 2.0 Authorization Server Metadata discovery][MSC2965] describes how a client can discover the authentication server metadata of the homeserver
- [MSC2966: Usage of OAuth 2.0 Dynamic Client Registration][MSC2966] describes how a client can register itself with the homeserver to get a client identifier
- [MSC2967: API scopes][MSC2967] defines the first set of access scopes and the basis for future access scopes
- [MSC4254: Usage of RFC7009 Token Revocation for Matrix client logout][MSC4254] describes how a client can end a client session

### Adjacent proposals

This set of core proposals doesn't cover everything previously covered by UIA-protected APIs.
The following proposals are meant to provide alternative APIs to fill in the gaps.

#### Account management

This moves the user-interface for some account management tasks from the client to the homeserver.
Existing APIs like [`/_matrix/client/v3/capabilities`] help clients understand which account-management API endpoints are unavailable, but they don't offer alternatives to a homeserver-provided user-interface.
To build this bridge between the client user-interface and the homeserver, [MSC4191: Account management deep-linking][MSC4191] proposes a way to deep-link to the account management capabilities of the homeserver.

#### Transition and existing client support

To help clients transition to the next-generation auth, this proposal is designed to offer backward-compatible APIs through the [`m.login.sso`] login flow.
How this is intended to work and let clients offer reasonable user experience is covered by [MSC3824: OIDC-aware clients][MSC3824].

#### Application services

In the longer term, application services could leverage alternative grant types like the [OAuth 2.0 Client Credentials Grant](https://tools.ietf.org/html/rfc6749#section-4.4) to obtain access to the homeserver.
In the meantime, homeservers should keep registration through the [`/_matrix/client/v3/register` with the `m.login.application_service` type][register-app-service] endpoint working for application services.
[MSC4190: Device management for application services][MSC4190] proposes a simple API to create and delete devices for users managed by application services, to remove the need for keeping the [`m.login.application_service`] login type working.

[register-app-service]: https://spec.matrix.org/v1.13/application-service-api/#server-admin-style-permissions

## Sample flow

This section describes a sample flow, taking together the steps described in more details in the dedicated MSCs.
**It is non-normative**, as the different parts of the flow are described in more details in their respective MSCs.
It assumes the client already discovered the homeserver's Client-Server API endpoint.

[areweoidcyet.com](https://areweoidcyet.com/client-implementation-guide/) has an interactive guide on how to use this flow.

### Discovery [MSC2965]

First step is to discover the homeserver's authorization server metadata.
This is defined by [MSC2965: OAuth 2.0 Authorization Server Metadata discovery][MSC2965] as follows:

```http
GET /_matrix/client/v1/auth_metadata HTTP/1.1
Host: matrix.example.com
Accept: application/json
```

```http
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: public, max-age=3600
```

```json
{
  "authorization_endpoint": "https://auth.example.com/oauth2/auth",
  "token_endpoint": "https://auth.example.com/oauth2/token",
  "registration_endpoint": "https://auth.example.com/oauth2/clients/register",
  "revocation_endpoint": "https://auth.example.com/oauth2/revoke",
  "...": "some fields omitted"
}
```

The client must save this document as the "authorization server metadata".
It must also check that it contains all the fields it will need for other parts of the flow.

### Client registration [MSC2966]

Next step is to register the client with the homeserver.
This uses the `registration_endpoint` value from the authorization server metadata.
This is defined by [MSC2966: Usage of OAuth 2.0 Dynamic Client Registration][MSC2966] as follows:

```http
POST /oauth2/clients/register HTTP/1.1
Content-Type: application/json
Accept: application/json
Server: auth.example.com
```

```json
{
  "client_name": "My App",
  "client_uri": "https://example.com/",
  "logo_uri": "https://example.com/logo.png",
  "tos_uri": "https://example.com/tos.html",
  "policy_uri": "https://example.com/policy.html",
  "redirect_uris": ["https://app.example.com/callback"],
  "token_endpoint_auth_method": "none",
  "response_types": ["code"],
  "grant_types": ["authorization_code", "refresh_token"]
}
```

The server replies with a JSON object containing the `client_id` allocated, as well as all the metadata values that the server registered.

With the previous registration request, the server would reply with:

```http
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: no-store
Pragma: no-cache
```

```json
{
  "client_id": "s6BhdRkqt3",
  "client_name": "My App",
  "client_uri": "https://example.com/",
  "logo_uri": "https://example.com/logo.png",
  "tos_uri": "https://example.com/tos.html",
  "policy_uri": "https://example.com/policy.html",
  "redirect_uris": ["https://app.example.com/callback"],
  "response_types": ["code"],
  "grant_types": ["authorization_code", "refresh_token"],
  "application_type": "web"
}
```

The client must store the `client_id` for later use.

### Authorization request [MSC2964]

The client is ready to start an authorization request.
It needs to determine a few other values:

- `state`: a usually random string that will be used to associate the response with the authorization request
- `code_verifier`: a random string with enough entropy which will be used to ensure the client is the one that initiated the request
- The Matrix device ID the client wants to use/create

In this example, we've picked:

- `state` to be `To29j0DdKUcc75Rt`
- `code_verifier` to be `NXt2S0jiptl4q0m8OYVJFFyuDB5i5aeJSOUJ4NpdmTv`
- The device ID to be `EIKO9QUIAL`

This will help create the authorization request URL, with the following parameters:

- `response_mode` set to `fragment` for a client-side web client
- `response_type` set to `code`
- `client_id` got from the registration request above, in this example `s6BhdRkqt3`
- `code_challenge_method` set to `S256`
- `code_challenge` derived from the `code_verifier` using the `S256` method. In this example, it is `8coMp56MvhmfFtjk0dYd9H9d3jQRV1qjS703hAOVnEk`
- `scope`: as defined by [MSC2967]
  - For full access, it needs to contain:
    - `urn:matrix:client:api:*`
    - `urn:matrix:device:XXYYZZ`, where `XXYYZZ` is the device ID
  - Our example is then using `urn:matrix:client:api:* urn:matrix:device:EIKO9QUIAL`
- `redirect_uri`: the client's redirect URI registered. In our example, it is `https://app.example.com/callback`

Building the full URL gives:

```
https://auth.example.com/oauth2/auth?response_mode=fragment&response_type=code&client_id=s6BhdRkqt3&code_challenge_method=S256&code_challenge=8coMp56MvhmfFtjk0dYd9H9d3jQRV1qjS703hAOVnEk&scope=urn:matrix:client:api:%20urn:matrix:device:EIKO9QUIAL&redirect_uri=https%3A%2F%2Fapp.example.com%2Fcallback&state=To29j0DdKUcc75Rt
```

The client then redirects the user to this URL.

### Authorization response [MSC2964]

At the end of the authorization flow, the user is redirected back to the client, with a `code` parameter in the URL fragment, as well as the `state` parameter.

```
https://app.example.com/callback#code=To29j0DdKUcc75Rt&state=To29j0DdKUcc75Rt
```

The client must now exchange the `code` for an access token.

This is defined by [MSC2964: Usage of OAuth 2.0 authorization code grant and refresh token grant][MSC2964] as follows:

```http
POST /oauth2/token HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Accept: application/json
Server: auth.example.com

grant_type=authorization_code&code=To29j0DdKUcc75Rt&redirect_uri=https%3A%2F%2Fapp.example.com%2Fcallback&code_verifier=NXt2S0jiptl4q0m8OYVJFFyuDB5i5aeJSOUJ4NpdmTv
```

```http
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: no-store
Pragma: no-cache
```

```json
{
  "access_token": "mat_ooreiPhei2wequu9fohkai3AeBaec9oo",
  "refresh_token": "mar_Pieyiev3aenahm4atah7aip3eiveizah",
  "expires_in": 300,
  "token_type": "Bearer"
}
```

The client can now use the access token to make authenticated requests to the homeserver.
It will expire after `expires_in` seconds, after which it must be refreshed, using the refresh token.

```http
POST /oauth2/token HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Accept: application/json
Server: auth.example.com

grant_type=refresh_token&refresh_token=mar_Pieyiev3aenahm4atah7aip3eiveizah
```

```http
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: no-store
Pragma: no-cache
```

```json
{
  "access_token": "mat_ohb2Chei5Ne5yoghohs8voochei1laep",
  "refresh_token": "mar_eequee6zahsee1quieta8oopoopeeThu",
  "expires_in": 300,
  "token_type": "Bearer"
}
```

### Token revocation [MSC4254]

To end a client session, the client must revoke the access token.
This is defined by [MSC4254: Usage of RFC7009 Token Revocation for Matrix client logout][MSC4254] as follows:

```http
POST /oauth2/revoke HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Accept: application/json
Server: auth.example.com

token=mat_ohb2Chei5Ne5yoghohs8voochei1laep&token_type_hint=access_token&client_id=s6BhdRkqt3
```

```http
HTTP/1.1 200 OK
```

Both the access token and the refresh token are revoked, and the associated device ID is deleted on the homeserver.

## Potential issues

Each individual proposal has its own potential issues section.
This section only covers the potential issues that are common to the proposal as a whole.

### User and ecosystem migration

This proposal fundamentally changes the way users and ecosystems interact with their accounts on their homeservers.
Users might be used to entering their credentials within their client, which means that migrating to this proposal will introduce a new web-based login flow that will be different from what users are used to.

In the long term, this is beneficial for the ecosystem, as it helps users familiarize themselves with the distinction between their homeserver and their client.
Where clients and servers are in a managed environment, branding between the flows can unify the user experience, similar to how many corporate email accounts work.

This proposal is not yet proposing to deprecate the existing APIs, in an effort to avoid breaking existing clients as much as possible.
This adds complexity for homeserver implementers if they want to support both the old and new APIs.

### Reliance on the system browser

The main authentication flow of this proposal is a web-based flow that is intended to run in the context of a system browser.
There are alternative flows which could help support login on devices where a browser is not available, or for automation purposes.
These flows are best implemented through future MSCs.

Additionally, in some contexts, the system browser can be a security risk, as it has a wide attack surface inherent to its complexity.
This can be mitigated to some extent by having homeservers implement authorization flows that don't require JavaScript, but this doesn't completely eliminate the risk.

### Homeserver implementation complexity

In practice, to provide a good user experience, homeservers have to implement web views for the authentication flows, which is complex to implement well.
This means having proper accessibility, translations, and UX.
Those concerns were previously mainly affecting client implementations, and will now also affect homeserver implementations.

On the other hand, the previous registration flow was notoriously complex to implement both for clients and homeservers, and this proposal removes a lot of that complexity from the client side.

Moreover, these concerns should, in theory, already apply to the homeserver-side implementation, as the homeserver is supposed to provide a [web-based fallback](https://spec.matrix.org/v1.13/client-server-api/#login-fallback) for the `/login` API,  as well as [fallbacks](https://spec.matrix.org/v1.11/client-server-api/#fallback) for all UIA steps.
In practice, this is often not the case, with either missing fallbacks for some UIA steps or sub-par user experiences in their implementations.

## Alternatives

The primary alternative is to continue to build out the auth capabilities within the Client-Server API.

For example, UIA (User-Interactive Auth) could be added to the [`/_matrix/client/v3/login`] endpoint and additional capabilities/flows added to UIA.

Examples of existing proposals include:

| Proposals                                                                                                                       | Comments                                                                                                                                                                                                                                                                                                                         |
| ------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [MSC1998: Two-Factor Authentication Providers][MSC1998]<br>[MSC2271: TOTP 2FA login][MSC2271]                                   | Homeservers are free to implement the authentication flows they want. The [Matrix OIDC Playground](https://github.com/vector-im/oidc-playground) contains a Keycloak configured to demonstrate this                                                                                                                              |
| [MSC2000: Server-side password policies][MSC2000]                                                                               | Because the UI is served by the homeserver, it is free to implement whatever password policies it sees fit                                                                                                                                                                                                                       |
| [MSC3105: Previewing UIA flows][MSC3105]<br>[MSC3741: Revealing the useful login flows to clients after a soft logout][MSC3741] | These become unnecessary as the burden to implement auth flows is moved away from the client to the homeserver                                                                                                                                                                                                                   |
| [MSC3262: aPAKE authentication][MSC3262]<br>[MSC2957: Cryptographically Concealed Credentials][MSC2957]                         | This is an interesting one as OAuth 2.0 explicitly discourages a user from trusting their client with credentials. As such there is no existing flow for PAKEs. To achieve this, you would need to implement a custom grant in the Client and homeserver (perhaps an extension of the Resource Owner Password Credentials flow). |
| [MSC3782: Matrix public key login spec][MSC3782]                                                                                | Similar to above                                                                                                                                                                                                                                                                                                                 |
| [MSC3744: Support for flexible authentication][MSC3744]                                                                         | This proposal would instead be used as the pluggable layer for auth in Matrix                                                                                                                                                                                                                                                    |

## History

This proposal was originally known as 'OIDC-native' authentication.
To avoid the confusion with OIDC as a single sign-on/identity protocol, this proposal removed its dependency on OpenID Connect and was renamed to 'next-generation auth'.

## Security considerations

Please refer to individual proposals.

## Unstable prefix

Please refer to individual proposals.

## Dependencies

The following MSCs map the aforementioned OAuth 2.0/OIDC requirements to Matrix APIs:

- [MSC2964: Usage of OAuth 2.0 authorization code grant and refresh token grant][MSC2964]
- [MSC2965: OAuth 2.0 Authorization Server Metadata discovery][MSC2965]
- [MSC2966: Usage of OAuth 2.0 Dynamic Client Registration][MSC2966]
- [MSC2967: API scopes][MSC2967]
- [MSC4254: Usage of RFC7009 Token Revocation for Matrix client logout][MSC4254]

The following MSCs are meant to cover less essential parts of the authentication and account management flows.
They are not strictly required for this proposal to be accepted, but should be considered shortly afterwards:

- [MSC3824: OIDC-aware clients][MSC3824]
- [MSC4190: Device management for application services][MSC4190]
- [MSC4191: Account management deep-linking][MSC4191]
- [MSC4198: Usage of OIDC login_hint][MSC4198]

The following MSCs were prerequisites for implementing this proposal in a sane way, and were accepted in the meantime:

- [MSC3970: Scope transaction IDs to devices][MSC3970]
- [MSC3967: Do not require UIA when first uploading cross signing keys][MSC3967]

[MSC1998]: https://github.com/matrix-org/matrix-spec-proposals/pull/1998
[MSC2000]: https://github.com/matrix-org/matrix-spec-proposals/pull/2000
[MSC2271]: https://github.com/matrix-org/matrix-spec-proposals/pull/2271
[MSC2957]: https://github.com/matrix-org/matrix-spec-proposals/pull/2957
[MSC2964]: https://github.com/matrix-org/matrix-spec-proposals/pull/2964
[MSC2965]: https://github.com/matrix-org/matrix-spec-proposals/pull/2965
[MSC2966]: https://github.com/matrix-org/matrix-spec-proposals/pull/2966
[MSC2967]: https://github.com/matrix-org/matrix-spec-proposals/pull/2967
[MSC3105]: https://github.com/matrix-org/matrix-spec-proposals/pull/3105
[MSC3262]: https://github.com/matrix-org/matrix-spec-proposals/pull/3262
[MSC3741]: https://github.com/matrix-org/matrix-spec-proposals/pull/3741
[MSC3744]: https://github.com/matrix-org/matrix-spec-proposals/pull/3744
[MSC3782]: https://github.com/matrix-org/matrix-spec-proposals/pull/3782
[MSC3824]: https://github.com/matrix-org/matrix-spec-proposals/pull/3824
[MSC3967]: https://github.com/matrix-org/matrix-spec-proposals/pull/3967
[MSC3970]: https://github.com/matrix-org/matrix-spec-proposals/pull/3970
[MSC4190]: https://github.com/matrix-org/matrix-spec-proposals/pull/4190
[MSC4191]: https://github.com/matrix-org/matrix-spec-proposals/pull/4191
[MSC4198]: https://github.com/matrix-org/matrix-spec-proposals/pull/4198
[MSC4254]: https://github.com/matrix-org/matrix-spec-proposals/pull/4254
[`m.login.application_service`]: https://spec.matrix.org/v1.13/client-server-api/#appservice-login
[`m.login.sso`]: https://spec.matrix.org/v1.13/client-server-api/#sso-client-loginauthentication
[`/_matrix/client/v3/capabilities`]: https://spec.matrix.org/v1.13/client-server-api/#get_matrixclientv3capabilities
[`/_matrix/client/v3/login`]: https://spec.matrix.org/v1.13/client-server-api/#post_matrixclientv3login
