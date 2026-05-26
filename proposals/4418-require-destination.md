# MSC4418: Make `destination` a required server authentication field

Currently the server to server authentication scheme allows `destination` to be optional for
backwards-compatibility, however most homeserver implementations today no longer permit this.
It additionally makes vHosting more difficult to implement and utilize.

## Proposal

Require `destination` for
[authenticated federation requests](https://spec.matrix.org/v1.17/server-server-api/#request-authentication).

## Potential issues

Older homeservers which do not send the field may be unable to federate
with servers that implement this MSC, however all major implementations
have caught up by now:

- Continuwuity:
  [read](https://forgejo.ellis.link/continuwuation/continuwuity/src/commit/8d66500c991202f464785d34f3cfa31a1c831997/src/api/router/auth.rs#L327-L329),
  [write](https://forgejo.ellis.link/continuwuation/continuwuity/src/commit/754959e80d4865cfcfd9c0de10ab9391b11bac39/src/service/federation/execute.rs#L251)
- Synapse:
  [read](https://github.com/element-hq/synapse/blob/7e4588ac4f2d18bab150a2c1a123ecb22e535534/synapse/federation/transport/server/_base.py#L111-L118),
  [write](https://github.com/element-hq/synapse/blob/df24e0f30244b1c423f4130d64c6008be341d0b7/synapse/http/matrixfederationclient.py#L956)
- Tuwunel:
  [read](https://github.com/matrix-construct/tuwunel/blob/da3e7539f4753e8c681c8f0ade447dfab201f408/src/api/router/auth/server.rs#L99-L101),
  [write](https://github.com/matrix-construct/tuwunel/blob/da3e7539f4753e8c681c8f0ade447dfab201f408/src/service/federation/execute.rs#L280)
- Conduit:
  [read](https://gitlab.com/famedly/conduit/-/blob/8def22bfb8b9b23bbd47e17772f2bd80500eacf6/src/api/ruma_wrapper/axum.rs#L198),
  [write](https://gitlab.com/famedly/conduit/-/blob/8def22bfb8b9b23bbd47e17772f2bd80500eacf6/src/api/server_server.rs#L282)
- gomatrixserverlib (Dendrite):
  [read](https://github.com/matrix-org/gomatrixserverlib/blob/6c4c6f7d0d301cef23e84d237b27d9e9ff4562d7/fclient/request.go#L216),
  [write](https://github.com/matrix-org/gomatrixserverlib/blob/6c4c6f7d0d301cef23e84d237b27d9e9ff4562d7/fclient/request.go#L158)

## Alternatives

None?

## Security considerations

None.

## Unstable prefix

None.

## Dependencies

None.
