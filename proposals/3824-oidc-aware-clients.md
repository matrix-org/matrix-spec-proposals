# MSC3824: OIDC aware clients

In the context of [MSC2964](https://github.com/matrix-org/matrix-doc/pull/2964) we can define four types of client:

1. *OIDC native client* - This is a client that, where the homeserver supports it, talks to the specified OP in order to complete login and registration. e.g. Element X (WIP), Hydrogen (WIP)
1. *OIDC aware client* - This is a client that is aware of OIDC but will still use existing auth types (e.g. `m.login.sso`) to auth with an OIDC enabled homeserver.
1. *Legacy client with SSO support* - This is a client that is not aware of OIDC but does support `m.login.sso` flow. e.g. Element Web, iOS, Android, Fluffy, Nheko, Cinny
1. *Legacy client without SSO support* - This is a client that is not aware of OIDC at all and nor does it support `m.login.sso` flow. Typically auth is done via `m.login.password` only. e.g. Fractal

The purpose of differentiating #2 and #3 is that, for a Legacy client with SSO support, the user journey can be optimised with minimal modifications when talking to an OIDC enabled homeserver.

This proposal outlines changes to facilitate clients in becoming OIDC aware.

## Proposal

Firstly, a client can specify which action the user is wanting to achieve at the point of SSO redirection. This allows the homeserver to display the most relevant UI to the user.

Secondly, the homeserver can optionally specify which auth type is `delegated.oidc.compatibility` are supported for an authentication type.

### Homeserver indicates that an `m.login.sso` flow is for compatibility

Add an optional `delegated.oidc.compatibility` field to the response of `GET /_matrix/client/v3/login`:

`"delegated.oidc.compatibility"?: boolean`

For example, if a homeserver is advertising password login for legacy clients only then it could return the following:

```
{
  "flows": [{
    "type": "m.login.password"
  }, {
    "type": "m.login.sso",
    "delegated.oidc.compatibility": true
  }]
}

```

If the client finds `delegated.oidc.compatibility` to be `true` then, assuming it supports that auth type, it should present this as the only login/registration method available to the user.

### Client indicates `action` on SSO redirect

Add an optional query parameter `action` to `GET /_matrix/client/v3/login/sso/redirect` and `GET /_matrix/client/v3/login/sso/redirect/{idpId}` with meaning:

- `login` - the SSO redirect is for the purposes of signing an existing user in
- `register` - the SSO redirect is for the purpose of registering a new user account

e.g. `https://matrix-client.matrix.org/_matrix/client/v3/login/sso/redirect?action=register`

n.b. we don't need to add this to the [Login Fallback](https://spec.matrix.org/v1.2/client-server-api/#login-fallback) as that isn't used for registration.

### Definition of OIDC aware

For a client to be considered *OIDC aware* it would:

- support the `m.login.sso` auth flow
- where a `delegated.oidc.compatibility` value of `true` is present on an `m.login.sso` then offer that auth flow to the user
- append `action=login` and `action=register` parameters to the SSO redirect URLs
- sign post and link users to manage their account at the OP web UI given by [MSC2965](https://github.com/matrix-org/matrix-spec-proposals/pull/2965)

For an OIDC enabled homeserver to provide support for *OIDC aware* clients it would:

- support OIDC delegation as per [MSC2964](https://github.com/matrix-org/matrix-spec-proposals/pull/2964) and others
- recommended to advertise the account management UI in accordance with [MSC2965](https://github.com/matrix-org/matrix-spec-proposals/pull/2965)
- provide a compatibility layer for `m.login.password` and `m.login.sso` that wraps on to OIDC
- indicate that the `m.login.sso` is preferred by setting `delegated.oidc.compatibility` to `true`
- make use of the `action` param on the SSO redirect endpoints

## Potential issues

None.

## Alternatives

Clients could assume that an `m.login.sso` is preferred directly from where [MSC2965](https://github.com/matrix-org/matrix-spec-proposals/pull/2965) OP discovery indicates OIDC is being used. However, this might hamper some more custom configuration.

The homeserver could only offer `m.login.sso` as the supported auth type but this would prevent non-SSO capable legacy clients from accessing the homeserver.

[Capabilities negotiation](https://spec.matrix.org/v1.2/client-server-api/#capabilities-negotiation) could be used to indicate that `m.login.sso` is preferred.

For the param on redirect: a `prompt` parameter with values [`create`](https://openid.net/specs/openid-connect-prompt-create-1_0.html#rfc.section.4) and [`login`](https://openid.net/specs/openid-connect-core-1_0.html#AuthRequest) exists in OIDC for use on the authorized endpoint. However, our use case is different and it might cause confusion to overload these terms.

## Security considerations

None relevant.

## Unstable prefix

While this feature is in development the following unstable prefixes should be used:

* `delegated.oidc.compatibility` --> `org.matrix.msc3824.delegated.oidc.compatibility`

## Dependencies

This MSC depends on the following MSCs, which at the time of writing have not yet
been accepted into the spec:

* [MSC2964](https://github.com/matrix-org/matrix-spec-proposals/pull/2964): Delegation of auth from homeserver to OIDC Provider
* [MSC2965](https://github.com/matrix-org/matrix-spec-proposals/pull/2965): OIDC Provider discovery
