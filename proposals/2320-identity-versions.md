# Versions information for identity servers

The client-server API currently specifies a `/versions` endpoint that allows
clients to know what version of that API are implemented by the server.
Identity servers could benefit from that endpoint as both homeservers and
clients interact with them, and therefore could know which features they can
expect a given identity server to implement by looking at the versions of the
API it claims to support.

## Proposal

This proposal adds the following endpoint to the identity server API.

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

## Alternative solutions

Another solution which was considered was using the status check endpoint ([`GET
/_matrix/api/v1`](https://matrix.org/docs/spec/identity_service/latest#get-matrix-identity-api-v1))
to serve this information. This solution was discarded because it's using a
versioned endpoint, which doesn't make sense to advertise the supported versions
of the API to use.
