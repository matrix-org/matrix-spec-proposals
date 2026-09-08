# MSC4519: MatrixRTC Transports Registry

[MSC4143](https://github.com/matrix-org/matrix-spec-proposals/pull/4143) describes the framework for
Real-Time Communication (RTC) applications to operate over Matrix. The MSC also allows for alternate
transports to be made available for accessing media streams of RTC application members. See MSC4143
for definitions and more information.

[MSC4518](https://github.com/matrix-org/matrix-spec-proposals/pull/4518) describes a process to
support interoperability of non-core Matrix components. The MSC supports a variety of data types
being stored within a registry, keyed by a string identifier, including chunks of specification.
See MSC4518 for more details on what registries are and how they intend to operate.

This proposal creates a new registry to hold RTC transports and their specifications, encouraging
interoperability without requiring those transports to enter the core Matrix specification. Transports
suitable for the core specification can still land there, though they'll also need placing in the
registry.

The primary motivation for a registry is to allow transports such as [MSC4195](https://github.com/matrix-org/matrix-spec-proposals/pull/4195)
to land with relative stability, but without placing a dependency on LiveKit into the core spec.


## Proposal

A new "MatrixRTC Transports" registry is created with the following information:

* A transport `type`. MUST be an [Opaque Identifier](https://spec.matrix.org/v1.19/appendices/#opaque-identifiers).
* Stability (`stable` or `unstable`).
* A link to the specification for that transport, per MSC4143.

`stable` transports are added/changed/removed through normal MSCs. `unstable` transports are automatically
added when a new proposal is opened which introduce a transport. They by default have a `type` of `msc0000.{stable_type}`,
but MAY be extended upon per the MSC's "Unstable Prefix" section provided they maintain the `msc0000`
prefix. For example, if a proposal changes substantially after the registration was made, the proposal 
might suggest using `msc0000.livekit.v2`.

Like with regular unstable implementation, `unstable` transport implementations MUST use the "Unstable
Prefix" section of the relevant MSC. For example, if the transport introduces `/new_endpoint`, then
implementations would use `/unstable/org.example.msc0000/new_endpoint` in the `msc0000.whatever`
transport. `/v1/new_endpoint` could only be used in the `whatever` transport (the `stable` type).

Twelve months after the FCP acceptance of the MSC the unstable type is automatically removed from the
registry. Early removal is possible if the public federation has adopted the stable type sooner than
expected - a normal spec PR with normal review requirements is used to propose that removal.

**Note**: The automation above is process automation. Someone will still need to actually open the
spec PR which adds/removes/changes a transport's registration.

This structure allows for registry changes to be as easy as modifying the specification itself. As
a worked example:

* MSC4195 gets opened, introducing the `livekit` type.
* The author opens a spec PR to register the `msc4195.livekit` unstable type, using the MSC URL as
  the specification reference (specifically the "Unstable Prefix" section/components).
* MSC4195 goes through normal review, and is eventually proposed for FCP (merge).
* MSC4195 succeeds at FCP and becomes accepted.
* A contributor opens a spec PR to register the `livekit` stable type. They also write a new section
  on the registry's page with MSC4195's contents. That new section's anchor becomes the spec URL.

  **Note**: If the MSC is detailed enough, a link to the rendered Markdown in the spec proposals repo
  is probably suitable too.
* Upon that spec PR being merged, MSC4195 also becomes merged (per MSC process).
* A year later, a contributor removes the `msc4195.livekit` unstable type through a spec PR.

Mentioned in this proposal's introduction, this process does not prohibit a transport from entering
the core spec. Instead of the spec PR for MSC4195 (for example) being an added section on the registry's
page, it would be somewhere within the core spec. The registry would then link to that versioned
section. Transports which intend to enter the core spec MUST declare that in their proposals - the
default assumption is that transports will not enter the core spec.

### Transport discovery

Some RTC transports might require server-side infrastructure such as SFUs and TURN servers. Clients
need a mechanism to discover the availability of such infrastructure and any potentially required
connection details. To enable this, a new authenticated, rate limited, and guest accessible endpoint
is added to the Client-Server API (core spec):

```json5
// GET /_matrix/client/v1/rtc/transports
// 200 OK
{
  "rtc_transports": [
    {
      "type": "{transport_type}",
      ... // Further transport-specific properties (if required)
    }
  ]
}
```

The endpoint requires authentication to permit different transports to be returned to different users.

`rtc_transports` is required and MUST be an array of objects with at least a registered `type`. Types
not in the registry are not permitted. Additional properties/schema are as per the specification for
the `type`.

If there are no transports available to the user, `rtc_transports` MUST be an empty array.

### Exception: MSC4195

Because MSC4195 has been used to test the unstable implementation of MSC4143 and has no unstable
prefixes itself, `livekit` is registered as an unstable type instead of `msc4195.livekit`. When
MSC4195 becomes accepted, its type is to be upgraded to `stable` with relevant changes to the spec
link. No implementation changes would be required outside what they'd need to do to support MSC4143
becoming stable itself.


## Potential issues

See MSC4518 for potential issues with registries.

Transports are not expected to be proposed often, so the regular MSC process should support the
registry well. Most transports would have tried to enter the core specification anyway, which
would generate MSCs. Per MSC4518, the team which reviews additions/changes/removals to the registry
can change at any time through another MSC.


## Alternatives

See MSC4518 for alternatives to registries. In the case of MSC4195 (LiveKit Transport), the alternative
is effectively putting the dependency into the core spec for all implementations.

`.well-known` was considered for the transport discovery endpoint, but as a traditionally unauthenticated
endpoint it doesn't fit infrastructure requirements for some transports. Well-Known URLs are often not
served by the homeserver (which would have transport information), but rather a different web server,
making populating the resource much harder. Authentication further allows for user-specific transports.


## Security considerations

Individual transports are expected to have their own security considerations. The presence of a
registry does not carry inherent security challenges, per MSC4518.


## Unstable prefix

Registries do not have an effective unstable prefix. To assist in editorial ease however, this
proposal's registry can be implemented as an added section in the [appendices](https://spec.matrix.org/v1.19/appendices/).
Later, when either more proposals use registries or the infrastructure is easier to use, the section
would be moved out.

The `GET /_matrix/client/v1/rtc/transports` endpoint should be accessed as `GET /_matrix/client/unstable/org.matrix.msc4143/rtc/transports`
while this proposal is considered unstable. Note that the namespace is from MSC4143 - this is to
reflect the endpoint being lifted out of that proposal and into this one.


## Dependencies

This proposal depends on MSC4518 (Registries).

This proposal SHOULD NOT be accepted without MSC4143 (MatrixRTC) being accepted
concurrently. Note that MSC4143 also depends on this proposal.
