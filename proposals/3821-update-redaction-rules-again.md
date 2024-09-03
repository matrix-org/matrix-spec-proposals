# MSC3821: Update redaction rules, again

[MSC2176](https://github.com/matrix-org/matrix-spec-proposals/pull/2176) aimed to fix inconsistencies
with the [redaction algorithm](https://spec.matrix.org/v1.6/rooms/v10/#redactions) where server-side
event auth required properties to exist that were being removed. While MSC2176 fixed a number of cases,
one was unfortunately missed.

This MSC aims to fix that missing case, originally identified long ago by [synapse#1831](https://github.com/matrix-org/synapse/issues/1831).

## Proposal

*Note*: It is recommended to read [MSC2176](https://github.com/matrix-org/matrix-spec-proposals/pull/2176)
before this proposal as MSC2176 contains a lot of backing context.

In a future room version, the following changes are made to the [redaction algorithm](https://spec.matrix.org/v1.6/rooms/v10/#redactions).
Note that this requires a new room version because changing the redaction algorithm changes how
[event IDs](https://spec.matrix.org/v1.6/rooms/v10/#event-ids) are calculated, as they are
[reference hashes](https://spec.matrix.org/v1.6/server-server-api/#calculating-the-reference-hash-for-an-event)
which redact the event during calculation.

* [`m.room.member`](https://spec.matrix.org/v1.6/client-server-api/#mroommember) events preserve a portion
  of `third_party_invite` under `content`, if present. Those properties being:

  * `signed`: the block is required for the server to validate the event, however excess adjacent properties
    such as `display_name` are not important.

Clients should note that because `display_name` is *not* preserved during redaction they might need to change
how that event is rendered/presented to users. For example, when rendering such a redacted event the client
might show it as "Bob accepted a third party invite".

## Unstable prefix

Implementations looking to test these changes before adopted into a stable room version should use
`org.matrix.msc3821.opt1` as the room version, using **v9** as a base and treating it as unstable.

**History**: This MSC was originally written before room version 10 existed. Implementations wishing to use
v10 as a base instead of v9 should use `org.matrix.msc3821.opt1.v10` as the room version instead.
