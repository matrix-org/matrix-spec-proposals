# MSC4107: Feature-focused versioning

**Disclaimer**: This MSC is an independent and initial idea which requires significant review and iteration.

Reading material:
* https://spec.matrix.org/v1.9/#specification-versions
* https://spec.matrix.org/v1.9/client-server-api/#get_matrixclientversions
* https://spec.matrix.org/v1.9/client-server-api/#modules

Implementation of a feature in Matrix can span multiple different systems and require multiple different
identifiers. Typically, a feature begins its implementation as an *unstable* feature flag attached to
a particular MSC. As that MSC progresses, the feature flag may change to accommodate sub-versioning of
the proposed feature. When the MSC finally finishes a `merge` FCP, implementations can then use *stable*
identifiers - the ones described in the actual normative sections of the MSC (`m.*`). Typically, clients
require further feature negotiation to determine if they can actually use that feature though, because
it hasn't yet been assigned to a specification version. This leads to *unstable* feature flags to denote
the *stable* state, such as `org.matrix.msc4107.stable`. Some time after that, the stable MSC gets
converted to formal spec, and that spec gets released as an assigned number. Clients are then able to
detect feature support using that specification number.

There are several issues with this approach. Most obviously, clients want to know if they can use
*features*, but the versioning prioritizes specification. Specification is important, however other
mechanics outside the versioning scheme can ensure MSCs are written up as formal spec.

In a related concern, server implementations *often* lag behind the spec release cycle due to the size
and complexity of the spec. The spec itself is very monolithic, and that causes friction when a server
wishes to support a given subset or limited scope, or when a server implementation is trying to get
started and immediately falls behind on client support. Unfortunately, reducing the release cadence
from quartly to biannually does not have an effect of easier releases to implement - the releases just
become chunkier (or don't happen at all because it doesn't feel "worth it" to release).

This proposal explores a feature-focused versioning scheme to prioritize the information needs of clients
over the full specification ideals imposed onto servers.

## Proposal

