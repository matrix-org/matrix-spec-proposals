# MSC4304: Room Version 12

A new room version, `12`, is proposed using [room version 11](https://spec.matrix.org/v1.15/rooms/v11/)
as a base and incorporating the following MSCs:

* [MSC4289](https://github.com/matrix-org/matrix-spec-proposals/pull/4289) - Explicitly privilege room creators
* [MSC4291](https://github.com/matrix-org/matrix-spec-proposals/pull/4291) - Room IDs as hashes of the create event
* [MSC4297](https://github.com/matrix-org/matrix-spec-proposals/pull/4297) - State Resolution v2.1

Though not technically required, [MSC4307: Validate `auth_events` are in the correct room](https://github.com/matrix-org/matrix-spec-proposals/pull/4307)
is explicitly included in this room version as well.

Other MSCs are capable of being included in this version, but they do not have sufficient implementation, acceptance,
and/or testing to be considered stable enough for v12 rooms. A future room version may still include them. Most
notable are:

* https://github.com/matrix-org/matrix-spec-proposals/pull/2870 - Lacking testing.
* https://github.com/matrix-org/matrix-spec-proposals/pull/2244 - Lacking implementation.

Room version 12 upon being added to the specification shall be considered stable. No other room versions
are affected by this MSC.

Typically, an MSC like this one which cuts a room version release would not be encouraged to make that same
room version the default for new rooms. Given the security context around the above MSCs however, this MSC
***does*** update the default room version to be v12 immediately. A wide variety of server implementations
already exist at the time of publishing this MSC, and major clients have been tested for compatibility with
the room version, though there are some noted incompatibilities expected.

As a result of those incompatibilities, servers are encouraged to exercise the "SHOULD" on the default room
version applied by the spec and deviate in the early days/weeks of v12's rollout. Once their respective
communities are better prepared, which may be a matter of days after publishing, servers SHOULD return back
to the default in the spec.

## Unstable prefix

Implementations looking to test v12 before written into the specification should use `org.matrix.hydra.11`
as the room version, treating it as unstable.

## Prior art

Room version MSCs are meant to be lightweight and fit a standard process. In backwards chronological
order, they are:

* https://github.com/matrix-org/matrix-spec-proposals/pull/4239 - Room version 11 (made default)
* https://github.com/matrix-org/matrix-spec-proposals/pull/3820 - Room version 11 (creation)
* https://github.com/matrix-org/matrix-spec-proposals/pull/3904 - Room version 10 (made default)
* https://github.com/matrix-org/matrix-spec-proposals/pull/3604 - Room version 10 (creation)
* https://github.com/matrix-org/matrix-spec-proposals/pull/3589 - Room version 9 (made default)
* https://github.com/matrix-org/matrix-spec-proposals/pull/3375 - Room version 9 (creation)
* https://github.com/matrix-org/matrix-spec-proposals/pull/3289 - Room version 8 (creation)
* https://github.com/matrix-org/matrix-spec-proposals/pull/2998 - Room version 7 (creation)
* https://github.com/matrix-org/matrix-spec-proposals/pull/2788 - Room version 6 (made default)
* https://github.com/matrix-org/matrix-spec-proposals/pull/2240 - Room version 6 (creation)
* https://github.com/matrix-org/matrix-spec-proposals/pull/2077 - Room version 5 (creation)
* https://github.com/matrix-org/matrix-spec-proposals/pull/2002 - Room version 4 (creation; made default [retroactively](https://github.com/matrix-org/matrix-doc/pull/2082))
* https://github.com/matrix-org/matrix-spec-proposals/pull/1943 - Room version 3 (made default; closed)
* https://github.com/matrix-org/matrix-spec-proposals/pull/1659 - Room version 3 (no-longer-standard inline creation)
* https://github.com/matrix-org/matrix-spec-proposals/pull/1759 - Room version 2 (creation)

Room version 1 was the first room version, released formally in https://github.com/matrix-org/matrix-doc/pull/1773 (~r0.5.0, "Matrix 1.0", June 2019)
