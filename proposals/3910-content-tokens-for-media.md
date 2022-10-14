# MSC3910: Content tokens for media

(Based on [MSC~~701~~3796](https://github.com/matrix-org/matrix-spec-proposals/issues/3796).)

Currently, access to media in Matrix has the following problems:
 
* The only protection for media is the obscurity of the URL, and URLs are
  easily leaked (eg accidental sharing, access
  logs). [synapse#2150](https://github.com/matrix-org/synapse/issues/2150)
* Anybody (including non-matrix users) can cause a homeserver to copy media
  into its local
  store. [synapse#2133](https://github.com/matrix-org/synapse/issues/2133)
* When a media event is redacted, the media it used remains visible to all.
  [synapse#1263](https://github.com/matrix-org/synapse/issues/1263)
* There is currently no way to delete
  media. [matrix-spec#226](https://github.com/matrix-org/matrix-spec/issues/226)
* If a user requests GDPR erasure, their media remains visible to all.
* When all users leave a room, their media is not deleted from the server.

## Proposal

### Overview

Each piece of uploaded media gains an associated `content_token`.  This is
included alongside the `mxc://` uri whenever the content is referenced; for
encrypted events it is included in the *cleartext* (unencrypted) part of the
event. Critically, it is never embedded into a URL.

Clients must present both their `access_token` (to prove they have the right to
use the server) *and* the `content_token` (to prove they have the right to see
the media in question).

Servers can count the number of references to a given `content_token`, and
expire any media whose refcount falls to zero.

### Detailed spec changes

1. [`/_matrix/media/v3/upload`](https://spec.matrix.org/v1.4/client-server-api/#post_matrixmediav3upload)
   creates a (cryptographically-secure) random "content token" for the media,
   and returns it alongside the `content_uri`. Result now looks like:
   ```json
   {
     "content_uri": "mxc://example.com/AQwafuaFswefuhsfAFAgsw",
     "content_token": "hunter2"
   }
   ```
2. Passing the content token on to other users:
   * When sending `m.image` and `m.video` messages, the client includes a `content_token` property:
     ```json
     {
       "type": "m.room.message",
       "content": {
         "body": "filename.jpg",
         "msgtype": "m.image",
         "url": "mxc://example.com/AQwafuaFswefuhsfAFAgsw",
         "content_token": "hunter2"
       }
     }
     ```
   * Encrypted media messages must include the `content_token` in the cleartext:
     ```json
     {
       "type": "m.room.encrypted",
       "content": {
         "algorithm": "m.megolm.v1.aes-sha2",
         "session_id": "<outbound_group_session_id>",
         "ciphertext": "<encrypted_payload_base_64>",
         "content_token": "hunter2"
       }
     }
     ```
   * Likewise `m.room.avatar_url` must include a `content_token`:
     ```json
     {
       "type": "m.room.avatar",
       "state_key": "",
       "content": {
         "url": "mxc://example.com/AQwafuaFswefuhsfAFAgsw",
         "content_token": "hunter2"
       }
     }
     ```
   * And `m.room.member` must include an `avatar_content_token`:
     ```json
     {
       "type": "m.room.member",
       "state_key": "@alice:example.org",
       "content": {
         "avatar_url": "mxc://example.org/AQwafuaFswefuhsfAFAgsw",
         "avatar_content_token": "hunter2",
         "displayname": "Alice Margatroid",
         "membership": "join"
       }
     }
     ```
   * [`PUT /_matrix/client/v3/profile/{userId}/avatar_url`](https://spec.matrix.org/v1.4/client-server-api/#put_matrixclientv3profileuseridavatar_url) 
     requests should include an `avatar_content_token` alongside the `avatar_url`.

3. New download endpoints
     
   The existing download endpoints are to be deprecated, and replaced with new
   endpoints specific to client-server or federation requests:
     
   | Old                                                                                                                                                              | Client-Server                                                             | Federation                                                          |
   | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------- |
   | [`GET /_matrix/media/v3/download/{serverName}/{mediaId}`](https://spec.matrix.org/v1.4/client-server-api/#get_matrixmediav3downloadservernamemediaid)            | `GET /_matrix/client/v1/media/download/{serverName}/{mediaId}`            | `GET /_matrix/federation/v1/media/download/{serverName}/{mediaId}`  |
   | [`GET /_matrix/media/v3/download/{serverName}/{mediaId}/{fileName}`](https://spec.matrix.org/v1.4/client-server-api/#get_matrixmediav3downloadservernamemediaid) | `GET /_matrix/client/v1/media/download/{serverName}/{mediaId}/{fileName}` | N/A                                                                 |
   | [`GET /_matrix/media/v3/thumbnail/{serverName}/{mediaId}`](https://spec.matrix.org/v1.4/client-server-api/#get_matrixmediav3thumbnailservernamemediaid)          | `GET /_matrix/client/v1/media/thumbnail/{serverName}/{mediaId}`           | `GET /_matrix/federation/v1/media/thumbnail/{serverName}/{mediaId}` |

   [Question: should we move `/config`, `/upload` and `/preview_url` while
   we're at it, per [MSC1902](https://github.com/matrix-org/matrix-spec-proposals/pull/1902)?]

   None of the new endpoints take an `allow_remote` query parameter. (For
   `/_matrix/client`, servers should always attempt to request remote
   media. For `/_matrix/federation`, servers should never attempt to request
   remote media they do not already have cached.)

   **Two** authorization headers must be given when calling these endpoints:
     
   * `Authorization` must be set the same as for any other CSAPI or federation
     request (ie, `Bearer {accessToken}` for `/_matrix/client`, or the
     signature for `/_matrix/federation`).
   * `X-Matrix-Content-Token` must be set to the `content_token`.

   `X-Matrix-Content-Token` should be omitted for legacy media which has no
   `content_token`.  Otherwise, if no `X-Matrix-Content-Token` header is given,
   the server should respond with an HTTP 401 error, with error code
   `{"errcode": "M_MISSING_CONTENT_TOKEN"}`.
       
   If the `content_token` does not match that for the media, the server should
   respond with an HTTP 403 error, with error code `{"errcode":
   "M_UNAUTHORIZED"}`.
   
   If `X-Matrix-Content-Token` is supplied, but the requested media has no
   `content_token`, the server should likewise reject the request with
   `M_UNAUTHORIZED`. (This is important to avoid a cache-poisoning attack.)

   For each of the new endpoints, the response format is the same as the
   corresponding original endpoints.

4. Flow for remote media downloads

   When a server receives a request to `GET
   /_matrix/client/v1/media/download/{remoteServer}/{mediaId}`, it first
   validates the `access_token` in the `Authorization` header.
   
   If the access token is valid, the server checks its cache for
   `(remoteServer, mediaId)`. If the media is cached, we should also have a
   record of the expected `content_token`.  The server therefore checks the
   `X-Matrix-Content-Token` header, and returns either the media or a 403
   error.
   
   If the media is uncached, the user's server makes a request to `GET
   /_matrix/federation/v1/media/download/{remoteServer}/{mediaId}` on the
   remote server, passing on any `content_token` provided by the client.
      
   The remote server will return either the media (with a 200 response), or an
   error.
     
   Errors are returned to the client (as today). If the request was successful,
   the local server may cache the returned media for future users. If it does
   so, it *must* also store the `content_token` so that future requests can be
   validated.
 
5. Backwards compatibility mechanisms

   a. Backwards compatibility with older servers: if a client or requesting
   server receives a 404 error with a non-JSON response, or a 400 error with
   `{"errcode": "M_UNRECOGNIZED"}`, in response to a request to one of the new
   endpoints, they may retry the request using the original endpoint.
   
   Servers must only do this if there is no `X-Matrix-Content-Token` in the
   request (the fact that a content token is available implies that the origin
   server must support the new endpoints).
   
   Clients should retry the request whether or not they have a content token.

   b. Backwards compatibility with older clients and federating servers:
   servers may for a short time choose to allow unauthenticated access via the
   deprecated endpoints, even for media with an associated `content_token`.

6. URL preview

   The
   [`/preview_url`](https://spec.matrix.org/v1.4/client-server-api/#get_matrixmediav3preview_url)
   endpoint returns an object that references an image for the previewed
   site. Such media should continue not to have a `content_token`. (It is not
   related to particular events, and servers should already be expiring such
   media anyway.)

Grammar:

* `content_token`: between 1 and 255 characters, from [ALPHA DIGIT "-" / "." /
  "_" / "~"]: consistent with
  [MSC1597](https://github.com/matrix-org/matrix-spec-proposals/blob/rav/proposals/id_grammar/proposals/1597-id-grammar.md#opaque-ids)
  and [`m.login.sso`
  identifiers](https://spec.matrix.org/v1.4/client-server-api/#mloginsso-flow-schema).

### Applications

The following discusses the impact of this proposal on various parts of
ecosystem: we consider the changes that will be required for existing
implementations, and how the proposal will facilitate future extensions.

#### IRC/XMPP bridges

Possibly the largest impact will be on IRC and XMPP bridges.  Since IRC and
XMPP have no media repository of their own, these bridges currently transform
`mxc:` URIs into `https://<server>/_matrix/media/v3/download/` URIs and forward
those links to the remote platform. This will no longer be a viable option.

This is largely a problem to be solved by the bridge implementations, but one
potential solution is for the bridges to provide a proxy.

In this scenario, the bridge would have a secret encryption key. When it
receives a matrix event referencing a piece of media, it would encrypt the
`content_token` and embed it in a new URI; for example:

```
https://<bridge_server>/media/{originServerName}/{mediaId}?t={encryptedContentToken}
```

When the bridge later receives a request to that URI, it can decrypt the
content token, and proxy the request to the homeserver, using its AS access
token in the `Authorization` header.

This mechanism also works for a secondary use of the content repository in
bridges: as a paste-bin. In this case, the bridge simply generates a link
referencing its own media.

The bridge might also choose to embed information such as the room that
referenced the media, and the time that the link was generated, in the URL.
(Such information would require an HMAC to prevent tampering.) This could be
used to help control access to the media.

Such mechanisms would allow the bridge to impose controls such as:

* Limiting the time a media link is valid for. Doing so would help prevent
  visibility to users who weren't participating in the chat.

* Rate-limiting the amount of media being shared in a particular room (in other
  words, avoiding the use of Matrix as a Warez distribution system).

#### Redacting events

Under this proposal, servers can determine which media is referenced by an
event that is redacted, and add that media to a list to be cleaned up, as long
as it is not referenced elsewhere.

This would also apply if all users in a room are deactivated (either via a GDPR
section 17 request or by a self-requested "Deactivate account" request). In
this case, all events in the room, and all media referenced by them, should be
removed. Currently, Synapse does not support removing the events (see also
[synapse#4720](https://github.com/matrix-org/synapse/issues/4720)); but if at
some point in the future this is added, then this proposal makes it easy to
extend to deleting the media.

Fixes [synapse#1263](https://github.com/matrix-org/synapse/issues/1263).

#### Icons for "social login" flows

When a server supports multiple login providers, it provides the client with
icons for the login providers as `mxc:` media URIs. These must be accessible
without authentication (because the client has no access token at the time the
icons are displayed).

This remains a somewhat unsolved problem. Possibly the clients can continue
to call the legacy `/_matrix/media/v3/download` URI for now: ultimately this
problem will be solved by the transition to OIDC. Alternatively, we may need
to provide an alternative `/_matrix/client/v3/login/sso/icon/{idpId}` API
specifically for access to these icons.

We also need to ensure that the icons are not deleted from the content
repository even though their `content_token`s are not referenced anywhere.  It
would be wise for servers to provide administrators with a mechanism to prevent
cleanup of certain media items.

(This was previously discussed in
[MSC2858](https://github.com/matrix-org/matrix-spec-proposals/pull/2858#discussion_r543513811).)

## Potential issues

* Setting the headers is going to be annoying for web clients. Service workers
  might be needed.

* Is it possible some reverse-proxies will strip the `X-Matrix-Content-Token`?

* Users will be unable to copy links to media from web clients to share out of
  band. This is considered a feature, not a bug.

## Alternatives

* Rather than trust users not to pass the content_token around, we could tie the media more
  strongly to an event, and then check that the user has access to the event. For example:
  
  * Uploading does not itself make the content visible by *anyone*; it does return a nonce
  * Sending events takes a `media_nonce` param. The media gets associated with
    the event and becomes visible to anyone who can see the event. The nonce
    gets invalidated.
  * For profile pics, the media gets duplicated for each m.room.member event it
    ends up in.
  * When the media is served over federation, we check if anyone on the server
    has a right to see it (as we would with its associated event), and if so,
    include the associated event in the response. The requesting server then
    filters further.
  
  (credit: based on ideas at
  https://cryptpad.fr/code/#/2/code/view/oWjZciD9N1aWTr1IL6GRZ0k1i+dm7wJQ7juLf4tJRoo/)
  
  Problems with this approach:
   * Forwarded media would require either a re-upload, or a server-side duplication.
     (Note that matrix-media-repo has a [LocalCopy](https://github.com/turt2live/matrix-media-repo/blob/master/api/unstable/local_copy.go#L19) implementation for this.)

* Allow clients to upload media which does not require authentication (for
  example via a `public=true` query parameter). This might be particularly
  useful for IRC/XMPP bridges, which could upload any media they encounter to
  the homeserver's repository.

  The danger with this is that is that there's little stopping clients
  continuing to upload media as "public", negating all of the benefits in this
  MSC. It might be ok if media upload it was restricted to certain privileged
  users.

* Rather than require a dedicated HTTP header, put something user-specific in
  the query string; for example, encrypt the content token with a key based on
  the access token? Tying it to the specific user means that the link isn't any
  use to anyone else.
  
  Not sure this offers much advantage over a separate header, whereas it does
  add complexity.
  
* Put the `content_token` within the encrypted content, for encrypted data.
  This reduces the metadata leak, but means that none of the automated media
  removal functionality works.

## Security considerations

* Letting servers track the relationship between events and media is a metadata
  leak, especially for e2ee rooms.

## Unstable prefix

TODO

## Dependencies

None at present.

## Prior art

* [MSC~~701~~3796](https://github.com/matrix-org/matrix-spec-proposals/issues/3796):
  a predecessor of this proposal

* [MSC2461](https://github.com/matrix-org/matrix-spec-proposals/pull/2461):
  adds per-user authentication but does not attempt to restrict access to
  individual items of media.

* [MSC2278](https://github.com/matrix-org/matrix-spec-proposals/pull/2278):
  Deleting attachments for expired and redacted messages

* [MSC1902](https://github.com/matrix-org/matrix-spec-proposals/pull/1902):
  Split the media repo into s2s and c2s parts

* [MSC2846](https://github.com/matrix-org/matrix-spec-proposals/pull/2846):
  Decentralizing media through CIDs
  
  
