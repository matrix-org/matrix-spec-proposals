# MSC4521: Adaptive Set Reconciliation via PinSketch

Several federation mechanisms need to know whether two servers contain the same
set of identifiers. With a lot of work, this MSC lets them compute the exact
symmetric difference between large populations, without any probabilistic
errors. This MSC helps ensure network synchronization.

Some consumers need that over a room's known event or resolved state set; others
use it to synchronize key IDs between notaries, or to reconcile ephemeral and
other identifier populations. This MSC defines the primitive once, as a named
digest profile, so that consumers can share the field, hash derivation, wire
encoding, and decoding contract instead of rebuilding them from scratch.

`algebraic_v1` couples a strata estimator, extraction sketch, and 128-bit
accumulator into one ladder.

The profile targets differences up to 4,096 elements per round in populations up
to $10^7$, keeps the initial depth-0 sketch under 256 B, and keeps a fully
saturated round under 32 KiB, excluding object payloads. Decoding a capacity-`k`
node costs $O(k^2 \log k)$. A difference of size $d$ spread over $n$ nodes
therefore costs $O\!\left(\frac{d^2}{n}\log\frac{d}{n}\right)$. Quadratic
complexity means that invertible bloom filters will outscale this MSC
asymptotically, but at smaller deltas, this MSC wins (nearly all typical use
cases). Larger differences are a frame problem, not a reconciliation problem
(see [Scalability](#scalability)); the baseline 20-round, 4096-capacity sequence
reaches about 82,000 differing elements under the default ceiling parameters.
More capacity extends a round; it does not restart it.

## Scope

This profile defines identifier derivation, the 64-bit field and `libminisketch`
compatibility contract, the level-0 accumulator, the syndrome sketch and its
capacity bounds, dynamic tree extraction and the strata estimator, the
decode-and-verify contract, capacity budgets, and the resident structure.

This profile does **not** define frames, negotiation, scheduling, endpoints, or
authorization; those belong to the consuming MSC. Consumers MUST still verify
that both sides digest the same population before comparing them.

## Element derivation

The profile operates over a set `S` of opaque elements. Each consumer MUST map
every element to a canonical 32-byte digest before applying this profile.
Consumers define what the elements mean; the kernel treats them as an opaque set
and does not interpret their content.

Let `D(e)` be the consumer-defined 32-byte digest for element `e`.

`libminisketch` requires non-zero inputs over $\mathbb{F}_{2^{64}}$.
Implementations derive $h_{64}(e)$ and $h_{128}(e)$ from `D(e)` using network
byte order (big-endian):

- **$h_{64}(e)$ (64-bit field element):** Scan `D(e)` in four 8-byte big-endian
  chunks. $h_{64}(e)$ MUST be the first non-zero chunk interpreted as an
  unsigned 64-bit integer, or `1` if all four chunks are zero.
- **$h_{128}(e)$ (128-bit accumulator element):** Take the first 16 bytes of
  `D(e)` as an unsigned 128-bit big-endian integer. Zero is permitted here; the
  accumulator is a plain XOR sum, so it does not need the $h_{64}$ non-zero
  fallback.

### Matrix event-ID binding

For event sets, `D(e)` is derived based on the room version:

- **Room versions 1 and 2** (string-formatted IDs): Set `D(e)` to the `SHA-256`
  digest of the UTF-8 event-ID string.
- **Room version 3**: Strip the leading `$` byte and decode the remaining
  unpadded standard Base64 payload.
- **Room versions 4 and later**: Strip the leading `$` byte and decode the
  remaining unpadded URL-safe Base64 payload.

Room versions with non-hash-derived event IDs MUST use the `SHA-256` digest of
the event-ID string or exclude the event from the population. This profile does
not use auxiliary hash functions (e.g., `XXH3`).

## Field

The 64-bit Galois field is defined as:

$$
\mathbb{F}_{2^{64}} \cong \mathbb{F}_{2}[x]
\big/ \langle x^{64} + x^4 + x^3 + x + 1 \rangle
$$

Bit `i` is the coefficient of $x^i$; bit `0` is the least-significant bit and
bit `63` the most-significant bit.

Sketches MUST be byte-for-byte compatible with `libminisketch` at field size 64
for identical input sets. This requirement covers coordinate ordering,
little-endian encoding, and field arithmetic; any mismatch renders an
implementation non-conforming, regardless of internal decode success.

The secure-sketch lineage for noisy inputs is discussed by Dodis et al.[^1]. The
syndrome construction is PinSketch; the field and reduction polynomial follow
`libminisketch`.[^7] Finite-field set reconciliation originates with Minsky,
Trachtenberg, and Zippel.[^2] The 128-bit accumulator layer is a bitwise XOR sum
and operates independently of this field.

## Level-0 accumulator

$$
\begin{aligned}
\mathrm{digest} &= \bigoplus_{e \in S} h_{128}(e) \\
\mathrm{count} &= |S|
\end{aligned}
$$

where $\bigoplus$ denotes bitwise XOR over the given elements; the digest is
serialized as 16 big-endian bytes, then encoded as an unpadded `base64url`
string.

Insertion and removal use the same operation: XOR $h_{128}(e)$ into the digest
and update the count. Updates are order-independent and require no state
rebuilds.

The count residual $c = \left\lvert|S_A| - |S_B|\right\rvert$ yields the exact
symmetric difference size $d = |S_A \triangle S_B|$ during one-sided divergence
(e.g., a lagging peer), and in that case $c = d$. Matching digests and counts
are consistency and fault-detection signals, not an authoritative proof of
equality; the decoder, frame checks, and population verification remain the
source of truth.

The accumulator provides fault detection (integrity) between honest peers. See
[Decode and verification](#decode-and-verification).

**Wire digest test vector.** Big-endian serialization is visible in the byte
order of this one-hot accumulator value:

```text
digest: 0x0000_0000_0000_0000_0000_0000_0000_0001
wire:   AAAAAAAAAAAAAAAAAAAAAQ
```

## Syndrome sketch

The extraction layer computes the odd-power syndrome map over
$\mathbb{F}_{2^{64}}$:

$$
\sigma_k(S) = \left(\sum h_{64}(e), \sum h_{64}(e)^3, \dots, \sum h_{64}(e)^{2k-1}\right)
$$

Even powers are omitted because $s_{2i} = s_i^2$ in characteristic 2 via the
Frobenius endomorphism. This odd-power syndrome representation adapts standard
Bose–Chaudhuri–Hocquenghem (BCH) error-correction machinery,[^3] forming the
substrate specialized by PinSketch.

**Serialization.** Syndrome coordinates $(s_1, s_3, \dots, s_{2k-1})$ are
serialized in ascending odd-power order as unsigned 64-bit **little-endian**
integers. The distinction between big-endian element parsing (following Matrix
conventions) and little-endian coordinate serialization (following
`libminisketch`)[^7] is normative and intentional.

A sketch of capacity $k$ is exactly $8k$ bytes, wire-encoded as unpadded
`base64url`.

**Subtraction.** Subtracting two sketches of equal capacity via XOR yields the
syndrome of their symmetric difference. This group-valued property allows an
over-capacity exchange to be extended additively rather than restarted.

## Dynamic tree extraction

A single sketch at `depth = 0` covers the whole population and is exact only
while the true difference is within its capacity. When it is not, the population
is localized via recursive binary subdivision (instead of a fixed partition).

`h_64(e)` determines an element's path down a binary tree: at depth `d`, an
element belongs to node `prefix` if and only if the most-significant `d` bits of
`h_64(e)` (bits `63` down to `64 - d`) equal `prefix`. Depth 0 has a single node
(`prefix = 0`) covering every element — the same population a single flat sketch
covers. Implementations MUST cap `depth` at 32, so `prefix` is at most 32 bits
wide. If a node still overflows at its requested capacity, the peer that detects
the failure requests two child sketches at `depth + 1`, for prefixes
`2 * prefix` and `2 * prefix + 1`. A child that still overflows is split again.
A node that still overflows at `depth = 32` MUST NOT be split further; the peer
that detects the failure MUST report failure for that prefix and allow the
consuming protocol to retry with a larger frame or a different reconciliation
mechanism. The recursion terminates: each split reduces node population weakly,
depth is bounded at 32, and a node still overflowing at the cap is reported
rather than split further.

Every node, at any depth, is decoded and verified exactly as in
[Decode and verification](#decode-and-verification), below: it either decodes
within its capacity and passes the 128-bit residual check, or it fails loudly
and is split. There is no separate "bucket" primitive and no persistent per-node
resident state — see [Resident structure](#resident-structure). A
`(depth, prefix)` pair is computed only when a peer actually requests it.

### Antichain invariant and wire ordering

Requests in a single exchange MUST form an antichain and MUST be transmitted in
canonical key-space range order. For a request $R=(d,p)$ with depth $d$
($0 \le d \le 32$) and prefix $p$ ($0 \le p < 2^d$), define:

$$
\text{start}(R) = p \cdot 2^{32-d}
$$

$$
\text{end}(R) = (p + 1) \cdot 2^{32-d}
$$

A request $R_i$ is an ancestor of $R_j$ if and only if $d_i \le d_j$ and the
$d_i$ most-significant bits of $p_j$ equal $p_i$.

A valid request sequence $[R_0, R_1, \dots, R_{N-1}]$ MUST satisfy:

$$
\text{end}(R_i) \le \text{start}(R_{i+1})
\quad
\text{for all } 0 \le i < N - 1
$$

If any pair of requests forms an ancestor-descendant relation, or if the
sequence violates the ordering condition above, the receiver MUST reject the
request before performing sketch subtraction or field operations.

Implementation note (non-normative): a receiver can validate a canonically
ordered slice in place, without heap allocation, by checking each request
against the previous request's `end` boundary. That yields `O(N)` time and
`O(1)` memory. A binary prefix trie remains a valid alternative internal shape
for implementations that want a different representation.

**Capacity bounds.** A `sketch` exchange consists of one or more extraction
requests, each a `(depth, prefix, capacity)` triple. A single entry's `capacity`
MUST NOT exceed 32; the sum of `capacity` across all requests in a single
exchange MUST NOT exceed 4096. These are separate bounds for separate reasons:
the per-entry cap bounds decode cost ($O(k^2 \log k)$ per node), while the
aggregate cap bounds total wire size and responder work across a whole exchange.
A future profile MAY raise either cap; `algebraic_v1` MUST NOT.

**Materializing a node.** Producing the syndrome sketch for `(depth, prefix)`
requires the subset of the population whose `h_64(e)` shares that `depth`-bit
prefix. A responder MUST NOT satisfy this by scanning its full population per
request: since `h_64(e)` is a fixed 64-bit key per element, any
`(depth, prefix)` subset is a contiguous range under `h_64`-sorted order.
Implementations MUST maintain (or build and cache) an index of element
identifiers ordered by `h_64`, so that a node's element subset is a range slice
— $O(\log n)$ to locate plus the slice size — not a full-population scan. This
index holds only identifiers and `h_64` keys, not precomputed syndromes; it is
far cheaper than the resident per-node syndrome structure a fixed partition
would require (see "Resident structure") — and unlike that structure it serves
every depth, not one fixed depth.

The depth-limited refine-and-resolve shape mirrors the practical reconciliation
architecture used by Erlay.[^4] Keep the field math fixed, size the exchange
before decoding, and split only when the current capacity is not enough.

This split is a localization step, not a proof that the peer is wrong: it only
narrows the candidate population to the prefix that still overflows.

## Strata estimator

Implementations SHOULD maintain a 32-entry strata estimator for pre-decode
difference sizing. MSCXXXX requires all 32 entries in `room_digest`; other
consumers MAY treat the estimator as a local recommendation if they expose it at
all.

This is the strata-estimator construction from _What's the Difference?:
Efficient Set Reconciliation without Prior Context_ (2011).[^5] Use a compact
pre-decode summary to estimate $d = |S_A \triangle S_B|$ before committing to a
decoder.

Stratum $s_i$ contains the same odd syndrome coordinates $s_1$ through $s_{15}$
as an extraction sketch, but only for elements whose $h_{64}(e)$ has exactly $i$
trailing zero bits. Stratum 31 also includes every value with 31 or more
trailing zero bits. Each stratum is therefore a 64-byte sketch.

Two peers XOR corresponding strata and inspect the highest nonempty residual
stratum to estimate $d$ before choosing between a single depth-0 extraction,
provisioning an initial dynamic-tree request, or abandoning the comparison.

If the highest nonempty residual stratum is $i < 31$ and it decodes to $k_i$
elements, the standard estimate is $2^{i+1} \cdot k_i$. If stratum 31 decodes to
$k_{31}$ elements, the standard estimate is $2^{31} \cdot k_{31}$. If the
highest nonempty residual stratum overflows, the standard fallback estimate is
$8 \cdot 2^{31}$.

The estimator is advisory. It MUST NOT override a consumer's population check,
and it MUST NOT substitute for 128-bit residual verification of a decoded
difference. Strata summaries accurately estimate the residual only when both
sides use the same validated frame, stratum assignment, hash mapping, and
coordinate order. If any of those boundaries shift, the estimate is meaningless.
A server MUST NOT estimate or subtract across differing frames; the estimator
MUST NOT substitute for or override frame validation.

In other words, the estimator chooses a likely starting capacity; it does not
determine whether the comparison is correct, nor does it replace decoding or
tree splitting.

## Decode and verification

A decoder recovers up to $k$ elements from a capacity-`k` syndrome residual.
Decode either succeeds with a set of $h_{64}$ values, or fails.

Decode failure is loud, and this is the central operational property of the
profile: a failed decode is reported as failure, not as an empty difference.
Consumers MUST distinguish `decoded` from `capacity_exceeded`.

**Verification.** A decoded difference MUST be checked against the 128-bit
accumulator before it is trusted. Let `E` be the expected remote digest, `R` the
residual digest, `L` the local full identifiers, and $A(\cdot)$ the 128-bit
accumulator:

$$
E = R \oplus A(L)
$$

The peer resolves the short IDs it holds, computes $A(L)$, and compares against
`E`. A mismatch means the decode was wrong or the populations differed; the
result MUST be discarded.

A peer cannot compute the 128-bit accumulator for identifiers it does not hold.
Each side asymmetrically verifies the half it can resolve, the residual carrying
the other half. See [Security considerations](#security-considerations) below
for adversarial limits.

**Decoder bounds.** The internal decoder is standard BCH-style syndrome decoding
over $\mathbb{F}_{2^{64}}$. The sketch exposes odd-power syndromes, and the
missing even syndromes are derived or implied. Implementations MAY use
Berlekamp-Massey or an equivalent recurrence solver to derive a locator
polynomial of degree at most `k`. If the observed syndromes are inconsistent
with any such polynomial, or if root searching fails to produce a consistent set
of roots, decoding fails, and the caller MAY split the node and retry at a
smaller prefix.

## Security considerations

XOR accumulators are fault-detecting, not binding. Any set of 129 `128-bit`
values is linearly dependent over $\mathbb{F}_2$, so a peer with freedom over
which identifiers to include can construct a nonempty subset whose accumulator
is zero. Nothing in this profile relies on the accumulator being binding.
Consumers MUST verify transferred objects by their own rules and MUST NOT treat
accumulator agreement as evidence of authenticity.

Deployments needing adversarial robustness MAY define a future profile with
negotiated per-link salting for transmitted extraction sketches. Such a profile
MUST specify salt negotiation, salt derivation, the salted identifier mapping,
and how both sides identify the profile before subtraction. `algebraic_v1`
defines no salting and its fixed $h_{64}$ mapping MUST remain byte-compatible
across implementations. Deployments needing transferable accumulator evidence
should look to an LtHash-style profile under a future `digest_type` rather than
to `algebraic_v1`.

## Capacity provisioning

Provision extraction capacity from the count residual. In the common one-sided
lag case, $c = \left\lvert|S_A| - |S_B|\right\rvert$ and
$d = |S_A \triangle S_B|$ are equal. Here $r_{\mathrm{obs}}$ is the observed
rate of newly arriving elements relevant to the comparison, and
$\widehat{\mathrm{RTT}}$ is the estimated round-trip time in seconds. The strata
estimate can guide first-round pre-splitting, but only within the same
aggregate-capacity budget described in [Scalability](#scalability).

$$
k = \min\left(32,\ \left\lceil 1.5c \right\rceil + 4 +
\left\lceil r_{\mathrm{obs}} \cdot \widehat{\mathrm{RTT}} \right\rceil\right)
$$

The three terms cover, respectively: measurement slack when divergence is not
purely one-sided, a small floor for tiny differences, and events arriving
concurrently during the round trip.

If the unclamped value exceeds 32, the profile uses tree extraction rather than
a single depth-0 request.

If decode fails at `k`, retry a larger `k` up to the cap, or split into
dynamic-tree children to localize a two-sided difference. Because sketches
subtract, a retry at higher capacity is a continuation of the same comparison,
not a restart. Additive extension is valid only when the syndrome coordinates
are strictly prefix-compatible: the frame anchor, hash mapping, field size, and
coordinate order MUST remain unchanged. If no compatible frame exists, peers
MUST abort the exchange and retry with a fresh frame.

The escalation sequence is:

1. Validate the frame and abort if the frame anchor does not match.
2. Execute the compact `algebraic_v1` exchange at depth 0.
3. Resolve small over-capacity differences by additive syndrome extension.
4. Isolate failures independently through dynamic tree extraction: split the
   overflowing node and retry each child.
5. For a difference so large or so heavy-tailed that it exhausts the 4096
   aggregate capacity across the tree, or would require recursing to impractical
   depth, treat it as a frame problem rather than a reconciliation problem — see
   the scale boundary section below.

### Scalability

Dynamic tree extraction is for bounded interior gaps within an agreed frame, not
arbitrary divergence. A value of $d \approx 100,000$ forces very wide
first-round fan-out under a k = 32 bucket cap, which makes end-to-end extraction
expensive even though per-bucket decode remains fast. The point is not that
reconciliation becomes mathematically impossible, but that the baseline ~82,000
figure reflects the MSC’s default operating point (not a hard algorithmic
ceiling). Beyond that point, applications can still choose to spend more round
budget or per-round capacity, while truly structural divergence should switch to
frame/DAG alignment.

Non-normative implementation note: a peer can use the strata estimate to
pre-split a first request into a wider antichain when it expects a large but
still bounded difference. This trades fewer rounds for a larger first exchange,
but the cap still applies, and bucket load remains probabilistic rather than
uniform in the face of clustering or skew.

**Scale illustration.** These benchmark points are not protocol upper bounds;
they show that a large population can still have a small difference and keep the
core algorithm cost nearly flat while setup scales with the resident set size.
The `Bookkeeping` column measures resident accumulator and strata work only; no
extraction or decode occurs in these numbers.

<!-- markdownlint-disable MD013 -->

| Population | Difference        | Setup (ms) | Bookkeeping (ms) | Interpretation                         |
| ---------- | ----------------- | ---------: | ---------------: | -------------------------------------- |
| 50,000     | +2,100/-1,900     |       6.25 |             1.80 | small population, small absolute diff  |
| 100,000    | +5,000/-4,000     |      12.89 |             1.44 | larger population, small absolute diff |
| 1,000,000  | +10,000/-9,000    |     123.93 |             2.26 | large population, small absolute diff  |
| 10,000,000 | +500,000/-400,000 |    1282.86 |             1.44 | very large population, setup dominates |

<!-- markdownlint-enable MD013 -->

## Resident structure

To make extraction deployable, implementations SHOULD maintain a resident
per-population structure:

<!-- markdownlint-disable MD013 -->

| Layer                 | Width            | Size  | Purpose                                      |
| --------------------- | ---------------- | ----- | -------------------------------------------- |
| Integrity accumulator | 128 bits         | 16 B  | ETag, level-0 agreement, decode verification |
| Strata estimator      | 64 bits × 8 × 32 | 2 KiB | pre-decode difference estimation             |

<!-- markdownlint-enable MD013 -->

Fixed resident state is ~2 KiB per population, independent of population size.
Node sketches are computed on demand from the `h_64`-sorted index
([Dynamic tree extraction](#dynamic-tree-extraction)), which is `O(n)` in
identifiers and not part of the fixed state.

**Update procedure.** On inserting or removing element `e`:

1. Compute $y = h_{128}(e)$ and $x = h_{64}(e)$.
2. XOR $y$ into the integrity accumulator. On insert, increment the count by 1;
   on remove, decrement by 1.
3. Choose the estimator stratum from `x.trailing_zeros()`.
4. Compute $x^2$ once and reuse it for the remaining odd powers.
5. Update $\left(x, x^3, ..., x^{15}\right)$ by repeatedly multiplying by $x^2$.

In characteristic 2, insertion and removal are the same XOR operation, so no
separate deletion path is needed.

This update path is the operational side of the same BCH/PinSketch machinery and
is why the profile remains fully additive while still supporting pre-decode
sizing.

**Measured cost.** The reference implementation measures about 618 ns per
resident update with the portable multiply and about 52 ns with `PCLMULQDQ` on
the benchmarked `x86-64` machine; the underlying $\mathbb{F}_{2^{64}}$ multiply
measures about 77.25 ns portable and 6.50 ns with `PCLMULQDQ`.

The strata estimator is an optimization; MSCXXXX requires it in `room_digest`,
while other consumers MAY treat it as a local recommendation.

## Advertisement

Consumers advertise support through their own capability mechanism. The
canonical feature flag for this profile is:

```json
{
  "unstable_features": {
    "tk.nutra.msc4521.digest.algebraic_v1": true
  }
}
```

Dynamic tree extraction is part of `algebraic_v1` itself, not a separate
`digest_type`: a server that supports `algebraic_v1` supports depth-0 sketches
and their recursive refinement under the same flag, since both use the same
field, hash derivation, and decoder.

A future profile that changes the field, hash derivation, coordinate ordering,
or capacity caps MUST use a new `digest_type` name. Profiles are not versioned
in place because a comparison between two different profiles has no defined
meaning and must fail at negotiation rather than at decode.

## Potential issues

**Fixed capacity caps.** The 4096 aggregate cap is conservative and chosen for
the small one-sided differences expected to dominate normal federation repair.
Populations with routinely large or heavy-tailed differences will hit the cap
and trigger dynamic tree extraction more often than necessary. Unlike a rateless
encoding, tree extraction requires no second decoder.

**64-bit collisions.** Two distinct identifiers can share $h_{64}$. At the
population sizes in scope, this is rare, and the 128-bit verification step
catches the resulting bad decode, but a decode can fail for reasons unrelated to
capacity. Implementations MUST NOT interpret repeated verification failure at
adequate capacity as evidence of peer misbehavior without further diagnosis.

**Resident state on many small populations.** 2 KiB per population is cheap even
in aggregate for a server participating in very many mostly-idle rooms.
Implementations SHOULD still evict resident structures under an LRU or TTL
policy and rebuild on demand.

## Alternatives

**Fixed-Capacity Invertible Bloom Lookup Tables (IBLT).** Standard IBLTs offer
linear-time decoding. They are rejected for the baseline because
BCH/PinSketch-style syndromes are significantly more compact. An IBLT requires
three fields per cell (`count`, `id_sum`, `hash_sum`) and typically requires
1.35x to 1.5x the cells as the expected difference size to decode successfully.
`algebraic_v1` requires exactly one field element per unit of capacity, making
it both cheaper per exchange and cheaper to provision when dynamic tree
extraction requests a node's sketch.

**Rateless IBLT (RIBLT).** Rejected. Rateless variants remove the need to choose
capacity up front, but they need their own wire format and a second decoder.
Dynamic tree extraction reuses PinSketch's decoder and `D(e)` digest without a
capacity guess.

**LtHash / homomorphic hashing.** Provides binding accumulators at substantially
higher per-update cost. Appropriate where accumulator evidence must be
transferable to a third party; unnecessary where, as here, transferred objects
are independently verifiable by signature and hash. Left to a future
`digest_type`.

## Theoretical models

The reconciliation mechanisms in this MSC use standard algebraic and
combinatorial ideas. Implementations need only follow the wire format and decode
contracts, but these analogies may help understand the protocol.

- **Syndrome sketches and BCH-style power sums:** The extraction layer computes
  an odd-power syndrome map over $\mathbb{F}_{2^{64}}$:
  $\sigma_k(S) = \left(\sum h_{64}(e), \sum h_{64}(e)^3, \ldots, \sum h_{64}(e)^{2k-1}\right)$.
  Even powers are omitted because the Frobenius endomorphism makes them
  redundant in characteristic 2. Recovering the symmetric difference from these
  coordinates is the finite-field analogue of power-sum/root recovery in
  classical algebra.[^8]

- **128-bit accumulator and linear dependence:** The $h_{128}$ accumulator
  provides fault detection but is explicitly not cryptographically binding. Over
  $\mathbb{F}_2$, any set of 129 128-bit values is linearly dependent, so a
  nonempty subset can always have XOR sum zero.

- **Dynamic tree extraction and antichain invariants:** When divergence exceeds
  a node's capacity, localization proceeds by recursive binary subdivision.
  Termination follows from two constraints: requests MUST form an antichain, and
  recursion depth is capped at 32. Each split weakly reduces the population, so
  the search state space remains finite, matching the termination pattern in
  Putnam 2008 A3.[^9]

- **Decode cost:** Decoding a single capacity-$k$ node costs $O(k^2 \log k)$.
  With per-node capacity capped at $k \le 32$ and failures isolated
  independently, a difference of size $d$ spread over $n$ nodes has total decode
  cost $O\left(\frac{d^2}{n}\log\frac{d}{n}\right)$.

- **Strata estimation and trailing-zero counts:** The pre-decode estimator
  buckets elements by trailing-zero count in $h_{64}$. Because $h_{64}(e)$ is
  modeled as uniformly distributed, the highest nonempty residual stratum gives
  a compact estimate of $d = \lvert S_A \triangle S_B \rvert$, in the same broad
  family as probabilistic counting heuristics.

### Exploratory implementer materials

Exploratory exercises. Useful for testing the theory before implementation.

- **XOR accumulator:** _LeetCode 260 (Single Number III)_[^11]. Bitwise XOR
  reduction.
- **Power-sum:** _LeetCode 2965 (Find Missing and Repeated Values)_[^12].
  Recover missing elements via aggregated sums and squares.
- **Recursive partitioning:** _LeetCode 427 (Construct Quad Tree)_[^13] and
  _Codeforces 842D (Vitya and Strange Lesson)_[^14]. Recursive subdivision and
  dynamic prefix-trie routing.
- **Prefix boundary:** _LeetCode 201 (Bitwise AND of Numbers Range)_[^15].
  Shared bit-prefix / range-bounding logic.
- **Syndrome decoder:** _Yosupo Library (Find Linear Recurrence)_[^16].
  Berlekamp-Massey recurrence recovery.
- **Rateless reconciliation:** _Practical Rateless Set Reconciliation_. Adaptive
  split-and-continue reconciliation when a fixed-capacity decode overflows.[^6]

## Test vectors

### Field multiplication

The 64-bit field multiply over `GF(2)[x] / <x^64 + x^4 + x^3 + x + 1>` is
illustrated by[^10]:

```text
mul(0x0000_0000_0000_0000  ×  0xffff_ffff_ffff_ffff)  =  0x0000_0000_0000_0000
mul(0x0000_0000_0000_0001  ×  0xffff_ffff_ffff_ffff)  =  0xffff_ffff_ffff_ffff
mul(0x0000_0000_0000_001b  ×  0x0000_0000_0000_001b)  =  0x0000_0000_0000_0145
mul(0xffff_ffff_ffff_ffff  ×  0xffff_ffff_ffff_ffff)  =  0x5555_5555_5555_5513
mul(0x8000_0000_0000_0000  ×  0x8000_0000_0000_0000)  =  0xc000_0000_0000_005a
```

### Legacy event ID (V1 and V2)

```text
input:  $legacy:example.org
D(e):   2633a2037c72be2c8bd68c983934e7be65aae011a71b8e1d15a23e628b9dedaf
h128:   0x2633_a203_7c72_be2c_8bd6_8c98_3934_e7be
h64:    0x2633_a203_7c72_be2c
```

### V3 event ID

For room version 3, strip the leading `$` and decode the remaining unpadded
standard Base64 payload to recover `D(e)`.

```text
input:  $ || STANDARD_NO_PAD.encode([0xfb; 32])
h128:   0xfbfb_fbfb_fbfb_fbfb_fbfb_fbfb_fbfb_fbfb
h64:    0xfbfb_fbfb_fbfb_fbfb
```

### V4+ event ID

For room version 4 and later, the leading `$` is stripped before decoding the
remaining unpadded URL-safe base64 payload.

```text
input:  $ || URL_SAFE_NO_PAD.encode([0x00; 7] ++ [0x2a] ++ [0x00; 24])
h128:   0x0000_0000_0000_002a_0000_0000_0000_0000
h64:    0x0000_0000_0000_002a
```

### All-zero digest fallback

```text
input:  $ || URL_SAFE_NO_PAD.encode([0x00; 32])
h128:   0x0000_0000_0000_0000_0000_0000_0000_0001
h64:    0x0000_0000_0000_0001
```

### PinSketch wire format

For capacity 2, toggling `1 << 63` and `u64::MAX` encodes to the little-endian
syndrome bytes before `base64url` encoding:

```text
FF FF FF FF FF FF FF 7F FD 32 33 33 33 33 33 93
```

Decoding those bytes round-trips to the same sketch.

For capacity 32, toggling `0x1234` and `0x5678` encodes to the little-endian
syndrome bytes before `base64url` encoding:

<!-- markdownlint-disable MD013 -->

```text
4C 44 00 00 00 00 00 00 40 41 96 BE 27 05 00 00 2A B3 F9 7D 92 3C 1E 3C 54 62 CC DE 5C 10 6F D7
41 74 56 42 69 A2 F2 78 FF C2 11 6D 45 E4 B3 EA AF 36 62 67 C8 E7 2A 94 6C FF 33 8A 89 B4 5B 6F
D0 40 12 A7 DE 3A C3 50 80 74 7E 77 E0 6D 8E AB D4 DF 23 95 59 BF 21 E7 DF 8E 6E AC 00 7A 81 24
93 9A 8B 72 A8 20 32 BD F7 2B 62 8F 0F 8A 9C 31 1A 33 34 7E F9 5D A9 0E 5E D3 95 B1 21 53 9D 0B
B4 DF 33 7D FF E2 5F 40 74 F1 74 59 F3 06 AC CC 61 09 E4 F1 3C BE 9C 87 F1 24 2D 88 43 D8 FF 82
6E E6 CC BF 8F 46 A2 D8 45 A0 DC FE C6 35 CF D7 F5 FD 88 FC 83 A6 35 7F EB 08 37 7F 4F B4 E3 23
F0 42 9C 7D 60 B9 88 3D 03 11 6A E0 75 A5 65 C6 53 DE 08 70 D5 99 56 BE F2 B7 5A 02 0E BA B8 00
FE 7C 2B 35 0D 4C 8B E9 FA 95 88 CE 09 1E 56 E7 D9 32 B3 BA E6 FD 33 99 19 45 A0 84 F2 75 1B 41
```

<!-- markdownlint-enable MD013 -->

## Unstable prefix

<!-- markdownlint-disable MD013 -->

| Proposed final identifier | Purpose     | Development identifier                 |
| ------------------------- | ----------- | -------------------------------------- |
| `algebraic_v1`            | digest type | `algebraic_v1`                         |
| feature flag              | capability  | `tk.nutra.msc4521.digest.algebraic_v1` |

<!-- markdownlint-enable MD013 -->

## Possible consumers

- MSC4242 (State DAGs) — over an index of state events.
- MSCXXXX (federation missed-PDU reconciliation) — over a room's known-event set
- MSCYYYY (federation EDU state reconciliation) may adapt the same algebraic
  machinery for EDU entries.

<!-- ## References -->

[^1]:
    _Fuzzy extractors: How to generate strong keys from biometrics and other
    noisy data_ (Dodis et al., 2008).
    [doi:10.1137/060651380](https://doi.org/10.1137/060651380)

[^2]:
    _Set reconciliation with nearly optimal communication complexity_ (Minsky et
    al., 2003).
    [doi:10.1109/TIT.2003.815784](https://doi.org/10.1109/TIT.2003.815784)

[^3]:
    _An introduction to BCH codes and finite fields_ (MacWilliams & Sloane,
    1977). The theory of error-correcting codes.
    [sciencedirect.com](https://www.sciencedirect.com/science/chapter/bookseries/abs/pii/S0924650908705282)

[^4]:
    _Erlay: Efficient transaction relay for Bitcoin_ (Naumenko et al., 2019).
    [doi:10.1145/3319535.3354237](https://doi.org/10.1145/3319535.3354237)

[^5]:
    _What's the difference?: Efficient set reconciliation without prior context_
    (Eppstein et al., 2011).
    [doi:10.1145/2018436.2018462](https://doi.org/10.1145/2018436.2018462)

[^6]:
    _Practical Rateless Set Reconciliation_ (Yang et al., 2024).
    [doi:10.1145/3651890.3672219](https://doi.org/10.1145/3651890.3672219)

[^7]:
    _libminisketch byte-compatibility reference for 64-bit field_ (Wuille).
    GitHub. <https://github.com/bitcoin-core/minisketch>

[^8]:
    Putnam Questionnaire. 1968 A6, solution archive:
    <https://prase.cz/kalva/putnam/psoln/psol686.html>

[^9]:
    Putnam Questionnaire. 2008 A3, archive PDF:
    <https://kskedlaya.org/putnam-archive/2008.pdf>

[^10]:
    Example Rust implementation with tests:
    [`rezzy`](https://github.com/gamesguru/rezzy/tree/788ae96c0e1601790d8f4618754726ac70e7c24b).

    Non-optimized example implementation in Golang:
    [`gomatrixcrypto`](https://github.com/Wombat-Foundation/gomatrixcrypto/blob/80fd84afc763f1812f548410a66511837bd84afc/reconcile/algebraic.go).

[^11]:
    LeetCode 260, Medium, _Single Number III_:
    <https://leetcode.com/problems/single-number-iii/>

[^12]:
    LeetCode 2965, Easy, _Find Missing and Repeated Values_:
    <https://leetcode.com/problems/find-missing-and-repeated-values/>

[^13]:
    LeetCode 427, Medium, _Construct Quad Tree_:
    <https://leetcode.com/problems/construct-quad-tree/>

[^14]:
    Codeforces 842D, _Vitya and Strange Lesson_:
    <https://codeforces.com/problemset/problem/842/D>

[^15]:
    LeetCode 201, Medium, _Bitwise AND of Numbers Range_:
    <https://leetcode.com/problems/bitwise-and-of-numbers-range/>

[^16]:
    Yosupo Library, _Find Linear Recurrence_:
    <https://judge.yosupo.jp/problem/find_linear_recurrence>
