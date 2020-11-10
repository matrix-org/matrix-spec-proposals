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
it currently), the APIs, room versions, and the appendices (which are also currently unversioned). This
effectively makes the marketing version previously mentioned an actual version.

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

Structurally, the API documents remain mostly unchanged. We'll still have a client-server API, server-server
API, etc, but won't have versions associated with those particular documents. This also means they would
lose their individual changelogs in favour of a more general changelog. An exception to this rule is
room versions, which are covered later in this proposal.

The more general changelog would likely have sections for each API that had changes (client-server,
server-server, etc), likely indicating if a particular API had no changes between the release for
completeness - things like the push gateway API are only updated every couple years at best.

For the endpoints which are currently individually versioned, specifically everything except the client-server
API's endpoints, there are no changes. The most this MSC does is formalize that endpoints can have
per-endpoint versions to them, though this MSC does not attempt to define when/how those versions work.

For the client-server API in particular, some changes are needed. For backwards compatibility reasons,
servers which support the `rN` (`r0.6.1`, etc) series of versions still advertise them as normal. To
support the new Matrix versions, a server would add the version number of Matrix to the `/versions`
endpoint: `{"versions":["r0.5.0", "r0.6.0", "v1.1.0"]}`. Servers do not need to advertise every
patch version as there should not be any significant changes in patch versions. If a server supports
`v1.1.0`, it also supports `v1.1.7`, for example.

The endpoints themselves in the client-server API also get converted to per-endpoint versions, where
all the `/r0/` endpoints now become `/v1/`.

Room versions are a bit special in that they have their own version number and are required to have that
version number so they can be baked into a room/the protocol. This MSC doesn't propose dropping the
room version's specification on versioning, though does propose that the (un)stability of a given room
version is covered by this new Matrix version. This MSC also proposes changing the brewing mechanics
of how room versions are formed to better suit the proposed versioning plan.

**TODO: Brewing mechanics of room versions**

For grammar, the Matrix version follows semantic versioning. Semantic versioning is typically used for
software and not specification though, so here's how it translates:

* Major versions indicate that a breaking change happened *somewhere* in the specification. Because we'd
  be under a global version, a breaking change in the push gateway (for example) would mean a breaking
  change for all of Matrix. We will want to avoid incrementing this number as much as humanly possible.
  The endpoints are also versioned invidually, so typically a format change in an endpoint would actually
  be a minor version increase for Matrix.
* Minor versions indicate new features, endpoints, or other enhancements which are backwards compatible
  in nature. This is the number we strive to increase most often.
* Patch versions are when the changes are solely aesthetic, such as clarifications to the specification,
  spelling error fixes, styling/organizational changes, etc.

If accepted, this MSC will declare the spec as it is at the time as Matrix v1.1.0.

## Potential issues / alternatives

To be completed.

## Alternatives

To be completed.

## Security considerations

None relevant - if we need to make a security release for Matrix then we simply make a release and
advertise accordingly.

## Unstable prefix

It's not recommended by this MSC to implement this proposal before it lands in the specification, however
if an implementation wishes to do so then it can advertise `org.matrix.msc2844` in the `unstable_features`
section of `/versions`, and use `/_matrix/client/unstable/org.matrix.msc2844` in place of
`/_matrix/client/r0`.
