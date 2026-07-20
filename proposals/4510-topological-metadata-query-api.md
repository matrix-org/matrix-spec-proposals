# MSC4510: Topological peek/query API with sparse fieldsets and Merkleized metadata

Currently the Matrix protocol relies on fetching entire events to perform
backfills or otherwise retrieve previous or missing events. Often we do not know
the shape of the graph we are traversing, whether it is a dead end, or whether
two branches reconnect at a known common ancestor. When a server encounters a
gap in the DAG, the current federation API provides limited ways to discover
which event IDs or remote servers are most likely to help bridge that gap before
fetching full events.

This proposal seeks to reduce these inefficiencies and traversal failures by
allowing homeservers to return routing hints as customized queries of highly
granular metadata and bounded graph facts, including:

- `prev_events` / `auth_events` edge event IDs, up to a recursion limit.
- `origin` for a missing event (potentially useful for retrieving it).
- whether a known edge target is outside the requested room.
- graph shape hints and bounded computed facts, such as common ancestors, hop
  distances, and per-event branching factor from returned edges.

For current room versions 3 and later, returned metadata remains a hint that
must be verified by fetching full events. This proposal also sketches an opt-in
future room-version extension for Merkleized event metadata, allowing selected
metadata fields to be independently verified without fetching the full event
payload.

## Proposal

A new federation endpoint is added:

```http
POST /_matrix/federation/unstable/tk.nutra.msc4510/topology_query
```

The endpoint accepts a bounded query over one or more starting events. The
requesting homeserver chooses the edge types it wants to walk, how deep it wants
to recurse, and which specific metadata fields it wants back.

For example:

```json
{
  "room_id": "!room:example.org",
  "start_event_ids": ["$missing_event_A", "$missing_event_B"],
  "edge_types": ["prev_events"],
  "max_depth": 50,
  "max_event_records": 1000,
  "max_nodes_visited": 5000,
  "fields": ["prev_events", "origin"],
  "compute": ["common_ancestor", "hop_distance"],
  "compute_event_pairs": [["$missing_event_A", "$prev_1"]]
}
```

This asks the responding server to walk backwards through `prev_events`, up to
50 hops, returning only previous-event edges and `origin` hints.

The response is intentionally sparse:

```json
{
  "events": {
    "$missing_event_A": {
      "prev_events": ["$prev_1", "$prev_2"],
      "origin": "example.org"
    },
    "$missing_event_B": {
      "prev_events": ["$prev_1"],
      "origin": "elsewhere.example"
    },
    "$prev_1": {
      "prev_events": ["$prev_0"],
      "origin": "example.org"
    }
  },
  "computed": {
    "common_ancestor": ["$prev_1"],
    "hop_distance": [1]
  },
  "limited": true
}
```

The returned metadata is a hint, not a replacement for fetching and verifying
events. A homeserver can use the hints to decide which servers and event IDs to
try next, then verify full events through normal Matrix rules once it retrieves
them.

### Query shape

The initial query fields are:

- `room_id`: the room being queried.
- `start_event_ids`: event IDs to start from.
- `edge_types`: one or more of `prev_events` or `auth_events`.
- `max_depth`: the maximum number of recursive hops requested.
- `max_event_records`: the maximum number of event records returned.
- `max_nodes_visited`: the maximum number of distinct events visited while
  serving raw traversal and all computed graph query pairs in the request.
- `max_compute_event_pairs`: the maximum number of event ID pairs accepted in
  `compute_event_pairs`.
- `fields`: the exact metadata fields requested.
- `compute`: optional graph facts to compute over the same bounded traversal.
- `compute_event_pairs`: ordered event ID pairs that each computed graph fact
  operates on.

The initial response fields for each event are:

- `room_id`: the room the event belongs to. This is always the requested room,
  since wrong-room events are never returned as records; it is a queryable field
  so that room versions with split canonicalization can prove it.
- `prev_events`: known previous-event edges.
- `auth_events`: known auth-event edges.
- `origin`: the best known origin server for the event.
- `origin_server_ts`: the event timestamp, if known.
- `depth`: the event depth, if known.
- `rejected`: whether the responding server has locally rejected the event, if
  known.
- `soft_failed`: whether the responding server has locally soft-failed the
  event, if known.
