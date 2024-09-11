# MSC3861: Next-generation auth for Matrix, based on OAuth 2.0/OIDC

This MSC proposes a new set of authentication APIs for Matrix, based on the OAuth 2.0 and OpenID Connect (OIDC) specifications.

## Motivation

The goal of this MSC is to propose a new set of authentication APIs for Matrix, based on the OAuth 2.0 and OpenID Connect (OIDC) specifications.
To understand this proposal, it is important to lay out the reasoning which led to this conclusion.

This section explains this reasoning before getting into the detailed proposal.
It is purely informative and not part of the actual proposal.
The proposal itself is high-level, and the technical implications are split into separate, more focused MSCs.

### Current paradigm

The Matrix Client-Server API currently has endpoints for authenticating and managing users.
This API design is focused on displaying authentication UI as native controls within the Matrix client.
It is meant to offer multiple server-defined, multi-staged authentication flows, which the client then uses to build a native UI.

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
- Because the password field is displayed by the client, any system password manager will save the password as associated with the client domain.
  This means that if the user chooses to use a different client, they will have to manually find the password in their password manager, as the password will not be associated with the _service_, i.e., the homeserver domain.

**Note**: We acknowledge that many of these points could be improved with individual improvements to each of those stages, and multiple MSCs already exist to address some of them.

### Benefits of authenticating end-users through the system browser

Rather than trying to fix the existing flows, this MSC proposes an alternative approach to authentication.
Authenticating end-users through the system browser is a well-established approach for many applications and would help solve most of the UI quirks mentioned above.

The general idea is simple: to authenticate a user, the client redirects the user to a URL on the homeserver, which completes the authentication flow, and then redirects the user back to the client.

This allows the homeserver to implement an authentication (and registration) flow tailored to its requirements.
A public service with open registration like Matrix.org could have secure CAPTCHA prompts, email verification, and terms of service agreements, with both password-based and social-based authentication.
A private service could have SSO-based authentication with specific 2FA requirements.

This has the benefit of working well with domain-bound authentication mechanisms:

- Password managers can be used to store the password for the homeserver domain, and the user can use a different client on a different domain without having to remember the password.
- WebAuthn credentials/Passkeys are bound to the domain, and would be impractical to introduce with the current authentication paradigm.
- The user could benefit from sharing a single browser session with multiple clients, requiring them to enter their credentials only once per physical device.
- Many other authentication mechanisms are effectively domain-bound: CAPTCHAs and client certificates, just to name a few.

This makes it possible to design widely different authentication flows for different homeservers, without having to cross an API boundary.
Implementers of said flows can focus on the specifics of their deployment without worrying about defining the right API between the client and the homeserver.

**Note**: We are not arguing that browser-based authentication should be the only way to authenticate users, but rather that it is a good default flow for most end-user use cases.

### Concealing the user's credentials

Another benefit of authenticating outside the client is that the client never has the user's full credentials.
This has two important implications:

- The client can't store the user's credentials, and thus can't use them to gain access without the user's consent.
- The user can use different clients without worrying about revealing their account credentials to unknown parties. Only their homeserver ever interacts with their credentials.

With the current authentication paradigm, sensitive account operations, such as changing passwords or deactivating the account, are protected with authentication steps where the client must present the user's credentials.

With the current state of the ecosystem, in a password-based account, this means sending the user's password again: nothing prevents the client from storing the password on the initial login and using it to perform these actions.
To put that in perspective, this means that if a user on the matrix.org homeserver tries to log in on a new client they want to try out, this client would be able to completely lock them out of their account by logging out other sessions and changing their password without additional confirmation from the user.

Making it mandatory for the client to go through the system browser to authenticate means there is a part of the login flow that the client can't skip and doesn't have control over.
The user has to give their explicit consent during that part of the flow, with no way for the client to bypass it.

This opens up the possibility of giving more restrictive access to the user's account.
It would open up Matrix to a new class of clients with only partial access to the user's account.

