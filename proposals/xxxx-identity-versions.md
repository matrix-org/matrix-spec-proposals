# Versions information for identity servers

The client-server spec currently specifies a `/versions` endpoint that allows
clients to know what version of that spec and unstable features are implemented
by the server. This allows MSC to be implemented and supported by both servers
and clients before they're merged and incorporated into the stable spec.

This is also a feature we will need on the identity server spec, because
clients talk to them and need to be aware of unstables features (such as
[MSC2265](https://github.com/matrix-org/matrix-doc/pull/2265)) when they're
implemented by the identity server it's using (if there is one).

## Proposal

This proposal extends the [`/_matrix/identity/v2`](https://matrix.org/docs/spec/identity_service/r0.2.1#get-matrix-identity-api-v1)
endpoint's response by adding information about the supported versions of the
identity server specification and unstable features implemented by the server
to it. Because the current response for this endpoint is an empty object
(which is discarded by the client), the new response would look like:

```json
{
    "unstable_features": {
        "m.casefold_email_addresses": true
    },
    "versions": [
        "r0.1.0",
        "r0.2.0",
        "r0.2.1",
    ]
}
```

This response would follow the format of the [`/_matrix/client/versions`](https://matrix.org/docs/spec/client_server/unstable#get-matrix-client-versions) endpoint.

## Alternative solutions

An alternative solution to this issue would be to add a
`/_matrix/identity/versions` endpoint to the identity server specificiation.
This would however add more complexity by adding a new endpoint whereas there's
already an existing endpoint which seems relevant for handling this kind of
information.