- `edge_errors`: non-followed edge targets grouped by edge type and reason.
- `proof`: Merkle proof material, only for future room versions which opt into
  split canonicalization.

Unrecognized `edge_types` entries cause the request to fail with
`M_INVALID_PARAM`, because silently ignoring them would change traversal
semantics without the requester knowing.

If the server does not support computed graph queries at all, it rejects any
request containing `compute` with `M_UNRECOGNIZED`, as described below. If the
server does support computed graph queries, unrecognized `compute` names cause
the request to fail with `M_INVALID_PARAM`.

Unrecognized `fields` entries are ignored, which is indistinguishable from a
server declining to disclose a known field and keeps the field set
forward-extensible.

A room version or extension MAY define additional queryable fields. Unrecognized
`fields` entries remain ignored unless a room version or extension specifies
otherwise.

Future extensions may also define an arbitrary query language over event fields,
including field projection, predicates over event JSON, and recursive relations,
provided the extension specifies deterministic evaluation, authorization
behavior, resource limits, and failure semantics.

The response maps each event ID to an object containing the fields returned for
that event. Servers may omit fields they do not know, do not store efficiently,
or are not willing to disclose to the requester.

The `rejected` and `soft_failed` fields describe the responding server's local
event-processing result. They are hints only, may differ between servers, and
are not independently provable event metadata.

### Traversal

Traversal is breadth-first. The starting events are included in the response at
recursion depth `0`. Events reached by following one requested edge are at depth
`1`, and so on.

Each event ID is visited at most once, even if it is reachable through multiple
paths or multiple edge types. This also prevents cycles from causing repeated
work: an already-seen event is not queued again.

Within the same recursion depth, events MUST be processed in bytewise
lexicographic order by the UTF-8 encoding of the event ID string. This gives
stable results when a response is limited. Because event IDs may be hashes, this
is not intended to prefer the most recent or most useful branch. It is only a
deterministic truncation rule.

The server applies limits in this order:

- reject malformed request fields before traversal;
- reject requests with more than the effective maximum number of start events
  before looking up any events;
- stop before returning more than the effective maximum event record count;
- do not follow edges past the requested or server-configured recursion depth;
- stop queueing or inspecting new events before visiting more than the effective
  maximum number of distinct events;
- stop before exceeding the server's response-size or processing-time limits.

If any limit, visibility check, wrong-room event, unknown event, response-size
cap, or timeout prevents the server from returning data it otherwise would have
walked, it sets `limited` to `true`. If several conditions apply, `limited` is
still just `true`.

When requested via `fields`, a server MAY include `edge_errors` explaining why
certain edge targets were not followed. Servers MUST omit `edge_errors` unless
it is requested in `fields`. The initial reason codes are:

- `wrong_room`: the target event is known to belong to a different room.

For example:

```json
"edge_errors": {
    "prev_events": {
        "$foreign_event": "wrong_room"
    }
}
```

The server MUST NOT include the other room's ID or any metadata from the
wrong-room event. Additionally, a server MUST only apply the `wrong_room` label
if it would be allowed to serve the target event to the requester under the
target event's own room's authorization and history-visibility rules; otherwise
the edge target is treated as unknown and omitted. Without this restriction, the
label would disclose whether the responding server holds an arbitrary event ID
from an unrelated, possibly private, room. Unknown, inaccessible, and hidden
events are omitted rather than labelled, because distinguishing those cases can
reveal room state or history-visibility information.

Implementations SHOULD maintain indexes for `prev_events`, `auth_events`, and
known forward extremities per room. These indexes allow the endpoint to answer
bounded reverse-edge queries and help local repair logic choose useful starting
events without scanning full event JSON. Forward extremities are not returned by
this endpoint because they describe a server's local view of the room DAG
boundary, rather than metadata committed to an individual event.

### Computed graph queries

Responding servers MAY support small computed graph queries in addition to raw
metadata fields. These queries are bounded by the same recursion, record, time,
authorization, and room-boundary limits as normal traversal.

If a server does not support computed graph queries, it MUST reject requests
containing the `compute` field with `M_UNRECOGNIZED`. This ensures the requester
can gracefully fall back to raw edge traversal rather than silently failing to
receive expected computations.

