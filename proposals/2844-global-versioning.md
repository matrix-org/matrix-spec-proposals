# MSC2844: Using a global version number for the entire specification

Currently we have 4 kinds of versions, all of which have slightly different use cases and semantics
which apply:

1. The individual API spec document versions, tracked as revisions (`r0.6.1`, for example).
2. Individual endpoint versioning underneath an API spec document version (`/v1/`, `/v2/`, etc). Note
   that the client-server API currently ties the major version of its spec document version to the
   endpoint, thus making most endpoints under it as `/r0/` (currently).
3. Room versions to freezing a set of behaviour and algorithms on a per-room basis. These are well
   defined in the spec and are not covered here: https://matrix.org/docs/spec/#room-versions
4. An overarching "Matrix" version, largely for marketing purposes. So far we've only cut Matrix 1.0
   back when we finalized the initial versions of the spec documents, but have not cut another one
   since.

This current system is slightly confusing, but has some drawbacks for being able to compile builds of
the spec documents (published on matrix.org) and generally try and communicate what supported versions
an implementation might have. For example, Synapse currently supports 4 different APIs, all of which
have their own versions, and all of which would need to be considered and compared when validating
another implementation of Matrix such as a client or push gateway. Instead, Synapse could say it
supports "Matrix 1.1", making compatibility much easier to determine - this is what this proposal aims
to define.

## Proposal

Instead of having per-API versions (`r0.6.1`, etc), we have a version that spans the entire specification.
This version represents versioning for the index (which has quite a bit of unversioned specification on
it currently), the APIs, room versions, and the appendices (which are also currently unversioned but
contain specification). Room versions are a bit more nuanced though, and are covered later in this MSC.

The version which covers the entire specification and all its parts is called the "Matrix version", and
is a promotion of the previously marketing-only version number assigned to the spec. Upon acceptance of
this MSC, the Matrix version would be 1.1.0. v1.0 from the marketing era would be recorded somewhere for
posterity, though largely has no significant meaning (unchanged by this MSC).

Doing this has the benefits previously alluded to:

* Implementations of Matrix can now easily compare their supported versions using a single identifier
  without having to (potentially) indicate which API they built support for.
* Publishing the specification is less likely to contain broken or outdated links due to API versions
  not matching up properly. This is currently an issue where if we want to release a new version of
  the server-server specification then we must also either rebuild or manually fix the blob of HTML
  known as the client-server API to account for the new version - we often forget this step, sometimes
  because it's just too difficult.
* Explaining to people what version Matrix or any of the documents is at becomes incredibly simplified.
  No longer will we have to explain most of what the introduction to this proposal covers to every new
  person who asks.

### Full Matrix version grammar

The Matrix versioning scheme takes heavy inspiration from semantic versioning, though intentionally does
not follow it for reasons described throughout this proposal. Primarily, the argument against semantic
versioning is held in the alternatives section below.

Given a version number `MAJOR.MINOR.PATCH`, incremement the:

* `MAJOR` version when a substantial change is made to the core of the protocol. This is reserved for
  interpretation by the Spec Core Team, though is intended to be for extremely invasive changes such
  as switching away from JSON, introducing a number of features where a `MINOR` version increase just
  doesn't feel good enough, or changes to the signing algorithms.
* `MINOR` version when a feature is introduced, or a backwards incompatible change has been managed
  through the specification. Later on, this proposal explains what it means to manage a breaking change.
* `PATCH` version when correctional changes are made, such as spelling, cosmetic, or other similarly
  small patches are done. Implementations do not need to worry about the patch version.

When present in the protocol itself, the Matrix version will always be prefixed with `v`. For example,
`v1.1.0`.

When a dash (`-`) is present after the `PATCH` version, the version is denoting some off-cycle release
information. This is how we'd, for example, make release candidates, alpha, beta, or unstable builds as
needed. This MSC does not propose a scheme for RCs or pre-releases, though the Spec Core Team may wish
to do so.

See the section on brewing Matrix versions for information on how the unstable version is decided.

