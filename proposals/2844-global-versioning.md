# MSC2844: Using a global version number for the entire specification

Currently we have 4 kinds of versions, all of which have slightly different use cases and semantics
which apply:

1. The individual API spec document versions, tracked as revisions (`r0.6.1`, for example).
2. Individual endpoint versioning underneath an API spec document version (`/v1/`, `/v2/`, etc). Note
   that the client-server API currently ties the major version of its spec document version to the
   endpoint, thus making most endpoints under it `/r0/` (currently).
3. Room versions which define a set of behaviour and algorithms on a per-room basis. These are well
   defined in the spec and are not covered here: https://spec.matrix.org/unstable/rooms/
4. An overarching "Matrix" version, largely for marketing purposes. So far we've only cut Matrix 1.0
   back when we finalized the initial versions of the spec documents, but have not cut another one
   since.

This current system is slightly confusing, and has some drawbacks for being able to compile builds of
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
is a promotion of the previously marketing-only version number assigned to the spec. The first version
after this proposal is expected to be Matrix 1.1, though the spec core team will make that decision.
v1.0 would be left in the marketing era and recorded for posterity (though still retains no significant
meaning).

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

Given a version number `MAJOR.MINOR`, incremement the:

* `MAJOR` version when a substantial change is made to the core of the protocol. This is reserved for
  interpretation by the Spec Core Team, though is intended to be for extremely invasive changes such
  as switching away from JSON, introducing a number of features where a `MINOR` version increase just
  doesn't feel good enough, or changes to the signing algorithms.
* `MINOR` version when a feature is introduced, or a backwards incompatible change has been managed
  through the specification. Later on, this proposal explains what it means to manage a breaking change.

When present in the protocol itself, the Matrix version will always be prefixed with `v`. For example,
`v1.1`.

Additional information can be supplied in the version number by appending a dash (`-`) to the end of the
version and including any relevant information. This is typically used to denote alpha, beta, unstable,
or other similar off-cycle release builds. This MSC does not propose a scheme for RCs or pre-releases,
though the Spec Core Team may wish to do so. This can also be used to represent patch builds for the
documentation itself, such as correcting spelling mistakes. An example would be `v1.1-patch.20210109`.

See the section on brewing Matrix versions for information on how the unstable version is decided.

`MINOR` versions have a backwards compatibility scheme described later in this proposal. `MAJOR`
versions are expected to have zero backwards compatibility guarantees to them.

For clarity, `v1.2` will probably work with `v1.1`, though implementations should be wary if they
depend on a version. As mentioned, the backwards compatibility scheme section goes into more detail on
this.

Most notably, this MSC does not propose including a patch version at all. The specifics of what would
be included in a patch version (spelling changes, release process bug fixes, etc) do not impact any
implementations of Matrix and thus are not needing of a patch version.

### Structure changes and changelogs

The API documents remain mostly unchanged. We'll still have a client-server API, server-server API, etc,
but won't have versions associated with those particular documents. This also means they would lose their
individual changelogs in favour of a more general changelog. An exception to this rule is room versions,
which are covered later in this proposal.

### Endpoint versioning

Under this MSC, all HTTP endpoints in the specification are to be per-endpoint versioned. This is already
the case for all APIs except the Client-Server API, and so this section deals specifically with that API.
The deprecation of endpoints is handled later in this proposal.

Under this proposal, all endpoints in the client-server API get assigned `v3` as their per-endpoint
version as a starting point. This is primarily done to avoid confusion with the ancient client-server API
versions which had `v1` and called the `rN` system "v2". Though many of the endpoints available today
are not present in those older API editions, it is still proposed that they start at `v3` to avoid
confusion with long-standing implementations.

Servers would advertise support for the new Matrix version by appending it to the array in `/versions`.
If the sever also supports an older `rN` version, it would include those too.
For example: `["v1.1", "r0.6.1"]`.

### Room versions

*Author's note*: Having many things with the root word "version" can be confusing, so for this section
"room versions" are called "room editions" and the Matrix version refers to what this proposal is
introducing. This MSC does not propose renaming "room versions" - that is another MSC's problem.

Room editions are a bit special in that they have their own versioning scheme as servers and, potentially,
clients need to be aware of how to process the room. As such, a room edition's versioning scheme is not
altered by this proposal, however the publishing of the (in)stability of a given edition is now covered by the
newly proposed Matrix version.

Whenever a room edition transitions from stable to unstable, or unstable to stable, or is introduced
then it would get counted as a feature for a `MINOR` release of Matrix. We don't currently have a plan
to remove any room editions, so they are not covered as a potential process for this MSC.

### Deprecation approach

Previous to this proposal the deprecation approach was largely undocumented - this MSC aims to codify
a standardized approach.

An MSC is required to transition something from stable (the default) to deprecated. Once something has
been deprecated for suitably long enough (usually 1 version), it is eligible for removal from the
specification with another MSC. Today's process is the same, though not defined explicitly.

The present system for deprecation also allows implementations to skip implementation of deprecated
endpoints. This proposal does not permit such behaviour: for an implementation to remain compliant
with the specification, it must implement all endpoints (including deprecated ones) in the version(s)
it wishes to target.

As an example, if `/test` were introduced in v1.1, deprecated in v1.2, and removed in v1.3 then an
implementation can support v1.1, v1.2, and v1.3 by implementing `/test` as it was defined in v1.2 (minus
the deprecation flag). If the implementation wanted to support just v1.2 and v1.3, then it still must
implement `/test`. If the implementation only wanted to support v1.3, then it *should not* implement
`/test` at all because it was removed.

Generally deprecation is paired with replacement or breaking changes. For example, if `/v3/sync` were
to be modified such that it needed to be bumped to `v4`, the MSC which does so would deprecate `/v3/sync`
in favour of its proposed `/v4/sync`. Because endpoints are versioned on a per-endpoint basis, `/v4/sync`
will still work with a server that supports `/v3/profile` (for example) - the version number doesn't mean
an implementation can only use v4 endpoints.

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
   the apparent unstable-ness of the specification. Similarly, the major version is used for advertising
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

This MSC is also inherently incompatible with semantic versioning due to its approach to deprecation.
Instead of encouraging breaking changes (removal of endpoints) be major version changes, this MSC
says that happens at the minor version change level. As mentioned in the relevant section, this is
not foreseen to be an issue for Matrix given its a system already used by the protocol and is common
enough to at least be moderately familiar - the arguments for using semantic versioning in this respect
do not hold up, per above.

## Security considerations

None relevant - if we need to make a security release for Matrix then we simply make a release and
advertise accordingly.

## Unstable prefix

The author does not recommend that this MSC be implemented prior to it landing due to the complexity
involved as well as the behavioural changes not being possible to implement. However, if an implementation
wishes to try anyways, it should use `org.matrix.msc2844` in the `unstable_features` of `/versions`
and use `/_matrix/client/unstable/org.matrix.msc2844` in place of `/_matrix/client/r0`.

This MSC is largely proven as possible through an in-development build of the specification which uses
an alternative toolchain for rendering the specification: https://adoring-einstein-5ea514.netlify.app/
(see the 'releases' dropdown in the top right; link may not be available or even the same as described
here due to development changes - sorry).
