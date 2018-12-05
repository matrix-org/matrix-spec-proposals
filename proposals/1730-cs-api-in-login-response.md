# MSC1730: Mechanism for redirecting to an alternative server during login

It may be useful, particularly for complex deployments consisting of multiple
backends, for homeservers to redirect clients to a different base URL for the
Client-Server API after initial login.

## Proposal

The response to `POST /_matrix/client/r0/login` currently includes the fields
`user_id`, `access_token`, `device_id`, and the deprecated `home_server`.

We will add to this the the field `well_known`, which has the same format as
the [`/.well-known/matrix/client`
object](https://matrix.org/docs/spec/client_server/r0.4.0.html#get-well-known-matrix-client).

Clients SHOULD use the URLs provided for the homeserver and identity server for
the rest of the user's session.
