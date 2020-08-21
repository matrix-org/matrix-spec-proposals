# MSC2451: Remove the `query_auth` federation endpoint

This API was added without sufficient thought nor testing. The endpoint isn't
used in any known implementations, and we do not believe it to be necessary
for federation to work. The only known implementation (in Synapse) was not fully
fleshed out and is broken.

For background, the idea behind this endpoint was that two homeservers would be
able to share state events with the hope of filling in missing state from one
of homeservers allowing state resolution to complete. This was to protect
against a joining server not providing the full (or providing stale) state.

In addition to the ideas above not coming to fruition, it is unclear whether the
current design of this endpoint would be sufficient. If this state negotiation
feature is needed in the future it should be redesigned from scratch via the MSC
proposal process.

## Proposal

Remove the following endpoint:

* [POST `/_matrix/federation/v1/query_auth/{roomId}/{eventId}`](https://matrix.org/docs/spec/server_server/r0.1.3#post-matrix-federation-v1-query-auth-roomid-eventid)

## Potential issues

Removing this endpoint impacts backwards compatibility, in practice removing
this endpoint should have minimal impact as it was an unused error path in
Synapse. The federation client code to call this endpoint was removed in Synapse
v1.5.0rc1.

There is no evidence of other homeserver implementations having implemented this
endpoint.

### History

This endpoint (and the federation client code) to call it was initially
added in Synapse v0.7.0 (see [#43](https://github.com/matrix-org/synapse/pull/43)).
The federation client code was heavily modified for v1.0.0rc1 (see
[#5227](https://github.com/matrix-org/synapse/pull/5227/)),

The federation client code to call this endpoint was removed in v1.5.0rc1 of
Synapse (see [#6214](https://github.com/matrix-org/synapse/pull/6214). After
that point this endpoint is not called).

During removal it was noted that the code to call this endpoint was already
unreachable. It seems that this code was never reachable and was meant for an
error situation which was never built out (see `git log -S NOT_ANCESTOR`, the
error condition is never assigned).

## Alternatives

The endpoint could be deprecated and removed in a future version of the specification.

## Security considerations

None.
