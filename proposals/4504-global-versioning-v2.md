# MSC4504: Using a global version number for the entire specification (v2)

**Note**: This proposal changes process rather than specification. It may be tested in production
ahead of formal acceptance under the supervison of the Spec Core Team.

[MSC2844](https://github.com/matrix-org/matrix-spec-proposals/pull/2844) ([merged](https://github.com/matrix-org/matrix-doc/blob/master/proposals/2844-global-versioning.md))
introduced the [modern vX.Y versioning scheme](https://spec.matrix.org/v1.19/#specification-versions)
used by the specification today. Unifying the spec under a single version has certainly helped simplify
the release process and clarify what makes up a "spec release". 18 quarterly releases have happened
under this scheme so far, spanning about 4.5 years.

The versioning scheme however has revealed at least two notable problems:

1. When we're removing something from the spec, we can't practically remove it from implementations.
   Implementations continue to support old versions of the specification, sometimes to extremes, which
   means they *always* need to support the newly-removed functionality to avoid breaking those older
   clients.

   Some servers, like Synapse, have never dropped support for an older spec version. The specification
   could ask/require servers to drop support for old specification versions so they can also remove
   features - this might not be desirable to the server implementations which *don't* want to remove
   functionality earlier than their local ecosystems are ready for.

2. Similarly, clients are effectively asked to verify support for an ever-increasing range of spec
   versions. They can't reasonably assume that v1.2 is going to be compatible with v1.1 due to the
   semver-incompatible versioning scheme, so they must test (or read the changelog of) v1.2 to ensure
   their client is compatible. If it is compatible, they can search for that spec version among a list
   of other "acceptable" spec versions.

   **Note**: Some clients have chosen to go with a "minimum" spec version, even when demonstrating
   the implementation of MSC2844, which [causes problems](https://github.com/matrix-org/matrix-js-sdk/issues/3915).
   If a client searches for a minimum spec version, it's list of "acceptable" versions is effectively
   one. If a server doesn't support that specific version, the client can't connect.

   When a client stops updating its acceptable spec versions it can also cause problems. If a new
   server implementation enters the ecosystem or an existing implementation finally decides to drop
   support for "ancient" spec versions, clients might find themselves unable to connect as well. This
   can happen even if the client is well maintained: the client developers simply need to forget to
   update their "acceptable" spec versions list for a few spec releases.

A natural solution to these problems may be to break the spec down into smaller pieces then have
servers and clients "negotiate" compatibility of those smaller pieces. This can lead to fragmentation
in the ecosystem, so we do not do that in this proposal. Instead, we give clients predictable version
numbers to expect removals in, and remind clients that they should be tolerant to errors when endpoints
are removed from under them.

This approach is preferred to maintain the SCT's ability to also decide when and how to pick the next
version number for the spec. In a traditional semver setup, the spec might see version numbers like
`v37.4.556`. Those version numbers are often suitable for software, but can be challenging to communicate
to the general public internet regarding Matrix as a project/specification.


## Proposal

Clients MUST tolerate the [`404 M_UNRECOGNIZED`](https://spec.matrix.org/v1.19/client-server-api/#common-error-codes)
error on *all* endpoints. In some cases this might mean the client synthesizes a [soft logout](https://spec.matrix.org/v1.19/client-server-api/#soft-logout)
for the user because the client is unable to continue working. For example, receiving `404 M_UNRECOGNIZED`
on [`/sync`](https://spec.matrix.org/v1.19/client-server-api/#get_matrixclientv3sync) would prevent
most clients from operating at all, so they might need to get the user to a screen where the client
wouldn't continue encountering errors.

Where removals or sufficiently breaking changes happen to events or rooms, clients will need to be
differently aware of their compatibility. Proposals like [MSC4292](https://github.com/matrix-org/matrix-spec-proposals/pull/4292)
attempt to address that as a distinct problem case.

Removals from the specification MUST only happen when the `Y` (`vX.Y`) version is divisible by 6.
Implementations can (and SHOULD) also remove functionality when they support such a spec version.
This is done to reduce the number of specification versions that clients need to check compatibility
for - they can assume that any spec release is compatible with the 5 prior at a minimum.

To add a time component to the above condition, the SCT MUST NOT release more than 4 `Y` versions and
1 `X` version in a calendar year. When these releases happen precisely within the year and what they
contain remains an SCT process implementation detail. However, the SCT SHOULD spread releases out over
the calendar year to avoid breaking assumptions regarding time. For clarity: fewer releases are
permitted. This allows the SCT to retain its current "roughly quarterly" release schedule, and have
one additional "featured" release (v2.0, etc) per year.

**Note**: Because a bump to `X` resets `Y` to `0`, any `X` release MAY contain removals. While still
not perfectly semver compatible, the general spirit is maintained.

MSCs which remove functionality can be *accepted* into the spec at any time, however the release which
formalizes the removal MUST happen when `Y` is divisible by 6.

These conditions allow for approximately 1.5 years worth of compatibility in clients. Features might
be *added* in that time, but they cannot be *removed* early.

The rules on deprecation before removal are unchanged by this proposal: at least one spec release
MUST happen before something can be removed. The deprecation release does *not* need to be divisible
by 6 - it can be any release. It is generally encouraged to wait several releases before removing
something from the spec, however.


## Potential issues

Needing to wait 5 releases or 1.5 years to remove something from the spec isn't great, though it's
not often that something gets removed from the spec anyway. Looking ahead, the number of features
which might be proposed for removal is also sufficiently small where 5 releases worth of time would
likely cover the review of their relevant MSCs:

* Removing legacy media endpoints. [MSC4249](https://github.com/matrix-org/matrix-spec-proposals/pull/4249)
  has already been open for 1.5 years as of writing, and can likely go through FCP quickly if needed.

* Removing room versions 1 through 9. [MSC4453](https://github.com/matrix-org/matrix-spec-proposals/pull/4453),
  though newer than MSC4249, already sets the ball rolling on eventual removal. Later, when rooms
  have had further chances to upgrade, servers might be able to start dropping support for those
  already-ancient room versions.

* Removing query string authentication. [MSC4127 (accepted)](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/4127-remove-query-string-auth.md)
  has already invoked the removal clause from the spec, 2 years after [MSC4126 (merged)](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/4126-deprecate-query-string-auth.md)
  landed.

Clients are also still required to maintain an "acceptable versions" list, though they can also
hardcode a wider lower bound of acceptable versions using the "divisible by 6" characteristic above.

Clients might further assume or implement version checking as though spec releases are semver compatible.
This proposal does not attempt to solve this particular issue, but hopes that its presence in the
proposal queue brings further awareness to the versioning system's actual properties. A future MSC
may introduce proper semver mechanics.


## Alternatives

Mentioned in the introduction, we could break the spec down into components then either version them
or advertise feature flag support for them. This is undesirable because it enables too much optionality
in particularly server implementations: it's the protocol's intention to be heavily consistent on what
is available so *any* client can work with that server.

We could also adopt dated release versions instead, like `26.1`, to indicate an "API level" compatibility.
Some platforms use this successfully, like Stripe, though it can mean that the platform (Matrix server)
needs to retain support for older versions indefinitely because clients rarely upgrade their API level.
This proposal also avoids breaking the version string format (again), which dated releases might cause.

A third option would be to label certain releases as Long-Term Stable (LTS) releases. Such a schedule
could allow for non-LTS releases to potentially make more breaking changes, but might carry higher
administrative burden to operate or determine the impact to server implementations. This proposal
still introduces the essence of LTS releases to the spec, but does not call them LTS releases because
the intermediary releases are requried to be compatible with the last "LTS" release.

Finally, we could require implementations to drop old spec versions on a schedule. As the introduction
mentions, this would potentially cause issues within local server ecosystems where they're not ready
to actually go forward with removal yet. For example, a server might be respecting an LTS contract
and therefore cannot comply with the spec's requirement to drop support for an N-year-old version. Or,
a server project might simply be aware that their users often use a client which still works fine
despite advancements in the spec, so they'd like to keep supporting the few things that client needs
to work.


## Security considerations

Though rare, the SCT might need to make a security release. Placing a limitation on the number of
spec releases the SCT is allowed to cut might interfere with the ability to put out a security
release. In practice, security releases at the spec level are usually heavily coordinated and would
not require an additional release slot in the year. In the event the SCT does need an additional
release within the year though, the SCT MAY take budget from future years to cut the necessary
release(s). For example, if the SCT has already cut 4 releases in the year and needs to make a 5th,
they can provided they only do 3 releases next year. At all times, the SCT SHOULD maintain the
"approximately 1.5 years for 6 releases to happen" assumption in this proposal.


## Unstable prefix

While this proposal is not considered stable, only the SCT MAY implement it. Clients and servers
wanting to assist the SCT in measuring this proposal's effectiveness MUST coordinate with the SCT
prior to implementation.

This means that nothing changes for clients or servers until this proposal is accepted. Clients still
need to check compatibility with all spec releases, and servers cannot remove functionality unless
they also drop the old spec versions which still have those features in them.

The SCT MAY modify all aspects of this proposal to assist in measuring effectiveness. For example,
starting the "every 6th release" counter at a specific number rather than one which is divisible by 6.

Clients SHOULD consider implementing the `404 M_UNRECOGNIZED` behaviour regardless of this proposal's
acceptance. Errors of any variety can happen at any time, and `404 M_UNRECOGNIZED` is a reasonable
error code to encounter in the wild (as is `500 M_UNKNOWN`).

It's expected that the first removal-containing release after this MSC is merged to the spec will be
at least 6 months later. This is to give time for implementations to discover the new requirements
and adapt accordingly. That release MAY be out of cycle (ie: not divisble by 6), but MUST be the last
out of cycle release until the process is changed by another MSC. If that release is out of cycle,
that fact SHOULD be advertised to developers during the minimum 6 month time period.


## Dependencies

This proposal has no direct dependencies.
