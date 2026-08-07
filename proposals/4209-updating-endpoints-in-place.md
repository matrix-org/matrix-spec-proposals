# MSC4209: Updating endpoints in-place

The current [deprecation policy](https://spec.matrix.org/v1.11/#deprecation-policy) does not clarify
how the specification should address endpoints being updated in a backwards incompatible manner. When
a breaking change is made to an endpoint, that endpoint's version is increased, however the old endpoint
may still exist on some server implementations. The deprecation policy can be read to mean that both
old and new endpoint must exist in the spec for at least 1 version, however this can add confusion
when attempting to implement the specification.

This proposal covers an alternative arrangement, where endpoints simply experiencing a version increase
are not required to maintain the old endpoint as deprecated. The deprecation is instead implied by
the version change. Servers which advertise support for old specification versions are still required
to implement both old and new endpoint.

This proposal does not apply to situations where the endpoint changes namespace, path structure, etc.

## Proposal

When an MSC makes a breaking change to an endpoint such that the version is increased, the old endpoint
is automatically deprecated and can be removed from the specification. This is to be codified in the
[deprecation policy](https://spec.matrix.org/v1.11/#deprecation-policy).

There may be situations where explicitly listing the old endpoint as deprecated in the specification
is preferred. This is supported by this policy clarification, and left to the discretion of the Spec
Core Team (SCT) during PR review.

Servers which implement multiple versions of the specification are still required to implement all
endpoints, regardless of per-endpoint versioning, described by those specification versions. For example,
if Matrix 1.1 has `/v1/test` and Matrix 1.2 replaces it with `/v2/test`, a server supporting both 1.1
and 1.2 would be required to implement both endpoints. A server only supporting 1.2 would only need
to support the `/v2` endpoint.

## Potential issues

No major issues are foreseen.

## Alternatives

There are no significant alternatives.

## Security considerations

This proposal does not materially affect the security profile of the protocol.

## Unstable prefix

This proposal does not implementation criteria which require an unstable prefix.

## Dependencies

There are no direct dependencies for this proposal.