Computed graph queries operate on `compute_event_pairs`. Each entry is a
two-element list of event IDs. If `compute` is present, `compute_event_pairs`
MUST also be present and non-empty. If `compute_event_pairs` is present without
`compute`, the server MUST reject the request with `M_INVALID_PARAM`. Malformed
pairs, pairs with fewer or more than two event IDs, or pairs containing
malformed event IDs cause the request to fail with `M_INVALID_PARAM`.

If the number of `compute_event_pairs` entries exceeds the effective
`max_compute_event_pairs` limit, the server MUST reject the request with
`M_INVALID_PARAM` before performing any event lookup, authorization check, graph
traversal, or computed query processing.

Servers MUST enforce a request-wide aggregate work budget covering raw traversal
and all computed graph query processing. At minimum this budget MUST include the
effective `max_nodes_visited` cap, processing time, and local database-read or
equivalent storage-operation limits. Raw traversal and computed queries consume
the same request-wide `max_nodes_visited` budget; the budget is not reset when
computed query processing begins. The effective cap is the lower of
`max_nodes_visited` and the responding server's local limit.

When more than one `compute_event_pairs` entry is supplied, the server MUST
process pairs in request order. The effective `max_nodes_visited` budget is
shared across the whole request rather than reset for each pair. If the
remaining budget is exhausted before a pair's result can be determined, that
pair's affected computed result is `null`, any later affected results are also
`null`, and the response sets `limited` to `true`. If the request-wide
processing-time, database-read, or storage-operation budget is exhausted after
processing has started, the server returns the partial response it can produce,
sets affected computed results to `null`, and sets `limited` to `true`.

The initial computed query names are:

- `common_ancestor`: given two event IDs, return the nearest event ID reachable
  from both. Distance is measured as the sum of directed hops from each start
  event to the ancestor. If the search is limited before a common ancestor is
  found, the result is `null`; the server MUST NOT return a partial local
  ancestor as if it were final. If multiple ancestors tie for the minimal
  combined hop distance, the server MUST return the bytewise lexicographically
  lowest event ID. Future computed query names may return multiple ancestors or
  richer path metadata, subject to their own result limits and deterministic
  ordering rules.

- `hop_distance`: given two event IDs, return the shortest directed hop distance
  from the first event to the second event following the selected edge types. If
  no directed path is found within the effective recursion limit, the result is
  `null`. If the search is limited (for example by `max_nodes_visited`,
  processing-time, or response-size limits) before a result can be determined,
  the result is `null` and the server MUST set `limited` to `true`.

Future computed query names or query-language extensions MUST specify their
inputs, outputs, limit behavior, authorization behavior, and deterministic
ordering. Extensions that introduce arbitrary predicates, recursive rule
evaluation, joins over arbitrary event fields, or a general-purpose query
language MUST also define hard evaluation budgets and truncation behavior, since
those features carry database-style recursive query execution risks.

Computed queries only walk events which belong to the requested room and are
visible to the requester. Hidden history-visibility branches are pruned, not
replaced with opaque markers. If pruning affects the answer, the server sets
`limited` to `true`.

If more than one pair is supplied, the server computes each requested graph fact
for each pair independently. The `computed` object maps each requested compute
name to a list of results aligned with `compute_event_pairs`. If either event in
a pair is unknown, wrong-room, or not visible to the requester, the result for
that pair is `null` and `limited` is set to `true`.

These results are hints. They MUST NOT be used as proof that two branches are
authentically related without fetching and verifying the relevant events, unless
the room version provides Merkleized topology proofs for the path.

### Limits

Responding servers MUST enforce local limits regardless of what the requester
asks for. The effective limit is the lower of the requester-provided limit and
the server's configured local limit. If the requester omits an optional limit,
the server's configured local default applies.

At minimum, implementations MUST enforce these limits:

- maximum recursion depth;
- maximum returned event records;
- maximum distinct events visited while serving raw or computed graph queries;
- maximum number of computed graph query pairs;
- maximum database reads or equivalent storage operations per request;
- maximum number of start events;
- maximum response body size;
- maximum processing time;
- request rate per origin server.

The following request limits are optional. If present, they MUST be positive
integers:

- `max_depth`;
- `max_event_records`;
- `max_nodes_visited`;
- `max_compute_event_pairs`.

Omitting a limit uses the server's configured default, which may be lower than
its configured maximum. There is no request syntax for unlimited traversal;
negative values such as `-1` are invalid.

