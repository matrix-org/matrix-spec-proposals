Currently, media is fetched from the homeserver it is sent from only. If said homeserver is down, there is no way to fetch said media. This is unlike room history, which is fetchable from other homeservers. This proposal aims to allow securely fetching media from homeservers that did not originate it.
## Proposal
Homeservers should create media ID's in the form `algorithm:hash`. Currently the only defined algorithm is `m.sha256`. For example, a media ID may look like `m.sha256:9834876dcfb05cb167a5c24953eba58c4ac89b1adf57f28f2f9d09af107ee8f0` and the corresponding mxc URI may look like `mxc://blob.cat/m.sha256:9834876dcfb05cb167a5c24953eba58c4ac89b1adf57f28f2f9d09af107ee8f0`.

Homeservers should first try to download media from the origin media server, as they do now. They should not reject media with a non-matching hash from the origin homeserver.

If the origin homeserver is unreachable, homeservers may attempt to download media from other homeservers they believe to have it. The fetching homeserver should only attempt this if the media ID is a valid hash type that it understands. These can be any homeservers that share a room where media was sent. A homeserver should prioritize the homeserver it backfills room history from as the first homeserver it attempts to fetch media from.

The homeserver fetching the media should reject the fetched media if the hash does not match.

## Alternatives
IPFS as a media repository [MSC2706](https://github.com/matrix-org/matrix-doc/pull/2706) also allows redundant media hosting, and fetching from the non-origin homeserver. However, that would require significant spec and server changes, while the changes here are minor.
