# MSCXXXX: Clarify that pagination tokens are directionless

The Matrix client-server API has several endpoints which handle pagination over events:

* [`/messages`][messages]
* [`/sync`][sync]
* [`/relations`][relations]
* [`/context`][context]
* [`/search`][search]

Each returns tokens that can be used for further pagination, though over time the
specification has accumulated inconsistencies around which tokens can be used with
which endpoints.

There is a [spec PR](spec2357) which attempts
to fix an inconsistency in the `/relations` endpoint: the `from` parameter currently lists
`next_batch` from `/sync` as an acceptable value, but this was likely meant to be
`prev_batch`.

From discussions, this has raised a broader question: are tokens directional or are they
just opaque positions in the timeline?

Synapse has always used a single [`StreamToken`][synapse-streamtoken] type at the API
level across `/sync`, `/messages`, and `/relations`. These tokens are accepted and returned
interchangeably between endpoints — the same `StreamToken.from_string()` parses
them regardless of which endpoint produced or consumes them. This makes
directionless tokens the de facto behavior, though it has never been explicitly
documented.

Note that Synapse internally embeds a [`RoomStreamToken`][synapse-roomstreamtoken]
within `StreamToken` which can represent either a stream position (`s` prefix) or a
topological position (`t` prefix). This distinction is an internal implementation
detail — the API-visible `StreamToken` envelope is the same type everywhere.

This MSC aims to codify that understanding and clean up the
inconsistencies across endpoints.

## Proposal

Pagination tokens returned by any of the pagination endpoints ([`/messages`][messages],
[`/sync`][sync], [`/relations`][relations], [`/context`][context], [`/search`][search])
represent opaque positions in the event timeline and are interchangeable between endpoints.
The direction of pagination is determined solely by the `dir` parameter where present,
not by the type of token.

The following updates are made to the spec text.

### [`/relations`][relations] endpoint

The `from` and `to` parameter descriptions are updated to note they can accept a token
from any pagination endpoint, rather than the narrow list currently specified.

### [`/messages`][messages] endpoint

The `from` and `to` parameter descriptions are updated to note they can accept a token
from [`/context`][context] or [`/search`][search], and the "not required to support" caveat
on `start` tokens is removed.

### [`/context`][context] endpoint

The `/context` endpoint returns `start` and `end` tokens in its response, currently
described with directional language ("A token that can be used to paginate backwards
with" / "A token that can be used to paginate forwards with"). These descriptions are
updated to remove the directional language.

### [`/search`][search] endpoint

The `/search` endpoint returns a `next_batch` token. Its description is sufficient
as-is, but it is noted that this token can be used with other pagination endpoints
as well.

## Potential issues

Implementations which perform validation on the shape or format of pagination
tokens might reject tokens from other endpoints. The extent to which tokens are
interchangeable varies by implementation.

### Synapse

Synapse uses a single [`StreamToken`][synapse-streamtoken] type for all pagination
tokens across `/sync`, `/messages`, `/relations`, `/context`, and `/search`. It
does not distinguish direction or origin in the token itself. (Internally, the
`room_key` sub-field is a [`RoomStreamToken`][synapse-roomstreamtoken] which can
represent a stream or topological position, but this is an implementation detail
— the API-visible token envelope is the same everywhere.) No changes are required.

### Conduit lineage (conduwuit / continuwuity / Tuwunel)

These implementations use a [`PduCount`][conduit-pducount] type (a signed integer
with `Normal(u64)` / `Backfilled(i64)` variants) across `/messages`, `/relations`,
`/threads`, and `/context`. Tokens from these endpoints are interchangeable.

However, `/sync` parses its `since` parameter as a `u64` — it accepts **only**
non-negative integers. A `PduCount::Backfilled` (negative) token from `/relations`
or `/messages` would fail to parse in `/sync`. The reverse direction works: sync
tokens are always non-negative and parse cleanly as `PduCount::Normal`.

**Changes needed:** `/sync` should accept `PduCount` (signed) instead of `u64` to
fully interoperate with other endpoints.

### Dendrite lineage (Dendrite / Zendrite)

These implementations use **three separate token types** with strict prefix-based
validation:

* [`StreamingToken`][dendrite-streaming] (`s{...}`) — used by `/sync`.
* [`TopologyToken`][dendrite-topology] (`t{...}`) — used by `/messages` and `/context`.
* [`StreamPosition`][dendrite-streampos] (bare integer) — used by `/relations`.

`/relations` parses its tokens via `strconv.Atoi`, which rejects both `s`- and
`t`-prefixed strings. Conversely, `/sync` expects only `StreamingToken` and
rejects bare integers and `t`-prefixed strings. Only `/messages` has dual-parsing
logic that tries `TopologyToken` first and falls back to `StreamingToken`,
converting server-side.

**Tokens are not interchangeable** across `/sync`, `/relations`, `/messages`, and
`/context` in these implementations. This MSC would call for them to become more
permissive.

**Changes needed:** At minimum, `/relations` should accept `StreamingToken` and
`TopologyToken` formats (or their underlying values), and `/sync` should accept
`TopologyToken` and bare integers. A pattern like `/messages` already uses
(try one format, fall back to another, converting server-side) could be applied
to the other endpoints.

## Alternatives

The main alternative is to leave the current inconsistencies as-is. The [spec PR](spec2357)
could land its minimal fix, though the review discussion showed it is unclear which
direction is correct without addressing the broader question of interchangeability.

Another alternative is to acknowledge the divergence: declare that tokens are specific
to each endpoint and not interchangeable. This would match Dendrite's current design
but would be a departure from Synapse's long-standing behavior and is inconsistent
with how developers use these tokens in practice (e.g. using a `/sync` `prev_batch`
token as the `from` parameter to `/messages`).

## Security considerations

None.

## Unstable prefix

N/A

## Dependencies

N/A

[messages]: https://spec.matrix.org/latest/client-server-api/#get_matrixclientv3roomsroomidmessages
[sync]: https://spec.matrix.org/latest/client-server-api/#get_matrixclientv3sync
[relations]: https://spec.matrix.org/latest/client-server-api/#get_matrixclientv1roomsroomidrelationseventid
[context]: https://spec.matrix.org/latest/client-server-api/#get_matrixclientv3roomsroomidcontexteventid
[search]: https://spec.matrix.org/latest/client-server-api/#post_matrixclientv3search

[spec2357]: https://github.com/matrix-org/matrix-spec/pull/2357

[synapse-streamtoken]: https://github.com/element-hq/synapse/blob/76b4fdceed0739d83ac79588416dc88f25d8d14e/synapse/streams/config.py#L39-L45
[synapse-roomstreamtoken]: https://github.com/element-hq/synapse/blob/76b4fdceed0739d83ac79588416dc88f25d8d14e/synapse/types/__init__.py#L722

[conduit-pducount]: https://github.com/continuwuation/continuwuity/blob/main/src/core/matrix/pdu/count.rs#L13-L17

[dendrite-streaming]: https://github.com/element-hq/dendrite/blob/main/syncapi/types/types.go#L106-L118
[dendrite-topology]: https://github.com/element-hq/dendrite/blob/main/syncapi/types/types.go#L213-L218
[dendrite-streampos]: https://github.com/element-hq/dendrite/blob/main/syncapi/types/types.go#L41-L52
