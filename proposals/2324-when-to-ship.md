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
   * If the client needs to be sure the server supports the feature, an unstable
     feature flag that MUST be vendor prefixed is to be used. This kind of flag
     shows up in the `unstable_features` field of `/versions` as, for example,
     `com.example.new_login`.
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
   of this is an implementation of the MSC (which does not necessarily need to have been shipped anywhere).
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

### Specific examples outside of the client-server API

There are some instances where a change might be made outside of the client-server API,
which is where much of this proposal is targeted. The general spirit of the process
should be followed where possible, if implementations decide to work ahead of spec releases.

#### Room versions

When a new room version is needed, implementations MUST use vendor-prefixed versions
before using the namespace reserved for Matrix (see https://spec.matrix.org/unstable/rooms/).
A room version is considered released once it is listed as an "available room version" in
the spec. Often a new room version is accompanied with a server-server API release, but
doesn't have to be.

#### Server-server / Identity / Push / Appservice API

These APIs don't yet have a `/versions` endpoint or similar. Typically behaviour changes in
these APIs are introduced with backwards compatibility in mind (try X and if that fails fall
back to Y) and therefore don't always need a flag to indicate support. If a flag were to
be required, an `unstable_features` or similar array would need to be exposed somewhere.

#### Changes to request/response parameters

Parameters being added to request/response bodies and query strings MUST be vendor-prefixed
per the proposed process. For example, a new JSON field might be `{"org.matrix.example": true}`
with the proposal being for `example` being added. A query string parameter would be prefixed
the same way: `?org.matrix.example=true`.

If the MSC is simply adding fields to already-versioned endpoints, it does not need to put
the whole endpoint into the `/unstable` namespace provided the new parameters are prefixed
appropriately.

#### .well-known and other APIs that can't be versioned

Best effort is appreciated. Typically these endpoints will be receiving minor behavioural
changes or new fields. New fields should be appropriately prefixed, and behaviour changes
should be rolled out cautiously by implementations (waiting until after FCP has concluded
is probably best to ensure there's no major problems with the new behaviour).
