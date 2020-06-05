# MSC2610: Remove `m.login.oauth2` User-Interactive Authentication type from the specification

The client-server API specification
[defines](https://matrix.org/docs/spec/client_server/r0.6.1#authentication-types)
a number of "authentication types" for use with the User-Interactive
Authentication protocol.

Of these, `m.login.oauth2` is underspecified and of no
real use. This MSC proposes removing them.

## Proposal

The definition of
[OAuth2-based](https://matrix.org/docs/spec/client_server/r0.6.1#oauth2-based)
authentication is incomplete. [OAuth2](https://oauth.net/2/) is best considered
as a framework for implementing authentication protocols rather than a protocol
in its own right, and this section says nothing about the grant types, flows
and scopes which a compliant implemenation should understand.

A better candidate for OAuth2-based authentication of matrix clients is via
[OpenID Connect](https://openid.net/connect/), but this has already been
implemented in Matrix via the `m.login.sso` authentication type.

The `m.login.oauth2` section is therefore unimplementable in its current form,
and redundant. It should be removed from the specification to reduce confusion.

## Alternatives

It would be possible to extend the definition so that it is complete: as
mentioned above, a likely implemenation would be based on OpenID
Connect. Matrix clients could then follow the standardised OpenID Connect flow
rather than the matrix-specific `m.login.sso` flow. However, this would require
significant design work, and development in both clients and servers, which
currently feels hard to justify when a working solution exists via
`m.login.sso`.