From an implementation perspective, compatibility is guaranteed between `PATCH` versions. `MINOR` versions
have a backwards compatibility scheme described later in this proposal. `MAJOR` versions are expected
to have zero backwards compatibility guarantees to them.

For clarity, `v1.1.0` and `v1.1.8` are functionally the same. `v1.2.0` will probably work with `v1.1.0`,
though implementations should be wary if they depend on a version. As mentioned, the backwards compatibility
scheme section goes into more detail on this.

A potential argument is that we don't need a patch version if no implementation will ever care about it,
which is a valid argument to have. This MSC believes that although the patch version is effectively useless
to implementations, it is valuable as evidence of progress and finality of a given version. Going back to
edit already-released versions of the specification can be damaging to the integrity of the protocol,
and thus it is proposed by this MSC that the Spec Core Team remain accountable by forcing them to release
a with a patch version increase for minor, functionally indifferent, changes.

### Structure changes and changelogs

The API documents remain mostly unchanged. We'll still have a client-server API, server-server API, etc,
but won't have versions associated with those particular documents. This also means they would lose their
individual changelogs in favour of a more general changelog. An exception to this rule is room versions,
which are covered later in this proposal.

Though the changelog format is not covered by the MSC process, this MSC proposes that the initial
changelog for the Matrix versioning scheme be broken out into sections for each API that had changes.
Ideally, the changelog would also indicate if no changes were made to a particular API/area to help
be clearer to implementation authors. The Push Gateway API is, for example, likely going to be one
of the few which will nearly always say "No relevant changes" for years.

### Endpoint versioning

Under this MSC, all HTTP endpoints in the specification are to be per-endpoint versioned. This is already
the case for all APIs except the client-server API, and so this section deals specifically with that API.
The deprecation of endpoints is handled later in this proposal.

Under this proposal, all endpoints in the client-server API get assigned `v3` as their per-endpoint
version as a starting point. This is primarily done to avoid confusion with the ancient client-server API
versions which had `v1` and called the `rN` system "v2". Though many of the endpoints available today
are not present in those older API editions, it is still proposed that they start at `v3` to avoid
confusion with long-standing implementations.

Servers which are lucky enough exist during this versioning scheme change are expected to continue
supporting the `rN` system. This is done by advertising the existing client-server API versions as
they always would have on `/versions`, though appending `"v1.1.0"` to indicate that this MSC is
supported.

As a further clarification to an solved problem, the `/versions` endpoint for the client-server API
does not need to advertise all patch version changes - just the major/minor versions it supports.
If a server does advertise a patch version, clients are expected to resolve that to the relevant
major/minor version equivalent (`v1.1.8` gets treated as `v1.1.0`, for example).

### Brewing changes for the specification

Prior to this MSC, the Spec Core Team would release a given version of an API whenever it felt like
the right time to do so. There's very little planning put into a release, and often times the call to
cut a release is arbitrary. Though this MSC doesn't solve this problem neccesarily, it does change
the dynamic the Spec Core Team has with the community when it comes to releases.

Instead of arbitrarily deciding when to cut a release, the Spec Core Team is expected to plan ahead
and choose a date for the next major/minor release. The team is not required to use a cadence to
perform releases, though is expected to perform at least one release a year. Reasonable notice is
expected to be given to the community to give them a chance to push their MSCs and ideas to
completion. "Reasonable" is intentionally left undefined by this MSC as it might change over time,
though the current suggestion is to give at least 2 months notice. Most MSC authors are currently
contributing on a volunteer or spare time basis and thus might not be able to rapidly push their
ideas through the stages as quickly.

Patch releases do not require such notice and can happen whenever.

The date advertised to the community is a cutoff date, not a release date. The Spec Core Team and
wider community might still need time to write up the formal specification for some MSCs or improve
their implementations to be more prepared for the impending official release. In the eyes of the MSC
process, the cutoff date is *not* enough for an implementation to switch to using stable endpoints.

