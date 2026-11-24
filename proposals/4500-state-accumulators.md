# MSC4500: State accumulator endpoint and transaction digests

Matrix servers replicate a room as a DAG of events and rely on state resolution
to eventually converge on a shared state. When servers diverge, the result can
be a serious nuisance. Matrix lacks an out-of-band or real-time mechanism for
state verification or re-alignment; servers often only learn of
de-synchronization once they disagree on a much later authorization failure
(e.g., another user's join is incorrectly rejected).

I present an "early-warning system" which rapidly confirms incremental state
consensus, or signals that divergence exists, so servers know they share the
exact same view of a room at a given point in the DAG.

This proposal does not impose any verification requirements on PDU handling. It
seeks to act as a secondary state convergence mechanism, while simultaneously
**relegating state group transitions** and naive iterative BFS implementations
to storage/retrieval with a cheap, bitwise, commutative, subtractable (supports
element removal), collision-resistant 2048-byte `LtHash16` accumulator function
[^3], [^6]. Similar additive lattice accumulators are increasingly used in
production blockchain architectures to compute real-time, incremental
cryptographic state commitments under high transactional volume [^5], [^6].

Avoiding diff chain reconstruction for point lookups will reduce Synapse's
electricity consumption across a wide range of API state endpoints.

The accumulator under question may be called 'homomorphic' and solves the
following hashing problem: "Given the hash of an input, along with a small
update to the input, how can we compute the hash of the new input with its
update applied, without having to recompute the entire hash from scratch?"

Should this proposal be accepted, for the sake of federation clarity homeservers
must embed a canonical `BLAKE2b-256` digest (of their 2048-byte room state
accumulator) in the `PUT /_matrix/federation/v1/send/{txnId}` transaction body.

## Proposal

Rather than attaching hashes to individual events (which are routinely stripped,
rewritten, or relayed by intermediate servers), this proposal places the hashes
in the body of the federation transaction.

When a homeserver sends or relays a federated transaction, it calculates the sum
accumulation of the room's state exactly at the DAG tip of each included PDU.

It then collapses each PDU's vectorized state into a standard 32-byte digest and
includes them in the transaction payload as a dictionary.

### Algorithm specification

To guarantee interoperability and collision resistance, the algorithm MUST be
implemented as follows:

1. **Input encoding.** Each entry in the room's resolved state map is serialized
   as: `len(type) || type || len(state_key) || state_key || event_id` where each
   `len()` is an unsigned 16-bit little-endian byte count of the UTF-8 field
   that follows. The `event_id` is appended raw with no length prefix (it is the
   final field, so the two prefixes already make decoding unambiguous). Length
   prefixes make the encoding injective for arbitrary field contents — including
   embedded null bytes — with no rejection or escaping rules needed. Two bytes
   per length is sufficient since no field in a valid PDU can exceed the global
   65 KB event size limit.
2. **Input expansion.** The encoded element, prefixed with the domain separation
   tag `msc4500_lthash16\x00`, is expanded to exactly 2048 bytes using the
   `SHAKE256` extendable-output function (XOF) from NIST FIPS 202:
   `expansion = SHAKE256("msc4500_lthash16\x00" || element, 2048)`. A
   fixed-width hash cannot fill the lattice; this uniform XOF expansion is
   essential for identical lane distribution. `SHAKE256` is natively supported
   across virtually all cryptographic libraries without custom parameter block
   requirements.

3. **Accumulation.** The 2048-byte expansion is interpreted as 1024
   little-endian unsigned 16-bit lanes and combined into the local lattice with
   lane-wise wrapping addition.
4. **Removal and replacement.** Removing an element is lane-wise wrapping
   subtraction of its expansion. Replacing the event for a `(type, state_key)`
   pair is one subtraction (old element) followed by one addition (new element)
   — the `O(1)` update at the heart of this proposal.
5. **Initial state.** The accumulator of the empty state set is 2048 zero bytes.
6. **Collapse.** Compute the final 32-byte digest $D$ by hashing the final
   2048-byte sum lattice $S$ using `BLAKE2b-256`, hex-encoded at 64 characters:
   $$D = \text{BLAKE2b-256}(S)$$

**NOTE:** elements bind the `event_id` only, never event content. Redacting an
event therefore has no effect on the accumulator (having no effect on event ID).

**NOTE:** It is the caller's responsibility to ensure the input is really a set
[^3]. The digest allows deducting elements which were never added, and it allows
adding the same element twice (producing different digests). Due to the wrapping
math of the 16-bit lanes, adding the exact same element $2^{16}$ ($65,536$)
times will roll the accumulator's lanes back to zero, returning to the starting
digest. This degenerate state is materially unattainable when the input domain
is a resolved state map (a set whose elements all have a multiplicity of 1). The
inbound accumulator is strictly a one-way _comparative_ tool; homeserver
databases MUST remain responsible for _managing_ actual set element membership.

### Transaction payload

Servers implementing this MSC MUST embed a `state_hashes` dictionary at the root
of the `PUT /_matrix/federation/v1/send/{txnId}` request body. It maps the IDs
of the PDUs included in the transaction to their respective `before` and `after`
digests. The `state_hashes` values always represent the transaction sender's
local resolved state, not necessarily the origin server's (meaning relays
forward their own view).

