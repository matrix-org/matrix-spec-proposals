# MSC3468: MXCs to Hashes

Currently, matrix media/content repositories work with a MXC to blob mapping, fetching the media
from the domain embedded in the MXC to present it to the user.

However, this becomes a problem when media retention, redaction, and resiliency come into play,
the singular MXC URI becoming a point of failure once the backing server retracts the URI, either
deliberately (aforementioned redaction), or accidentally (via server reset, or losing the backing media).

This is in opposition to how MXCs are used in matrix today, much like Discord media URLs;
immutable and always online, links are copied and reused across rooms.

## Proposal

I propose for MXCs to be reworked into being a pointer to hashes.

This gives the extra benefit of decoupling aliasing pointers (such as the MXC is) with the underlying media.

Alongside this change, I also propose for an additional client-side endpoint which can quickly "clone"
a MXC. This being done by having the server look up the MXC's hash,
and then creating a new MXC also referencing that hash.

The client-server content API would expose a method for the client to retrieve the hash of a
particular MXC, alongside aforementioned method to clone it.

The server-server content API would add a dedicated fetch method for fetching the hash to a MXC, and
fetching the media to a hash.

### Specification

#### Client-Server

This proposal would like to add the following two methods to CS;

```
POST _matrix/media/v4/clone/{serverName}/{mediaId}

Rate-limited: Yes
Authentication: Yes

Responses:
  200: JSON (see below)
  429: Ratelimited
  503: Could not fetch remote MXC-to-hash mapping
```
200 response:
```json
{
  "m.clone.mxc": "mxc://local.server/media_id"
}
```

```
GET _matrix/media/v4/hash/{serverName}/{mediaId}

Rate-limited: Yes
Authentication: Yes

Responses:
  200: JSON (see below)
  429: Ratelimited
  503: Could not fetch remote MXC-to-hash mapping
```

200 response:
```json5
{
  "m.mxc.hash": "1234567890abcdef" // hex-encoded hash
}
```

#### Server-Server

This proposal would like to add the following two endpoints to S2S;

```
GET _matrix/federation/v?/media/hash

Rate-limited: No
Authentication: Yes

Query parameters:
  media_id: string, the local part of an MXC for which the hash is queried

Responses:
  200: Pure-binary encoding of corresponding hash
  404: Media ID does not exist
```

```
GET _matrix/media/v4/media/fetch/{hash}

Rate-limited: Yes
Authentication: Yes

Responses:
  200: Blob of data corresponding to hash
  404: Hash-media not found
  429: Ratelimited
```

### "Which hash?"

*Note: this is an area of feedback, this'll be removed in the final draft*

So far, the definition of "hash" has been vague. I think converging on a specific hash function
could be a lock-in for future expansion.

So, i'd like to propose using [`multihash`](https://github.com/multiformats/multihash) for these
purposes, this would allow a common format self-describing the hashes used.

For now, only a set series of hashes would be included (see
[here](https://github.com/multiformats/multicodec/blob/master/table.csv) for a full table), which
can be expanded/deprecated with subsequent matrix spec releases, without changing up the format of
the hash, or documenting checks to differentiate the types of hash used, or to reinvent multihash.

However, this is up for debate.

## Motivation

This MSC wishes to unblock efforts for media retention and redaction;
- https://github.com/matrix-org/synapse/issues/6832
- https://github.com/matrix-org/matrix-doc/issues/701

By addition of the `/clone` endpoint, any client wishing to preserve media, can do so by simply
fetching/storing media locally, reducing the linkrot effect that remote servers redacting media
could have.

This MSC would also wish to make matrix more flexible for diverse media delivery systems.

Mapping MXCs to hashes could allow the hashes themselves to become self-verifying keys in any
(centralized or distributed) KV store.

This, in turn, could prepare matrix better for P2P efforts.

This MSC also wishes to make matrix content delivery more resilient, with the exception of mapping a
MXC alias to a hash, a hash could be retrieved from anywhere, and still be self-verifying,
considerably lessening the bus factor, and allowing for better distributed load (see the first
"future extension" in below section)

## Potential issues

This could have a slight performance hit, as an extra RTT between servers is needed to fetch the
media actual, after fetching the hash corresponding to that bit of media.

I think this is a more acceptable tradeoff, an alternative would be to side-channel the hash in a
header, in an endpoint fetching directly from a MXC.

## Future extensions

*Note: this is free-form speculation, and serves to illustrate how future MSCs can extend the
behavior this MSC is enabling.*

A possible extension would be a server-server endpoint which requests what recommended content
endpoints would be to fetch hashes from.

(I.e. a server would ask `/media/endpoints`, and the server can respond with
`["https://common.caching.server", "https://matrix.org"]`, in decreasing order of priority)

This can be helpful when servers share a common "media server", as is the case today with
[matrix-media-repo](https://github.com/turt2live/matrix-media-repo), which "tricks" federation by
redirecting any request for media to itself. This future extension would formalize this process.

This would also be helpful with dealing with "thundering herds", as servers can be redirected to
multiple servers to fetch media from a hash from.

(However, as-is, this could have security problems with DoS-ing, issues with cache invalidation
after redacting media, and possibly more. This is only to illustrate flexibility.)

Another possible extension could be to allow to tap in natively to decentralized media stores, which
often key their data to hashes. This could make media P2P easier to implement and work with.

One last possible extension is to add `410` to every endpoint pertaining fetching media, this could
help with communicating that media has been deleted to servers and clients.

## Security considerations

A big part of this MSC's motivation is to unblock media redaction/retention efforts. However, that
does not mean this MSC should be blind to the struggle of containing unsavory media across
federation.

This MSC adds a `/clone` endpoint, by which a client, on any server, could easily "copy" media,
seemingly making containment efforts useless.

However, at a room-level, and possibly a server-level, hashes themselves could be banned. This can
be implementation-specific, or be built-into bots like mjolnir.

## Unstable prefix

*If a proposal is implemented before it is included in the spec, then implementers must ensure that the
implementation is compatible with the final version that lands in the spec. This generally means that
experimental implementations should use `/unstable` endpoints, and use vendor prefixes where necessary.
For more information, see [MSC2324](https://github.com/matrix-org/matrix-doc/pull/2324). This section
should be used to document things such as what endpoints and names are being used while the feature is
in development, the name of the unstable feature flag to use to detect support for the feature, or what
migration steps are needed to switch to newer versions of the proposal.*
