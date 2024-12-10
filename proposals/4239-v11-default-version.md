# MSC4239: Room version 11 as the default room version

[Room version 11](https://spec.matrix.org/v1.12/rooms/v11/) was introduced in Matrix 1.8 back in
August 2023. The room version is a light cleanup from [room version 10](https://spec.matrix.org/v1.12/rooms/v10/),
particularly around the redaction algorithm. There are no other major changes.

Over the last year since release, the expectation was that there might be a room version 12 in quick
succession, however as is tradition for any expectation, things changed. This proposal bumps the
[default suggested room version](https://spec.matrix.org/v1.12/rooms/#complete-list-of-room-versions)
from version 10 to version 11, bringing the redaction algorithm cleanup to the wider ecosystem.

## Proposal

The specification adopts room version 11 as the suggested default room version. No stability status
changes are made to any room version.

## Potential issues

Some servers may not have updated to support version 11 yet, though many servers support version 10.
The delta between the versions is minimal.

## Alternatives

No relevant alternatives.

## Security considerations

No relevant security considerations (they would have been made in [MSC3820](https://github.com/matrix-org/matrix-spec-proposals/pull/3820)).

## Unstable prefix

No relevant prefix - servers can already choose a different default room version. This MSC formalizes
the default.

## Dependencies

No outstanding blockers are listed.

## Prior art

* https://github.com/matrix-org/matrix-spec-proposals/pull/3904 - Room version 10 to default (released in Matrix 1.6, February 2023)
* https://github.com/matrix-org/matrix-spec-proposals/pull/3589 - Room version 9 to default (released in Matrix 1.3, June 2022)
* https://github.com/matrix-org/matrix-spec-proposals/pull/2788 - Room version 6 to default (released in Matrix 1.1(?), November 2021)
* https://github.com/matrix-org/matrix-spec-proposals/pull/2334 - Room version 5 to default (released in r0.6.0, November 2019)
* https://github.com/matrix-org/matrix-spec-proposals/pull/2002 - Room version 4 to default (released ~r0.5.0, "Matrix 1.0", June 2019)
* https://github.com/matrix-org/matrix-spec-proposals/pull/1943 - Room version 3 to default (closed in favour of version 4)

Note: Room versions 2, 3, 7, and 8 were never adopted as the default room version. Version 1 was the original room version,
released formally in https://github.com/matrix-org/matrix-doc/pull/1773 (~r0.5.0, "Matrix 1.0", June 2019).