Network overhead for duplicate digests (e.g. across multiple non-state PDUs in a
batch) is collapsed by standard federation HTTP compression (gzip/brotli).

When a PDU lists multiple `prev_events`, the `before` state is the output of
state resolution (v2) applied across the states at each of those events — i.e.
the same resolved state the server would use to authorize the PDU. The `after`
state is `before` with the PDU applied, if it is an accepted state event;
otherwise `after` equals `before`. If a server does not know about a PDU in the
given `prev_events`, they shall omit it entirely from the dictionary.

- `before`: The 32-byte digest of the room state evaluated exactly at the given
  PDU's `prev_events`, excluding and preceding the given event.
- `after`: The 32-byte digest of the room state after the current PDU is
  applied. (For non-state events, this will be identical to `before`).
- `n_before`: An unsigned integer representing the exact number of elements in
  the room's resolved state map at the `before` DAG point.
- `n_after`: An unsigned integer representing the exact number of elements in
  the room's resolved state map at the `after` DAG point (identical to
  `n_before` for non-state events).

```json
{
  "origin": "example.com",
  "pdus": [
    {
      "type": "m.room.message",
      "event_id": "$sample_pduid_abc123def456",
      "sender": "@alice:example.com",
      "content": {
        "body": "Hello world",
        "msgtype": "m.text"
      }
    }
  ],
  "state_hashes": {
    "$sample_pduid_abc123def456": {
      "before": "a85dfe1d480705482f37d582ffa27611117b577f8734532a5a6379bc666b2104",
      "after": "a85dfe1d480705482f37d582ffa27611117b577f8734532a5a6379bc666b2104",
      "n_before": 2,
      "n_after": 2
    }
  }
}
```

### Network efficiency

To avoid event bloat, the full `LtHash16` lattice state (2048 bytes) is **never
explicitly transmitted over transactions.**

Transmitting only the collapsed 32-byte digest keeps payload footprints small.
Adding both `before` and `after` digests plus both cardinality counts consumes
approximately 200 bytes of JSON overhead per PDU in the transaction.

### Receiver contract

Each server independently maintains its own `LtHash16` lattice in local storage.

When a server catches a `/send` transaction containing the `state_hashes`
payload, it collapses its own local lattice at that exact DAG point using fast
bitmap operations, hashing it down to a canonical 32-byte `BLAKE2b-256` digest.
If the local digest matches the incoming one, all systems are nominal.