If a request limit is `0`, negative, or not an integer, the server MUST reject
the request with `M_INVALID_PARAM`. A request limit larger than the server's
configured maximum is not an error: consistent with the effective-limit rule
above, it is clamped to that maximum. Clamping by itself does not set `limited`;
`limited` is only set if the effective limit actually truncates the response.

If the number of `start_event_ids` entries exceeds the responding server's
effective maximum start-event count, the server MUST reject the request with
`M_INVALID_PARAM` before performing any event lookup, authorization check, or
graph traversal. This rejection does not produce a partial response and
therefore has no `limited` flag.

If the number of `compute_event_pairs` entries exceeds the effective
`max_compute_event_pairs` limit, the server MUST reject the request with
`M_INVALID_PARAM` before performing any event lookup, authorization check, or
graph traversal. This rejection does not produce a partial response and
therefore has no `limited` flag.

Implementations SHOULD use conservative defaults no higher than:

- `max_depth`: 500;
- `max_event_records`: 1000;
- `max_nodes_visited`: 5000;
- `max_compute_event_pairs`: 20;
- maximum start events: 20;
- maximum response body size: 1 MiB;
- maximum processing time: 3 seconds.

Implementations MAY use lower local defaults or absolute maxima. If a response
is truncated because of an effective limit, the server sets `limited` to `true`.

### Authorization

The responding server MUST only return sparse metadata which the requesting
server is allowed to learn over federation. This endpoint should not bypass
normal room access checks, membership checks, or history visibility policy.

The `room_id` is part of the query boundary. The responding server MUST validate
that each `start_event_ids` entry is a well-formed event ID before processing
the request. Malformed event IDs cause the request to fail with
`M_INVALID_PARAM`.

For every start event and every event discovered during traversal, the
responding server MUST validate that the event belongs to the requested
`room_id` before returning metadata for it or following its edges. Unknown
events and wrong-room events are omitted from the response as event records. If
`edge_errors` was requested, the server MAY label a known wrong-room edge target
as `wrong_room` on the source event, subject to the disclosure restriction in
the traversal section, but MUST NOT follow that edge or return metadata from the
wrong-room event. If any requested or discovered event is omitted for being
unknown, wrong-room, or not visible to the requester, the response MUST set
`limited` to `true`.

The responding server MUST NOT return event metadata if it would not be allowed
to serve the corresponding full event to the requester.

This means the answer can differ by room and event. A joined server can normally
query visible history for the room. An invited server should only receive
metadata that would already be visible through invite-stripped state or other
invite-legal federation flows. A non-joined server should not get private room
metadata merely because it knows an event ID. For world-readable history, the
server may answer consistently with the room's history visibility rules, but
should still avoid disclosing fields beyond what the requester asked for.

Where the relevant historical state is known, visibility should be evaluated at
the event being queried, not only against current room state. If the responding
server cannot reconstruct the relevant historical state, it may fall back to
current room policy only when that fallback is at least as restrictive as the
known historical policy. Otherwise it should omit the event.

If the requester is not allowed to access the room at all, for example because
no user on the requesting server is joined or otherwise permitted by the room's
federation rules, the server MUST reject the request with `M_FORBIDDEN`. If the
requester is allowed to access the room but some branches, events, or fields are
not visible, the server omits those branches, events, or fields and sets
`limited` to `true`. Hidden branches are not replaced with opaque markers,
because such markers would still leak graph shape.

### Room versions

This endpoint applies to room versions 3 and later in a hint-only capacity.

Older room versions (1 and 2) use server-assigned event IDs and include hashes
in `prev_events` / `auth_events` entries rather than using bare event IDs.
Servers MUST reject requests for older room versions with
`M_UNSUPPORTED_ROOM_VERSION` to avoid version-specific response shapes and lossy
hash stripping.

The metadata returned by this endpoint for current room versions is strictly a
**hint**. A server must still fetch the full event payload to verify the claimed
topology against the event hash. Cryptographic proofs of topology without
fetching the payload require a future room version that explicitly opts into
split canonicalization.

## Split canonicalization and Merkleized metadata (opt-in sketch)

To make selected event metadata independently verifiable, this MSC sketches a
split canonicalization design for future room versions to opt into.

A compatible future room version modifies event hashing to generate an
`event_root` from isolated metadata leaves:

