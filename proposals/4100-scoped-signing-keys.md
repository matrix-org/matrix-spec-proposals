# MSC4100: Scoped signing keys

Matrix uses signing keys to authorize [requests](https://spec.matrix.org/v1.9/server-server-api/#authentication)
between servers and [events](https://spec.matrix.org/v1.9/server-server-api/#signing-events) in a room.
Servers can additionally expose multiple signing keys through the [key exchange system](https://spec.matrix.org/v1.9/server-server-api/#retrieving-server-keys).
All exposed signing keys can currently be used for either purpose: requests or events.

Following a principle of lease privilege, large distributed servers (one logical homeserver represented
by several physical servers) may prefer to narrow the capabilities of a given key. These scoped keys
can then be given to individual services within the overall homeserver system to perform exactly what
is required.

Few examples of this homeserver architecture exist today, however components are emerging: providers
which use a detached media repository service within their infrastructure may reasonably expect that
signing capabilities are limited. If the media repository is further responsible for multiple homeservers,
multiple homeserver signing keys may be stored in a single place. It is therefore more desirable to
have highly specific and narrowly scoped keys to limit the reach of a malicious actor, should they
get access to the collection of signing keys.

This proposal introduces such scoped signing keys, allowing large deployments (when they exist) to
segment their infrastructure with highly specific keys.

**Note**: Currently, the media repository does *not* need a signing key in order to function. With
the introduction of [MSC3916](https://github.com/matrix-org/matrix-spec-proposals/pull/3916) and
similar however, the service does need to be able to authenticate requests. The specific use case of
the author's own [MMR](https://github.com/t2bot/matrix-media-repo) project wishing to support MSC3916
is the (non-blocking) motivation for this MSC.

## Proposal

A new [`GET /_matrix/key/v2/server`](https://spec.matrix.org/v1.9/server-server-api/#get_matrixkeyv2server)
endpoint at `GET /_matrix/key/v3/server` is introduced. The existing endpoint returns keys which serve
any purpose, and simply adding a `scope` to them could still cause events to be sent in existing room
versions or wrongly authorize network requests against servers unaware of the `scope`. By introducing
a new endpoint, servers must explicitly be aware of the keys, therefore allowing them to be properly
scoped.

The new `/server` endpoint takes the same request parameters as the old one. The response includes a
`scope` on each of the keys, but is otherwise the same:

```jsonc
{
  "server_name": "example.org",
  "valid_until_ts": 1652262410000,
  "verify_keys": {
    "ed25519:abc123": {
      "key": "VGhpcyBzaG91bGQgYmUgYSByZWFsIGVkMjU1MTkgcGF5bG9hZA",
      "scope": ["m.events"] // NEW!
    },
    "ed25519:def456": {
      "key": "ThisShouldBeABase64Key",
      "scope": ["m.requests"] // NEW!
    }
  },
  "old_verify_keys": {
    "ed25519:0ldk3y": {
      "expired_ts": 1532645052628,
      "key": "VGhpcyBzaG91bGQgYmUgeW91ciBvbGQga2V5J3MgZWQyNTUxOSBwYXlsb2FkLg",
      "scope": ["m.events"] // NEW!
    }
  },
  "signatures": {
    "example.org": {
      "ed25519:abc123": "VGhpcyBzaG91bGQgYWN0dWFsbHkgYmUgYSBzaWduYXR1cmU",
      "ed25519:def456": "VGhpcyBzaG91bGQgYWN0dWFsbHkgYmUgYSBzaWduYXR1cmU"
    }
  }
}
```

> **TODO**: Make example truthful. Use real keys, valid signatures.

`scope` is *required* and must be an array of [namespaced](https://spec.matrix.org/v1.9/appendices/#common-namespaced-identifier-grammar)
identifiers. The key can only be used for the listed scopes (see below). The scopes *may* change over
time, and should only be cached for as long as the response object is (typically half the lifetime of
`valid_until_ts`).

When a server is attempting to verify something, it will already know which scope is required. Therefore,
unknown or empty scopes do not affect the validity of a given key.

This proposal defines two scopes:

* `m.events` - The key may be used to sign events.
* `m.requests` - The key may be used to sign requests (`X-Matrix` authentication).

> **TODO**: Consider further scoping `m.requests` and maybe `m.events` down into smaller parts. For
> example, a key that can only sign `/_matrix/media/*` requests or `m.room.member` events.

To match the new `/server` endpoint, v3 endpoints for [`POST /_matrix/key/v2/query`](https://spec.matrix.org/v1.6/server-server-api/#post_matrixkeyv2query)
and [`GET /_matrix/key/v2/query/{serverName}`](https://spec.matrix.org/v1.6/server-server-api/#get_matrixkeyv2queryservername)
are introduced. The endpoints both use the new `/_matrix/key/v3/server` endpoint, but otherwise remain
unchanged in request and response behaviour.

The legacy `/_matrix/key/v2/*` endpoints are deprecated and discouraged from use.

> **TODO**: Do we need to list `m.requests`-only keys in `old_verify_keys` when they rotate, or can
> we simply exclude them? `old_verify_keys` is typically used for proving old events are properly
> signed, and those keys can't be used to verify requests anyways.

### Backwards compatibility: requests

[MSC4029](https://github.com/matrix-org/matrix-spec-proposals/pull/4029) clarifies how the `X-Matrix`
authentication scheme is meant to work, and currently states that *if* a key is present then it *must*
be valid. As part of a transition towards scoped signing keys, a server may expose a generic, all-purpose,
key at `/v2/server` and a different, scoped, key at `/v3/server`. If the server included both keys in
the `Authorization` headers, the request would fail when reaching a legacy server because that server
would be unable to locate the newer signing key.

To get around this, the `X-Matrix` auth scheme is duplicated to `X-Matrix-Scoped`. Only scoped signing
keys may be used for `X-Matrix-Scoped`. `X-Matrix` thus becomes deprecated, and only capable of legacy
non-scoped keys.

Requests containing both `X-Matrix` and `X-Matrix-Scoped` auth *must* be valid in their respective
schemes, otherwise the request is failed. Servers *should* use both in independent `Authorization`
headers if possible, or otherwise downgrade their requests to `X-Matrix` if an auth error is received
for `X-Matrix-Scoped` alone.

> **TODO**: Verify this approach is compatible with existing servers. ie: that they don't fail requests
> due to unknown auth schemes being present (when combined with `X-Matrix`).

### Backwards compatibility: events

Similar to requests, using a scoped signing key in an existing room version will potentially cause
older servers to reject the event due to being unable to locate the newer key. We fix this by introducing
a room version which *requires* the use of scoped signing keys, banning the use of legacy all-purpose
keys. Existing room versions enact the opposite, as we have today: events *must* be signed by all-purpose
keys, not scoped keys.

This sufficiently requires servers to become aware of scoped signing keys to continue participating
in increasingly modern room versions.

## Potential issues

This proposal does nothing to make a future breaking change to signing keys more manageable. Instead,
this MSC attempts to diminish the impact of the change by providing fallback for requests and isolating
event signing to dedicated room versions. This approach is awkward, however, and may need to be
duplicated if the signing key scope/purpose were to ever change again in future.

## Alternatives

Implied throughout is adding the `scope` to the existing signing key endpoints, however this can cause
issues. Critically, a legacy server unaware of scopes could allow what is intended to be a scoped signing
key to perform an action that is otherwise illegal in modern servers. This provides a high degree of
backwards compatibility, but when a concern is that the media repo doesn't need to sign events, the
security benefits of scoping are lost.

## Security considerations

This proposal theoretically increases security for distributed or partially distributed homeserver
systems. Such systems are not currently prevalent in Matrix today, however.

## Unstable prefix

**Before completing FCP**:

* `X-Matrix-Scoped` becomes `X-MSC4100-Scoped`.
* `/_matrix/key/v3/*` becomes `/_matrix/key/unstable/org.matrix.msc4100/*`.
* The room version is `org.matrix.msc4100.11`, based on [room version 11](https://spec.matrix.org/v1.9/rooms/v11/).

**After completing FCP, but before released in spec**:

* `X-Matrix-Scoped` may be used as described.
* `/_matrix/key/v3/*` may be used as described.
* The room version remains `org.matrix.msc4100.11`.

**After released in the spec**:

* `X-MSC4100-Scoped` should no longer be used, except for backwards compatibility.
* `/_matrix/key/unstable/org.matrix.msc4100/*` should no longer be used, except for backwards compatibility.
* The room version remains `org.matrix.msc4100.11`.

Note that for a room version to become 'stable', an MSC needs to incorporate the changes described by
this MSC and assign it a stable identifier. See [MSC3820](https://github.com/matrix-org/matrix-spec-proposals/pull/3820)
as an example of this process.

## Dependencies

This MSC would benefit from [MSC4029](https://github.com/matrix-org/matrix-spec-proposals/pull/4029)
being merged, but does not require it.