Considering these are only expectations and not requirements, the Spec Core Team might break them
from time to time for various reasons including urgent security releases, last minute realizations
that something might not work as proposed, etc. Under the Foundation, the Spec Core Team is required
to act in the best interest of the protocol and therefore should be able to reasonably justify why
an expectation is being broken at the time of breaking it - in no way does this MSC propose that
the Spec Core Team be able to blindside the community with a release for no justifiable reason.

To recap, the process is as follows:

1. Sometime after a given release happens, the Spec Core Team announces a cutoff date for MSCs to land
   that is at least 2 months in the future.
2. Upon cutoff, the Spec Core Team takes responsibility for ensuring all relevant changes are written
   up in a timely fashion.
3. The Spec Core Team makes the release. At this point, implementations can stop using unstable
   prefixes for any included MSC.

Because the release schedule is well-advertised, it should be clear to everyone what the next non-patch
version number will be. By default, the assumption can be made that the `MINOR` version will increase
by 1. For the purposes of producing built copies of the spec, the version number for unstable (unreleased)
versions shall be the next *expected* version number followed by `-unstable`. For example, if `v1.1.0`
were the current release, the unstable specification would be built as `v1.2.0-unstable`. In the event
that a change lands where the major version needs incremementing, `v1.2.0` (in this example) would never
see the light of day and instead turn into `v2.0.0-unstable`.

### Room versions & brewing room versions

*Author's note*: Having many things with the root word "version" can be confusing, so for this section
"room versions" are called "room editions" and the Matrix version refers to what this proposal is
introducing. This MSC does not propose renaming "room versions" - that is another MSC's problem.

Room editions are a bit special in that they have their own versioning scheme as other servers need to
be aware of how to process the room. As such, a room edition's versioning scheme is not altered by this
proposal, however the publishing of the (in)stability of a given edition is now covered by the newly
proposed Matrix version.

Whenever a room edition transitions from stable to unstable, or unstable to stable, or is introduced
then it would get counted as a feature for a `MINOR` release of Matrix. We don't currently have a plan
to remove any room editions, so they are not covered as a potential process for this MSC.

The brewing process for a room edition has typically been a last minute MSC to declare an edition number
and which other MSCs are included. This MSC proposes changing that slightly to instead allow accepted
MSCs to be batched up at release time into a new room edition. Each MSC will have needed testing and
implementation validation prior to their acceptance, so it should be fine to merge them together. If
a concern or conflict were to arise about doing so, an explicit MSC could be raised just like in today's
model where the conflicts/concerns are resolved. Such concerns might be the compatibility of the features,
and some conflicts might be two MSCs changing the same authorization rule (for example). The new, explicit,
MSC would require implementation validation and testing to be approved and thus would then be fine.

Though somewhat implicit, it might not be clear: multiple room editions can be included in a single Matrix
release, though how they get built is not really addressed by this MSC. Using the spirit of the ideas
proposed, it would likely mean as many MSCs as room editions to bring them into effect. This sort of
practice is believed to be extremely rare, however - it'd be more likely that the Spec Core Team uses
their capability to do an emergency release of Matrix to get a room edition into the wild rather than
brew two (or more) room editions at once.

The recommended default room edition is not automatically changed under this proposal either - changing
the recommended default requires an MSC just like any other part of Matrix and would fall under general
feature changes.

### Deprecation approach

This MSC doesn't change much about how things get deprecated, though it would be codified by this MSC.

An MSC is required to transition something from stable (the default) to deprecated. Once something has
been deprecated for suitably long enough, it is eligible for removal from the specification with another
MSC. Today's process is the same, though not defined explicitly.

Also not mentioned in today's system is that implementations are not required to implement deprecated
endpoints. This MSC also changes that and says that they do for versions in which they were deprecated
in. For example, if an endpoint was introduced in v1.1, deprecated in v1.2, and removed in v1.3 then
a server would have to implement the endpoint for v1.1 and v1.2 if it wanted to claim support for those
versions - v1.3 doesn't have the endpoint, so the endpoint's existence is not conditional for being
able to claim support for that version.

