---
type: module
---

### Content repository

The content repository (or "media repository") allows users to upload
files to their homeserver for later use. For example, files which the
user wants to send to a room would be uploaded here, as would an avatar
the user wants to use.

Uploads are POSTed to a resource on the user's local homeserver which
returns a MXC URI which can later be used to GET the download. Content
is downloaded from the recipient's local homeserver, which must first
transfer the content from the origin homeserver using the same API
(unless the origin and destination homeservers are the same).

When serving content, the server SHOULD provide a
`Content-Security-Policy` header. The recommended policy is
`sandbox; default-src 'none'; script-src 'none'; plugin-types application/pdf; style-src 'unsafe-inline'; object-src 'self';`.

#### Matrix Content (MXC) URIs

Content locations are represented as Matrix Content (MXC) URIs. They
look like:

    mxc://<server-name>/<media-id>

    <server-name> : The name of the homeserver where this content originated, e.g. matrix.org
    <media-id> : An opaque ID which identifies the content.

#### Client behaviour

Clients can upload and download content using the following HTTP APIs.

{{% http-api spec="client-server" api="content-repo" %}}

##### Thumbnails

The homeserver SHOULD be able to supply thumbnails for uploaded images
and videos. The exact file types which can be thumbnailed are not
currently specified - see [Issue
\#1938](https://github.com/matrix-org/matrix-doc/issues/1938) for more
information.

The thumbnail methods are "crop" and "scale". "scale" tries to return an
image where either the width or the height is smaller than the requested
size. The client should then scale and letterbox the image if it needs
to fit within a given rectangle. "crop" tries to return an image where
the width and height are close to the requested size and the aspect
matches the requested size. The client should scale the image if it
needs to fit within a given rectangle.

The dimensions given to the thumbnail API are the minimum size the
client would prefer. Servers must never return thumbnails smaller than
the client's requested dimensions, unless the content being thumbnailed
is smaller than the dimensions. When the content is smaller than the
requested dimensions, servers should return the original content rather
than thumbnail it.

Servers SHOULD produce thumbnails with the following dimensions and
methods:

-   32x32, crop
-   96x96, crop
-   320x240, scale
-   640x480, scale
-   800x600, scale

In summary:
-   "scale" maintains the original aspect ratio of the image
-   "crop" provides an image in the aspect ratio of the sizes given in
    the request
-   The server will return an image larger than or equal to the
    dimensions requested where possible.

Servers MUST NOT upscale thumbnails under any circumstance. Servers MUST
NOT return a smaller thumbnail than requested, unless the original
content makes that impossible.

#### Security considerations

The HTTP GET endpoint does not require any authentication. Knowing the
URL of the content is sufficient to retrieve the content, even if the
entity isn't in the room.

MXC URIs are vulnerable to directory traversal attacks such as
`mxc://127.0.0.1/../../../some_service/etc/passwd`. This would cause the
target homeserver to try to access and return this file. As such,
homeservers MUST sanitise MXC URIs by allowing only alphanumeric
(`A-Za-z0-9`), `_` and `-` characters in the `server-name` and
`media-id` values. This set of whitelisted characters allows URL-safe
base64 encodings specified in RFC 4648. Applying this character
whitelist is preferable to blacklisting `.` and `/` as there are
techniques around blacklisted characters (percent-encoded characters,
UTF-8 encoded traversals, etc).

Homeservers have additional content-specific concerns:

-   Clients may try to upload very large files. Homeservers should not
    store files that are too large and should not serve them to clients,
    returning a HTTP 413 error with the `M_TOO_LARGE` code.
-   Clients may try to upload very large images. Homeservers should not
    attempt to generate thumbnails for images that are too large,
    returning a HTTP 413 error with the `M_TOO_LARGE` code.
-   Remote homeservers may host very large files or images. Homeservers
    should not proxy or thumbnail large files or images from remote
    homeservers, returning a HTTP 502 error with the `M_TOO_LARGE` code.
-   Clients may try to upload a large number of files. Homeservers
    should limit the number and total size of media that can be uploaded
    by clients, returning a HTTP 403 error with the `M_FORBIDDEN` code.
-   Clients may try to access a large number of remote files through a
    homeserver. Homeservers should restrict the number and size of
    remote files that it caches.
-   Clients or remote homeservers may try to upload malicious files
    targeting vulnerabilities in either the homeserver thumbnailing or
    the client decoders.
