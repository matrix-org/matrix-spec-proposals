Currently, media is fetched from the homeserver it is sent from only. If said homeserver is down, there is no way to fetch said media.
This is unlike room history, which is fetchable from other homeservers. This proposal aims to allow securely fetching media from homeservers that did not originate it.

## Proposal
Homeservers should create media IDs in the form `algorithm:hash`. Currently the only defined algorithm is `m.sha256`.
For example, a media ID may look like `m.sha256:9834876dcfb05cb167a5c24953eba58c4ac89b1adf57f28f2f9d09af107ee8f0`.

Since secure hashing algorithms will create hashes that are unique across the Matrix network, homeservers are no longer part of the `mxc`.
To allow routing, two parameters are added to the `mxc` URI, and therefore also supported by all endpoints for fetching media and media thumbnails: `via` and `viaroom`.
`via` specifies which homeserver to fetch the media from, and should be specified at least once.
`viaroom` specifices which room the media is and may be supplied exactly once.

For example, when uploading a file, the mxc URI returned by the server should look like the following: `mxc:m.sha256:9834876dcfb05cb167a5c24953eba58c4ac89b1adf57f28f2f9d09af107ee8f0?via=blob.cat`.
When sent to the room `!exampleroom:blob.cat`, the client should send it as `mxc:m.sha256:9834876dcfb05cb167a5c24953eba58c4ac89b1adf57f28f2f9d09af107ee8f0?via=blob.cat&viaroom=!exampleroom:blob.cat`.

Homeservers should first look in their cache when serving media, then attempt to fetch it from any `via` parameters of the request, then attempt to fetch it from any homeservers in the room specified by `viaroom`.
The homeserver may also attempt to fetch it from any other homeservers it thinks may have the media, for whatever reasons specified outside of this proposal.

Homeservers must reject media with a non-matching hash, and treat it as if the media was not available from the homeserver it was fetched from.

Servers must not supply `via` or `viaroom` parameters when fetching media from remote servers. This is to avoid infinite recursion, leading to DoS.

## Implementation details

Homeservers may wish to store which homeserver media was fetched from, and which room it was fetched from, to aid in things such as cleaning up spam.
Homeservers may also choose to prioritize storing media which was uploaded by their users over media which was fetched from remote homeservers.

## API changes

`POST /_matrix/media/r0/upload`'s output should be like the following:
```
{
  "content_uri": "mxc:m.sha256:9834876dcfb05cb167a5c24953eba58c4ac89b1adf57f28f2f9d09af107ee8f0?via=blob.cat"
}
```
* `GET /_matrix/media/r0/download/{mediaId}`  
* `GET /_matrix/media/r0/download/{mediaId}/{fileName}`
* `GET /_matrix/media/r0/thumbnail/{mediaId}`

are added as APIs, with the parameters `via` and `viaroom` as specified earlier in the spec.

### Backwards compatiblity
Old format `mxc` URIs, like `mxc://blob.cat/d9663bbcfad4a4ef4612e9bb6aab2c696bc0f038`, should still be supported as before in all media APIs, with the exception of the upload API, which should return `mxc` URIs following this spec.

## Alternatives
IPFS as a media repository [MSC2706](https://github.com/matrix-org/matrix-doc/pull/2706) also allows redundant media hosting, and fetching from the non-origin homeserver. However, that would require significant spec and server changes (implementing an entirely separate protocol), while the changes here are relatively minor (though breaking), and easier to integrate with current Matrix homeservers and clients.
