# MSC3824: OAuth 2.0 API aware clients

As of spec 1.15 we now have two APIs for clients to authenticate:

- the [Legacy API](https://spec.matrix.org/v1.15/client-server-api/#legacy-api)
- the [OAuth 2.0 API](https://spec.matrix.org/v1.15/client-server-api/#oauth-20-api)

In this context we can define four types of client:

1. *OAuth native client* - This is a client that, where the homeserver supports it, uses the OAuth 2.0 API for login and registration. e.g. Element X, Element Web
1. *OAuth aware client* - This is a client that is aware of the OAuth 2.0 API but will still uses the Legacy PI (e.g. `m.login.sso`) to auth with an OAuth 2.0 API enabled homeserver.
1. *Legacy client with SSO support* - This is a client that is not aware of the OAuth 2.0 API but does support the `m.login.sso` flow. e.g. Element Classic on iOS and Android
1. *Legacy client without SSO support* - This is a client that is not aware of the OAuth 2.0 API at all and nor does it support `m.login.sso` flow. Typically auth is done via `m.login.password` only. e.g. Fractal

The purpose of differentiating #2 and #3 is that, for a Legacy client with SSO support, the user journey can be optimised with minimal modifications when talking to an OAuth 2.0 API enabled homeserver.

This proposal outlines changes to facilitate clients in becoming OAuth 2.0 API aware.

## Proposal

Firstly, a client can specify which action the user is wanting to achieve at the point of SSO redirection. This allows the homeserver to display the most relevant UI to the user.

Secondly, the homeserver can optionally specify which auth type is `delegated_oidc_compatibility` are supported for an authentication type.

### Homeserver indicates that an `m.login.sso` flow is for compatibility

Add an optional `delegated_oidc_compatibility` field to the response of `GET /_matrix/client/v3/login`:

`"delegated_oidc_compatibility"?: boolean`

For example, if a homeserver is advertising password login for legacy clients only then it could return the following:

```json
{
  "flows": [{
    "type": "m.login.password"
  }, {
    "type": "m.login.sso",
    "delegated_oidc_compatibility": true
  }]
}

```

If the client finds `delegated_oidc_compatibility` to be `true` then, assuming it supports that auth type, it should present this as the only login/registration method available to the user.

### Client indicates `action` on SSO redirect

Add an optional query parameter `action` to `GET /_matrix/client/v3/login/sso/redirect` and `GET /_matrix/client/v3/login/sso/redirect/{idpId}` with meaning:

- `login` - the SSO redirect is for the purposes of signing an existing user in
- `register` - the SSO redirect is for the purpose of registering a new user account

e.g. `https://matrix-client.matrix.org/_matrix/client/v3/login/sso/redirect?action=register`

n.b. we don't need to add this to the [Login Fallback](https://spec.matrix.org/v1.15/client-server-api/#login-fallback) as that isn't used for registration.

### Definition of OAuth 2.0 aware

For a client to be considered fully *OAuth 2.0 aware* it **must**:

- support the `m.login.sso` auth flow
- where a `delegated_oidc_compatibility` value of `true` is present on an `m.login.sso` then *only* offer that auth flow to the user
- append `action=login` and `action=register` parameters to the SSO redirect URLs
- link users to manage their account at the `account_management_uri` given by [MSC4191](https://github.com/matrix-org/matrix-spec-proposals/pull/4191) instead of native UI
- check and honour the `m.3pid_changes` [capability](https://spec.matrix.org/v1.15/client-server-api/#m3pid_changes-capability) so that the user is not offered the ability to add or remove 3PIDs when the server has the OAuth 2.0 API enabled
- if the user wishes to sign out a device session other than it's own then the client **must**:
  - link the user to the `account_management_uri` given by [MSC4191](https://github.com/matrix-org/matrix-spec-proposals/pull/4191) if provided
  - append the `action` and `device_id` to the web UI link parameters described by [MSC4191](https://github.com/matrix-org/matrix-spec-proposals/blob/quenting/account-deeplink/proposals/4191-account-deeplink.md#account-management-url-parameters) so that the web UI knows that the user wishes to sign out a device and which one it is. e.g. `?action=session_end&device_id=<device_id>`

Optionally, an *OAuth 2.0 aware* client **could**:

- label the SSO button as "Continue" rather than "SSO". This is because after redirect the server may then offer a password and/or further upstream IdPs
- pass other [query parameters for context](https://github.com/matrix-org/matrix-spec-proposals/blob/quenting/account-deeplink/proposals/4191-account-deeplink.md#account-management-url-parameters) when linking to the account web UI

For an OIDC enabled homeserver to provide support for *OAuth 2.0 aware* clients it **must**:

- support the [OAuth 2.0 API](https://spec.matrix.org/v1.15/client-server-api/#oauth-20-api)
- provide a compatibility layer for `m.login.password` and `m.login.sso`
- indicate that the `m.login.sso` is preferred by setting `delegated_oidc_compatibility` to `true`
- make use of the `action` param on the SSO redirect endpoints

Additionally, the homeserver **should**:

- advertise the account management UI in accordance with [MSC4191](https://github.com/matrix-org/matrix-spec-proposals/pull/4191)

## Potential issues

None.

## Alternatives

Clients could assume that an `m.login.sso` is preferred directly from where the [server metadata discovery](https://spec.matrix.org/v1.15/client-server-api/#server-metadata-discovery) indicates the OAuth 2.0 API is being used. However, this might hamper some more custom configuration.

The homeserver could only offer `m.login.sso` as the supported auth type but this would prevent non-SSO capable legacy clients from accessing the homeserver.

[Capabilities negotiation](https://spec.matrix.org/v1.15/client-server-api/#capabilities-negotiation) could be used to indicate that `m.login.sso` is preferred.

For the param on redirect: a `prompt` parameter with values [`create`](https://openid.net/specs/openid-connect-prompt-create-1_0.html#rfc.section.4) and [`login`](https://openid.net/specs/openid-connect-core-1_0.html#AuthRequest) exists in OIDC for use on the authorized endpoint. However, our use case is different and it might cause confusion to overload these terms.

## Security considerations

None relevant.

## Unstable prefix

While this feature is in development the following unstable prefixes should be used:

- In the /login response body: `org.matrix.msc3824.delegated_oidc_compatibility` instead of `delegated_oidc_compatibility`
- On the SSO redirect: `org.matrix.msc3824.action` instead of `action` query parameter

## Dependencies

This MSC depends on the following MSCs, which at the time of writing have not yet
been accepted into the spec:

- [MSC4191](https://github.com/matrix-org/matrix-spec-proposals/pull/4191): Account management deep-linking
