# MSCxxxx: Remove the `query_auth` federation endpoint

The `query_auth` federation endpoint is unused by Synapse and should be removed.
The current implementation in Synapse is not robust and will return a 500 error
in some situations.

## Proposal

Remove the following endpoint:

* [POST `/_matrix/federation/v1/query_auth/{roomId}/{eventId}`](https://matrix.org/docs/spec/server_server/r0.1.3#post-matrix-federation-v1-query-auth-roomid-eventid)

## Potential issues

Removing this endpoint impacts backwards compatibility, in practice removing
this endpoint should have minimal impact as it was an unused error path in
Synapse. The federation client code to call this endpoint was removed in Synapse
v1.5.0rc1.

Note that dendrite has never implemented this federation endpoint.

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

The endpoint could be deprecated in removed in a future version of the specification.

## Security considerations

None.
