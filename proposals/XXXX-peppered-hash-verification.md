# MSC: Peppered Hash Verification for End-to-End Encrypted Content Moderation

When users report problematic content in encrypted rooms, server administrators have no way to verify that the reported plaintext matches what was actually sent. Reporters can claim an encrypted message contains policy violations when it does not, enabling false reporting and coordinated brigading attacks.

This proposal adds a `verification_hash` field to encrypted events that allows servers to cryptographically verify reported content without requiring decryption keys or breaking E2EE privacy guarantees.

## Proposal

Add a `verification_hash` field to `m.room.encrypted` events:

```
verification_hash = SHA-256(plaintext || ciphertext_hash)
```

Where:
- `plaintext` is the unencrypted message body
- `ciphertext_hash` is the existing `hashes.sha256` field value
- `||` represents concatenation

### Example Event

```json
{
  "type": "m.room.encrypted",
  "sender": "@alice:example.org",
  "content": {
    "algorithm": "m.megolm.v1.aes-sha2",
    "ciphertext": "AwgAEtAB...",
    "session_id": "SESSION_ID"
  },
  "hashes": {
    "sha256": "k13N8DRLpSIaP9l8..."
  },
  "verification_hash": "f9d8c7b6a5e4d3c2...",
  "signatures": { ... }
}
```

### Verification Process

When a user reports encrypted content, they provide the event ID and claimed plaintext. The server verifies:

```python
computed_hash = SHA256(reported_plaintext + event.hashes['sha256'])
if computed_hash == event.verification_hash:
    # Report verified - plaintext is authentic
else:
    # Report is false - reporter is lying
```

The server never needs decryption keys or access to the encrypted content.

### Security Properties

**Prevents rainbow table attacks**: Each message has a unique pepper (its ciphertext hash), preventing pre-computation of common phrases. An attacker would need to generate a new rainbow table for every single message, making mass surveillance infeasible.

**Prevents pattern matching**: Same plaintext produces different hashes in different messages since each has a unique ciphertext hash.

**Allows targeted verification**: Servers can verify suspected content in specific messages when they have reason to investigate (the intended moderation use case).

**Does not enable mass surveillance**: Checking if a keyword exists requires testing it against every individual message's unique pepper, which does not scale.

## Potential Issues

**Backwards compatibility**: Existing clients don't send `verification_hash`. The field should be optional during transition, with servers falling back to social trust when absent. During the unstable period, use `org.matrix.msc####.verification_hash`.

**Event size increase**: Adds 32 bytes per encrypted event (~10% overhead for typical messages). This is considered acceptable for the moderation benefit provided.

**Targeted attacks possible**: If a server suspects specific content in a specific message, it can verify that suspicion. This is by design - it's the intended moderation use case and requires prior knowledge about which messages to check.

**Server could cache plaintexts**: Malicious servers could cache reported plaintext-hash pairs. However, servers can already cache reported content in the current system, so this proposal doesn't make the situation worse.

## Security Considerations

The hash uses SHA-256, which provides 2^128 collision resistance. The probability of accidental collision is negligible, and malicious collisions are infeasible with current technology.

The `verification_hash` is covered by the event's existing signature scheme (Ed25519), so it cannot be forged without the sender's signing key.

This proposal trades perfect unlinkability for practical moderation capability. It prevents mass surveillance and pattern matching while enabling verification of specific reported messages. Servers can verify suspected content in targeted messages (similar to lawful intercept capabilities), but cannot scan all messages for keywords at scale.

The threat model assumes honest-but-curious or malicious servers. A malicious server could attempt targeted verification of high-value messages, but this requires prior suspicion about specific messages and cannot be done at scale. This is comparable to existing lawful intercept capabilities.

## Unstable Prefix

During development, implementations should use:
- Field name: `org.matrix.msc####.verification_hash`
- Client capability: `org.matrix.msc####.peppered_hash_verification`

## Dependencies

This MSC has no dependencies on other proposals. It builds on the existing E2EE implementation (Megolm/Olm), event signing (Ed25519), and content reporting mechanisms.
