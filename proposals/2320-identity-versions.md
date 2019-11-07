# Versions information for identity servers

The client-server API currently specifies a `/versions` endpoint that allows
clients to know what version of that API and unstable features are implemented
by the server. This allows MSC to be implemented and supported by both servers
and clients before they're merged and incorporated into the stable API.

This is also a feature we will need on the identity server API, because
clients talk to them and need to be aware of unstables features (such as
[MSC2265](https://github.com/matrix-org/matrix-doc/pull/2265)) when they're
implemented by the identity server it's using (if there is one).

## Proposal

This proposal adds two endpoints to the identity server API.

### `GET /_matrix/identity/versions`

This endpoint serves information about the versions of the identity server API
this identity server supports. Its response uses the following format:

```json
{
    "versions": [
        "r0.1.0",
        "r0.2.0",
        "r0.2.1",
    ]
}
```

### `GET /_matrix/identity/unstable_features`

This endpoint serves information about the unstable features, i.e. features
specified in a MSC or an unstable version of the Matrix specification but not in
a stable one, supported by the server. Its response uses the following format:

```json
{
    "unstable_features": {
        "org.matrix.casefold_email_addresses": true
    }
}
```

## Alternative solutions

Another solution which was considered was using the status check endpoint ([`GET
/_matrix/api/v1`](https://matrix.org/docs/spec/identity_service/latest#get-matrix-identity-api-v1))
to serve this information. This solution was discarded because it's using a
versioned endpoint, which doesn't make sense to advertise the supported versions
of the API to use, and this endpoint was serving both the supported versions and
the supported unstable features, whereas it makes more sense to have each of
these pieces of information served on a different endpoint.
