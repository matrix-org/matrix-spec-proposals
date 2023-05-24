# Update redaction rules, again

The current [redaction algorithm](https://spec.matrix.org/v1.2/rooms/v9/#redactions) are
still missing some key fields, even after [MSC2176](https://github.com/matrix-org/matrix-spec-proposals/pull/2176)
attempted to fix some of the obvious cases. This MSC aims to fix more fields.

## Proposal

*Note*: It is recommended to read [MSC2176](https://github.com/matrix-org/matrix-spec-proposals/pull/2176)
before this proposal as MSC2176 contains a lot of backing context.

In a new room version due to redactions affecting event hashes, we:

* `m.room.member` events additionally preserve part of `third_party_invite` under `content`, if present:
  * Spec: https://spec.matrix.org/v1.2/client-server-api/#mroommember
  * Under `third_party_invite`, `signed` is preserved. Rationale being that the `signed` block is required
    for the server to validate the event, however excess fields and `display_name` are not as important.
    Clients which are trying to represent a redacted `m.room.member` event with `third_party_invite` should
    not rely on `display_name` being present but rather state "Bob accepted a third party invite" or similar.

## Unstable prefix

Implementations looking to test these changes before adopted into a stable room version should use
`org.matrix.msc3821.opt1` as the room version, using v9 as a base and treating it as unstable.
