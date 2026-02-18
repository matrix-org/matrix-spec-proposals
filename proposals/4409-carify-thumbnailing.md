# MSC4409: Clarify thumbnailing behavior

The purpose of this spec change is to clarify how clients should behave in regards to thumbnails in an E2EE world.

Matrix clients capable of rendering media can choose to render the original source or a thumbnail representing it. For 
example one would not want to render a full video player within a scrollable timeline view but would a thumbnail image,
for performance reasons. The clients are still able to choose the original source if the situation warrants it e.g. animating
GIFs.

Historically homeservers would come to the clients' help by providing an [endpoint to do so](https://spec.matrix.org/latest/client-server-api/#get_matrixclientv1mediathumbnailservernamemediaid). 
The [Thumbnails](https://spec.matrix.org/latest/client-server-api/#thumbnails) section of the Spec's client behavior 
states that homeserver provided thumbnails are available for certain media formats, in a fixed number of resolutions and
following rules like no upscaling and returning the original if the thumbnail is smaller than the original (for supported
formats).

With the advent of E2EE aware clients server support is no longer possible. Clients are instead expected to 
upload their own thumbnail resources and attach them to newly introduced (at the time) `thumbnail_url`/`thumbnail_info` 
fields on various events.

The spec does not however clarify how the 2 should be handled in mixed encrypted and non-encrypted environments.

## Proposal

The proposal is to introduce new language in the [Thumbnails](https://spec.matrix.org/latest/client-server-api/#thumbnails)
section that does address this as follows:

E2EE aware clients are expected to provide thumbnail resources next to the original media they're uploading as close 
in resolution to what the maximum backend endpoints would provide (800x600 at the time of writing).

For image media smaller than that no thumbnail should be provided. Uploading clients can provide thumbnails larger than 
800x600 for non-image media.

Providing thumbnails should happen for both encrypted and non-encrypted rooms in order to provide maximum flexibility in 
thumbnail choice, reduce backend strain and improve format compatibility.

Rendering clients are expected to choose the thumbnail resources (if available) when rendering media previews.
Calling the thumbnailing homeserver endpoint on a thumbnail resource is allowed, similar to any other resource, but will 
return the original resource in encrypted rooms, where backend support isn't available.

Client SDKs are encouraged to apply post network request processing to original thumbnails to have them fit 
the final client's request size if necessary but that's an optimization left to the implementer.

## Security concerns

Malicious clients can of course upload thumbnails that do not represent the original content but that does not fall 
under the umbrella of this MSC.
