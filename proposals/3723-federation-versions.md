# MSC3723: Federation Versions

This MSC aims to add a `/versions` endpoint to federation, similar to `/client/versions`.

# Background

Today, Matrix has a unversioned `/versions` endpoint on the client-server specification that
responds with an object containing an array of global matrix versions the server supports.

This endpoint, together with global versioning, provides the source of truth for client-server
compatibility, where clients can detect pre-emptively if a server supports certain endpoints, and/or
provide or tune the user experience according to those versions provided, or provide a friendly
error explaining the server is too old/new for that particular client.

# Proposal

This proposal aims to add a similar API to the federation side;

`GET /_matrix/federation/versions`

Which returns a JSON object, which will contain at least one key, `versions`, with an array of
supported matrix versions, in the same format as `/client/versions`.

This JSON object can also include a `unstable_features` object, with a mapping of feature names to
booleans, in a manner similar to `/client/versions`.

## Rationale

Today, there exists no server-server versioning, this has historically not been a problem, as
server-server communications were relatively stable, and did not change in backwards-incompatible
ways.

However, this may change in the future, and this MSC can enable servers to specify version(s) of
federation behaviour they support.

As such, future MSCs can rely on the fact that their intended behaviour does not need explicit
backwards compatibility detection cases, and could reliably assume the other server (can) know this
server supports its endpoint(s) with this version check.

A wider philosophy surrounding federation endpoint deprecation is out of scope for this MSC, as the
author believes it is up to the SCT to weigh the costs and benefits of deprecating those endpoints,
with the risks of possible federation fragmentation attached to them.

There is currently no expectation that `/client/` endpoints are mounted or listening to
federation-reachable endpoint, so this proposal wishes to address the uncomfortable situation where
a server may have to "probe" another server for its `/client/` endpoint, and fetch versions from
there.

Furthermore, it could be useful that the set of supported matrix
versions are disjointed between the client-version `/versions` and a server-server `/versions`
endpoint, as federation endpoints may have a longer "lifetime" than client-server ones might.

## Forwards compatibility

Considering that this MSC was written after the general introduction of global versioning, it is
possible that a small strata of servers will not implement this endpoint, yet other servers may wish
to probe version-specific federation behavior with this endpoint.

Thus, if a server queries this endpoint, and it does not receive an expected response, it should
also query `/federation/v1/version` to cross-check general availability of the federation endpoints.

If this last call succeeds, the sending server should behave as if the receiving server supports all
versions from v1.1 up until the last version before the version that includes this MSC.

## Caching

Considering that matrix servers are designed (and often expected to) stay up for prolonged periods
of time, and may wish to send and receive much federation traffic in this period, caching could be
introduced for this endpoint.

The cache for `/federation/versions` is valid for 24 hours, this value is chosen as to not re-request
this endpoint unnecessarily, yet allow for (relatively) quick transitions for matrix versions in
this time.

# Unstable endpoint

For the time in this proposal, this endpoint should be mounted on;

`/_matrix/federation/unstable/org.matrix.msc3723/versions`