The [`GET /versions`](https://spec.matrix.org/v1.9/client-server-api/#get_matrixclientversions) endpoint
is modified to add a new `features` key. The existing `unstable_features` and `versions` keys are deprecated.

```json5
{
  // New field
  "features": {
    "msc3440": ["org.matrix.msc3440", "fcp-stable:msc3440", "v1.4", "v1.5", "v1.6"],
    "msc1772": ["org.matrix.msc1772"],
    "encryption": ["r0.0.0", /* ... */, "v1.9"],
    "msc2659": ["fcp-stable:msc2659"],
    "core": ["r0.0.0", /* ... */, "v1.9"]
  },

  // Existing fields - now deprecated
  "versions": ["v1.2", "v1.3"],
  "unstable_features": {
    "org.matrix.msc4107": true
  }
}
```

The new `features` key maps a feature ID to array of supported versions by the server. The supported
versions are a combination of unstable feature flags (like `org.matrix.msc4107`), the string `fcp-stable`,
and specification releases. The feature ID is typically the MSC number, though for historical modules
in the Client-Server API some are named features. If a given feature spans multiple MSCs, it is expected
that an MSC to allocate a feature ID is created.

**TODO**: Needing an MSC to create a feature ID is awkward. Can we make it a line of text in the
'foundational' MSC for the feature? (should we always require an architecture/foundation MSC for
large features?)

**TODO**: Assign feature IDs to existing modules where appropriate. There's an assumption that a 'core'
feature ID would be assigned to, well, the core functionality of Matrix. Core would probably encompass
anything not covered by a more specific feature ID, like the ability to send/receive events.

Versions matching the `rX.Y.Z` or `vX.Y` formats are specification releases. If a feature is unchanged
in a given spec release, the array is not required to list it. However, servers may find it easier to
list all supported specification releases in each array.

The string `fcp-stable` is used to denote the time between successful `merge` FCP and specification
release. The string contains a `:` to delineate the string from the MSC number which completed FCP.
This allows for the feature ID to be modified by future MSCs - see the example case below for details.

All other strings not mentioned by this proposal are considered to be unstable feature flags.

Instead of having to detect and estimate the specification version, clients can simply look up the
specific features they need and disable/degrade as appropriate. Servers can then also incrementally
make progress on new spec releases without affecting clients, as one feature might support "latest"
while another is stuck 4 versions behind. In the existing (deprecated) system, a server would be
required to have *both* features fully supported before it could advertise the specification version.

### Example case: Net-new feature

An MSC is opened to describe a new feature such as threads or spaces. That MSC is assigned a number,
in our case MSC4107, and that number becomes the feature ID going forwards.

Implementation then begins on the feature using *unstable* prefixes and feature flags. `/versions`
would look something like:

```json5
{
  "features": {
    "msc4107": ["org.matrix.msc4107"]
  }
}
```

Though rare, sometimes the MSC iterates in a breaking way and needs another unstable feature flag.
This gets implemented, and `/versions` updated to include that flag:

```json5
{
  "features": {
    "msc4107": ["org.matrix.msc4107", "org.matrix.msc4107.v2"]
  }
}
```

Later, the MSC is proposed for `merge` FCP. After sufficient time, the FCP completes, MSC is adopted
into `matrix-spec-proposals` `main` branch, and everyone can start using stable prefixes. The server
implements the stable prefixes, and adds `fcp-stable` to the `/versions`:

```json5
{
  "features": {
    "msc4107": ["org.matrix.msc4107", "org.matrix.msc4107.v2", "fcp-stable:msc4107"]
  }
}
```

Then, the MSC is written up as formal specification and released in v1.10 (in this example). Like the
FCP concluding, the server implements the needed changes (if any), and adds the spec release to `/versions`:

```json5
{
  "features": {
    "msc4107": [
      "org.matrix.msc4107",
      "org.matrix.msc4107.v2",
      "fcp-stable:msc4107",
      "v1.10"
    ]
  }
}
```

At this point, it's advised that the server wait 2 months before dropping the unstable feature flag
versions, but it is not required to. To fully demonstrate the lifecycle here, the example server does
*not* drop the unstable feature support.

Eventually, after 2 spec releases go by, a new MSC is opened to modify the feature. Instead of getting
a whole new feature ID, the existing one is reused. The server implements the unstable feature using
unstable prefixes, and advertises that on `/versions`:

```json5
{
  "features": {
    "msc4107": [
      "org.matrix.msc4107",
      "org.matrix.msc4107.v2",
      "fcp-stable:msc4107",
      "v1.10",
      "v1.11", // optional - the feature didn't change in this version, but time did pass
      "v1.12", // optional - the feature didn't change in this version, but time did pass
      "org.matrix.msc0001",
    ]
  }
}
```

The new MSC then completes its FCP and is formally released in v1.13, which the server dutifully
implements each step of.

```json5
{
  "features": {
    "msc4107": [
      "org.matrix.msc4107",
      "org.matrix.msc4107.v2",
      "fcp-stable:msc4107",
      "v1.10",
      "v1.11", // optional - the feature didn't change in this version, but time did pass
      "v1.12", // optional - the feature didn't change in this version, but time did pass
      "org.matrix.msc0001",
      "fcp-stable:msc0001",
      "v1.13" // required - the feature changed in this version
    ]
  }
}
```

The server is once again encouraged to drop the unstable feature flags 2 months after the spec release.
This time, the server does that:

```json5
{
  "features": {
    "msc4107": [
      "v1.10",
      "v1.11", // optional - the feature didn't change in this version, but time did pass
      "v1.12", // optional - the feature didn't change in this version, but time did pass
      "v1.13" // required - the feature changed in this version
    ]
  }
}
```

... and that's it. If the second MSC were to change the feature dramatically, it may be best to use
a new feature ID instead. For example, if "threading v2" is completely incompatible with "threading v1",
then a new feature ID would be recommended. The SCT is responsible for determining when/if a new feature
ID should be used.

## Potential issues

This approach could fragment implementation slightly, allowing servers to selectively implement a given
MSC up to the "latest" spec release, but exactly zero other features receive the same treatment. This
situation is how XMPP largely works: implementations are a mix of core functionality and whatever
desirable XEPs are needed. We at Matrix want to avoid this. Though the MSC doesn't go into detail about
it currently, the author's theory is that a `core` feature ID could be assigned to most functions in
the spec, and clients would in practice be checking `core + msc4107` support of the server. This still
encourages the server to keep up to date on the core functionality, and push for complete features as
well.

Another possible way to ensure full compliance with the specification is The Matrix.org Foundation C.I.C.
running a "certification" program to verify a given implementation's level of spec support.

**TODO**: There's probably other issues. They should be documented.

## Alternatives

**TODO**: Reiterate alternatives which are buried in prose above.

## Security considerations

**TODO**: This section

## Unstable prefix

While this proposal is not considered stable, implementations should use `org.matrix.msc4107.features`
on `/versions` instead.

## Dependencies

This proposal has no direct dependencies.
