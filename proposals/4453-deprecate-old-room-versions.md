# MSC4453: Deprecate old room versions

As Matrix has evolved, so has its capabilities. In order to indicate feature support, rooms are
tagged with *versions*, which servers must claim support for in order to participate in. Currently,
there are 12 stable room versions (v1 through v12) listed as "stable" by the specification. However,
many of these versions are not suitable for modern Matrix projects due to assumptions that no longer
hold true, and behaviours that may be difficult or impossible to replicate in new projects.

This proposal will deprecate room versions 1 through 9, disallowing their creation once implemented,
but not affecting existing rooms using these versions.

## Proposal

Deprecating room versions that are no longer suitable will allow the ecosystem to progress faster,
in a less buggy manner, as new projects will not have to implement potentially unstable support for
older room versions. As such, this proposal will deprecate all room versions before v10.

As for what "deprecation" means in this context, jump to the relevant section:

- Client developers: [§ For client implementations](#for-client-implementations)
- Server developers: [§ For server implementations](#for-server-implementations)

### Justification

The rationale for deprecating pre-v10 rooms can generally be summarised as:

- Rooms version 9 and below permit
  [string values](https://github.com/matrix-org/matrix-spec-proposals/pull/3667) in power levels,
  which causes problems for implementations not written in Python (example of a new issue caused by
  this in 2026: <https://github.com/matrix-org/matrix-spec/issues/2314>)
- Rooms version 5 and below do not enforce
  [canonical JSON](https://spec.matrix.org/unstable/rooms/v6/#canonical-json), which means
  interoperability relies on the sender always using canonical JSON first. This also means really
  old rooms may have valid events that are not in canonical form, and new implementations may not
  be able to use these rooms safely.
- Room version 4 does not enforce signing key validity, meaning events may be forged by compromised
  signing keys.
- Room version 3 does not use URL-safe event IDs, which may be problematic for some clients, and may
  cause request signature errors due to some reverse proxy behaviours.
- Room version 2 and below use opaque event IDs, which can be spoofed. These room versions also use
  union types for `auth_events` and `prev_events` in PDUs, which introduces additional complexity
  for languages that don't support typing `[[string|object<string, string>]]`.
- Room version 1 uses a state resolution algorithm that has known exploits that make it unsafe to
  expose to federation.

Due to all of the above, I propose room version 10 as a sensible cutoff. Modern room
versions also have problems (notably, v10 does not protect `m.room.create` from redaction,
v11 is prone to state resets when federation is involved, v12 less so), but more importantly, are
fairly consistent, and have significantly stronger interoperability guarantees than their
predecessors.

There are also relatively few rooms using v9 or older, and those that are, are typically planning to
upgrade eventually. From a sample of 6005 rooms kindly provided by `maunium.net` on 2026-04-21:

| Room version | Room count (total) | No. tombstoned |
| ------------ | ------------------ | -------------- |
| 12           | 260                | 13 (5.0%)      |
| 11           | 694                | 42 (6.0%)      |
| 10           | 2138               | 64 (3.0%)      |
| 9            | 979                | 53 (5.4%)      |
| 8            | 18                 | 4  (22.2%)     |
| 7            | 7                  | 3  (42.9%)     |
| 6            | 1195               | 62 (5.2%)      |
| 5            | 418                | 76 (18.2%)     |
| 4            | 138                | 18 (13.0%)     |
| 3            | 16                 | 9  (43.7%)     |
| 2            | 2                  | 1  (50.0%)     |
| 1            | 332                | 89 (27.0%)     |

*Note: 8 entries in the data set had an empty room version, which is treated as v1*

N.B: More data points are accepted with open arms. Highlighting the number of rooms that have been
used (i.e. had a new non-membership event sent) in the past year would also be a very nice data
point.

### For server implementations

As part of the deprecations, servers MUST mark supported versions v1 through v9 as *unstable* in the
`m.room_versions` capability. This will signal to clients that the room version is now deprecated,
and may allow them to prompt administrators to upgrade the room to a new version.

In order to prevent people creating *new* deprecated rooms, the server MUST refuse to create new
rooms with deprecated room versions with the error code `400 / M_UNSUPPORTED_ROOM_VERSION`. In order
to disambiguate between an actually unsupported room version vs a deprecated one, the server MAY
choose to return a different error *message*, such as "this room version is too old". Servers
MUST NOT allow a configuration that sets their default room version to one below version 10.

In order to not impact rooms still of deprecated versions, servers MUST NOT refuse to join or
participate in rooms of deprecated versions they still support.

Appservices MUST NOT be allowed to bypass this restriction, no matter how nicely they ask.

### For client implementations

Per the above, as servers will now advertise deprecated room versions as *unstable*, clients SHOULD
present a prominent notice to users who have the `m.room.tombstone` power level that the room
version is now unstable, and provide them with the option to upgrade. In order to alleviate some of
the concerns in [potential issues](#potential-issues), clients SHOULD also provide links to
resources that explain room upgrades, such as
<https://matrix.org/docs/communities/administration/#room-upgrades>, in order to encourage the weary
to take the leap.

Clients MUST NOT offer rooms version 1 through 9 as options when creating a room, if a UI for
version selection is presented to the user. The server will enforce this restriction anyway.

## Potential issues

After discussing with several communities, a few patterns were identifiable that prevented them
upgrading their rooms, such as:

- Not sure how to (client inconsistencies). "I thought it would do that automatically" was mentioned
  a couple times.
- Not sure why they should ("it works on my machine", and "it doesn't work for the non-majority"
  didn't outweigh the inconvenience of upgrading), or not sure what it even *does*.
- Don't have an available administrator to perform the upgrade.
- Friction regarding tooling (e.g. would have to re-configure a bunch of bots/bridges).
- Bad experiences with previous upgrades leading to apprehension.

Hopefully the first two problems can be alleviated by improved client implementations, as outlined
by [§ For client implementations](#for-client-implementations). Not having an available
administrator is unavoidable. Hopefully, with this deprecation in place, the ecosystem will stop
being reluctant to bother to support new versions, and will inherently improve accordingly. Bad
room upgrade UX is a well known pain and will be addressed by other proposals.

## Alternatives

None considered at this time. This proposal is solely to *deprecate* these room versions, not remove
them, so alternatives are not particularly relevant.

A question frequently received when writing this proposal is generally along the
lines of "well why not anything below v12?", or "why not wait until v13 and then anything below
that?". Readers are encouraged to skim over [§ Justification](#justification) again - v10 is a very
common room version that coincidentally also has significantly stronger interoperability capability
than its predecessors.

## Security considerations

None considered at this time, for the same reasons as outlined above.

## Unstable prefix

No unstable prefix applies to this proposal.

## Dependencies

This proposal has no dependencies.
