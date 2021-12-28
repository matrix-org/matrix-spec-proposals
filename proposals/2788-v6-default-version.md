# MSC2788: Room version 6 as a default

Enough time has passed to allow the public federation to upgrade their servers to support room
version 6. This proposal aims to make v6 the default room version.

## Proposal

The specification adopts v6 as the suggested default room version, making no changes to the stability
of any room versions. As of writing, v5 is currently the suggested room version.

Room version 6 has the following specification: https://matrix.org/docs/spec/rooms/v6

## Potential issues

Servers will be encouraged to update their config/internal defaults to use v6 instead of v5. This
is considered a good problem to have.

## Alternatives

None relevant.

## Security considerations

None relevant.

## Unstable prefix

None relevant - servers can already choose a different default room version legally. This MSC
just formalizes v6 as the default.
