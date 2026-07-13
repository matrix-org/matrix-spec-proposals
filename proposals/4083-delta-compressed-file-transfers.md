# MSC4083: Delta-compressed E2EE file transfers

## Problem

When collaborating on a large file of some kind, it's common to store that file in Matrix, and then need a way to
express incremental changes to it.  For instance, in Third Room, you might store a large glTF scene graph as a GLB
file, and then want to express a small change to it (e.g. using the editor to transform part of the scene graph).  Or
you might want to store a change to a markdown or HTML file.

Currently, your only option is to save a whole new copy of the file - or invent your own delta-compression scheme at
the application layer. Instead, we could make Matrix itself aware of delta-compression, letting the content repository
help users efficiently collaborate around updates to binary files, regardless of what the file is.

## Solution

When uploading a file, specify that it's a delta against a previous piece of content, using a given algorithm.

 * `delta_base` is the mxc URL of the content the delta applies to
 * `delta_format` is the file format of the binary diff
   * This MSC defines `m.vcdiff.v1.gzip` to describe gzipped RFC3284 compatible binary VCDIFF payloads, picked for
     computation efficiency rather than patch size (whereas bsdiff + bzip might provide better patch size at worse
     computation complexity; other MSCs are welcome to propose different diff formats).

Clients should upload a new snapshot of a piece of content if the sum of the deltas relative to the last snapshot
is larger than 50% of the original piece of content

For instance:

`POST /_matrix/media/v3/upload?delta_base=mxc://matrix.org/b4s3v3rs10n&delta_format=m.vcdiff.v1.gzip`

returning:
```json
{
  "content_uri": "mxc://matrix.org/n3wv3rs10n"
}
```

(or with the same parameters for MSC2246-style `POST /_matrix/media/v3/create`).

The server tracks the graph of which deltas apply to which files, so it can only hand the relevant deltas to clients
when they download them.

For instance, when downloading a delta-compressed piece of content, a client might ask to pull in any delta dependencies
it doesn't already have stored locally, relative to the last version that it has a full copy of:

`GET /_matrix/media/v3/download/matrix/org/n3wv3rs10n?delta_base=mxc://matrix.org/b4s3v3rs10n`

This would return an ordered multipart download of the deltas (once unencrypted, if needed) to apply to the base-version
to get a copy of the new-version.

## Alternatives

### Track deltas on events rather than media repository

Alternatively we could store the delta info on the `m.file` event itself as a mixin. This would allow us to shift the
task of tracking deltas purely to clients, and protect the delta info within the E2EE payload.  However, this would then
force the client to do many more roundtrips to spider the events (if needed) and files (if needed) one by one in order
to calculate diffs, which would be O(N) latency with the number of diffs rather than O(1) for the above API.  Given the
traffic pattern of these requests would reveal the delta graph to the server anyway, it's not clear that it provides a
sufficient advantage. This would look like this:

```json
{
  "content": {
    "filename": "something-important.doc",
    "info": {
      "mimetype": "application/msword",
      "size": 46144
    },
    "msgtype": "m.file",
    "url": "mxc://example.org/n3wv3rs10n",
    "delta_base": "$1235135aksjgdkg",
    "delta_format": "m.vcdiff.v1.gzip"
  },
}
```

We could go even further down this path by defining an arbitrary CRDT for tracking these deltas, a bit like the
(Saguaro CRDT-over-Matrix)[https://github.com/matrix-org/collaborative-documents/blob/main/docs/saguaro.md] proposal,
with files decorating each event - effectively modelling the problem as a collaborative document problem (with binary
diffs attached) rather than a binary file diffing problem.

### Other alternatives

We could use HTTP PATCH rather than POST when sending diffs.  This feels needlessly exotic, imo.

Rather than having a delta_format field, we could use the MIME type of the upload to indicate that it's a patch to a
given underlying MIME type. However, Matrix doesn't currently have to parse MIME types anywhere, so it's more matrixy
to destructure this in JSON.

For unencrypted files, the server could apply the diffs serverside as a convenience to clients who don't know
how to apply the diffs themselves (or who don't have CPU to apply the diffs, or want to benefit from the server caching
diff results).  This could be proposed as a separate MSC.

## Security considerations

This exposes the metadata of which file is a delta to which other file to the server.

DoS by too many deltas

DoS by using async uploads to create a cycle

## Unstable prefix

| Param        | Unstable prefixed param          | 
| ------------ | -------------------------------- |
| delta_base   | org.matrix.msc4083.delta_base    |
| delta_format | org.matrix.msc4083.delta_format  |

## Dependencies

None. Although [MSC4016](https://github.com/matrix-org/matrix-spec-proposals/pull/4016) was sketched out at the same
time and the two are siblings.