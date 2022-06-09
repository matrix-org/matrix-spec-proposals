# HS -> AS authorization header
Most of the auth tokens in the spec are passed in the `Authorization` header,
with the `access_token` query parameter supported for backwards-compatibility.
For some reason, the application service spec was not updated in the same way
and it still requires using the archaic query parameter when the homeserver
pushes transactions to the appservice.

## Proposal
The `access_token` query parameter is removed from all requests made by the
homeserver to appservice and is replaced with the `Authorization` header with
`Bearer <token>` as the value.

### Backwards-compatibility
Homeservers which want to support old spec versions in the appservice API may
send both the query parameter and header. Similarly, appservices may accept the
token from either source.

## Security considerations
Not fixing this causes access tokens to be logged in many bridges.

## Alternatives
We could add a way for appservices to explicitly specify which spec version
they want in order to implement backwards-compatibility without sending both
tokens.

## Unstable prefix
The authorization header is already used in the client-server spec, and an
unstable prefix would just unnecessarily complicate things.
