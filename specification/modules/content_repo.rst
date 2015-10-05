Content repository
==================

.. _module:content:

This module allows users to upload content to their homeserver which is
retrievable from other homeservers. Its' purpose is to allow users to share
attachments in a room. Content locations are represented as Matrix Content (MXC)
URIs. They look like::

  mxc://<server-name>/<media-id>

  <server-name> : The name of the homeserver where this content originated, e.g. matrix.org
  <media-id> : An opaque ID which identifies the content.

Uploads are POSTed to a resource on the user's local homeserver which returns a
token which is used to GET the download. Content is downloaded from the
recipient's local homeserver, which must first transfer the content from the
origin homeserver using the same API (unless the origin and destination
homeservers are the same).

Client behaviour
----------------

Clients can upload and download content using the following HTTP APIs.

{{content_repo_http_api}}

Thumbnails
~~~~~~~~~~
The thumbnail methods are "crop" and "scale". "scale" tries to return an
image where either the width or the height is smaller than the requested
size. The client should then scale and letterbox the image if it needs to
fit within a given rectangle. "crop" tries to return an image where the
width and height are close to the requested size and the aspect matches
the requested size. The client should scale the image if it needs to fit
within a given rectangle.

Server behaviour
----------------

Homeservers may generate thumbnails for content uploaded to remote
homeservers themselves or may rely on the remote homeserver to thumbnail
the content. Homeservers may return thumbnails of a different size to that
requested. However homeservers should provide exact matches where reasonable.
Homeservers must never upscale images.

Security considerations
-----------------------

The HTTP GET endpoint does not require any authentication. Knowing the URL of
the content is sufficient to retrieve the content, even if the entity isn't in
the room.

Homeservers have additional concerns:

 - Clients may try to upload very large files. Homeservers should not store files
   that are too large and should not serve them to clients.

 - Clients may try to upload very large images. Homeservers should not attempt to
   generate thumbnails for images that are too large.

 - Remote homeservers may host very large files or images. Homeservers should not
   proxy or thumbnail large files or images from remote homeservers.

 - Clients may try to upload a large number of files. Homeservers should limit the
   number and total size of media that can be uploaded by clients.

 - Clients may try to access a large number of remote files through a homeserver.
   Homeservers should restrict the number and size of remote files that it caches.

 - Clients or remote homeservers may try to upload malicious files targeting
   vulnerabilities in either the homeserver thumbnailing or the client decoders.

