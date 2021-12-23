# MSC3589: Room version 9 as a default

Enough time has passed to allow the public federation to upgrade their servers to support room
version 9. This proposal aims to make v9 the default room version.

## Proposal

The specification adopts v9 as the suggested default room version, making no changes to the stability
of any room versions. As of writing, v6 is currently the suggested room version.

Room version 9 does not currently have a published specification, though the details are recorded at
https://github.com/matrix-org/matrix-doc/pull/3387

## Potential issues

Servers will be encouraged to update their config/internal defaults to use v9 instead of v6. This
is considered a good problem to have.

Prominent server implementations besides Synapse have partial or no support for v9. Namely, Conduit
is lacking support and Dendrite appears to have most of an implementation but is not complete. For
these projects, and other servers in the wild, it is encouraged that implementation progresses to
support v9 fully.

Note that servers are not required to honour the default room version due to it being a suggestion
in the specification, however they might fall behind as other servers set their defaults accordingly.

Some server implementations, like Synapse, support configurable default room versions: servers which
have set this flag will not necessarily be affected by this change.

## Alternatives

None relevant.

## Security considerations

None relevant.

## Unstable prefix

None relevant - servers can already choose a different default room version legally. This MSC
just formalizes v9 as the default.