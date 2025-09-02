# MSC3824: OIDC aware clients

This proposal is part of the broader [MSC3861: Matrix architecture change to delegate authentication via OIDC](https://github.com/matrix-org/matrix-spec-proposals/pull/2967).

In the context of [MSC2964](https://github.com/matrix-org/matrix-doc/pull/2964) we can define four types of client:

1. *OIDC native client* - This is a client that, where the homeserver supports it, talks to the specified OpenID Provider in order to complete login and registration. e.g. Element X (WIP), Hydrogen (WIP)
1. *OIDC aware client* - This is a client that is aware of OIDC but will still use existing auth types (e.g. `m.login.sso`) to auth with an OIDC enabled homeserver.
1. *Legacy client with SSO support* - This is a client that is not aware of OIDC but does support `m.login.sso` flow. e.g. Element Web, iOS, Android, Fluffy, Nheko, Cinny
1. *Legacy client without SSO support* - This is a client that is not aware of OIDC at all and nor does it support `m.login.sso` flow. Typically auth is done via `m.login.password` only. e.g. Fractal

The purpose of differentiating #2 and #3 is that, for a Legacy client with SSO support, the user journey can be optimised with minimal modifications when talking to an OIDC enabled homeserver.

This proposal outlines changes to facilitate clients in becoming OIDC aware.

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

n.b. we don't need to add this to the [Login Fallback](https://spec.matrix.org/v1.2/client-server-api/#login-fallback) as that isn't used for registration.

### Definition of OIDC aware

For a client to be considered fully *OIDC aware* it **must**:

- support the `m.login.sso` auth flow
- where a `delegated_oidc_compatibility` value of `true` is present on an `m.login.sso` then *only* offer that auth flow to the user
- append `action=login` and `action=register` parameters to the SSO redirect URLs
- link users to manage their account at the OpenID Provider web UI given by [MSC2965](https://github.com/matrix-org/matrix-spec-proposals/pull/2965) instead of native UI
- check and honour the `m.3pid_changes` [capability](https://spec.matrix.org/v1.7/client-server-api/#m3pid_changes-capability) so that the user is not offered the ability to add or remove 3PIDs when OIDC is used
- if the user wishes to sign out a device session other than it's own then the client **must**:
  - link the user to the OpenID Provider web UI given by [MSC2965](https://github.com/matrix-org/matrix-spec-proposals/pull/2965) if provided
  - append the `action` and `device_id` to the web UI link parameters described by [MSC2965](https://github.com/sandhose/matrix-doc/blob/msc/sandhose/oidc-discovery/proposals/2965-oidc-discovery.md#account-management-url-parameters) so that the web UI knows that the user wishes to sign out a device and which one it is. e.g. `?action=session_end&device_id=<device_id>`

Optionally, an *OIDC aware* client **could**:

- label the SSO button as "Continue"
- pass other [query parameters for context](https://github.com/sandhose/matrix-doc/blob/msc/sandhose/oidc-discovery/proposals/2965-oidc-discovery.md#account-management-url-parameters) when linking to the account web UI

For an OIDC enabled homeserver to provide support for *OIDC aware* clients it **must**:

- support OIDC delegation as per [MSC2964](https://github.com/matrix-org/matrix-spec-proposals/pull/2964) and others
- provide a compatibility layer for `m.login.password` and `m.login.sso` that wraps on to OIDC
- indicate that the `m.login.sso` is preferred by setting `delegated_oidc_compatibility` to `true`
- make use of the `action` param on the SSO redirect endpoints

Additionally, the homeserver **should**:

- advertise the account management UI in accordance with [MSC2965](https://github.com/matrix-org/matrix-spec-proposals/pull/2965)

## Potential issues

None.

## Alternatives

Clients could assume that an `m.login.sso` is preferred directly from where [MSC2965](https://github.com/matrix-org/matrix-spec-proposals/pull/2965) OpenID Provider discovery indicates OIDC is being used. However, this might hamper some more custom configuration.

The homeserver could only offer `m.login.sso` as the supported auth type but this would prevent non-SSO capable legacy clients from accessing the homeserver.

[Capabilities negotiation](https://spec.matrix.org/v1.2/client-server-api/#capabilities-negotiation) could be used to indicate that `m.login.sso` is preferred.

For the param on redirect: a `prompt` parameter with values [`create`](https://openid.net/specs/openid-connect-prompt-create-1_0.html#rfc.section.4) and [`login`](https://openid.net/specs/openid-connect-core-1_0.html#AuthRequest) exists in OIDC for use on the authorized endpoint. However, our use case is different and it might cause confusion to overload these terms.

## Security considerations

None relevant.

## Unstable prefix

While this feature is in development the following unstable prefixes should be used:

- `delegated_oidc_compatibility` --> `org.matrix.msc3824.delegated_oidc_compatibility`
- `action` query param --> `org.matrix.msc3824.action`

## Dependencies

This MSC depends on the following MSCs, which at the time of writing have not yet
been accepted into the spec:

- [MSC2964](https://github.com/matrix-org/matrix-spec-proposals/pull/2964): Delegation of auth from homeserver to OIDC Provider
- [MSC2965](https://github.com/matrix-org/matrix-spec-proposals/pull/2965): OIDC Provider discovery
