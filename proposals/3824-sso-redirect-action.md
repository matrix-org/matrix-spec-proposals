# MSC3824: Ability to distinguish between login and registration

A client can determine the available authentication methods/types via the `GET /_matrix/client/v3/login` endpoint.

However, unless registration is blanket disabled (i.e. `POST /_matrix/client/v3/register` returns `403`) then it is assumed that both login and registration are possible using all given auth types.

Furthermore, a homeserver cannot tell if a `m.login.sso` request for `GET /_matrix/client/v3/login/sso/redirect` is intended to be used to login an existing user or register a new user.

In the context of [MSC2964](https://github.com/matrix-org/matrix-doc/pull/2964):

1. a client needs to know whether registration can be completed by a particular auth type;
2. the homeserver needs to know the intent so that the correct UI can be shown to the user.

## Proposal

Firstly, the homeserver can optionally specify which actions are supported for an authentication type.

Secondly, a client can specify which action the user is wanting to achieve at the point of SSO redirection.

### Homeserver specifies available actions per auth type

Add an optional `actions` field to the response of `GET /_matrix/client/v3/login`:

`actions?: ("login" | "register")[]`

For example, if a homeserver supports password for login only, and SSO for login and registration then a response could look like:

```
{
  "flows": [{
    "type": "m.login.password",
    "actions": ["login"],
  }, {
    "type": "m.login.sso",
    "actions": ["login", "register"]
  }]
}

```

If no `actions` field is present then the client should assume that both `login` and `register` are both supported unless indicated elsewhere by the API (e.g. registration disabled `403`).

If `actions` is empty array (i.e. `[]`) then no action is supported.

### Client indicates `action` on SSO redirect

Add an optional query parameter `action` to `GET /_matrix/client/v3/login/sso/redirect` and `GET /_matrix/client/v3/login/sso/redirect/{idpId}` with meaning:

- `login` - the SSO redirect is for the purposes of signing an existing user in
- `register` - the SSO redirect is for the purpose of registering a new user account

e.g. `https://matrix-client.matrix.org/_matrix/client/v3/login/sso/redirect?action=register`

n.b. we don't need to add this to the [Login Fallback](https://spec.matrix.org/v1.2/client-server-api/#login-fallback) as that isn't used for registration.

## Potential issues

None.

## Alternatives

[Capabilities negotiation](https://spec.matrix.org/v1.2/client-server-api/#capabilities-negotiation) could be used for availability of login vs register.

For the param on redirect: a `prompt` parameter with values [`create`](https://openid.net/specs/openid-connect-prompt-create-1_0.html#rfc.section.4) and [`login`](https://openid.net/specs/openid-connect-core-1_0.html#AuthRequest) exists in OIDC for use on the authorized endpoint. However, our use case is different and it might cause confusion to overload these terms.

## Security considerations

None relevant.

## Unstable prefix

Not applicable.
