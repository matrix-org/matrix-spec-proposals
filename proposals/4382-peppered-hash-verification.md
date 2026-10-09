# MSC4382: Peppered Hash Verification for E2EE Content Moderation

When users report problematic content in encrypted rooms, server
administrators have no way to verify that the reported plaintext matches
what was actually sent. Reporters can claim an encrypted message contains
policy violations when it does not, enabling false reporting and
coordinated brigading attacks.

This proposal adds a `verification_hash` field to encrypted events that
allows servers to cryptographically verify reported content without
requiring decryption keys or breaking E2EE privacy guarantees.

## Proposal

Add a `verification_hash` field within the `content` of `m.room.encrypted`
events, constructed as follows:

```
verification_hash = base64(SHA-256(canonical_json(plaintext) || ciphertext))
```

Where:
- `plaintext` is the unencrypted message body, encoded as canonical JSON
- `ciphertext` is the encrypted payload from `content.ciphertext`
- `||` represents concatenation
- The result is base64-encoded for JSON representation

### Example Event

```json
{
  "type": "m.room.encrypted",
  "sender": "@alice:example.org",
  "content": {
    "algorithm": "m.megolm.v1.aes-sha2",
    "ciphertext": "AwgAEtAB...",
    "session_id": "SESSION_ID",
    "verification_hash": "+djHtqXk08IwN5cQ..."
  },
  "signatures": { ... }
}
```

### Report Endpoint Extension

The content reporting endpoint is extended to include the plaintext event:

```
POST /_matrix/client/v3/rooms/{roomId}/report/{eventId}
{
  "reason": "Human-readable explanation",
  "plaintext": {
    "type": "m.room.message",
    "content": {"msgtype": "m.text", "body": "..."},
    "room_id": "!room:server"
  }
}
```

The `plaintext` field contains the full plaintext event structure that
was fed into the encryption algorithm, as specified in the Megolm
documentation. This is the same structure that clients decrypt when
receiving encrypted events.

### Verification Process

When a user reports encrypted content, the server verifies:

```python
# Server receives report with event_id and claimed plaintext
report = receive_report(room_id, event_id)

# Fetch stored encrypted event from database (local operation)
event = database.get_event(event_id)

# Extract verification data (all already stored locally)
ciphertext = event['content']['ciphertext']
verification_hash = event['content']['verification_hash']

# Compute hash of reported plaintext with stored ciphertext
plaintext_event = canonical_json(report['plaintext'])
computed = base64(sha256(plaintext_event + ciphertext))

# Single comparison - no decryption, no network requests
if computed == verification_hash:
    # Report verified - plaintext is authentic
else:
    # Report is false - reporter is lying
```

The server never needs decryption keys or access to the encryption
session. All verification data (ciphertext and verification_hash) is
already stored in the database. Verification requires only a local
database fetch and a single SHA-256 computation.

### Security Properties

**Prevents rainbow table attacks**: Each message has a unique pepper
(its ciphertext), preventing pre-computation of common phrases. An
attacker would need to generate a new rainbow table for every single
message, making mass surveillance infeasible.

**Prevents pattern matching**: Same plaintext produces different hashes
in different messages since each has unique ciphertext.

**Allows targeted verification**: Servers can verify suspected content
in specific messages when they have reason to investigate (the intended
moderation use case).

**Does not enable mass surveillance**: Checking if a keyword exists
requires testing it against every individual message's unique pepper,
which does not scale.

## Potential Issues

**Backwards compatibility**: Existing clients don't send
`verification_hash`. The field should be optional during transition,
with servers falling back to social trust when absent. During the
unstable period, use `org.matrix.msc4382.verification_hash`.

**Event size increase**: Adds approximately 43 bytes for base64-encoded
SHA-256 output, plus field name and JSON delimiters (~60 bytes total).
For typical messages this represents ~10-15% overhead, which is
considered acceptable for the moderation benefit provided.

**Targeted attacks possible**: If a server suspects specific content in
a specific message, it can verify that suspicion. This is by design -
it's the intended moderation use case and requires prior knowledge about
which messages to check.

**Server could cache plaintexts**: Malicious servers could cache
reported plaintext-hash pairs. However, servers can already cache
reported content in the current system, so this proposal doesn't make
the situation worse.

## Security Considerations

The hash uses SHA-256, which provides 2^128 collision resistance. The
probability of accidental collision is negligible, and malicious
collisions are infeasible with current technology.

The `verification_hash` is included in the signed `content` object, so
it cannot be forged without the sender's signing key (Ed25519).

This proposal trades perfect unlinkability for practical moderation
capability. It prevents mass surveillance and pattern matching while
enabling verification of specific reported messages. Servers can verify
suspected content in targeted messages (similar to lawful intercept
capabilities), but cannot scan all messages for keywords at scale.

The threat model assumes honest-but-curious or malicious servers. A
malicious server could attempt targeted verification of high-value
messages, but this requires prior suspicion about specific messages and
cannot be done at scale. This is comparable to existing lawful intercept
capabilities.

## Unstable Prefix

During development, implementations should use:
- Field name: `org.matrix.msc4382.verification_hash`
- Report field: `org.matrix.msc4382.plaintext`
- Client capability: `org.matrix.msc4382.peppered_hash_verification`

## Dependencies

This MSC has no dependencies on other proposals. It builds on the
existing E2EE implementation (Megolm/Olm), event signing (Ed25519), and
content reporting mechanisms.
