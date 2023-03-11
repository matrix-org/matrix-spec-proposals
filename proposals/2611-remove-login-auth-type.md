# MSC2611: Remove `m.login.token` User-Interactive Authentication type from the specification

The client-server API specification
[defines](https://matrix.org/docs/spec/client_server/r0.6.1#authentication-types)
a number of "authentication types" for use with the User-Interactive
Authentication protocol.

Of these, `m.login.token` is unused and confusing. This MSC proposes removing it.

## Proposal

The definition of
[token-based](https://matrix.org/docs/spec/client_server/r0.6.1#token-based)
authentication is unclear about how this authentication type should be used. It
suggests "via some external service, such as email or SMS", but in practice
those validation mechanisms have their own token-submission mechanisms (for
example, the
`submit_url` field of the responses from
[`/account/password/email/requestToken`](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-account-password-email-requesttoken)
and
[`/account/password/msisdn/requestToken`](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-account-password-msisdn-requesttoken)
respectively). Additionally, the specification requires that "the server must
encode the user ID in the token", which seems at odds with any token which can
be sent to a user over SMS.

Additional confusion stems from the presence of an `m.login.token` [login
type](https://matrix.org/docs/spec/client_server/r0.6.1#login), which is used
quite differently: it forms part of the single-sign-on login flow. For clarity:
this proposal does not suggest making any changes to the `m.login.token` login
type.

In practice, we are not aware of any implementations of the `m.login.token`
authentication type, and the inconsistency adds unnecessary confusion to the
specification.

## Potential Issues

It's possible that somebody has found a use for this mechanism. However, that
would necessarily entail some custom development of clients and servers, so is
not materially affected by the removal from the specification.
