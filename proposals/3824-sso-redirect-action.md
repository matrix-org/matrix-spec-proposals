# MSC3824: Login/register indication on SSO redirect

At present a homeserver cannot tell if a request for `GET /_matrix/client/v3/login/sso/redirect` is intended to be used to sign in an existing user or register a new user.

In the context of [MSC2964](https://github.com/matrix-org/matrix-doc/pull/2965) the homeserver needs to know the intent so that the correct UI can be shown to the user.

## Proposal

Add an optional query parameter `action` to `GET /_matrix/client/v3/login/sso/redirect` with meaning:

- `login` - the SSO redirect is for the purposes of signing an existing user in
- `register` - the SSO redirect is for the purpose of registering a new user account

## Potential issues

None.

## Alternatives

A `prompt` parameter with values [`create`](https://openid.net/specs/openid-connect-prompt-create-1_0.html#rfc.section.4) and [`login`](https://openid.net/specs/openid-connect-core-1_0.html#AuthRequest) exists in OIDC for use on the authorized endpoint. However, our use case is different and it might cause confusion to overload these terms.

## Security considerations

None relevant.

## Unstable prefix

Not applicable.
