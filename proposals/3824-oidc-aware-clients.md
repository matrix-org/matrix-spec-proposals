# MSC3824: OAuth 2.0 API aware clients

As of spec 1.15 we now have two APIs for clients to authenticate:

- the [Legacy API]
- the [OAuth 2.0 API]

It is anticipated that in time all clients will support the [OAuth 2.0 API]. However, in the interim, some existing
clients will continue to only support the [Legacy API].

During this transition period it is proposed that a client could make some small changes to improve the user experience
when talking to a homeserver that is using the [OAuth 2.0 API] without actually having to implement the full
[OAuth 2.0 API].

In this context it is helpful to distinguish four types of client:

1. *OAuth native client* - This is a client that, where the homeserver supports it, uses the [OAuth 2.0 API] for login
   and registration. e.g. Element X, Element Web
1. *OAuth aware client* - This is a client that is "aware" (see below) of the [OAuth 2.0 API] but will still uses the
   [Legacy API] (e.g. [`m.login.sso`]) to auth with an [OAuth 2.0 API] enabled homeserver.
1. *Legacy client with SSO support* - This is a client that is not aware of the [OAuth 2.0 API] but does support the
   [`m.login.sso`] from the [Legacy API]. e.g. Element Classic on iOS and Android
1. *Legacy client without SSO support* - This is a client that is not aware of the [OAuth 2.0 API] at all and nor does
   it support the [`m.login.sso`] [Legacy API] flow. Typically auth is done via `m.login.password` only. e.g. Fractal

The purpose of differentiating #2 and #3 is that, for a Legacy client with SSO support, the user journey can be
optimised with minimal modifications when talking to an [OAuth 2.0 API] enabled homeserver.

## Proposal

Firstly, we make two backwards compatible changes to the [Legacy API]:

