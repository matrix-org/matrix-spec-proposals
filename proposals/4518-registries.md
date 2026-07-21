# MSC4518: Registries

**Note**: This proposal formalizes a process rather than significant specification. It may be
tested in production under the supervision of the Spec Core Team (SCT).

As Matrix continues to grow and expand its capability, there is increased want for a structured place
to put coordinated implementation-specific details. For example, event types which cover a feature
that wouldn't necessarily be accepted into the "main" spec, transport options for VoIP media, or a
set of common identifiers which aren't explicitly needed in Matrix itself.

This proposal calls those structured places "registries", using [BCP 26 (RFC 8126)](https://datatracker.ietf.org/doc/html/rfc8126)
as a set of guiding principles. The major difference between this proposal and BCP 26 is reduced governance
overhead. Creation, population, removal, etc of a registry is already quite easy under BCP 26, though
other IETF and IANA policies and procedures often layer to create more involved steps - Matrix does
not have the same process requirements.

More information about BCP 26 and this proposal's base principles can be found from the IETF Internet-Draft
Author Resources: <https://authors.ietf.org/en/iana-considerations>


## Proposal

Registries consist of usually-optional functionality for a Matrix implementation. They are not part
of the versioned specification, similar to how the [proposals page](https://spec.matrix.org/proposals/)
is set up, but still have light governance to manage additions, removals, and changes. The precise
deployment of a registry is left as an editorial detail - a GitHub repo with a bunch of Markdown docs
is just as equally suitable as `https://spec.matrix.org/registry/whatever`.

How functionality contained in a registry is discovered is left as a detail for the proposal(s) which
define it, if one is needed. For example, a VoIP transport registry might also introduce a `/transports`
endpoint so clients can discover those transports. Or, in the case of an event type-like registry, no
discovery mechanism is necessarily required - clients would render the event types they support without
needing to know what the server supports.

When a registry should be used is not strictly defined. The intention is to give proposals an additional
tool for improving interoperability without bloating the versioned specification. In general, a registry
SHOULD NOT be used to list required identifiers, like join rules, but SHOULD be used to record optional
extensions, like VoIP transports.

The structure of a registry is left as a detail for the proposal(s) which define that registry. Some
non-normative examples are included later in this proposal.

The operation and what types of information are included in a registry are defined by normal MSCs for
SCT review. The actual contents of a registry do not need to use MSCs, but unless otherwise defined
by the registry's processes, MSCs are required.

This setup ensures that the SCT is involved in changes to the "schema" of a registry, but is not
required to be involved in the population of data in the registry. An external team or Governing Board
Working Group could be given the ability to manage the contents of a registry. Though, to ensure
registries can continue operating when volunteers are unavailable, the SCT is always able to modify
the contents of a registry through normal MSCs.

**Note**: If a non-SCT body chooses to use MSCs as the way to manage a registry's contents, those
MSCs will still require SCT review and normal MSC process. Non-SCT bodies are encouraged to develop
external approval/submission processes to avoid MSC process delay where needed.

As a (deliberately lengthy) worked example:

* MSC0001 defines an event types registry. The proposal states that the registry contains an event
  `type`, description of what that event type is, and a schema for the event `content`. The proposal
  is successfully merged through FCP review.
* Later, the Event Types Working Group is established by the Governing Board and wants to take on
  management of the registry from the SCT. The SCT has been managing the registry all this time
  because MSC0001 didn't specify an alternative approval/curation process.

  The new Working Group opens MSC0002 to change the registry's curation to the Working Group, but
  doesn't remove the MSC requirement to add/remove/change contents.
* MSC0003 is opened by a contributor to add their event type to the registry. The Working Group and
  SCT both review the proposal. Ultimately, the MSC is merged after a successful FCP started by the
  SCT.
* The Working Group finds this dual review a little hard to manage, so they open MSC0004 to move
  curation to a dedicated GitHub repo. The SCT reviews the proposal under normal process. The MSC
  is successful during a FCP merge.
* Another contributor wants to add to the event types registry, so they open an issue against the
  dedicated GitHub repo. The SCT is no longer directly involved in review, so it's just the Working
  Group which manages approval.
* Yet another contributor wants to make a change to the registry, so they open a similar issue on
  the dedicated GitHub repo. However, this time the Working Group isn't able to review it for some
  reason. The SCT steps in and reviews the change, approving or denying it as required.
* Later, Extensible Events lands in the specification and the Working Group wants to change the
  schema of their registry to support Content Blocks and rendering options. Because they only have
  curation capability, they need to open MSC0005 to get SCT review on the proposed schema changes.

As shown, it's preferable that if a non-SCT body is to have curation capability then they should also
avoid using MSCs as it creates extra process steps.

### Non-normative registry examples

The following are example (minimal) MSCs which demonstrate how a registry might be created and what
they might contain. Any resemblance to other proposals, ideas, or thoughts is coincidental - this
section is non-normative.

#### Event type registry

A new "Event Types" registry is established with the following details:

* The event `type` using [Common Namespaced Identifier Grammar](https://spec.matrix.org/unstable/appendices/#common-namespaced-identifier-grammar).
* A description of what the event is.
* A schema for the event's `content`.

The registry contains an additional table for Extensible Event Content Blocks:

* The block `type`, also using Common Namespaced Identifier Grammar.
* A description of what the block is used for/represents.
* A schema for the block.

The registry is curated through MSCs and normal process.

#### VoIP transports registry

A new `/available_transports` endpoint is made available. It returns a `transports` array containing
identifiers from the below-defined transports registry. The array MAY be empty to indicate no transports
are supported.

The transports registry contains:
* A transport ID using Common Namespaced Identifier Grammar.
* A link to the proposal or other specification-like document which defines it. The contents of the
  linked document MUST be backwards compatible with when the transport ID was first introduced.
* A flag to indicate whether server implementations SHOULD support the transport.

The registry is curated by the VoIP Working Group via the `matrix-org/voip-transports` GitHub repo.

This MSC also introduces an initial `io.element.msc0006.livekit` transport to be included in the
registry: ...

#### T&S harms registry

A new harm identifiers registry is established with the following details:

* The identifier using Common Namespaced Identifier Grammar.
* The minimum specification version where support for the identifier is mandatory. For example, if
  this were to be `v1.19`, then servers MUST support receiving reports with this `harm` if they also
  support at least `v1.19`.
* A user-facing description for the identifier.

The categories which contain the identifiers are left as an editorial detail.

The registry is curated by the Foundation's T&S team via normal MSCs. This registry is not expected
to be updated frequently.

The following identifiers form the start of the registry: ...


## Potential issues

Registries can increase optionality too much in Matrix, leading to several capability negotiation
endpoints being available. The SCT is expected to carefully review whether a registry is required,
and ensure their prompt removal (via another MSC) as soon as they aren't needed.

Registries might also increase burden on the existing MSC process by default. Proposals which create
registries SHOULD aim to include as many starting values as possible to avoid flooding the MSC process.
A future MSC can change the use of MSCs to curate/modify registries if needed.


## Alternatives

The only meaningful alternative is incorporating the functionality into the spec itself. Placing
features like VoIP transports directly into the spec can hinder development because it's hard to change,
remove, or adapt each transport when there's only 4 releases a year. Instead, by having a registry
it's possible to iterate on the transport options faster. Later, when the set of transports is believed
stable or ready for inclusion in the spec, the registry can be removed too.


## Security considerations

There is opportunity for spammy/malicious submissions to registries, just like there are for regular
proposals. The SCT retains curation capability of all registries to remove such submissions without
placing burden on the registry's managing team.


## Unstable prefix

This proposal defines a process, not something which can be prefixed. The SCT MAY explore using this
proposal in production ahead of formal acceptance.

Prefixes might still be used within a registry.


## Dependencies

This proposal has no direct dependencies.
