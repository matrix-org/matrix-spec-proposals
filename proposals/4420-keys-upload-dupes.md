# MSC4420: Duplicate one-time key error response for /keys/upload

[`/_matrix/client/v3/keys/upload`] allows clients to publish the public part of their one-time keys.
Under exceptional but not impossible circumstances, a client may lose track of the private parts of
its published one-time keys. This may, for instance, happen through disk failures, disk rollbacks or
general bugs in the client implementation. In such a situation the client will innocently attempt to
publish new keys. If the client uses numeric auto-incrementing key IDs such as vodozemac[^1] does,
this will result in a different key being uploaded for a previously published key ID.

The spec currently doesn't cover this situation and defines neither error responses nor replacement
semantics for [`/_matrix/client/v3/keys/upload`]. Nevertheless, both Synapse[^2] and
Dendrite[^3] [^4] throw an HTTP 400 error in this case. On the client-side matrix-rust-sdk even
parses Synapse's error message to identify the issue[^5].

A client forgetting about its published one-time keys is a grave problem that may result in UTDs for
incoming messages. It appears paramount that a client is made aware of this situation wherever
possible. Therefore, the duplicate key error found in Synapse and dendrite appears sensible and this
proposal attempts to standardise the behavior into the spec.

## Proposal

A new HTTP 400 error response with an error code of `M_DUPLICATE_ONE_TIME_KEY` is added to
[`/_matrix/client/v3/keys/upload`].

``` json5
{
  "errcode": "M_DUPLICATE_ONE_TIME_KEY",
  "error": "One-time key signed_curve25519:AAAAAAAAABA already exists."
}
```

Servers MUST reject requests to [`/_matrix/client/v3/keys/upload`] with the above error if any
one-time key IDs in the request already exist with a different public key on the server.

## Potential issues

None.

## Alternatives

Rather than throwing an error, the server could silently replace the previously published key. This
would prevent UTDs for this particular key ID. It would keep the client unaware of the larger
problem of having lost track of its private one-time keys though.

## Security considerations

None.

## Unstable prefix

While this proposal is not considered stable, `M_DUPLICATE_ONE_TIME_KEY` should be referred to as
`io.github.johennes.msc4420.M_DUPLICATE_ONE_TIME_KEY`.

## Dependencies

None.

[^1]: <https://github.com/matrix-org/vodozemac/blob/a4807ce7f8e69e0a512bf6c6904b0d589d06b993/src/olm/account/one_time_keys.rs#L142>

[^2]: <https://github.com/element-hq/synapse/blob/7e4588ac4f2d18bab150a2c1a123ecb22e535534/synapse/handlers/e2e_keys.py#L978>

[^3]: <https://github.com/element-hq/dendrite/blob/933a12d00e9f3010cb1570c32ca9d87b79665aa4/clientapi/routing/keys.go#L67>

[^4]: <https://github.com/element-hq/dendrite/blob/933a12d00e9f3010cb1570c32ca9d87b79665aa4/userapi/internal/key_api.go#L774>

[^5]: <https://github.com/matrix-org/matrix-rust-sdk/blob/main/crates/matrix-sdk/src/encryption/mod.rs#L680>

  [`/_matrix/client/v3/keys/upload`]: https://spec.matrix.org/v1.17/client-server-api/#post_matrixclientv3keysupload
