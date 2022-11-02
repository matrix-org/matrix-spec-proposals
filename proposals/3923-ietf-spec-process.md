# MSC3923: Bringing Matrix into the IETF process

With the formation of the More Instant Messaging Interoperability (MIMI) working group within the
IETF, Matrix has a strong interest in getting involved to describe the federation API and event
schema as core pieces for solving the working group's area of concern. This interest raises concerns
about how rapid prototyping and development would work in relation to a naturally slower IETF process,
namely whether moving parts of Matrix into the IETF space would cause Matrix to be "frozen" or unable
to change. 

This proposal aims to cover an approach where we support a version of Matrix which can be slower to
make progress on, alongside a version that can make more invasive or experimental changes, without
forking. This proposal additionally covers how the Matrix spec process is affected, particularly as
it relates to the areas being proposed for MIMI's area of concern.

## Proposal

Currently the only areas in scope for proposing for MIMI are the Federation API (server-server spec),
a selected Room Version, and schema of an event (using [MSC1767: Extensible Events](https://github.com/matrix-org/matrix-spec-proposals/pull/1767)). 
All other areas, such as the Client-Server API, Identity Service API, Application Service API, etc 
are *not* in scope and would remain with the Matrix.org Foundation entirely.

The Federation API would be split into two parts: The Matrix Federation API and the Matrix HTTP Federation
Transport. The new Federation API would describe a series of RPC-like calls that servers must support
while the HTTP Transport would be similar to what is currently found in the Server-Server API specification:
a set of endpoints which map to those RPC calls, describing how JSON and similar algorithms work, etc.

This split can be hard to reason about, but is demonstrated by [I-D.ralston-mimi-matrix-api] (TODO)
([MSC0001] (TODO)) and [I-D.ralston-mimi-matrix-http] (TODO) ([MSC0002] (TODO)).

Similarly, only the event schema would be proposed rather than the event types specifically. As a more
simple model than the Federation API, what describes an arbitrary event's format would be specified
with the IETF, though the event types would be available through a "registrar"-like process, namely
the Matrix.org Foundation and the existing Matrix Spec Change (MSC) proposal process. In future,
this would be expanded to 3rd party vendor specifications once available at the Matrix.org Foundation
level.

The event model is described as [I-D.ralston-mimi-matrix-events] (TODO) ([MSC0003] (TODO)).

Finally, there's Room Versions. Not all room versions would be sent up to the IETF, instead only
considering a stable version every so often. This could mean divergence of numbering from the "IETF
room version" and "Matrix.org room version" though, which [I-D.ralston-mimi-matrix-api] (TODO) 
([MSC0001] (TODO)) attempts to solve. Much of the Federation API and parts of the event schema
would defer to the room version, like how a DAG might work, any applicable authorization rules,
structures for event IDs within the room version, etc. This opens up an opportunity for a different
kind of storage other than a DAG, if the usecase calls for it (and is no different from Matrix
today: if needed, we'd just move the DAG out of the SS API and into the existing room versions, just
as we've done for redaction rules, authorization rules, event ID format, and more in the past).

The room version proposed for inclusion is described by [I-D.ralston-mimi-matrix-room-version-1] (TODO)
([MSC0004] (TODO)).

**Author's Note**: While the draft's TODO state implies room version 1, we're not actually proposing
v1 for IETF. Instead, we'd likely be aiming for v11 or v12 to be defined instead (with extensible events,
faster room joins, etc). The version strings would change slightly with the IETF model in the mix.

### Impact on the Matrix.org process

The above describes how the pieces get cut up, but not how those pieces are expected to adopt changes
that will be needed over time. In the proposed model, the IETF gets a "long-term stable" (LTS) version
of the pieces it can amend using its own process - changes made to the IETF version get ported to the
Matrix.org edition (the original edition) of Matrix through MSCs. These MSCs would not be fait accompli, 
however: if the MSC process were to reject a change, it simply would not be included in the Matrix.org 
edition of Matrix. Generally, however, it would be likely that IETF changes are improvements or useful 
additions to the protocol and therefore be extremely well thought through solutions to a real problem, 
thus likely to be accepted.

Meanwhile, the Matrix.org edition keeps powering along at its normal pace. MSCs still get landed, and 
implementations still get written. Every so often, as deemed useful, the Matrix.org Foundation brings
any relevant changes to the IETF through the IETF's processes. This could, for example, mean proposing
every 3rd room version to the IETF (using its specific versioning scheme), or updating fundamental concepts
on an as-needed basis.

This approach has some potential for the two editions of Matrix to become incompatible, thus appearing
as a fork, however with careful consideration for how to structure Matrix in terms of IETF proposals, it 
should be possible to contain the riskiest parts to a room version. This would allow massively breaking 
changes (like not using a DAG) to be entirely kept within a room version that is gated by implementation 
effort (not all servers need to implement all room versions). With further involvement of the Matrix.org
Foundation throughout the lifetime of Matrix at the IETF level, it should be relatively easy to navigate
any potential disruptions to the protocol and its compatibility. It is also likely that both Matrix.org
and the IETF will want backwards compatibility in their invasive changes, providing a path for the other
affected party in case of conflict.

## Alternatives

Other ideas have been discussed with some members of the Spec Core Team, with the combination of them
appearing in the above proposal. Taking elements of the proposal and creating a new proposal around them
is feasible, though those approaches do not independently solve the concerns the SCT has. Namely, we'd
like to:

* have a compatible version of Matrix specified at the IETF level (specifically for federation)
* be free to experiment without the burden of process, and rapidly respond to shifts in the larger,
  external, ecosystem as needed
* keep the layers which aren't needed out of the IETF, for sake of implementation effort for Matrix-compatible
  implementations from the IETF level

... and other points along those same sentiments. 

Suggestions for alternative approaches are welcome, though unlike other MSCs, solutions which are more
carefully considered than usual are appreciated.

## Dependent MSCs

This MSC ends up affecting the future of the following MSCs:
* https://github.com/matrix-org/matrix-spec-proposals/pull/3918
* https://github.com/matrix-org/matrix-spec-proposals/pull/3919
* MSC0001 (TODO)
* MSC0002 (TODO)
* MSC0003 (TODO)
* MSC0004 (TODO)
