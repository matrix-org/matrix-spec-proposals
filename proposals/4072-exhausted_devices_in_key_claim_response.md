# MSC4072: Handling devices with no one-time keys in `/keys/claim`

Currently, the specification for [`POST
/_matrix/client/v3/keys/claim`](https://spec.matrix.org/v1.8/client-server-api/#post_matrixclientv3keysclaim)
is unclear about how devices which have no remaining one-time keys should be
handled. It is however explicit that unknown devices be omitted
from the response, and in practice Synapse (at least) treats both scenarios the
same.

This requires clients to keep a record of which devices were included in the
request. This MSC proposes that such devices be included in the response.

## Background

Suppose Alice wishes to send an encrypted message to Bob. To do so, she must
share the message decryption key over peer-to-peer encrypted channels with each
of Bob's devices. To establish an encrypted channel with a given device, Alice
must claim a
[one-time key](https://spec.matrix.org/v1.8/client-server-api/#one-time-and-fallback-keys)
(or fallback key) for that device. To do so, she makes a request to [`POST
/_matrix/client/v3/keys/claim`](https://spec.matrix.org/v1.8/client-server-api/#post_matrixclientv3keysclaim).

However, suppose that Bob rarely uses one of his devices. (For example, it may
be a mobile device he rarely switches on; or it may be a web session he forgot
to log out of.) Suppose also that this device does not support fallback
keys. In this scenario, there may be no one-time keys left to be claimed.

The Matrix specification is unclear about how `/keys/claim` should behave in
this situation. In practice, Synapse omits the device from the response.

A second scenario concerns Alice attempting to claim a one-time-key for a
device (or user) which no longer exists. (This can happen in various
circumstances, the most likely being a network outage leading to a delay in
Bob's server sending the federation request telling Alice's sever that Bob has
logged out on a given device.) In this case, the specification is explicit that
the device be omitted from the response.

Therefore, in order to avoid making a (potentially slow) `/keys/claim` request
for every message that Alice sends, her client must remember exactly which
devices were included in the request. This is not impossible, but can be
slightly fiddly to do in a way that does not cause memory leaks.

## Proposal

For every user and device mentioned in the `one_time_keys` object in the
request for [`POST
/_matrix/client/v3/keys/claim`](https://spec.matrix.org/v1.8/client-server-api/#post_matrixclientv3keysclaim)
and [`POST
/_matrix/federation/v1/user/keys/claim`](https://spec.matrix.org/v1.8/server-server-api/#post_matrixfederationv1userkeysclaim),
the response must contain *exactly one of*:

 * An entry in `one_time_keys` for that user and device. If the device is
   either unknown or has no remaining one-time keys or fallback key, the entry
   should be an empty object (instead of the map from algorithm name to key
   which indicates a successful claim).

 * In the case of `/_matrix/client/v3/keys/claim` only: an entry in `failures`
   corresponding to the server name for the requested user.

A server handling a request to `/_matrix/client/v3/keys/claim` and making an
outgoing federation request to `/_matrix/federation/v1/user/keys/claim` must
itself ensure the response object is correctly populated for any remote users
(otherwise a single misbehaving server in the room may cause problems for the
entire room).

For clarity: servers remain free to reject an entire request with a 40x error
if the request is malformed in some way, such as containing a malformed user
ID. This is not affected by this MSC.

## Potential issues

1. This MSC proposes to make a modification to the specified response of
   `/keys/claim` without having clients opt into the new behaviour (such as via
   a new endpoint version). In theory, it is possible that this could break
   existing clients; however this seems unlikely.

2. A client has no way of telling whether a server is following this proposal,
   or the legacy behaviour.

   This is not seen as a significant problem. If a client assumes that the
   server follows this proposal but it does not, we simply get the existing
   behaviour - i.e., the client makes a `/keys/claim` request on every outgoing
   message, which is a little slow but does not significantly affect functionality.

## Alternatives

### Status Quo

It is of course possible to remember the requested devices on the client side,
which would make this proposal redundant.

This turns out to be particularly fiddly for the `matrix-sdk-crypto` crate
within
[`matrix-rust-sdk`](https://github.com/matrix-org/matrix-rust-sdk). In this
model:

 * The client calls
   [`get_missing_sessions`](https://matrix-org.github.io/matrix-rust-sdk/matrix_sdk_crypto/struct.OlmMachine.html#method.get_missing_sessions)
   which will generate a `/keys/claim` request for the relevant devices at that
   point in time.

 * The client makes the corresponding HTTP request.

 * The client returns the results of the HTTP request via
   [`mark_request_as_sent`](https://matrix-org.github.io/matrix-rust-sdk/matrix_sdk_crypto/struct.OlmMachine.html#method.mark_request_as_sent).

There is therefore no direct correlation between generating the request and
handling the response on the Rust side. The Rust side could remember the
devices included in the `/keys/claim` request, but there is no guarantee that
the client will ever actually call `mark_request_as_sent`; indeed, if the
HTTP request fails for any reason, there will be no such call.

So it would be easy to introduce a memory leak in this way. A correct
implementation might involve some sort of expiring map, or more substantial
changes to the API of `matrix-sdk-crypto`. In any case it is likely to be
non-trivial compared with changing the behaviour on the server side.

### Variations in response shape

There exist various alternatives in how devices with no one-time keys are
represented in the response. None seem significantly superior to simply
returning an empty object.

### Client opt-in

If this proposal is found to cause breaking changes, it may be necessary to
have clients opt-in to the new behaviour in some way (such as with a new
endpoint version). This is not currently believed to be necessary.

### Extensions to `/keys/query`

[`POST
/_matrix/client/v3/keys/query`](https://spec.matrix.org/v1.8/client-server-api/#post_matrixclientv3keysquery)
suffers related problems (in particular, unknown devices are again omitted from
the result). We might consider extending the proposal to that endpoint.

However, whilst the two responses appear similar, the endpoints are used in
quite different ways and it is not obvious that solutions relevant to
`/keys/claim` are automatically relevant to `/keys/query`. This proposal
therefore does not suggest any changes to the behaviour of `/keys/query`.

## Security considerations

None foreseen.

## Unstable prefix

No new identifiers are proposed; it is proposed that servers implementing this
proposal simply do so on the existing endpoints.

## Dependencies

None.
