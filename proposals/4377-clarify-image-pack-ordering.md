# MSC4377: Clarify Image Pack Ordering

## Dependencies

This MSC builds on MSC2545 (which at the time of writing have not yet been accepted
into the spec).

## Proposal

To Preface: Within the `m.image_pack.rooms` state event for rooms and account data, `rooms` defines a map between room IDs, and a map between a stateKey and an **empty object**.

Instead of an **empty object**, this MSC defines this object like so:

- `order` **Optional, String**. Lexicographic ordering key.

So for example, before:
```
{
  "rooms": {
    "!NasysSDfxKxZBzJJoE:matrix.org": {
      "Nonexistent-Stickers": {}
    },
  }
}
```
After:
```
{
  "rooms": {
    "!NasysSDfxKxZBzJJoE:matrix.org": {
      "Nonexistent-Stickers": {
        "order": "abcd"
      }
    },
  }
}
```

### Sorting

Clients can continue to use the image pack source priority defined in MSC2545, but within the sources that utilize `m.image_pack.rooms`, clients should sort the packs lexicographically by the `order` field.

This sorting should be done WITHIN the packs in each `m.image_pack.rooms` event, e.g. room-local packs should NOT appear before user-account-local packs, if following the suggested pack source priority.

## Known Limitations

This MSC does not specify or support an `order` field when no state keys are specified, which translates to "*all image packs that a room defines*". It is expected that the pack source is redefined with state keys for each image pack if the user wants to reorder packs within a single pack source.

# Security considerations

There are no obvious security concerns with this MSC.

## Unstable prefix

Until this proposal is accepted into the spec, implementations SHOULD refer to `order` as `com.enovale.msc4377.order`.