Generally deprecation is paired with replacement or breaking changes. For example, if `/v3/sync` were
to be modified such that it needed to be bumped to `v4`, the MSC which does so would deprecate `/v3/sync`
in favour of its proposed `/v4/sync`. Because endpoints are versioned on a per-endpoint basis, `/v4/sync`
will still work with a server that supports `/v3/profile` (for example) - the version number doesn't mean
an implementation can only use v4 endpoints.

### Supported versions schedule

Currently implementations are left to fend for themselves on deciding which versions of their APIs to
support. This MSC doesn't change this due to a wide variety of potential use cases for different
environments and older specifications, though this MSC does bring forth a guiding principle which is
applicable to most standard implementations.

Implementations are encouraged to support the latest version of Matrix as soon as feasibly possible,
and the two most recent `MINOR` versions past that. Given a cadence of about 1 release every 6 months,
this should mean that the standard implementation supports roughly 1.5 years worth of Matrix history.

Room versions are special in that they will essentially always be included in a Matrix release, even if
unstable. The current specification says that implementatiosn don't have to implement unstable room
versions, and this is true under this MSC too.

For extreme clarity, the suggested schedule for supported versions would be (all examples):

* v1.1.0 - Released in January 2019 - No support needed due to age.
* v1.2.0 - Released in July 2019 - Should be supported as part of the 1.2.x series.
* v1.2.5 - Released in August 2019 - Should be supported because it's part of the 1.2.x series.
* v1.3.0 - Released in December 2019 - Should be supported.
* v1.4.0 - Released in January 2020 - The current release so should definitely be supported.

## Potential issues

None appear to be relevant to be discussed on their own - they are discussed in their respective
sections above when raised.

## Alternatives

There are some strong opinions that we should use proper semantic versioning for the specification
instead of the inspired system proposed here. So, why shouldn't we use semantic versioning?

1. It's meant for software and library compatibility, not specifications. Though it could theoretically
   be used as a specification version, the benefits of doing so are not immediately clear. The scheme
   proposed here is simple enough where rudimentary comparisons are still possible between versions,
   and existing semantic versioning libraries can still be made to work. Further, the specification's
   version number should not be relied upon by a library for its versioning scheme - libraries,
   applications, etc should have their own versioning scheme so they may work independently of the
   spec's release schedule.

2. It has potential for causing very high major version numbers. Though largely an aesthetic concern,
   it can be hard to market Matrix v45 (or even Matrix v4) to potential ecosystem adopters due to
   the apparant unstable-ness of the specification. Similarly, the major version is used for advertising
   purposes which could be confusing or overly noisy to say there's a major version every few
   releases. By instead staying in the 1.x series for a long period of time, the specification appears
   stable and easy to work with, attracting potential adopters and making that 2.0 release feel all
   that more special.

3. The semantic versioning spec is not followed in practice. Most uses of semantic versioning are
   actually off-spec adaptations which are largely compatible with the ideals of the system. This, however,
   puts Matrix in a difficult spot as it would want to say we follow semantic versioning, but can't
   because there's no relevant specification document to link to. Even if there was, it would appear
   as though we were encouraging the idea of forking a specification as a specification ourselves,
   which may be confusing if not sending the wrong message entirely. Though the system proposed here
   is a reinvention of semantic versioning to a degree, this proposed system is different from how
   semantic versioning works in so many ways it is not entirely comparable.

4. The benefit of saying we use a well-popularized versioning system is not a strong enough argument
   to be considered here.

## Security considerations

None relevant - if we need to make a security release for Matrix then we simply make a release and
advertise accordingly.

## Unstable prefix

It's not recommended by this MSC to implement this proposal before it lands in the specification, however
if an implementation wishes to do so then it can advertise `org.matrix.msc2844` in the `unstable_features`
section of `/versions`, and use `/_matrix/client/unstable/org.matrix.msc2844` in place of
`/_matrix/client/r0`.
