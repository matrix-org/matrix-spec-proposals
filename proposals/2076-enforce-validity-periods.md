# MSC2076: Enforce key-validity periods when validating event signatures

## Background

The [Federation API
specification](https://matrix.org/docs/spec/server_server/r0.1.1.html#validating-hashes-and-signatures-on-received-events)
specifies that events should be validated via the signature verification
algorithm, but does not specify how the keys for that check should be obtained
and validated.

In practice, the implementation has been as follows. The receiving server
first requests a copy of the key via the [`GET /_matrix/key/v2/server/`
API](https://matrix.org/docs/spec/server_server/r0.1.1.html#get-matrix-key-v2-server-keyid)
directly from the server which created the signature, or via the [`POST
/_matrix/key/v2/query` API](https://matrix.org/docs/spec/server_server/r0.1.1.html#post-matrix-key-v2-query)
from a trusted key server. Once such a key is obtained, it is then cached
forever. No check is made on the `valid_until_ts` field, and
`minimum_valid_until_ts` is set to zero for calls to `POST
/_matrix/key/v2/query`.

This is highly unsatisfactory, as it means that, should a key be compromised,
then an attacker can spoof arbitrary events claiming to be from the compromised
server forever, since there is no revocation mechanism.

## Proposal

This MSC proposes to enforce the `valid_until_ts` property when validating
event signatures. In particular, the server must ensure that it has a copy of
the key with a `valid_until_ts` at least as large as the `origin_server_ts` of
the event being validated. If it does not have such a copy, it must try to
obtain one via the `GET /_matrix/key/v2/server/` or `POST
/_matrix/key/v2/query` APIs.  For the latter, it must set
`minimum_valid_until_ts` to prompt the notary server to attempt to refresh the
key if appropriate.

Since this changes the rules used to validate events, it will be introduced
with a new room version. This will reduce the risk of divergence between
servers in a room due to some servers accepting events which others reject.

This MSC also proposes that the current situation - where `valid_until_ts` is
ignored - be formalised for the existing room versions v1-v4, rather than be
left as implementation-specific behaviour.