- `prev_events_hash`: canonical hash of the event's `prev_events`;
- `auth_events_hash`: canonical hash of the event's `auth_events`;
- `event_header_root`: Merkle root over routing and authorship fields:
  `room_id`, `sender`, `type`, `state_key`, `redacts`, `depth`, and
  `origin_server_ts`;
- `content_hash`: canonical hash of the remaining event body after the topology
  and header components above are separated out. This is distinct from the
  legacy event `hashes` field unless a future room-version MSC explicitly maps
  them together;
- `other_signed_fields_hash`: canonical hash of every remaining signed event
  field which is not included in `prev_events_hash`, `auth_events_hash`,
  `event_header_root`, or `content_hash`;
- `event_root`: the root hash committing to the above components.

The future room version MUST define this partition so every signed,
identity-relevant event field is committed to exactly once. Two events which
differ in any signed field that contributes to event identity, including
`redacts`, MUST NOT derive the same `event_root` or event ID.

The hash algorithm is `SHA3-256`. Each hash input is domain-separated:

```text
leaf_hash =
  SHA3-256("msc4510:leaf:v1" || field_name || "\x00" || canonical_value)

inner_hash =
  SHA3-256("msc4510:node:v1" || left_hash || right_hash)

event_root =
  SHA3-256("msc4510:root:v1" || prev_events_hash || auth_events_hash ||
           event_header_root || content_hash || other_signed_fields_hash)
```

All concatenations above are byte concatenations: domain-separation strings and
`field_name` are UTF-8 bytes; `\x00` is a single `0x00` byte; `canonical_value`
is the UTF-8 encoding of the canonical JSON value; and
`left_hash`/`right_hash`/component hashes are the raw 32-byte hash outputs.

The top-level component hashes (`prev_events_hash`, `auth_events_hash`,
`content_hash`, and `other_signed_fields_hash`) are computed with the leaf-hash
construction above, using the field names `prev_events`, `auth_events`,
`content`, and `other_signed_fields` respectively.

The domain-separation strings use the stable MSC identifier `msc4510` and are
part of the event ID derivation. Implementations MUST NOT use the unstable
endpoint namespace or an implementation-local identifier for these domain
separators, because changing the identifier changes the derived `event_root` and
event ID.

### Header tree construction

The `event_header_root` is constructed as a binary Merkle tree. Header leaves
are ordered bytewise by field name. Missing optional fields use the canonical
JSON value `null`; present fields use their standard Matrix canonical JSON
encoding.

Because the number of header leaves is not guaranteed to be a power of two,
implementations MUST construct `event_header_root` using the Merkle tree
algorithm defined in
[RFC 6962, Section 2.1](https://datatracker.ietf.org/doc/html/rfc6962#section-2.1),
substituting the domain-separated leaf and inner hash constructions defined
above for the RFC's `0x00`- and `0x01`-prefixed hashes. Only the tree shape (the
largest-power-of-two split rule and its recursion) is taken from RFC 6962; no
padding leaves are used.

<!-- RFC 6962 tree shape: dyadic interval decomp over ordered leaves. -->

### Event IDs and signatures

The event ID is derived directly from the root:
`"$" || unpadded_base64url(event_root)`.

The origin server's Ed25519 signature covers the canonical signed envelope
containing this root:

```json
{
  "room_id": "!room:example.org",
  "room_version": "<room_version>",
  "event_root": "unpadded_base64url_sha3_256_hash"
}
```

For room versions adopting this format, a future room-version MSC MUST specify
how the root signature interacts with, or replaces, existing event authorization
and verification rules. This keeps the proposal focused on the topology query
API and defers signature migration mechanics to the room-version proposal.

### Cryptographic proof responses

When `proof` is requested in `fields` and the queried room version supports
split canonicalization, a server MAY include proof material for provable
requested fields inside a `proof` object. A room version adopting this format
also extends the queryable `fields` set with the header leaves not exposed in
hint-only mode (`sender`, `type`, `state_key`, `redacts`), since a field must be
returnable to be provable.

The `proof` object schema explicitly maps the proven fields to their Merkle
paths, provides any required top-level component hashes needed to reconstruct
`event_root`, and includes the origin signature:

