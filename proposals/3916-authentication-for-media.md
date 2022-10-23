# MSC3916: Authentication for media access, and new endpoint names

Currently, access to media in Matrix has a number of problems including the following:
 
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

These problems are all difficult to address currently, because access to media
is entirely unauthenticated. The first step for a solution is to require user
authentication. Once that is done, it will be possible to impose authorization
requirements to address the problems mentioned above. (See, for example,
[MSC3911](https://github.com/matrix-org/matrix-spec-proposals/pull/3911) which
builds on top of this MSC.)

This proposal supersedes [MSC1902](https://github.com/matrix-org/matrix-spec-proposals/pull/1902).

## Proposal

1. New endpoints

   The existing `/_matrix/media/v3/` endpoints are to be deprecated, and replaced
   by new endpoints under the `/_matrix/client` and `/_matrix/federation`
   hierarchies.

   The table below shows a mapping between old and new endpoint:

   | Old                                                                                                                                                              | Client-Server                                                             | Federation                                                          |
   | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------- |
   | [`GET /_matrix/media/v3/preview_url`](https://spec.matrix.org/v1.4/client-server-api/#get_matrixmediav3preview_url) | `GET /_matrix/client/v1/media/preview_url` | - |
   | [`GET /_matrix/media/v3/config`](https://spec.matrix.org/v1.4/client-server-api/#get_matrixmediav3config) | `GET /_matrix/client/v1/media/config` | - |
   | [`GET /_matrix/media/v3/download/{serverName}/{mediaId}`](https://spec.matrix.org/v1.4/client-server-api/#get_matrixmediav3downloadservernamemediaid)            | `GET /_matrix/client/v1/media/download/{serverName}/{mediaId}`            | `GET /_matrix/federation/v1/media/download/{serverName}/{mediaId}`  |
   | [`GET /_matrix/media/v3/download/{serverName}/{mediaId}/{fileName}`](https://spec.matrix.org/v1.4/client-server-api/#get_matrixmediav3downloadservernamemediaidfilename) | `GET /_matrix/client/v1/media/download/{serverName}/{mediaId}/{fileName}` | -                                                                 |
   | [`GET /_matrix/media/v3/thumbnail/{serverName}/{mediaId}`](https://spec.matrix.org/v1.4/client-server-api/#get_matrixmediav3thumbnailservernamemediaid)          | `GET /_matrix/client/v1/media/thumbnail/{serverName}/{mediaId}`           | `GET /_matrix/federation/v1/media/thumbnail/{serverName}/{mediaId}` |

   **Note**: [`POST /_matrix/media/v3/upload`](https://spec.matrix.org/v1.4/client-server-api/#post_matrixmediav3upload)
   is **not** modified by this MSC: it is intended that it be brought into line with the other
   endpoints by a future MSC, such as [MSC3911](https://github.com/matrix-org/matrix-spec-proposals/pull/3911).

2. Removal of `allow_remote` parameter from `/download`

   The current
   [`/download`](https://spec.matrix.org/v1.4/client-server-api/#get_matrixmediav3downloadservernamemediaid)
   and
   [`/thumbnail`]((https://spec.matrix.org/v1.4/client-server-api/#get_matrixmediav3thumbnailservernamemediaid)
   endpoints take an `allow_remote` query parameter, indicating whether the
   server should request remote media from other servers. This is redundant
   with the new endpoints, so will not be supported.

   Servers should never return remote media from `GET
   /_matrix/federation/v1/media/download` or `GET
   /_matrix/federation/v1/media/thumbnail`; indeed, the `serverName` is
   included in the URI only for consistency with the CS-API.

   `/_matrix/client/v1/media/download` and
   `/_matrix/client/v1/media/thumbnail` should return remote media as normal.
   
3. Authentication on all endpoints

   Currently, the `/download` and `/thumbnail` endpoints have no authentication
   requirements. Under this proposal, the new endpoints will be authenticated
   the same way as other endpoints: they will require an `Authorization` header
   which must be `Bearer {accessToken}` for `/_matrix/client`, or the signature
   for `/_matrix/federation`.

4. Updated response format

   * For the new `/_matrix/client` endpoints, the response format is the same as
     the corresponding original endpoints.

   * To enable future expansion, for the new `/_matrix/federation` endpoints,
     the response is
     [`multipart/mixed`](https://www.w3.org/Protocols/rfc1341/7_2_Multipart.html)
     content with two parts: the first must be a JSON object (and should have a
     `Content-type: application/json` header), and the second is the media item
     as per the original endpoints.

     No properties are yet specified for the JSON object to be returned.

     An example response:

     ```
     Content-Type: multipart/mixed; boundary=gc0p4Jq0M2Yt08jU534c0p

     --gc0p4Jq0M2Yt08jU534c0p
     Content-Type: application/json

     {}

     --gc0p4Jq0M2Yt08jU534c0p
     Content-Type: text/plain

     This media is plain text. Maybe somebody used it as a paste bin.

     --gc0p4Jq0M2Yt08jU534c0p
     ```
     
5. Backwards compatibility mechanisms

   a. Backwards compatibility with older servers: if a client or requesting
   server receives a 404 error with a non-JSON response, or a 400 or 404 error with
   `{"errcode": "M_UNRECOGNIZED"}`, in response to a request to one of the new
   endpoints, they may retry the request using the original endpoint.
   
   b. Backwards compatibility with older clients and federating servers:
   servers may for a short time choose to allow unauthenticated access via the
   deprecated endpoints.

### Effects on client applications

Naturally, implementations will be required to provide `Authorization` headers
when accessing the new endpoints. This will be simple in some cases, but rather
more involved in others. This section considers some of those cases.

#### IRC/XMPP bridges

Possibly the largest impact will be on IRC and XMPP bridges.  Since IRC and
XMPP have no media repository of their own, these bridges currently transform
`mxc:` URIs into `https://<server>/_matrix/media/v3/download/` URIs and forward
those links to the remote platform. This will no longer be a viable option.

One potential solution is for the bridges to provide a proxy.

In this scenario, the bridge would have a secret HMAC key. When it
receives a matrix event referencing a piece of media, it should create a new URI
referencing the media, include an HMAC to prevent tampering. For example:

```
https://<bridge_server>/media/{originServerName}/{mediaId}?mac={hmac}
```

When the bridge later receives a request to that URI, it checks the hmac,
and proxies the request to the homeserver, using its AS access
token in the `Authorization` header.

The bridge might also choose to embed information such as the room that
referenced the media, and the time that the link was generated, in the URL.
Such mechanisms would allow the bridge to impose controls such as:

* Limiting the time a media link is valid for. Doing so would help prevent
  visibility to users who weren't participating in the chat.

* Rate-limiting the amount of media being shared in a particular room (in other
  words, avoiding the use of Matrix as a Warez distribution system).

#### Icons for "social login" flows

When a server supports multiple login providers, it provides the client with
icons for the login providers as `mxc:` media URIs. These must be accessible
without authentication (because the client has no access token at the time the
icons are displayed).

This remains a somewhat unsolved problem. Possibly the clients can continue
to call the legacy `/_matrix/media/v3/download` URI for now: ultimately this
problem will be solved by the transition to OIDC. Alternatively, we may need
to provide an alternative `/_matrix/client/v3/login/sso/icon/{idpId}` API
specifically for access to these icon.

(This was previously discussed in
[MSC2858](https://github.com/matrix-org/matrix-spec-proposals/pull/2858#discussion_r543513811).)

## Potential issues

* Setting the `Authorization` header is going to be annoying for web clients. Service workers
  might be needed.

* Users will be unable to copy links to media from web clients to share out of
  band. This is considered a feature, not a bug.

## Alternatives

* Allow clients to upload media which does not require authentication (for
  example via a `public=true` query parameter). This might be particularly
  useful for IRC/XMPP bridges, which could upload any media they encounter to
  the homeserver's repository.

  The danger with this is that is that there's little stopping clients
  continuing to upload media as "public", negating all of the benefits in this
  MSC. It might be ok if media upload it was restricted to certain privileged
  users.

* We could simply require that `Authorization` headers be given when calling
  the existing endpoints. However, doing so would make it harder to evaluate
  the proportion of clients which have been updated, and it is a good
  opportunity to bring these endpoints into line with the rest of the
  client-server and federation APIs.
  
* There's no real need to rename `GET /_matrix/media/v3/preview_url` and `GET
  /_matrix/media/v3/config` at present, and we could just leave them in
  place. However, changing them at the same time makes the API more consistent.

  Conversely, we should make sure to rename `POST
  /_matrix/media/v3/upload`. The reason to delay doing so is because MSC3911
  will make more substantial changes to this endpoint, requiring another
  rename, and it is expected that both proposals will be mergeed at the same
  time (so a double rename will be confusing and unnecessary). However, if
  MSC3911 is delayed or rejected, we should reconsider this.

* Rather than messing with multipart content, have a separate endpoint for
  servers to get the metadata for a media item. That would mean two requests,
  but might make more sense than both `/thumbnail` and `/download` providing
  the info.

## Unstable prefix

While this proposal is in development, the new endpoints should be named as follows:

* `GET /_matrix/client/unstable/org.matrix.msc3916/media/preview_url`
* `GET /_matrix/client/unstable/org.matrix.msc3916/media/config`
* `GET /_matrix/client/unstable/org.matrix.msc3916/media/download/{serverName}/{mediaId}`
* `GET /_matrix/client/unstable/org.matrix.msc3916/media/download/{serverName}/{mediaId}/{fileName}`
* `GET /_matrix/client/unstable/org.matrix.msc3916/media/thumbnail/{serverName}/{mediaId}`
* `GET /_matrix/federation/unstable/org.matrix.msc3916/media/download/{serverName}/{mediaId}`
* `GET /_matrix/federation/unstable/org.matrix.msc3916/media/thumbnail/{serverName}/{mediaId}`

## Dependencies

None at present.
