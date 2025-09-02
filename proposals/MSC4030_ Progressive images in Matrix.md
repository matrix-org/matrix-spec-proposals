# MSC4030: Progressive Images in Matrix

## Introduction

Efficient image handling is essential for delivering a seamless user experience within a communication platform like Matrix.
This proposal recognizes the potential of modern progressive image formats to enhance image management within Matrix.

While this document will occasionally highlight JPEG XL (referred to as 'jxl') as a notable use case, it is important to note
that the concepts discussed herein are applicable to both progressive and non-progressive image formats,
including WebP2 and JPEG itself.

## Clarifications

In Matrix, there are two types of thumbnails:

- **Server-side generated thumbnails** available at the `thumbnail/` endpoint.
- **Event thumbnails**, uploaded by clients and referenced using a separate MXC.

This distinction exists because server-side generated thumbnails cannot be served in encrypted rooms or for media types other than `m.image`.

### Reasons behind these changes

The Matrix specification currently does not take into account that clients may benefit from receiving content in formats
that align with their capabilities. By introducing media negotiation mechanisms, Matrix can enhance the client experience
by serving content in the most efficient way possible.

See [Issue #453](https://github.com/matrix-org/matrix-spec/issues/453) for further details.

## Encrypted Rooms

Due to the inability to re-encode images server-side, it is necessary to maintain the existing structure and functionality of the current API.

To enhance user experience, it would be ideal loosening the requirements for progressive images in `m.image` events
by eliminating the need for an event thumbnail (`"thumbnail_file"` entry). This change reduces storage costs,
as progressive images do not need thumbnails. For proper functionality, client implementations should support on-the-fly
decoding and decryption of media during download.

In summary, if an image is progressive, clients MAY NOT generate the `"thumbnail_file"` entry (and the associated resources)
in `m.image` messages sent in encrypted rooms.

## Unencrypted Rooms

Since we can re-encode the image server-side it would be optimal to serve the image (`/download` endpoint) and the server-side thumbnails
(`/thumbnail` endpoint) with the best format that align with the client capabilities.

### Eliminating Unwanted Behavior

Clients do not acknowledge that, in unencrypted rooms, server-side generated thumbnails should be available for image resources.
As a result, they unnecessarily generate client-side thumbnails, upload them to the server, and reference them in the `m.image` event,
creating redundant and unnecessary resources.

To fix this issue, clients SHOULD NOT generate the `"thumbnail_file"` entry (and the associated resources) in `m.image` messages
sent in unencrypted rooms.

Note that while the Matrix specification states that servers SHOULD provide thumbnails via the `/thumbnail` endpoint, this is not mandatory.
If a server chooses not to implement thumbnail generation or does not support it for certain formats, then no thumbnails will be available for those
images in unencrypted rooms. This is an acceptable trade-off to eliminate the storage overhead and complexity of redundant client-side thumbnails.

### Supporting Different Formats

As proposed in [MSC4011](https://github.com/matrix-org/matrix-spec-proposals/pull/4011), media negotiation MUST be performed
using the [HTTP Content Negotiation mechanism](https://developer.mozilla.org/en-US/docs/Web/HTTP/Content_negotiation).
This mechanism allows the delivery of images in progressive or more modern formats to clients that support such features.

If the `Accept` header field is unspecified, absent or list unsupported formats, the server MUST provide the image resource
as `image/png` or `image/jpeg`.

All progressive-capable formats MUST always provide the image as a progressive one, even if the image is uploaded
as a non-progressive image in a progressive-capable format. When serving the content, the server MUST provide the image
in the same format (and all others) as a progressive image.

If the negotiation is successful and a different non-progressive format is chosen for the image, the server MAY compare
the size between the image in the transcoded format and the image in the original format, if the image in the original format
is smaller than the transcoded one and is supported by the client, the server could chose to send the image in
the original format instead of the transcoded one. However, this behavior SHOULD NOT be implemented for progressive formats.

Clients SHOULD NOT connect to the `/thumbnail` endpoint if the server can provide images in progressive formats,
supported by the client, at the `/download` endpoint.

*Note: If a server does not implement the `/thumbnail` endpoint or does not support thumbnail generation for certain formats, 
those images will simply not have thumbnails available in unencrypted rooms. This is preferable to the current situation 
where redundant client-side thumbnails are generated and stored.*

*Enabling this feature allows the server to store images in more efficient formats such as JPEG XL, reducing storage costs.
These images can be quickly served as JPEG for clients that do not support the jxl format. Additionally,
JPEG XL can perform lossless conversion of PNG and JPEG, further reducing storage costs and bandwidth usage.*

## Alternatives

[MSC4011 - Thumbnail media negotiation](https://github.com/matrix-org/matrix-spec-proposals/blob/clokep/thumbnail-media-negotiation/proposals/4011-thumbnail-media-negotiation.md).
