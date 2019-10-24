# MSC2324: Facilitating early releases of software dependent on spec

*Note*: This is a process change MSC, not a change to the spec itself.

There's currently an unanswered question by the spec process: when is it
safe to start using stable endpoints or to present a feature as "stable"?
Historically this question would receive very different answers depending
on who you asked, so in an effort to come up with a concise answer the
following process change is proposed.

## Proposal

The new process, from start to finish, is proposed as:

1. Have an idea for a feature.
2. Optionally: implement the feature using unstable endpoints, vendor prefixes,
   and unstable feature flags as appropriate.
   * When using unstable endpoints, they MUST include a vendor prefix. For
     example: `/_matrix/client/unstable/com.example/login`. Vendor prefixes
     throughout this proposal always use the Java package naming convention.
   * Unstable endpoints **do not** inherit from stable (`/r0`) APIs. Previously,
     one could access the entirety of the Matrix API through `/unstable` however
     this is generally considered a bad practice. Therefore an implementation
     can no longer assume that because its feature-specific endpoint exists that
     any other endpoint will exist in the same unstable namespace.
   * When using an unstable feature flag, they MUST include a vendor prefix.
     This kind of flag shows up in `/versions` as, for example, `com.example.new_login`.
     This flag should only be created if the client needs to be sure that the
     server supports the feature.
   * You can ship the feature at *any* time, so long as you are able to accept
     the technical debt that results from needing to provide adequate backwards
     and forwards compatibility for the vendor prefixed implementation. The
     implementation MUST support the flag disappearing and be generally safe for
     users. Note that implementations early in the MSC review process may also be
     required to provide backwards compatibility with earlier editions of the
     proposal.
   * If you don't want to support the technical debt (or if it's impossible to
     provide adequate backwards/forwards compatibility - e.g. a user authentication
     change which can't be safely rolled back), do not implement the feature and
     wait for Step 7.
   * If at any point the idea changes, the feature flag should also change so
     that implementations can adapt as needed.
3. In parallel, or ahead of implementation, open an MSC and solicit review.
4. Before a FCP (Final Comment Period) can be called, the Spec Core Team will
   require that evidence to prove the MSC works be presented. A typical example
   of this is an implementation of the MSC (ie: Step 2).
5. FCP is gone through, and assuming nothing is flagged the MSC lands.
6. A spec PR is written to incorporate the changes into Matrix.
7. A spec release happens.
8. Implementations switch to using stable prefixes (e.g.: `/r0`) if the server
   supports the specification version released. If the server doesn't advertise
   the specification version, but does have the feature flag, unstable prefixes
   should still be used.
9. A transition period of about 2 months starts immediately after the spec release, before
   implementations start to loudly encourage other implementations to switch to stable
   endpoints. For example, the Synapse team should start asking the Riot team to
   support the stable endpoints (as per Step 8) 2 months after the spec release if they
   haven't already.

It's worth repeating that this process generally only applies if the implementation
wants to ship the feature ahead of the spec being available. By doing so, it takes
on the risk that the spec/MSC may change and it must adapt. If the implementation
is unable to take on that risk, or simply doesn't mind waiting, it should go through
the spec process without shipping an unstable implementation.

To help MSCs get incorporated by implementations as stable features, the spec core
team plans to release the specification more often. How often is undefined and is
largely a case-by-case basis.

To reiterate:

* Implementations MUST NOT use stable endpoints before the MSC is in the spec. This
  includes NOT using stable endpoints post-FCP.
* Implementations CAN ship features that are exposed by default to users before an
  MSC has been merged to the spec, provided they follow the process above.
* Implementations SHOULD be wary of the technical debt they are incurring by moving
  faster than the spec.

To clarify:

* The vendor prefix is chosen by the developer of the feature, using the Java package
  naming convention. For example, `org.matrix` is the foundation's vendor prefix.
* The vendor prefixes, unstable feature flags, and unstable endpoints should be included
  in the MSC so other developers can benefit. The MSC MUST still say what the stable
  endpoints are to look like.
