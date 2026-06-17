# MSC4492: Clarify that pagination tokens are directionless

The Matrix client-server API has several endpoints which handle pagination over events:

* [`/messages`][messages]
* [`/sync`][sync]
* [`/relations`][relations]
* [`/context`][context]
* [`/search`][search]'s `context` field for each result

Each returns tokens that can be used for further pagination, though the specification is
vague around which tokens can be used with which endpoints.

There is a [spec PR](spec2357) which attempts to fix an inconsistency in the `/relations`
endpoint: the `from` parameter currently lists `next_batch` from `/sync` as an acceptable
value, but this was likely meant to be `prev_batch`. This has raised a broader question:
are pagination tokens directional, or do they represent an opaque position in the event
stream without inherent direction?

Synapse has always treated tokens as opaque positions — a [`StreamToken`][synapse-streamtoken]
can be used for both forward and backward pagination depending on the `dir` parameter.
(Internally it embeds a [`RoomStreamToken`][synapse-roomstreamtoken] with stream (`s`)
and topological (`t`) variants, but this is an implementation detail — the API-visible
type is the same everywhere.)

This MSC aims to codify that understanding: pagination tokens do not have an
inherent direction, even if they happen to be labelled `next_batch` or
`prev_batch`. The direction is always determined by the `dir` parameter.

## Proposal

Pagination tokens produced by `/messages`, `/relations`, `/context`, and `/search`'s
`context` field represent a position in the event stream and MUST be indistinguishable.
Tokens SHOULD
only be used within the context of a single room. (E.g. a request for `/messages` in
room #test:matrix.org does not make sense to re-use for #foo:matrix.org.)

A token produced by `/messages`, `/relations`, `/context`, the `context` response field of `/search`, or the `prev_batch` response field of `/sync`, is tied to the room it
was produced for and clients MUST NOT use them for another room. There are no guarantees
using one in a different room will produce the correct results; servers MAY throw
an error in this case.

`next_batch` tokens produced by [`/sync`][sync] resolve against the server's
global event stream and is safe to use across rooms for `/messages`, `/relations`,
and `/context`. `/sync` only accepts tokens produced by `/sync`.

The following table summarises which tokens each endpoint currently accepts and proposed changes:

| Endpoint | Input | Currently accepts | Output | Change |
|---|---|---|---|---|
| `/sync` | `since` | Its own `next_batch` | `next_batch`, `prev_batch` | None |
| `/messages` | `from` | `/sync` (`prev_batch`/`next_batch`), itself (`end`), optionally itself (`start`) | `start`, `end` | `/sync`, `/messages`, `/relations`, `/context`, and `/search`'s `context` |
| `/messages` | `to` | `/sync` (`prev_batch`/`next_batch`), itself (`end`) | — | `/sync`, `/messages`, `/relations`, `/context`, and `/search`'s `context` |
| `/relations` | `from` | Itself, `/messages` (`start`), `/sync` (`next_batch`) | `next_batch`, `prev_batch` | `/sync`, `/messages`, `/relations`, `/context`, and `/search`'s `context` |
| `/relations` | `to` | Itself, `/messages`, `/sync` (vague) | — | `/sync`, `/messages`, `/relations`, `/context`, and `/search`'s `context` |
| `/context` | (none) | Output only | `start` ("backwards"), `end` ("forwards") | Remove directional language |
| `/search` result | (none) | Output only | `start`, `end` (no directional language) | None |

Note that this does not modify the pagination of `/search` results itself, which are
only usable within `/search`.

Open question: should `/threads` also be part of this list?

## Potential issues

Homeserver implementations differ in how they structure pagination tokens. The rules
above may drastically break how a homeserver generates pagination tokens.

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
and `/context`. Tokens from these endpoints do not encode direction.

`/sync` parses its `since` parameter as a `u64` — it accepts **only**
non-negative integers. A `PduCount::Backfilled` (negative) token from `/relations`
or `/messages` would fail to parse in `/sync`. The reverse direction works: sync
tokens are always non-negative and parse cleanly as `PduCount::Normal`.

### Dendrite lineage (Dendrite / Zendrite)

These implementations use **three separate token types** where each type is tied to
a specific endpoint, encoding both direction and origin in the token format:

* [`StreamingToken`][dendrite-streaming] (`s{...}`) — used by `/sync`.
* [`TopologyToken`][dendrite-topology] (`t{...}`) — used by `/messages`, `/context`,
  and `/search`'s `context`.
* [`StreamPosition`][dendrite-streampos] (bare integer) — used by `/relations`.

`/relations` parses its tokens via `strconv.Atoi`, which rejects both `s`- and
`t`-prefixed strings. Conversely, `/sync` expects only `StreamingToken` and
rejects bare integers and `t`-prefixed strings. Only `/messages` has dual-parsing
logic that tries `TopologyToken` first and falls back to `StreamingToken`,
converting server-side.

**Changes needed:** At minimum, `/relations` should accept any token format (not
just bare integers). A pattern like `/messages` already uses (try one format,
fall back to another, converting server-side) could be applied to the other endpoints.

## Alternatives

The main alternative is to leave the current inconsistencies as-is. The [spec PR](spec2357)
could land its minimal fix, though the review discussion showed it is unclear which
direction is correct without addressing the broader question of interchangeability.

Another alternative is to leave each endpoint describing its own accepted token
types independently, with no general principle. This is the status quo.

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
