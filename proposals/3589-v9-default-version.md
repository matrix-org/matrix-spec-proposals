# MSC3589: Room version 9 as a default

Enough time has passed to allow the public federation to upgrade their servers to support room
version 9, though with some caveats (see "potential issues"). This proposal aims to make v9 the
default room version.

## Proposal

The specification adopts v9 as the suggested default room version, making no changes to the stability
of any room versions. As of writing, v6 is currently the suggested room version.

Room version 9 is currently published here: https://spec.matrix.org/v1.2/rooms/v9/

## Potential issues

Servers will be encouraged to update their config/internal defaults to use v9 instead of v6. This
is considered a good problem to have.

Note that servers are not required to honour the default room version due to it being a suggestion
in the specification, however they might fall behind as other servers set their defaults accordingly.

Some server implementations, like Synapse, support configurable default room versions: servers which
have set this flag will not necessarily be affected by this change.

As of writing (Jan 26, 2022), some prominent server implementations are only just getting support for
the room version. Namely, Dendrite released a version with support about 2 months ago and Conduit is
working on including Ruma's changes which landed also about 2 months ago.

Though both Dendrite and Conduit (meaning Ruma) have not had the same amount of time as Synapse to
reach maturity on v9-capable versions, both the Dendrite and Conduit communities appear to update to
newer versions much more quickly. This implies, without statistics to back it up, that nearly all
Dendrite servers out there will have upgraded and that a similar percentage of Conduit servers will
upgrade once available.

No major issues appear to be reported to Synapse or Dendrite with respect to v9, however Conduit
has [reported](https://gitlab.com/famedly/conduit/-/merge_requests/257#note_814327701) that the auth
rules for v9 might not be perfect. All of this indicates to the author that the implementation is at
least sane and accomplishable, even if a bit difficult to incorporate.

For completeness, some links:

**Dendrite**:

* Tracking issue: https://github.com/matrix-org/dendrite/issues/2010
* Library support: https://github.com/matrix-org/gomatrixserverlib/pull/279
* Release: https://github.com/matrix-org/dendrite/commit/b4a007ecceafd2b93fee2e775b0a61283d4a3844
* Testing: https://github.com/matrix-org/complement/pull/220

**Conduit**:

* Tracking issue: https://gitlab.com/famedly/conduit/-/issues/161
* Library support: https://github.com/ruma/ruma/pull/771
* Release: N/A
* Testing: N/A

## Alternatives

None relevant.

## Security considerations

None relevant.

## Unstable prefix

None relevant - servers can already choose a different default room version legally. This MSC
just formalizes v9 as the default.
