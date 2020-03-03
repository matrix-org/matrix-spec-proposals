# MSCxxxx: Remove the `query_auth` federation endpoint

The `query_auth` federation endpoint is unused by Synapse and should be removed.
The current implementation in Synapse is broken and will return a 500 error in
some situations.

## Proposal

Remove:

* [POST `/_matrix/federation/v1/query_auth/{roomId}/{eventId}`](https://matrix.org/docs/spec/server_server/r0.1.3#post-matrix-federation-v1-query-auth-roomid-eventid)

## Potential issues

Removing this endpoint impacts backwards compatibility.

In practice, removing this endpoint should have minimal impact. Since 1.5.0rc1
of Synapse this endpoint is not called (see [#6214](https://github.com/matrix-org/synapse/pull/6214)).
During removal it was noted that the code to call this endpoint was already
unreachable.

Note that it seems like this was initially supported in Synapse v0.7.0. It is
not clear at what point it became unused.

## Alternatives

The endpoint could be deprecated in removed in a future version of the specification.

## Security considerations

None.