```json
"proof": {
    "leaf_paths": {
        "prev_events": [],
        "origin_server_ts": [
            { "side": "right", "hash": "base64url_sha3_256_hash" },
            { "side": "left", "hash": "base64url_sha3_256_hash" }
        ]
    },
    "top_level_hashes": {
        "auth_events_hash": "base64url_sha3_256_hash",
        "content_hash": "base64url_sha3_256_hash",
        "other_signed_fields_hash": "base64url_sha3_256_hash"
    },
    "signatures": {
        "example.org": {
            "ed25519:key": "signature_base64"
        }
    }
}
```

To verify the authenticity of a field all the way to the root, the requester
performs the following steps:

1. Canonicalize the returned field and compute its domain-separated leaf hash.
2. Apply each step in `leaf_paths`, computing the parent inner hash using the
   provided left or right sibling, to reconstruct `event_header_root` or the
   relevant top-level component hash. For top-level components (`prev_events`,
   `auth_events`, content, and other signed fields), the path list is empty and
   the leaf hash is used directly.
3. Combine the reconstructed component with the remaining hashes in
   `top_level_hashes` to compute the master `event_root`. `top_level_hashes`
   MUST contain every component hash not reconstructed from a proof in the same
   response.
4. Verify that the event ID matches `"$" || unpadded_base64url(event_root)`.
5. Verify the origin server's Ed25519 signature over the canonical signed
   envelope containing the `event_root`.

If a required hash is missing or any hash check fails, verification fails. By
chaining hashes upward, the server only needs to send missing neighbor hashes in
the proof, and the verifier recomputes the root locally.

Redaction semantics are deferred to the future room-version MSC that adopts
split canonicalization. That room version MUST define whether `content_hash`
commits to the full unredacted content, the redacted event representation, or
separate full and redacted content commitments. This topology proof format only
proves the selected metadata leaves and their inclusion in `event_root`; it does
not by itself authorize disclosure of redacted content or change Matrix
redaction rules.

## Future extensions

Future room versions may extend the proof fields or add more independently
provable metadata fields.

## Performance characteristics and benchmarking

Exact speedups depend on implementation, database layout, cache state, and
workload, but the theoretical bandwidth bounds and storage overhead can be
quantified.

### Asymptotic bandwidth analysis

For a traversal visiting `N` events:

- full-event retrieval transfers `O(N * S_event)` bytes;
- sparse topology query transfers `O(N * S_meta + P)` bytes, where `S_meta` is
  the size of the requested metadata fieldset and `P` is the size of optional
  proof material.

When proofs are not requested, the bandwidth reduction approaches
`1 - (S_meta / S_event)`. As an illustrative range, if a full event is 1 to 5
KiB and the requested topology metadata is 80 to 300 bytes per event, the
bandwidth reduction is roughly 70% to 98%. Implementations MUST NOT rely on
these illustrative percentages as protocol guarantees.

### Storage overhead

The split-canonicalization sketch introduces storage overhead if a server stores
the top-level hashes `prev_events_hash`, `auth_events_hash`,
`event_header_root`, `content_hash`, `other_signed_fields_hash`, and
`event_root`.

Using SHA3-256, each hash is 32 bytes, so storing these six hashes adds 192
bytes of raw hash material per event before database row, index, and encoding
overhead. For a 2 KiB event, this raw hash material is approximately 9.4% of the
event size; for a 5 KiB event, it is approximately 3.8%. Implementations can
recompute proof paths on demand; caching intermediate Merkle nodes or proof
indexes is optional and would increase this overhead.

### Empirical benchmarking

Implementations SHOULD benchmark this endpoint against their specific event
store and federation workload. Recommended metrics include total bytes
transferred, number of round trips, database rows read, full event JSON decode
count, CPU time, active RAM usage, wall-clock latency, and success rate for gap
repair path selection.

## Relationship to other proposals

This proposal is a lower-level, targeted, pull-based metadata primitive. A
set-reconciliation or gossip protocol could use it as a lookup step after
detecting divergence.

This proposal does not define push gossip, session state, set digests, or bulk
event repair. If another reconciliation proposal defines those higher-level
flows, this endpoint should compose underneath it rather than compete with its
wire format.

