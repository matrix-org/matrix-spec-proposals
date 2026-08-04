# MSC4499: Strict server signing key caching and key ID uniqueness

Because the specification lacks a strict caching contract, new homeserver
implementations often attempt to be "helpful." Without explicit guidance,
developers may design flexible caches that store multiple key bodies for a
single key ID and perform verification either with the most recently observed
key or the first one which works (trial verification).

While existing implementations such as Synapse effectively enforce a unique
`(server_name, key_id)` constraint at the storage layer, the protocol itself
remains underspecified and does not mandate this behavior.

This ambiguity leads to an annoying loophole where key collisions in the wild
can cause room state DAG divergence (divergent event acceptance/rejection across
peers), and introduces a potential CPU-exhaustion DoS vector for any
implementation that attempts to gracefully handle them.

This MSC standardizes signing key caching requirements, introduces a strict
**First Seen Wins** rule for key IDs, and lays the groundwork for future work.

## Proposal

### Relationship to existing specification

This MSC strengthens and supersedes the existing key caching and verification
rules defined in the Matrix specification (specifically the
[Server-Server API § Retrieving server keys](https://spec.matrix.org/v1.18/server-server-api/#retrieving-server-keys)
and the notary query endpoint). In particular, this proposal upgrades the
existing `SHOULD` caching guidance to `MUST`, formalizes the `valid_until_ts`
7-day validity clamp as a normative cache constraint, and replaces any implicit
"trial verification" logic with a strict 1:1 key ID uniqueness requirement.

### Key caching requirements

Servers MUST cache remote server signing keys obtained from
`/_matrix/key/v2/server` responses and `/_matrix/key/v2/query` notary responses.
The following requirements apply to all signing algorithm types (`ed25519`, and
any future signing algorithms, like `fn-dsa-512`).

**Cache refresh lifetime.** Servers MUST cache key responses and SHOULD
proactively refresh cached keys before their clamped `valid_until_ts` expiry
(e.g., restricted to 7 days from fetch) to avoid verification failures during
key rotation windows. When a server re-fetches a key and receives the exact same
key body it already has, this is a normal refresh; the server MUST simply update
its cached `valid_until_ts` and `expired_ts` timestamps. Furthermore, servers
MUST rely on their cache. They MUST NOT fetch keys from the network for every
single inbound message or request if a valid key is already cached locally.

**Negative caching and backoff.** Servers MUST cache fetch failures. A dead or
unreachable remote server can cause fetch storms if every inbound event or
reference triggers a fresh network request. Servers MUST implement exponential
backoff (e.g., starting at 1 minute, capping at 1 hour) per remote server for
failed key fetches. An inbound federation request whose authentication
_requires_ a key fetch for the backoff-listed server SHOULD permit one immediate
(rate-limited) fetch attempt. Implementations SHOULD coalesce concurrent
outgoing key fetch requests for the same remote domain into a single active HTTP
request to prevent network saturation. If that fetch succeeds and the request
authenticates, servers SHOULD clear the backoff state.

**Cache persistence.** Key caches SHOULD be persisted to durable storage (e.g.,
database) rather than held only in memory. A server restart should not require
re-fetching every remote server's keys from the network.

**Notary internal indexing.** Notary servers act as massive aggregation points
for federation keys. To prevent them from becoming distribution vectors for
collisions, notaries MUST also enforce the First Seen Wins rule internally.
However, to preserve a forensic trail of misconfigurations and anomalous event
rejections, notary implementations SHOULD internally index observed key bodies
by their full SHA-256 digest. This allows the notary to safely store historical
collisions without database constraint violations, even if it only serves the
"first seen" key via the active API. This also familiarizes developers with the
inescapable future where key _bodies_ (values as opposed to IDs) become close to
~1 KB (prohibitively large for a "unique identifier" in a relational database).

**Notary fallback (two-tier binding).** When a required signing key is not
present in the local cache, servers typically query a configured notary server
(`/_matrix/key/v2/query`). Because a notary is a relay, a direct fetch over
validated TLS to the actual server name (`/_matrix/key/v2/server`) provides
strictly stronger cryptographic proof of ownership.

To prevent a malicious or compromised notary from permanently calcifying a
poisoned key binding, bindings first observed via a notary are **provisional**.
They are used normally for verification, but if a subsequent _direct_ fetch from
the origin server yields a key body that conflicts with the provisional binding,
the direct fetch MUST override the provisional one. The server updates its cache
to the direct-observed key body and MUST log the collision loudly. The server
SHOULD log which events (or at minimum which rooms/time window) were verified
under the displaced binding, and MAY re-verify recent events. Bindings observed
directly from the origin server are **permanent** (see below). Servers MUST NOT
treat notary unavailability as a verification success.

**Binding promotion.** A provisional (notary-observed) binding becomes permanent
the first time a direct fetch from the origin confirms the same key body.
Servers SHOULD attempt a prompt direct fetch after learning any binding via a
notary, to promote the binding and close the provisional window. Once permanent,
the binding is subject to the standard First Seen Wins rule: a later direct
fetch presenting a different key body for the same key ID is a collision and
MUST be rejected and logged. Direct-versus-direct conflicts are always resolved
by First Seen Wins; the two-tier rule applies only to the notary-versus-direct
case. Notary-versus-notary conflicts (or the same notary at two different times)
are also resolved by First Seen Wins among provisional observations.

### Key ID uniqueness requirement

A key ID (`algorithm:key_id`) MUST map to exactly one public key body for a
given remote server. This is a strict, permanent 1:1 binding. The purpose of a
key ID is to provide an unambiguous reference from a signature entry to a
specific cryptographic key; allowing multiple key bodies under the same ID
defeats this purpose. **Permanent binding.** The cryptographic binding between a
key ID and its public key body is a **permanent record**, not a cache entry.
This permanence governs _key-body identity_ only; it does not alter the
validity-window semantics (e.g., event signatures are still verified against the
key's validity at the event's `origin_server_ts`, and federation requests still
require a currently valid key). While `valid_until_ts` dictates when a server
should refresh the `/_matrix/key/v2/server` endpoint, the observed association
between a key ID and its key body MUST NOT be purged from the server's key
database when `valid_until_ts` expires. Purging this binding would leave the
server naive to future collisions and blindly accepting colliding key bodies.

**Collision detection.** If a server observes a key response (whether fetched
directly via `/_matrix/key/v2/server` or via a `/_matrix/key/v2/query` notary)
from a remote server where a key ID that was previously associated with public
key `A` is now associated with a different public key `B`, the receiving server:

1. **MUST retain the previously observed key.** The original key body remains
   authoritative for that key ID, unless the existing binding is provisional and
   the new observation is a direct fetch, in which case the two-tier override
   rule applies (see Notary fallback). In all other cases, the conflicting
   response MUST NOT replace it.
2. **SHOULD log the collision.** It helps forensically to log the key ID
   collision at warning level, including the remote server name, the key ID, and
   the SHA-256 fingerprints of both the cached and conflicting public keys. This
   alerts the operator to a potential misconfiguration or compromise on the
   remote server and may aid in community forensic or reconciliation efforts.
3. **MUST NOT perform trial verification.** The server SHOULD NOT cache multiple
   key bodies under the same key ID and MUST NOT attempt extra signature
   verification (except against the first nominally promoted instance). See
   [Security considerations](#security-considerations) for the vulnerabilities
   and general annoyances this would introduce.

**Intra-payload rejection.** A single key response payload MUST NOT contain
multiple different public key bodies for the same key ID (e.g., across
`verify_keys` and `old_verify_keys`, or duplicated within the same dictionary).
The same key body appearing under one key ID in both `verify_keys` and
`old_verify_keys` is legal. If a receiving server detects a key ID collision
within a single HTTP response, the entire response MUST be rejected as
malformed.

**First Seen Wins.** The collision detection rule follows a strict **First Seen
Wins** policy. The first public key body observed for a given
`(server_name, algorithm, key_id)` tuple (whether found in `verify_keys` or
`old_verify_keys`) is the permanent binding. This rule becomes less relevant in
the future, once key IDs are reduced to collision-resistant canonical checksums
of the key body (rather than admin-supplied near arbitrary strings).

**Local impact.** The First Seen Wins rule causes a **localized DAG divergence**
for the misconfigured server: peers that cached the original key will reject new
events from the server (signature verification fails against the wrong key
body), while peers that never cached the original key will accept them. This is
an unavoidable consequence of out-of-band key resolution — different servers
observe different key states at different times. This MSC does not and _cannot_
eliminate this divergence, because key fetching is not part of the room DAG
mainline. What this MSC does is make the divergence **deterministic, documented,
and intentional**: it prioritizes strict cryptographic integrity over silently
corrupting historical verification. While this unavoidably leaves affected peers
with a split-brain view of the room (requiring manual cache eviction or state
resets to recover) if the origin server is not fixed, it creates an immediate,
visible failure that forces the misconfigured administrator to correct their
setup. Eliminating this collateral damage entirely requires a new room version
mandating Content-Addressed Key IDs, which is deferred to a future MSC (see
[Future considerations](#future-considerations)).

### Key rotation procedure

When a server rotates its signing key, the administrator MUST:

1. **Generate a new key with a new, unique key ID.** For example, rotating from
   `ed25519:1` to `ed25519:2`, or from `fn-dsa-512:pqc0` to `fn-dsa-512:pqc1`.
2. **Retire the old key.** The old key MUST appear in the `old_verify_keys`
   section of the `/_matrix/key/v2/server` response with an appropriate
   `expired_ts` timestamp.
3. **Publish the new key.** The new key appears in `verify_keys` with the new
   key ID.

Reusing a key ID with a different key body is a **protocol violation**. This
most commonly occurs when an administrator wipes a server's database,
regenerates signing keys, but leaves the server configuration set to the same
key ID (e.g., the default `ed25519:auto`).

If this happens, administrators must rotate to a fresh key ID immediately. They
should further take efforts to correct membership or state drifts that occurred
during the period when an invalid, duplicated key was used to sign PDUs.

### Admin startup guardrails

Homeserver implementations SHOULD detect key ID reuse at startup. If the
server's configured signing key has a different key body than what was
previously persisted for that key ID, the server MUST refuse to start and emit a
clear error message instructing the administrator to either restore the original
key or assign a new key ID. This prevents the misconfiguration from propagating
to the federation in the first place. Ideally the server should also check for
pre-existing keys under that ID with its configured notaries (but if they abide
by the paragraph below, this is a largely unnecessary precaution).

Because local startup guardrails cannot detect collisions if the server's
database has been entirely wiped (the most common cause of key ID reuse),
homeserver implementations SHOULD ensure that default key ID generation
incorporates a timestamp or high-entropy component (e.g., `ed25519:a7B_93k`
rather than the default `ed25519:auto` or `ed25519:1`). This ensures that if an
administrator regenerates keys after a total state loss, a novel key ID is
structurally guaranteed. It also protects against a new server owner unwittingly
re-registering under a domain which formerly ran a Conduit server.

This is the most effective mitigation because it eliminates the root cause: it
all but certainly stops the bad key from ever being published and sidesteps the
federation-wide collision detection and localized divergence entirely.

### Recovery from key loss

If a remote server has irrecoverably lost its private signing key (e.g.,
unrecoverable database failure without backup):

1. **The administrator MUST generate a new key with a new key ID.**
2. **If the public key material is still known** (e.g., from backups, logs, or
   cached by peers), the lost key SHOULD be published in `old_verify_keys` with
   `expired_ts` set to the approximate time of loss. If it can be corroborated
   from an established notary, it should also be self-published under old keys.
3. **If the public key material is completely lost**, the administrator must
   accept that historical events signed by the lost key may fail verification on
   servers that never cached it. By design there is no protocol-level recovery
   for this scenario.

The protocol does not provide an automated recovery mechanism for key ID
collisions. Under the current constraints, it is best for the federation to
surface the misconfiguration as a visible failure — forcing the administrator to
discover and fix the error — than to bake dangerous trial verification logic or
other accommodations into homeservers to quietly allow administrative mistakes.

**Manual cache eviction.** Because the First Seen Wins policy permanently binds
a key ID, a successful TOFU poisoning attack (or serious remote
misconfiguration) will result in permanent federation failure with that server.
To allow recovery, homeserver implementations MUST provide an administrative
mechanism (e.g., an admin API or CLI interface) to manually evict cached
key-body bindings for a specific remote server name, allowing a human operator
to break the binding and re-initiate TOFU.

This manual eviction MUST be logged loudly by the homeserver, including both the
server name and the fingerprints of the evicted keys. This is an intentionally
manual, operator-gated ability to perform cache merges or manually overrides. It
must not be automated or triggered via inbound/outbound federation traffic.

### Historical event verification

Cached keys, including keys retired to `old_verify_keys`, MUST be retained for
historical PDU verification. An event signed by `algorithm:key_id` at time `T`
(where `T` is the event's `origin_server_ts`) is valid if and only if: (1) `T`
falls within the key's validity window (i.e., `T` is less than the key's
`expired_ts` if present, and `T` is less than the `valid_until_ts` asserted when
the key was active), and (2) the event signature cryptographically validates.
The 7-day cache validity clamp restricts the window in which the key is
authorized to sign new events, but does not invalidate historically signed
events when verifying them years later.

Servers MUST sanity-check `expired_ts` values in `old_verify_keys`. A future
`expired_ts` (beyond a small clock-skew allowance) MUST be treated as malformed
for that specific key entry, but does not poison the rest of the response
payload. This should be uncommon, but servers must not use the key in this case.

The strict key ID uniqueness requirement ensures that this lookup is always
unambiguous: for any `(server_name, algorithm, key_id)` tuple, there is at most
one public key body, and its validity window is well-defined. This permanent
binding also acts as a forensic asset post-compromise: you can definitively
prove which specific key body signed what event, and when.

## Potential issues

- **Misconfigured servers will experience local isolation.** An administrator
  who wipes their database and regenerates keys under the same key ID will find
  their server unable to federate with peers that cached the original key. This
  is intentional — the protocol prioritizes correctness and security over
  convenience. The fix is straightforward: change the key ID in the server
  configuration and remediate any membership or state divergences.

- **No automated key ID collision recovery.** Unlike some protocols that provide
  key-reset ceremonies or trusted-third-party recovery, Matrix provides no
  automated mechanism, since it conflicts the zero-trust federation model.

- **Permanent key-body storage.** The permanent binding requirement means
  servers must retain key-body records indefinitely, proportional to the number
  of remote servers encountered. For a typical homeserver federating with a few
  thousand servers, this is negligible (a few megabytes of public key material).

- **Two-tier binding and the TOFU window.** Allowing a direct fetch to override
  a provisional notary binding means an attacker who can serve a direct
  `/_matrix/key/v2/server` response (IP hijack, DNS spoofing) can displace a
  notary-learned key. While this extends the window of vulnerability beyond the
  initial TOFU race, requiring servers to attempt a prompt direct fetch upon
  learning a notary binding bounds this window. The override primarily removes
  the ability of a compromised _notary_ to permanently calcify a poisoned
  binding. Security limitations or concerns here hint at the need for follow-up
  work (e.g., allowing admins to configure 2-FA or a Global Settings Lock).

- **Localized DAG divergence is unavoidable.** The First Seen Wins rule means
  that peers with different cache histories may disagree on events from a
  misconfigured server. This is an inherent property of out-of-band key
  resolution and cannot be solved at the protocol level. This MSC makes the
  behavior deterministic rather than implementation-dependent, which is an
  improvement over the status quo. A solution to this concern is deferred to
  content-addressable keys or to Member Keys; see
  [Future considerations](#future-considerations).

## Alternatives

- **Trial verification (try all cached keys for a key ID).** Explicitly
  rejected. Trial verification introduces a CPU-exhaustion DoS vector, breaks
  historical DAG verification (which key was active when?), needlessly
  complicates the spec and homeserver requirements, while violating the
  cryptographic identity contract implicitly specified by the key ID.

- **Soft failure on key ID collision (warn but accept the new key).** This
  silently breaks historical verification. Events signed under the old key body
  would fail verification using the new key, corrupting state resolution for any
  room involving the affected host and any other pre-MSC4499 server.

- **Key ID collision resolution via notary consensus.** Peers could query
  multiple notary servers and accept the key body attested by a majority. This
  introduces a trusted-third-party assumption that Matrix's federation model
  explicitly avoids. Notary servers may themselves have stale caches,
  complicating efforts at gossip or consensus.

## Security considerations

- **CPU-exhaustion DoS prevention.** The strict "1:1 key ID to key body mapping"
  eliminates the trial verification attack vector. Signature verification is
  performed against exactly one key per key ID, bounding the computational cost
  of event verification.

- **TOFU cache poisoning.** Under Matrix's Trust-On-First-Use model, a
  `/_matrix/key/v2/server` response is self-signed by the private key associated
  with the payload. An attacker who briefly hijacks a server's IP (DNS spoofing,
  BGP hijacking) can generate a new keypair and re-publish it under the target's
  key ID — with valid self-signature. The First Seen Wins policy protects
  against this: if the legitimate key was cached first, the attacker's key is
  rejected as a collision. If the attacker's key is cached first (the server was
  never contacted before), TOFU provides no protection regardless of this MSC —
  an inherent limitation of TOFU, not a flaw in the proposal. Currently
  mitigating this is an admin effort.

- **Direct-override spoofing.** While allowing direct fetches to override
  provisional notary-learned keys prevents notary-enforced lock-in, it
  temporarily exposes the server to DNS/BGP spoofing on direct connections. This
  is an acceptable TOFU trade-off because (1) direct connections use WebPKI TLS
  certificate validation (bringing in standard internet-grade security), (2) the
  window of vulnerability is bounded to the brief provisional period before the
  server performs a confirming direct fetch, and (3) future MSCs such as a
  Global Settings Lock would effectively mitigate this concern.

- **DAG integrity.** The key ID uniqueness requirement protects abiding servers
  by guaranteeing that historical signature verification is locally
  deterministic. For any event at any point in time, the key that signed it is
  unambiguously identified by the `(server_name, algorithm, key_id)` tuple in
  the `signatures` dictionary.

- **Compromise detection.** Key ID collisions are a potential indicator of
  server compromise (an attacker generating a new key and attempting to publish
  it under an existing ID). Hard rejection with operator alerting provides an
  early warning mechanism. They can also be a sign of outdated, legacy servers.

- **Cache expiration is not binding expiration.** The `valid_until_ts` field
  governs when to _refresh_ the key endpoint, not when to _forget_ the key body.
  Servers that purge key-body bindings on `valid_until_ts` expiry create a
  window where collision detection is blind. This MSC explicitly requires
  permanent retention of key-body bindings to close this gap.

- **Storage exhaustion DoS.** Mandating permanent storage of key-body bindings
  introduces a theoretical storage exhaustion vector if an attacker forces a
  server to fetch and permanently store millions of unique key IDs. Homeserver
  implementations SHOULD mitigate this by enforcing a reasonable maximum limit
  on the number of cached key IDs per remote server name (e.g., 1,000 keys). If
  a remote server reaches this quota, receiving servers MUST NOT ignore new Key
  IDs permanently. Instead, they MUST evict the oldest or least-recently-used
  expired keys (keys in `old_verify_keys` with the oldest `expired_ts`). Keys
  currently published in the `verify_keys` section of a direct fetch MUST always
  be prioritized and exempt from eviction. Implementations MUST rely on existing
  federation rate-limiting to discard junk traffic before allocating database
  records. In practice, legitimate servers publish single-digit numbers of
  active keys at any given time; a server claiming thousands of key IDs is
  unambiguously hostile. A future Proof-of-Work gated proposal may mitigate the
  spurious bulk generation of keys behind Equihash or Cuckoo Cycle.

## Unstable prefix

This MSC does not introduce new protocol identifiers and does not require an
unstable prefix. The behavior changes (mandatory caching, permanent key-body
binding, collision detection, trial verification prohibition) are implementation
requirements that can be readily adopted. No API endpoints substantially change.

## Dependencies

- None. This MSC is independent of other proposals. It applies to `ed25519` keys
  today. It will apply equally to `fn-dsa-512` keys if accepted into the spec
  and if this document is not superseded by a refined or more encompassing MSC.

## Backwards compatibility

This proposal is fully backwards-compatible:

- **No protocol wire changes.** No new fields, endpoints, or response formats.
- **No room version changes.** No changes in auth or state resolution rules.
- **Existing well-configured servers are unaffected.** Servers that already use
  unique key IDs on rotation (the newly-defined behavior) experience no change.
- **Misconfigured servers experience a clarified failure mode.** Servers that
  reuse key IDs with different key bodies will be rejected by peers implementing
  this MSC. This failure already occurs unpredictably today (depending on cache
  state and timing); this MSC makes the behavior expected and codified.

## Future considerations

### Content-addressed key IDs (stricter protocol requirements)

The root cause of key ID collisions is that the `key_id` is currently an
arbitrary, administrator-defined string (e.g., `ed25519:auto`). A future room
version could eliminate this entire class of vulnerabilities by mandating that
the `key_id` must be deterministically derived from the public key body
itself—for example, `ed25519:<base64(SHA256(KeyBody))[:16]>`.

Under this paradigm, a key ID collision becomes exceedingly difficult. If an
administrator regenerates their keys, the new key body structurally enforces a
novel key ID. This entirely mitigates the TOFU poisoning vulnerability (an
attacker cannot assert a new key under an old ID without conducting a
computationally intractable simulation). It would eliminate the need for
out-of-band collision detection heuristics, allowing us to enforce strict key
uniqueness directly within room version auth rules.

Because this requires changing how PDU signatures are verified and supplants
legacy key formats thoroughly entrenched in the wild, it requires a new room
version and is deferred to a future MSC. Until then, protection must remain
strictly at the local server caching layer as outlined in this proposal.

### Member Keys [MSC4430]

The Member Keys proposal caps these concerns to a future room version by moving
the key body in-band (and reducing the complications inherent in today's
out-of-band notary model, while freeing up notary capacity to serve future
functions such as aiding in EDU reconciliation or corroborating correct room
state accumulation for a given epoch).
