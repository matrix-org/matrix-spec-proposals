Content repository
==================

HTTP API
--------

Uploads are POSTed to a resource which returns a token which is used to GET
the download.  Uploads are POSTed to the sender's local homeserver, but are
downloaded from the recipient's local homeserver, which must thus first transfer
the content from the origin homeserver using the same API (unless the origin
and destination homeservers are the same).  The upload/download API is::

    => POST /_matrix/media/v1/upload HTTP/1.1
       Content-Type: <media-type>

       <media>

    <= HTTP/1.1 200 OK
       Content-Type: application/json

       { "content-uri": "mxc://<server-name>/<media-id>" }

    => GET /_matrix/media/v1/download/<server-name>/<media-id> HTTP/1.1

    <= HTTP/1.1 200 OK
       Content-Type: <media-type>
       Content-Disposition: attachment;filename=<upload-filename>

       <media>

Clients can get thumbnails by supplying a desired width and height and
thumbnailing method::

    => GET /_matrix/media/v1/thumbnail/<server_name>
            /<media-id>?width=<w>&height=<h>&method=<m> HTTP/1.1

    <= HTTP/1.1 200 OK
       Content-Type: image/jpeg or image/png

       <thumbnail>

The thumbnail methods are "crop" and "scale". "scale" tries to return an
image where either the width or the height is smaller than the requested
size. The client should then scale and letterbox the image if it needs to
fit within a given rectangle. "crop" tries to return an image where the
width and height are close to the requested size and the aspect matches
the requested size. The client should scale the image if it needs to fit
within a given rectangle.

Homeservers may generate thumbnails for content uploaded to remote
homeservers themselves or may rely on the remote homeserver to thumbnail
the content. Homeservers may return thumbnails of a different size to that
requested. However homeservers should provide exact matches where reasonable.
Homeservers must never upscale images.

Security considerations
-----------------------

Clients may try to upload very large files. Homeservers should not store files
that are too large and should not serve them to clients.

Clients may try to upload very large images. Homeservers should not attempt to
generate thumbnails for images that are too large.

Remote homeservers may host very large files or images. Homeserver should not
proxy or thumbnail large files or images from remote homeservers.

Clients may try to upload a large number of files. Homeservers should limit the
number and total size of media that can be uploaded by clients.

Clients may try to access a large number of remote files through a homeserver.
Homeservers should restrict the number and size of remote files that it caches.

Clients or remote homeservers may try to upload malicious files targeting
vulnerabilities in either the homeserver thumbnailing or the client decoders.

