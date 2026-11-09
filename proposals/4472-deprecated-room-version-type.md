# MSC4472: Deprecated Room Version Kind

Currently only `stable` and `unstable` are stability types that can be advertised by servers in the
`m.room_versions` capability. This proposal introduces `deprecated` as a new kind, which can be used
to advertise that a room version is being sunset, and should no longer be used (predecessor for
[MSC4453: Deprecate old room versions][MSC4453]).

[MSC4453]: https://github.com/matrix-org/matrix-spec-proposals/pull/4453

## Proposal

Alongside `stable` and `unstable`, `deprecated` is added as a stability category. `deprecated`
should be treated the same as `unstable` (i.e. users should be discouraged from using them), but
with the following restrictions:

* `deprecated` room versions MUST NOT be the server's default room version.
* Clients that allow users to choose the room version when creating a room MUST NOT offer
  `deprecated` room versions as an option.
* Clients that allow users to choose the room version when upgrading a room MUST NOT offer
  `deprecated` room versions as an option.
* Clients SHOULD encourage users to upgrade rooms with a `deprecated` version.
  * In order to make a distinction between unstable support (potentially stable in the future), and
    deprecated (potentially removed in the future), clients SHOULD present a different message to
    users to what they would normally present for unstable rooms. For example, instead of
    "Your server administrator has marked this room version as unstable, some things may not work
    correctly", the room's limited future lifespan may be highlighted instead: "Your server
    administrator has marked this room version as deprecated and it may stop working in the future".

Servers SHOULD NOT mark room versions as *deprecated* unless they are also deprecated in the
[room versions][room-versions] specification, to prevent confusion between users of different
implementations.

[room-versions]: https://spec.matrix.org/unstable/rooms/

## Potential issues

Clients that do not understand this proposal may not make the correct distinction. Per
<https://spec.matrix.org/v1.18/rooms/#complete-list-of-room-versions>:

> Stable room versions may be used by rooms safely. Unstable room versions are everything else which
> is either not listed in the specification or flagged as unstable for some other reason.

Since `deprecated` is neither `stable` nor `unstable`, consumers are expected to treat `deprecated`
as `unstable` in this scenario. This means outdated clients may still offer deprecated room versions
to users, however the more important "users are encouraged to upgrade the room" functionality will
still happen, so the downside isn't major. [MSC4453] will allow servers to prevent the creation of
new deprecated rooms altogether, so this is seen as a growing pain more than a problem.

## Alternatives

The existing `unstable` type could continue to be used and re-used for deprecation, however this
does not easily allow clients to make the distinction between unstable support and room version
deprecation, which prevents them adequately guiding users into using newer room versions.

## Security considerations

None.

## Unstable prefix

While this proposal is unstable, `uk.timedout.msc4472.deprecated` should be used in place of
`deprecated`.

## Dependencies

None.