If digests mismatch, servers SHOULD log an error or warning message of the state
split. The receiver can automatically trigger a background `/get_missing_events`
or perform a state bisection (see
[Reconciliation (bisecting forks)](#reconciliation-bisecting-forks)) with
authoritative servers, while replying to the sender with the mismatched digest
embedded in a `state_hash_mismatch` dictionary as part of the PDU's processing
result and the `200 OK` response. Unknown keys in per-PDU result objects are
silently ignored by existing implementations, so adding `state_hash_mismatch` is
backwards-compatible.

```json
{
  "pdus": {
    "$sample_pduid_abc123def456": {
      "state_hash_mismatch": {
        "expected_after": "b85dfe1d480705482f37d582ffa27611117b577f8734532a5a6379bc666b2104",
        "received_after": "a85dfe1d480705482f37d582ffa27611117b577f8734532a5a6379bc666b2104"
      }
    }
  }
}
```

Mismatch handling SHOULD be deduplicated per room (i.e. the first detection
triggers logging/bisection, but subsequent mismatching transactions within a
reasonable cooldown period are deprioritized to limit logger output and network
activity). Note that if a receiving server **rejects** an incoming state event
due to auth/power-level rules, their `after` hash will instantly (and correctly)
mismatch the sender's `after` hash. This mechanism instantly detects split-brain
authorization failures.

Homeservers operating under Partial State (MSC3706) MUST silently defer hash
validation for that room. They cannot compare state to emit warnings or trigger
bisection (until the room state is fully synchronized).

The emphasis here is on agility: if a receiver cannot validate the `before` and
`after` hashes readily (e.g., from an in-memory LRU cache or a point database
lookup), they MUST defer the verification pipeline.

A mismatched or deferred hash does not block the PDU; it is still processed
under standard rules. Whether homeservers implements an automated healing
pipeline or merely log the divergence for admin intervention is left as an
implementation detail.

### Endpoint definition

`GET /_matrix/federation/v1/state_accumulator/{roomId}?event_id={eventId}`

Returns the raw lattice for the room state immediately **after** `eventId` is
applied (the `after` accumulator of that PDU).

**Response (200):**

```json
{
  "event_id": "$sample_pduid_abc123def456",
  "algorithm": "lthash16",
  "lattice": "<base64url, unpadded, 2048 raw bytes>",
  "n_state_events": 2,
  "digest": "99d3ed0ae604d2fb5849f7280062e27ecea4425b64b25190e067e3d6a755680c"
}
```

The receiver MUST verify that `BLAKE2b-256(lattice)` equals `digest` before
using the lattice; a mismatch indicates the response is malformed or tampered
with, and MUST be discarded.

**Errors:** `404 M_NOT_FOUND` if the server does not hold resolved PDU state at
that event (unknown event, outlier, purged history, bug). `403 M_FORBIDDEN` if
the requesting server is not a participant in the room or is denied by
`m.room.server_acl` — identical semantics to other federation endpoints.

**Rate limiting:** Servers SHOULD rate-limit per peer per room. Bisection
requires `O(log ΔD)` sequential network calls, so a short burst allowance (e.g.
30 requests) with a sustained rate of ~1/second is a reasonable default. The
response is ~3 KB; amplification risk is negligible.

### Other affected endpoints

The introduction of a cryptographically verifiable state accumulator enables
several zero-cost optimizations across the existing Matrix Client-Server and
Server-Server APIs.

- **`GET /_matrix/federation/v1/state/{roomId}`**,
  **`GET /_matrix/federation/v1/state_ids/{roomId}`**, and
  **`/_matrix/client/v3/rooms/{roomId}/state`** Currently, homeservers must
  fully materialize the room state to serve these endpoints, which is an
  expensive $O(S)$ operation for large rooms. These endpoints become instantly
  cacheable via standard HTTP semantics. Servers SHOULD include the digest as an
  `ETag` header on `200 OK` responses so standard conditional-request semantics
  hold end-to-end. Requesters SHOULD include the 32-byte accumulator digest in
  the `If-None-Match` header. The receiving server simply compares this against
  its own local LRU cache of the requested event's digest. If they match, the
  server immediately returns `304 Not Modified`, bypassing the legacy database
  traversal and JSON serialization of tens of thousands of state events.

## Reconciliation (bisecting forks)

When the 32-byte digest triggers a mismatch alarm, the receiving server knows at
least one party is desynchronized. The receiver performs homomorphic subtraction
against the sender's full accumulator lattice.

The delta lattice tells you _that_ you've diverged and lets you **bisect** to
_where_. Because both servers can produce digests at historical DAG points, the
receiver can query accumulators at $O(\log \Delta D)$ depth (topological
bisection—similar to `git bisect`—over the known `prev_events` graph or auth
chain) to find the earliest event where the digests diverged. For historical
PDUs where a server has no stored accumulator (and deems retroactive computation
prohibitive), it responds `404 M_NOT_FOUND`; the bisecting requester then treats
the oldest event for which both sides _can_ produce accumulators as a lower
bound on the divergence point and proceeds from there.

It is important to note that the delta lattice cannot name events you have never
seen—a lattice sum isn't invertible to its summands (the property that makes it
collision-resistant). Once the exact divergence point is isolated via bisection,
enumeration and healing are delegated to MSCXXXX [Gossip-based federation room
reconciliation] and its `/room_diff` and `/room_events` endpoints.

Furthermore, this MSC cannot detect omissions in messages, redactions, or other
non-state-altering events. For this capability, it fully defers to MSCXXXX.

## Synergy with MSCXXXX (event set reconciliation)

This proposal and MSCXXXX (`room_digest` / `room_diff`) solve fundamentally
different sets. MSC4500's accumulator covers the room's _current state set_ at
arbitrary DAG positions. MSCXXXX's bloom digest and LCA/RMQ fall-back cover the
_event set_ (full PDU timeline).

Because state divergence implies event-set divergence (with the converse _often_
also holding true), the two proposals nicely complement each other:

1. **Detect (MSC4500, passive, free):** Every `/send` carries before/after
   digests. Active rooms get continuous state-consistency checks with zero extra
   round trips.
2. **Bisect (MSC4500, active):** On mismatch, optional bisection via the
   `/state_accumulator` endpoint alerts to the divergence point.
3. **Reconcile (MSCXXXX):** `room_diff` (with a `scope: "state"` parameter)
   fetches omissions, auth chains included, triggering state re-resolution.

Because MSC4500 gives active rooms free passive detection, MSCXXXX's periodic
polling can back off significantly for rooms with recent inbound transactions.

## Implementation notes

The natural storage model is one 2048-byte lattice per state group. Creating a
new state group from a delta is one subtraction plus one addition against the
parent's lattice — `O(1)`, no chain walk and no full state materialization.
Historical `/state_accumulator` queries then reduce to the existing event (state
group lookup plus a single row or cache read).

Servers without persisted lattices can compute them on demand per-event during
naive delta chain traversals or iterative BFS sweeps (accumulating the already
materialized state in CPU cache and persisting the accumulator, thereby
obviating any need for traversals of that delta chain during future point
lookups or state group transitions).

### State identifiers and local storage optimizations

While this proposal primarily addresses federation, the adoption of a
homomorphic sum accumulator introduces a paradigm shift for local homeserver
database architectures, shifting state management from being _path-dependent_ to
_path-independent_. This database paradigm mirrors modern high-stakes ledger
optimizations (such as Solana's "Accounts Lattice Hash" system [^5]) that
compute rolling, $O(1)$ state-root identities directly via vector addition to
entirely bypass quadratic or linearithmic sorting and hashing bottlenecks.

Currently, homeservers are forced into a trade-off between read-time CPU
consumption and write-time I/O amplification:

- Homeservers like **Synapse** track room states using locally-incrementing IDs
  ("state groups"). Determining if two state groups contain identical state
  requires cache-heavy dictionary comparisons or expensive backward graph
  traversals. Synapse currently relies on complex background workers to
  eventually deduplicate converging state groups.
- Rust-based implementations like **Conduit-based derivatives** optimize
  read-time reconstruction by hashing sorted lists of state events (e.g.,
  `ShortStateHash`), but incur heavy write-time amplification. Because standard
  hashes (like SHA-256) are not homomorphic, generating a hash requires
  materializing, re-sorting, and re-hashing the entire state vector upon every
  state change.

With an `LtHash16` accumulator, the 32-byte collapsed digest acts as a
deterministic, cryptographically-secure natural fingerprint for the resolved
state dictionary. This solves multiple architectural bottlenecks:

1. **$O(1)$ State progression (write-path efficiency gain):** To compute the
   state fingerprint for a newly arriving event, the homeserver no longer needs
   to walk a delta chain or re-hash a materialized, canonically sorted JSON
   dictionary. The server simply loads the parent's cached 2048-byte lattice,
   homomorphically subtracts the replaced event (if any), adds the new event,
   and collapses it to the new 32-byte digest. Generating the deterministic
   identity of a new state group in a massive room is a microsecond operation
   strictly independent of the room's total size or the fork's depth.

2. **Maintaining commutativity (fast deduplication):** Because Matrix history is
   a Directed Acyclic Graph (DAG), concurrent branches frequently apply
   independent state changes in different orders (e.g., Server A sees event $X$
   then $Y$; Server B sees $Y$ then $X$). Because the accumulator relies on
   commutative modulo addition, `Base + X + Y` produces the exact same lattice
   and digest as `Base + Y + X`. Homeservers can instantly deduplicate
   convergent DAG branches into a single shared state group ID upon ingestion
   (e.g., via a relational `UNIQUE` index or a key-value point lookup map),
   without ever expanding or comparing dictionaries.

3. **Fast-path state resolution:** During state resolution v2/v2.1, an expensive
   early step is determining if diverging DAG tips actually contain different
   states before building a conflict set. With the accumulator, this
   historically expensive code path is short-circuited by a single 32-byte
   memory comparison. If the diverging branches have the same digests, the
   server knows with cryptographic assurance that there is no conflict set, and
   can safely bypass the state resolution algorithm.

While relational delta chains (pointers to parent state groups) are still
required to materialize state into memory for client APIs and to isolate actual
conflict sets during resolution (since a homomorphic hash cannot be inverted to
name its constituent events), the accumulator relegates these structures purely
to storage compression and certain cases of read-path retrievals. The
traditionally bottlenecked write-path and the fast-path equality checks are
entirely decoupled from delta chains or full state materialization.

## Potential issues

### Direct-hop survival (ease of audit)

Because the hashes are attached to the transaction body rather than the
individual PDUs, they only survive the direct origin-to-first-hop transmission.
If an event is relayed, or fetched later via `/backfill`, the hashes are
missing.

However, this is an acceptable constraint. The direct `/send` hop is precisely
where real-time early-warning detection is most valuable to prevent split-brain.
The `unsigned` dictionary on individual PDUs suffers from similar survival
issues, as it is routinely stripped or rewritten by intermediate servers, making
it prone to replication drift and structural or semantic ambiguity.

### False alarms (federation signal noise and DoS vectors)

If a malicious, misconfigured, or malfunctioning server transmits mismatched
digests in a transaction, it could trigger state resync loops for the receiver.

**Mitigations:**

1. **Rate-limiting:** Receiving servers implementing automated remediation
   methods SHOULD rate-limit out-of-band state sync requests triggered by
   mismatching hints. Repetitive warning logs are unnecessary and should be
   subject to a cool-down period.

2. **Reputation:** Servers implementing Bandit-based peer scoring on manually
   triggered or heavily federated endpoints SHOULD factor state accuracy into
   their weighting. If a peer consistently transmits mismatched digests that do
   not reflect the actual resolved state or differ too wildly from the perceived
   majority or authoritative ground truth, the receiver should temporarily
   decrement that peer's reputation score and the worthiness of their hints.

## Alternatives

### Hashes in the signed PDU

The primary alternative is placing the state hash directly into the signed
payload of the event, enforcing it as a protocol-level requirement.

**Disadvantages:**

- **PDU bloat:** PDUs already suffer from excessive meta-data.
- **Leads to confusion:** Matrix allows for servers being slightly out of sync.
  Implying consensus on every event leads to ambiguity (situations even arise
  where administrative power events can rewrite formerly correct state).
- **Compatibility:** Modifying the signed PDU alters the event's reference hash
  (unless the definition of "canonical event JSON" is further complicated). This
  requires a global room version upgrade and excludes older homeservers. It is
  possible this approach will be interleaved with MSC4242 (Stage DAGs), which
  _does_ make intentional PDU format changes intended for a new room version.

A transaction-level approach achieves similar diagnostic goal without friction.

### Hashes in the `unsigned` dictionary

**Advantages:**

- **Accessibility and persistence:** Generally, `unsigned` is more durable. This
  allows some degree of trustworthy relaying of the origin's viewpoint.

**Disadvantages:**

- **Tampering:** The `unsigned` dictionary is not covered by any signature,
  allowing silent modification in transit.
- **Survival:** Like transaction-level hashes, `unsigned` data is frequently
  stripped by relays or backfill endpoints, offering no structural advantage
  over transaction-level hashes.

By placing these digests in the `PUT /send` request body, they are automatically
protected by the sending server's `X-Matrix` authorization headers, providing
free tamper-resistance on the primary hop. Consequently, relaying servers assert
their own perceived state digest rather than blindly forwarding the origin
server's viewpoint — limiting the propagation of unverified hints and offering
broader auditability of major servers that frequently act as relays.

## Security considerations

Homeservers MUST NEVER use a _remote_ accumulator digest (received from a peer
via `/send` or `/state_accumulator`) as a source of truth to construct, modify,
or authorize state. Local state resolution MUST proceed normally as the sole
authoritative driver of state convergence. Locally-computed lattices, derived
from the server's timeline and resolved state, _are_ safe for any internal
optimizations and representations described in this proposal (state group
identity, fast-path deduplication, short-circuiting state resolution).

The hashes are purely diagnostic tools and performance boosters. Servers must
still rely exclusively on their internal state to judge soft-failures. Servers
should only implement changes in federation prioritization at their discretion,
since needless complexity can introduce unintended side-effects and the benefits
of reconciliation remain, at the time of writing, investigative or speculative.

**State-isolation assurance:** Even a successful collision attack cannot corrupt
room state. Because remote digests are never used to construct, modify, or
authorize local state maps, the worst outcome of a forged digest is a missed
mismatch alarm — the adversary fools the receiver into believing sync is nominal
when it is not. No state is injected, no auth decisions are affected, and the
receiver's local database remains unaffected.

**"Honest hash" bypass:** It is important to contextualize the threat model. If
a malicious server wishes to hide a split-brain partition, it does not need to
find a lattice collision. Because Matrix room events are public, a malicious
server can simply compute the correct `LtHash` of the _honest_ room state and
transmit that correct hash in their federation payloads while secretly keeping a
diverged database. `LtHash` must therefore be understood as a highly efficient
fault _detection_ mechanism for honest-but-buggy servers and natural network
partitions, _not_ an authoritative proof of a peer's internal room state.

**Parameter security:** The lattice parameters ($L = 1024$ lanes, $q = 2^{16}$)
are the instantiation analyzed by Lewi et al. [^2], with an estimated security
level in excess of 200 bits against known lattice-reduction [^4] and generalized
birthday (k-list) attacks [^1]. This analysis requires that no element appear
with multiplicity $\ge 2^{16}$ in the accumulated multiset. MSC4500 satisfies
this structurally: the input is a resolved state _map_, which holds exactly one
`event_id` per `(type, state_key)` key — every element has multiplicity 1,
regardless of total room size. Total state cardinality ($N$) is _not_ bounded by
$2^{16}$; massive rooms are fully supported.

The `n_before` and `n_after` payload fields are diagnostic only — they help a
receiver gauge the magnitude of a divergence when choosing between bisection,
full resync, and inaction. They MUST NOT be used as a validation shortcut:
digest comparison is the sole equality check.

## Test vectors

To assist implementers, the following test vectors are provided. They are
generated using the `SHAKE256` element expansion (prefixed with the domain
separation tag `msc4500_lthash16\x00`), 16-bit little-endian wrapping lane
addition/subtraction, and standard `BLAKE2b-256` collapse digest.

### Empty state

The starting lattice $S_0$ is 2048 bytes of all zeros.

- Lattice $S_0$ prefix (first 16 bytes): `00000000000000000000000000000000`
- Collapse digest:
  `200823e5158b3774c11b5c61850ada762f8264144a9bebec3ebac5a2adde67b8`

### Scenario 1: one element (addition)

Add event `m.room.member` with state key `@alice:example.com` and event ID
`$event_1`.

- Raw encoded element:
  `0d006d2e726f6f6d2e6d656d626572120040616c6963653a6578616d706c652e636f6d246576656e745f31`
- Element 1 expansion prefix (first 16 bytes of
  $SHAKE256(\text{tag} \parallel \text{el}_1)$):
  `d72df88a72ff61da6b2287649ff6001c`
- Lattice $S_1$ prefix (first 16 bytes): `d72df88a72ff61da6b2287649ff6001c`
- Collapse digest:
  `3bcd9f595b4b5c7095b300ec5cf37ff1ff3f79400643f7ba66171e150ddb6606`

### Scenario 2: add-then-remove (element removal)

Subtracting the expanded element for `$event_1` from lattice $S_1$ returns the
accumulator to the empty state.

- Lattice $S_{\text{back}}$ prefix (first 16 bytes):
  `00000000000000000000000000000000`
- Collapse digest:
  `200823e5158b3774c11b5c61850ada762f8264144a9bebec3ebac5a2adde67b8`

### Scenario 3: two elements

Starting from $S_1$, add event `m.room.name` with empty state key `""` and event
ID `$event_2`.

- Raw encoded element: `0b006d2e726f6f6d2e6e616d650000246576656e745f32`
- Element 2 expansion prefix (first 16 bytes of
  $SHAKE256(\text{tag} \parallel \text{el}_2)$):
  `8c9d4997da61e28d7e6b83255fff064e`
- Lattice $S_2$ prefix (first 16 bytes): `63cb41224c614368e98d0a8afef5066a`
- Collapse digest:
  `99d3ed0ae604d2fb5849f7280062e27ecea4425b64b25190e067e3d6a755680c`

### Scenario 4: instant replacement

Starting from $S_2$, replace the membership event for `@alice:example.com` with
event ID `$event_3`. This is performed by subtracting the expansion for
`$event_1` and adding the expansion for `$event_3`.

- Raw encoded element for `$event_3`:
  `0d006d2e726f6f6d2e6d656d626572120040616c6963653a6578616d706c652e636f6d246576656e745f33`
- Element 3 expansion prefix (first 16 bytes of
  $SHAKE256(\text{tag} \parallel \text{el}_3)$):
  `9dd1af20e6ee125f8e98969793b8c650`
- Lattice $S_3$ prefix (first 16 bytes): `296ff8b7c050f4ec0c0419bdf2b7cc9e`
- Collapse digest:
  `8b611750bb056a38f9e3f9fcc74ae1f0771f12ade0daecc6963e302d15f8e67f`

## Unstable prefix

For experimental implementations, the features should be referred to using the
following unstable identifiers:

- The transaction payload key: `tk.nutra.msc4500.state_hashes`
- The reconciliation endpoint:
  `GET /_matrix/federation/unstable/tk.nutra.msc4500/state_accumulator/{room_id}`

## Backwards compatibility

This proposal is fully backwards-compatible:

- Unknown transaction keys (`state_hashes`) are silently ignored by existing
  servers, per current federation behavior.
- The unstable reconciliation endpoint returns a `404 Not Found` on
  non-implementing servers, which callers treat as an "unsupported" signal.
- No room version consensus rules are modified.

## Dependencies

This proposal currently has no known dependencies.

## Open questions

- Impact on or relevance to partial joins (MSC3902)?

## References

[^1]:
    **Bellare, M., & Micciancio, D. (1997).** _A New Paradigm for Collision-free
    Hashing: Incrementality at Reduced Cost._ Advances in Cryptology — EUROCRYPT
    '97. Lecture Notes in Computer Science, vol 1233. Springer, Berlin,
    Heidelberg. Available at: <https://doi.org/10.1007/3-540-69053-0_13>

[^2]:
    **Lewi, K., Kim, W., Maykov, I., & Weis, S. (2019).** _Securing Update
    Propagation with Homomorphic Hashing._ IACR Cryptology ePrint Archive,
    2019/227. Available at: <https://eprint.iacr.org/2019/227>

[^3]:
    **Digital Asset (Canton).** _LtHash16 Scala Documentation._ Available at:
    <https://docs.digitalasset.com/operate/3.5/scaladoc/com/digitalasset/canton/crypto/LtHash16.html>

[^4]:
    **Micciancio, D. (2002).** _Generalized Compact Knapsacks, Cyclic Lattices,
    and Efficient One-Way Functions._ Proceedings of the 43rd Annual IEEE
    Symposium on Foundations of Computer Science (FOCS '02). Available at:
    <https://cseweb.ucsd.edu/~daniele/papers/Cyclic.pdf>

[^5]:
    **Solana Labs (2025).** _SIMD-0215: Accounts Lattice Hash._ Solana
    Improvement Documents. Available at:
    <https://github.com/solana-foundation/solana-improvement-documents/pull/215>

[^6]:
    **Meta Platforms, Inc.** _folly::crypto::LtHash — Homomorphic hash using
    lattice-based cryptography._ Facebook Folly Library. Available at:
    <https://github.com/facebook/folly/blob/main/folly/crypto/LtHash.h>
