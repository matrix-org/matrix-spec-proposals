# MSC4166: Specify `/turnServer` response when no TURN servers are available

Currently, there is no clear response specified for the
[`/turnServer`](https://spec.matrix.org/v1.10/client-server-api/#get_matrixclientv3voipturnserver)
endpoint when there are no TURN servers configured, leading to
[inconsistent responses from server implementations](https://github.com/matrix-org/matrix-spec/issues/1795)
under these conditions.

## Proposal

When there are no TURN servers available for the server to provide to the requesting client, the server MUST
respond with a `M_NOT_FOUND` `404` error response.

## Potential issues

None considered.

## Alternatives

- Use a new error code. This was not used as `M_NOT_FOUND` is not that bad of a fit, and an error code
  only usable for a single endpoint would be redundant.
- Respond with a different `200 OK` response. This would technically be a breaking change, whereas this
  is not (to the same extent, as clients should already try to handle errors), hence it is not preferred.

## Security considerations

None considered.

## Unstable prefix

None required, as no new endpoints or field are being proposed.

## Dependencies

None.