**Note**: This does not change the level of trust that the user places in their homeserver. Their E2EE keys are still controlled by the client and never exposed to the homeserver, keeping the content of their events secret from the homeserver.

### Limitations of the existing `m.login.sso` flow

The Matrix Client-Server API already has an existing browser-based authentication flow.
The `m.login.sso` flow is effectively used as a single-staged flow, which works as follows:

1. The client redirects to the homeserver to start the authentication
1. The homeserver authenticates the user
1. It redirects back to the client with a single-use "login token"
1. The client exchanges that "login token" to get an access token

This flow design is very similar to the industry-standard OAuth 2.0 authorization code flow as described in [RFC 6749](https://tools.ietf.org/html/rfc6749#section-4.1). However, `m.login.sso` is relatively simple and does not incorporate many of the security features commonly found in OAuth 2.0 flows.

- There is no protection to ensure the client at the end of the flow is the same as the one that started it.
- Because of this, clients using custom URI schemes as redirect URLs are vulnerable to interception by other applications.
- The login token is passed to the client in the query parameters of the redirect URL, which can be visible to the server hosting a web-based client.
- The homeserver has limited metadata about the client, only the redirect URL. This makes it hard to display relevant information about the client to the user during the flow.
- There is no way for the server to return an error message to the client.
- There is no built-in way to keep state throughout the flow, making it hard for the client to distinguish multiple concurrent flows, and potentially leaking the "login token" to the wrong homeserver.

### OAuth 2.0 and OpenID Connect as building blocks

Quoting the [specification](https://spec.matrix.org/latest/#introduction-to-the-matrix-apis):

> Matrix is a set of open APIs for open-federated Instant Messaging (IM), Voice over IP (VoIP) and Internet of Things (IoT) communication, designed to create and support a new global real-time communication ecosystem. The intention is to provide an **open decentralised pubsub layer for the internet for securely persisting and publishing/subscribing JSON objects**.

Fundamentally, Matrix does not set out to be an authentication protocol.
The ecosystem needs authentication to work, but it is not core to the mission.

This MSC essentially proposes building on top of well-established authentication protocols, defined by OAuth 2.0 RFCs and OpenID Connect specifications.

OAuth 2.0 is a framework for building authorization systems, defined across multiple RFCs by the IETF.
OpenID Connect is an effort by the OpenID Foundation to standardize on top of OAuth 2.0.

This set of MSCs is an attempt to build on top of these existing specifications, defining what clients and homeservers must implement to comply with the Matrix specification.

### Beyond browser-based authentication

This MSC intentionally does not cover the use of alternative authorization flows that don't rely on a web browser, for automation or other purposes.
This does not mean that the Matrix ecosystem should not embrace such flows, but it is rather an attempt to keep this proposal focused on making this a good default flow for most users, ensuring it is treated as a first-class citizen in the ecosystem.

The goal is to set a new widely-adopted base for authentication in the Matrix ecosystem, eventually replacing the current custom authentication protocol.
Solving Matrix-specific problems with this new base could benefit the wider ecosystem of decentralized protocols, rather than staying confined to Matrix.

## Proposal

TODO: fill out the actual proposal

Due to the complexity of this proposal it has been broken down into a number of constituent sub-proposals:

| Ref                                                           | Purpose                                                                                                                                                                                  |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [MSC2964](https://github.com/matrix-org/matrix-doc/pull/2964) | Describes how homeservers can delegate auth to an OpenID Provider                                                                                                                        |
| [MSC2965](https://github.com/matrix-org/matrix-doc/pull/2965) | Describes how participants in the Matrix ecosystem can discover the available capabilities of OIDC-enabled Homeservers and OpenID Providers                                              |
| [MSC2966](https://github.com/matrix-org/matrix-doc/pull/2966) | Describes how OAuth 2.0 Dynamic Client Registration can be used to facilitate interoperability and openness of clients whilst promoting trust                                            |
| [MSC2967](https://github.com/matrix-org/matrix-doc/pull/2967) | Defines the namespace for a set of API scopes that can can expanded in future to allow for finer grained permissioning                                                                   |
| [MSC3824](https://github.com/matrix-org/matrix-doc/pull/3824) | Proposes some minor changes to the C-S API to allow Matrix clients that are not fully OIDC-native to work best with an OIDC enabled homeserver that has is serving a compatibility layer |

## Sample flow

TODO: This section will give an overview of a sample flow, referencing the MSCs above.

## Potential issues

TODO

## Alternatives

The primary alternative is to continue to build out the auth capabilities within the Client-Server API.

For example, UIA (User-Interactive Auth) could be added to the `/login` endpoint and additional capabilities/flows added to UIA.

Examples of existing proposals include:

| Proposals                                                                                                                                                                                                                                   | Comments                                                                                                                                                                                                                                                                                                                   |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [MSC1998: Two-Factor Authentication Providers](https://github.com/matrix-org/matrix-spec-proposals/pull/1998)<br>[MSC2271: TOTP 2FA login](https://github.com/matrix-org/matrix-spec-proposals/pull/2271)                                   | OP is free to implement MFA and many do. The [Matrix OIDC Playground](https://github.com/vector-im/oidc-playground) contains a Keycloak configured to demonstrate this                                                                                                                                                     |
| [MSC2000: Server-side password policies](https://github.com/matrix-org/matrix-spec-proposals/pull/2000)                                                                                                                                     | Because the UI is served by the OP it is free to implement whatever password policies it sees fit                                                                                                                                                                                                                          |
| [MSC3105: Previewing UIA flows](https://github.com/matrix-org/matrix-spec-proposals/pull/3105)<br>[MSC3741: Revealing the useful login flows to clients after a soft logout](https://github.com/matrix-org/matrix-spec-proposals/pull/3741) | These become unnecessary as the burden to implement auth flows is moved away from the client to the OP                                                                                                                                                                                                                     |
| [MSC3262: aPAKE authentication](https://github.com/matrix-org/matrix-spec-proposals/pull/3262)<br>[MSC2957: Cryptographically Concealed Credentials](https://github.com/matrix-org/matrix-spec-proposals/pull/2957)                         | This is an interesting one as OIDC explicitly discourages a user from trusting their client with credentials. As such there is no existing flow for PAKEs. To achieve this in OIDC you would need to implement a custom grant in the Client and OP (perhaps an extension of the Resource Owner Password Credentials flow). |
| [MSC3782: Matrix public key login spec](https://github.com/matrix-org/matrix-spec-proposals/pull/3782)                                                                                                                                      | Similar to above                                                                                                                                                                                                                                                                                                           |
| [MSC3744: Support for flexible authentication](https://github.com/matrix-org/matrix-spec-proposals/pull/3744)                                                                                                                               | OIDC would instead be used as the pluggable layer for auth in Matrix                                                                                                                                                                                                                                                       |

## Security considerations

Please refer to individual proposals.

## Unstable prefix

Please refer to individual proposals.

## Dependencies

The following MSCs are part of this proposal:

- [MSC2964](https://github.com/matrix-org/matrix-doc/pull/2964)
- [MSC2965](https://github.com/matrix-org/matrix-doc/pull/2965)
- [MSC2966](https://github.com/matrix-org/matrix-doc/pull/2966)
- [MSC2967](https://github.com/matrix-org/matrix-doc/pull/2967)
- [MSC3824](https://github.com/matrix-org/matrix-doc/pull/3824)

The following MSCs are not directly part of this proposal but this proposal assumes that these are accepted:

- [MSC3970: Scope transaction IDs to devices](https://github.com/matrix-org/matrix-spec-proposals/pull/3970)
- [MSC3967: Do not require UIA when first uploading cross signing keys](https://github.com/matrix-org/matrix-spec-proposals/pull/3967)
