# MSC4245: Immutable encryption algorithm

Enabling encryption in a room after it's been created works well for some encryption algorithms,
like Megolm in today's specification, but doesn't work well when aiming to support RFC 9420 MLS in
Matrix. Rooms using MLS will be required to change their authorization rules and possibly state
resolution behaviours, which could be breaking if a server misses the [`m.room.encryption`](https://spec.matrix.org/v1.13/client-server-api/#mroomencryption)
state event being sent. To avoid this situation, this proposal suggests that the encryption algorithm
can *optionally* be specified in the [`m.room.create`](https://spec.matrix.org/v1.13/client-server-api/#mroomcreate)
event instead, nullifying the `m.room.encryption` event's `algorithm` field.


## Proposal

When the `m.room.create` event's `content` contains an `encryption_algorithm` field, that encryption
algorithm MUST be used within that room. The `algorithm` field of `m.room.encryption` serves no purpose
in such rooms.

If the `m.room.create` event's `content` does not have an `encryption_algorithm`, the `m.room.encryption`
state event operates as per usual.

Other fields/properties of `m.room.encryption` are not modified by this proposal, such as key rotation
periods.

Note that an empty string, or unrecognized value, may be present in `encryption_algorithm`: this is
legal, and causes `m.room.encryption`'s `algorithm` to be ignored.


## Alternatives

None applicable


## Potential issues

From a security perspective, it's entirely possible that the `m.room.encryption` event's `algorithm`
is different from the `m.room.create`'s `encryption_algorithm`. Clients may (rightly) get confused
if they don't yet recognize `encryption_algorithm` in the create event, and use a less secure algorithm
in the room. Receiving clients may further accept these events and attempt to decrypt them instead
of rejecting due to the wrong algorithm being used. Or, worse, there are effectively two rooms going
on as half the participants only encrypt for their half of the room.

Solving this is tricky, and may require a room version bump with significant public information
campaigns to encourage client developers to adopt the change, once the MSC is accepted. The Spec Core
Team should consider rollout requirements prior to Final Comment Period of `merge` for this MSC.


## Security considerations

See potential issues.


## Dependencies

This MSC is not dependent on any other MSCs. [MSC4244](https://github.com/matrix-org/matrix-spec-proposals/pull/4244)
relies on the functionality introduced by this proposal. Others may additionally exist.


## Unstable prefix

While this proposal is not considered stable, implementations should use `org.matrix.msc4245.encryption_algorithm`
in the create event instead of `encryption_algorithm`. Developers should note that rooms created
using this unstable prefix may break when implementations drop support for the unstable prefix,
and not expose such rooms to production end users.
