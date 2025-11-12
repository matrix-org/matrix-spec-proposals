# MSC3956: Extensible Events - Encrypted Events

[MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767) describes Extensible Events in detail,
though deliberately does not include schemas for encrypted events. This MSC covers a replacement
for `m.room.encrypted` in rooms.

*Rationale*: Splitting the MSCs down into individual parts makes it easier to implement and review in
stages without blocking other pieces of the overall idea. For example, an issue with the way encryption
is represented should not block the overall schema from going through.

## Proposal

**Author's note**: There is fairly strong, and reasonable, opposition to having encryption be a content
block. This could theoretically allow an event to be partially encrypted, which is undesirable.

Like `m.room.message`, `m.room.encrypted` is also deprecated in favour of a new `m.encrypted` event
type. `m.encrypted` expects an `m.encrypted` content block, which is the current `content` schema for
an `m.room.encrypted` event:

```json5
{
    // irrelevant fields not shown
    "type": "m.encrypted",
    "content": {
        "m.encrypted": {
            "algorithm": "m.megolm.v1.aes-sha2",
            "sender_key": "<sender_curve25519_key>",
            "device_id": "<sender_device_id>",
            "session_id": "<outbound_group_session_id>",
            "ciphertext": "<encrypted_payload_base_64>"
        }
    }
}
```

This allows the `m.encrypted` content block to be reused by other event types, if required.

For clarity, this is *not* intended to allow unencrypted fallback on an encrypted event - doing
so would be extraordinarily dangerous and is explicitly discouraged.

## Potential issues

***TODO: Address author's note in proposal body***

***TODO***

## Alternatives

***TODO***

## Security considerations

***TODO***

## Unstable prefix

While this MSC is not considered stable, implementations should use `org.matrix.msc1767.*` as a prefix in
place of `m.*` throughout this proposal. Note that this uses the namespace of the parent MSC rather than
the namespace of this MSC - this is deliberate.

Note that extensible events should only be used in an appropriate room version as well.
