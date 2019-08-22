# MSC2240: Room Version 6

A new room version, `6`, is proposed using [room version 5](https://matrix.org/docs/spec/rooms/v5.html)
as a starting point and incorporating the following MSCs:

* [MSC2174](https://github.com/matrix-org/matrix-doc/pull/2174) - Moving the `redacts` key.
* [MSC2175](https://github.com/matrix-org/matrix-doc/pull/2175) - Removing the `creator` from create events.
* [MSC2176](https://github.com/matrix-org/matrix-doc/pull/2176) - Modern redaction rules.
* [MSC2209](https://github.com/matrix-org/matrix-doc/pull/2209) - Including notifications in power level auth rules.
* [MSC2212](https://github.com/matrix-org/matrix-doc/pull/2212) - Third party user power levels.
* [MSC2213](https://github.com/matrix-org/matrix-doc/pull/2213) - Rejoinability of invite-only rooms.
* [MSC1849](https://github.com/matrix-org/matrix-doc/pull/1849) - Event aggregations/relationships.

MSCs which require a new room version and are excluded from v6 are:
* [MSC2214](https://github.com/matrix-org/matrix-doc/pull/2214) - Joining upgraded private rooms.
  This MSC is excluded due to the solution not being fully worked out. As this v6 proposal progresses,
  it is possible for it to be included in the future.


Room version 6 upon being added to the specification shall be considered stable. No other room versions
are affected by this MSC.