- The homeserver can optionally specify that where more than one
  [authentication type](https://spec.matrix.org/v1.16/client-server-api/#authentication-types)
  is suppored, that a specific [`m.login.sso`] auth type is preferred.
- A client can specify which action the user is wanting to achieve at the point of SSO redirection. This allows the
  homeserver to display the most relevant UI to the user.

We then describe how a client can use these new features and others to optimise the user experience without having
to support the [OAuth 2.0 API].

These are detailed below.

### Homeserver indicates that an `m.login.sso` flow is preferred

Add an optional `oauth_aware_preferred` field to the response of
[`GET /_matrix/client/v3/login`](https://spec.matrix.org/v1.16/client-server-api/#get_matrixclientv3login):

- `"oauth_aware_preferred"?: boolean`

For example, if a homeserver is advertising password login for legacy clients only then it could return the following:

```json
{
  "flows": [{
    "type": "m.login.password"
  }, {
    "type": "m.login.sso",
    "oauth_aware_preferred": true
  }]
}

```

If the client finds `oauth_aware_preferred` to be `true` then, assuming it supports that auth type, it should
present this as the only login/registration method available to the user.

### Client indicates `action` on SSO redirect

Add an optional query parameter `action` to [`GET /_matrix/client/v3/login/sso/redirect`](https://spec.matrix.org/v1.16/client-server-api/#get_matrixclientv3loginssoredirect)
and [`GET /_matrix/client/v3/login/sso/redirect/{idpId}`](https://spec.matrix.org/v1.16/client-server-api/#get_matrixclientv3loginssoredirectidpid)
with meaning:

- `login` - the SSO redirect is for the purposes of signing an existing user in
- `register` - the SSO redirect is for the purpose of registering a new user account

e.g. `https://matrix-client.matrix.org/_matrix/client/v3/login/sso/redirect?action=register`

The client might determine the value based on whether the user clicked a "Login" or "Register" button.

n.b. we don't need to add this to the [Login Fallback](https://spec.matrix.org/v1.16/client-server-api/#login-fallback)
as that isn't used for registration.

### Definition of OAuth 2.0 aware

For a client to be considered fully *OAuth 2.0 aware* it **must**:

- support the [`m.login.sso`] auth flow
- where a `oauth_aware_preferred` value of `true` is present on an [`m.login.sso`] then *only* offer that auth flow
  to the user
- append `action=login` and `action=register` parameters to the SSO redirect URLs
- link users to manage their account at the `account_management_uri` given by [MSC4191] instead of native UI
- do not offer the user the function to deactivate their account and instead refer them to the account management URL
  described above
- check and honour the `m.3pid_changes`
  [capability](https://spec.matrix.org/v1.16/client-server-api/#m3pid_changes-capability) so that the user is not
  offered the ability to add or remove 3PIDs when the server has the OAuth 2.0 API enabled
- if the user wishes to sign out a device session other than it's own then the client **must**:
  - link the user to the `account_management_uri` given by [MSC4191] if provided
  - append the `action` and `device_id` to the web UI link parameters described by
    [MSC4191](https://github.com/matrix-org/matrix-spec-proposals/blob/quenting/account-deeplink/proposals/4191-account-deeplink.md#account-management-url-parameters)
    so that the web UI knows that the user wishes to sign out a device and which one it is.
    e.g. `?action=org.matrix.device_delete&device_id=<device_id>`
  - n.b. an earlier version of this MSC used the `session_end` value instead of `org.matrix.device_delete`. This has
    changed for consistency with [MSC4191].

Optionally, an *OAuth 2.0 aware* client **could**:

- label the SSO button as "Continue" rather than "SSO". This is because after redirect the server may then offer a
  password and/or further upstream IdPs
- pass other
  [query parameters for context](https://github.com/matrix-org/matrix-spec-proposals/blob/quenting/account-deeplink/proposals/4191-account-deeplink.md#account-management-url-parameters)
  when linking to the account web UI

For an OIDC enabled homeserver to provide support for *OAuth 2.0 aware* clients it **must**:

- support the [OAuth 2.0 API]
- provide an implementation of the  `m.login.password` and [`m.login.sso`]
  [authentication types](https://spec.matrix.org/v1.16/client-server-api/#authentication-types) from the [Legacy API]
- indicate that the [`m.login.sso`] is preferred by setting `oauth_aware_preferred` to `true`
- provides a value for the `action` param on the SSO redirect endpoints as defined above

Additionally, the homeserver **should**:

- advertise the account management UI in accordance with [MSC4191]

## Potential issues

Clients might be discouraged from making the full transition to the [OAuth 2.0 API] because this proposal outlines a
kind of "half way house".

## Alternatives

Clients could assume that an [`m.login.sso`] is preferred directly from where the
[server metadata discovery](https://spec.matrix.org/v1.16/client-server-api/#server-metadata-discovery) indicates the
[OAuth 2.0 API] is being used. However, this might hamper some more custom configuration.

The homeserver could only offer [`m.login.sso`] as the supported auth type but this would prevent non-SSO capable legacy
clients from accessing the homeserver.

[Capabilities negotiation](https://spec.matrix.org/v1.16/client-server-api/#capabilities-negotiation) could be used to
indicate that [`m.login.sso`] is preferred.

For the param on redirect: a `prompt` parameter with values 
[`create`](https://openid.net/specs/openid-connect-prompt-create-1_0.html#rfc.section.4) and
[`login`](https://openid.net/specs/openid-connect-core-1_0.html#AuthRequest) exists in OIDC for use on the authorized
endpoint. However, our use case is different and it might cause confusion to overload these terms.

## Security considerations

None relevant.

## Unstable prefix

While this feature is in development the following unstable prefixes should be used:

- In the /login response body: `org.matrix.msc3824.delegated_oidc_compatibility` instead of
  `oauth_aware_preferred`
- On the SSO redirect: `org.matrix.msc3824.action` instead of `action` query parameter

An earlier version of this MSC used the `session_end` value instead of the [MSC4191]
value `org.matrix.device_delete`. This should be resolved once the feature gets stabilised.

## Dependencies

This MSC depends on the following MSCs, which at the time of writing have not yet
been accepted into the spec:

- [MSC4191]: Account management for [OAuth 2.0 API]

[MSC4191]: https://github.com/matrix-org/matrix-spec-proposals/pull/4191
[Legacy API]: https://spec.matrix.org/v1.16/client-server-api/#legacy-api
[OAuth 2.0 API]: https://spec.matrix.org/v1.16/client-server-api/#oauth-20-api
[`m.login.sso`]: https://spec.matrix.org/v1.16/client-server-api/#client-login-via-sso