This proposal is also complementary to
[MSC4242: State DAGs](https://github.com/matrix-org/matrix-spec-proposals/pull/4242).
State DAGs split state progression from the message event DAG; this endpoint
provides a sparse query primitive that can compose with state-DAG edges. A
state-DAG extension of this query shape can add efficient filters by event
`type` and `state_key`, allowing a server to ask targeted questions such as
"which membership-state branch contains this user?" without fetching full state
events or scanning unrelated state keys.

## Security considerations

The major risks are:

- recursive queries hanging or entering unbounded traversals;
- large repeated queries increasing bandwidth or processing load;
- metadata leaks about rooms, participants, or historical graph shape;
- buggy or misrepresented topology output causing incorrect repair attempts.

These are mitigated by hard local limits, normal federation authorization,
rate-limiting, and treating responses as hints unless the room version provides
verifiable Merkle topology proofs. A server should still fetch and verify full
events before accepting them, repairing state, or considering a gap resolved.

### Bandwidth consumption

This MSC does expose a bandwidth-consumption surface for servers which implement
the endpoint. Authenticated federation peers could issue repeated large bounded
topology queries, so implementations should apply the same conservative
response-size and rate-limit controls described above.

This is not unique to this endpoint: `/event`, `/backfill`,
`/get_missing_events`, and `/state_ids` already expose heavier bandwidth
surfaces.

The intended use case here is real-world gap repair: inbound transactions,
backfill attempts, and auth-chain recovery often need to know a few edges or
origins before deciding which full events to fetch. Returning compact metadata
can reduce total bandwidth compared to fetching full PDUs or state sets blindly.
This can also support operator-initiated repair tooling.

Servers should still treat this as an optional endpoint with hard response-size
limits, per-origin rate limits, and conservative defaults. If a deployment does
not see federation repair value from this query shape, it can decline to expose
the endpoint.

### Hint validation and reputation

Because current room versions cannot independently verify topological hints
without fetching the full event, requesting servers are exposed to potential
misdirection from responding nodes. To mitigate this without strictly
standardizing a global reputation system, implementations should rely on local
heuristics.

Requesting servers SHOULD track topology hints they later verify against full
events. If a responding server repeatedly returns metadata contradicted by
verified event payloads, the requester MAY deprioritize that server for future
topology queries, apply local rate limits, or ignore its topology hints for a
limited period.

Implementations should decay these penalties over time to prevent transient
corruption or partial-state desyncs from permanently poisoning a peer. Such
reputation data MUST NOT cause the requester to reject a valid event which
passes normal Matrix authorization and event verification.

## References

- [Matrix Server-Server API](https://spec.matrix.org/latest/server-server-api/)
  for `/event`, `/backfill`, `/get_missing_events`, `/state_ids`, federation
  authorization, and the existing PDU flow this proposal tries to avoid
  overusing.
- [Matrix room version 12](https://spec.matrix.org/latest/rooms/v12/) for the
  current default room-version baseline, including event format behavior
  inherited from room version 11, event IDs inherited from room versions 3 and
  later, and v12-specific room ID and state-resolution changes.
- [MSC4186: Simplified Sliding Sync](4186-simplified-sliding-sync.md), as prior
  art for selective, client-chosen field/query shapes in Matrix.
- [MSC2836: Twitter-style Threading](https://github.com/matrix-org/matrix-spec-proposals/pull/2836),
  as prior art for bounded traversal of Matrix event relationships over
  federation.
- [MSC2716: Incrementally Importing History](https://github.com/matrix-org/matrix-spec-proposals/pull/2716),
  as related background for historical DAG gaps and inserted history chunks.
- [MSC4242: State DAGs](https://github.com/matrix-org/matrix-spec-proposals/pull/4242),
  as related work for representing state progression separately from the message
  event DAG.
- [Polkadot Fellowship RFC-0078: Merkleized Metadata][polkadot-rfc-0078] as
  prior art for committing to metadata with a root hash while revealing only the
  pieces needed by the verifier.
- [Crosby and Wallach, Efficient Data Structures for Tamper-Evident
  Logging][crosby-wallach] as foundational work on the security model and proof
  semantics for tamper-evident logs, including logarithmic membership and
  consistency proofs and authenticated query results over logged event
  attributes.
- [RFC 6962, Section 2.1](https://datatracker.ietf.org/doc/html/rfc6962#section-2.1)
  for the Merkle tree construction used by `event_header_root`.

[polkadot-rfc-0078]:
  https://polkadot-fellows.github.io/RFCs/approved/0078-merkleized-metadata.html
[crosby-wallach]:
  https://static.usenix.org/event/sec09/tech/full_papers/crosby.pdf
