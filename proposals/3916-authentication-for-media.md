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

   The existing `/_matrix/media/v3/` endpoints become deprecated, and new
   endpoints under the `/_matrix/client` and `/_matrix/federation`
   hierarchies are introduced. Removal of the deprecated endpoints would be a
   later MSC under [the deprecation policy](https://spec.matrix.org/v1.10/#deprecation-policy).

   The following table below shows a mapping between deprecated and new endpoint:

   | Deprecated                                                                                                                                                       | Client-Server                                                             | Federation                                                          |
   | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------- |
   | [`GET /_matrix/media/v3/preview_url`](https://spec.matrix.org/v1.6/client-server-api/#get_matrixmediav3preview_url) | `GET /_matrix/client/v1/media/preview_url` | - |
   | [`GET /_matrix/media/v3/config`](https://spec.matrix.org/v1.6/client-server-api/#get_matrixmediav3config) | `GET /_matrix/client/v1/media/config` | - |
   | [`GET /_matrix/media/v3/download/{serverName}/{mediaId}`](https://spec.matrix.org/v1.6/client-server-api/#get_matrixmediav3downloadservernamemediaid)            | `GET /_matrix/client/v1/media/download/{serverName}/{mediaId}`            | `GET /_matrix/federation/v1/media/download/{serverName}/{mediaId}`  |
   | [`GET /_matrix/media/v3/download/{serverName}/{mediaId}/{fileName}`](https://spec.matrix.org/v1.6/client-server-api/#get_matrixmediav3downloadservernamemediaidfilename) | `GET /_matrix/client/v1/media/download/{serverName}/{mediaId}/{fileName}` | -                                                                 |
   | [`GET /_matrix/media/v3/thumbnail/{serverName}/{mediaId}`](https://spec.matrix.org/v1.6/client-server-api/#get_matrixmediav3thumbnailservernamemediaid)          | `GET /_matrix/client/v1/media/thumbnail/{serverName}/{mediaId}`           | - |

   **Note**: [`POST /_matrix/media/v3/upload`](https://spec.matrix.org/v1.6/client-server-api/#post_matrixmediav3upload)
   is **not** modified by this MSC: it is intended that it be brought into line with the other
   endpoints by a future MSC, such as [MSC3911](https://github.com/matrix-org/matrix-spec-proposals/pull/3911).
   It is subsequently **not** deprecated either.

   **Note**: `/thumbnail` does not have a federation endpoint. It appears as though
   no servers request thumbnails over federation, and so it is not supported here.
   A later MSC may introduce such an endpoint.

   The new `/download` and `/thumbnail` endpoints additionally drop the `?allow_redirect`
   query parameters. Instead, the endpoints behave as though `allow_redirect=true` was
   set, regardless of actual value. See [this comment on MSC3860](https://github.com/matrix-org/matrix-spec-proposals/pull/3860/files#r1005176480)
   for details.

   After this proposal is released in a stable version of the specification, servers
   which support the new `download` and `thumbnail` endpoints SHOULD cease to serve
   newly uploaded media from the unauthenticated versions. This includes media
   uploaded by local users and requests for not-yet-cached remote media. This is
   done with a 404 `M_NOT_FOUND` error, as though the media doesn't exist. Servers
   SHOULD consider their local ecosystem impact before freezing the endpoints. For
   example, ensuring that common bridges and clients will continue to work, and
   encouraging updates to those affected projects as needed.

2. Removal of `allow_remote` parameter from `/download`

   The current
   [`/download`](https://spec.matrix.org/v1.6/client-server-api/#get_matrixmediav3downloadservernamemediaid)
   and
   [`/thumbnail`](https://spec.matrix.org/v1.6/client-server-api/#get_matrixmediav3thumbnailservernamemediaid)
   endpoints take an `allow_remote` query parameter, indicating whether the
   server should request remote media from other servers. This is redundant
   with the new endpoints, so will not be supported.

   Servers MUST never return remote media from `GET /_matrix/federation/v1/media/download`;
   indeed, the `serverName` is included in the URI only for consistency with the CS-API.

   `/_matrix/client/v1/media/download` and
   `/_matrix/client/v1/media/thumbnail` return remote media as normal.

3. Authentication on all endpoints

   Currently, the `/download` and `/thumbnail` endpoints have no authentication
   requirements. Under this proposal, the new endpoints will be authenticated
   the same way as other endpoints: they will require an `Authorization` header
   which must be `Bearer {accessToken}` for `/_matrix/client`, or the signature
   for `/_matrix/federation`.

   **Note**: This fixes [matrix-spec#313](https://github.com/matrix-org/matrix-spec/issues/313).

4. Updated response format

   * For the new `/_matrix/client` endpoints, the response format is the same as
     the corresponding original endpoints.

   * To enable future expansion, for the new `/_matrix/federation` endpoints,
     the response is
     [`multipart/mixed`](https://www.w3.org/Protocols/rfc1341/7_2_Multipart.html)
     content with exactly two parts: the first MUST be a JSON object (and should have a
     `Content-type: application/json` header), and the second MUST be the media item
     as per the original endpoints.

     No properties are yet specified for the JSON object to be returned. One
     possible use is described by [MSC3911](https://github.com/matrix-org/matrix-spec-proposals/pull/3911).

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

   a. Backwards compatibility with older servers: if a client or requesting server
   receives a 404 error with `M_UNRECOGNIZED` error code in response to a request
   using the new endpoints, they may retry the request using the deprecated
   endpoint. Servers and clients should note the [`M_UNRECOGNIZED`](https://spec.matrix.org/v1.10/client-server-api/#common-error-codes)
   error code semantics.

   b. Backwards compatibility with older clients and federating servers: mentioned
   in Part 1 of this proposal, servers *may* freeze unauthenticated media access
   once stable authenticated endpoints are available. This may lead to client and
   server errors for new media. Both clients and servers are strongly encouraged
   to update as soon as possible, before servers freeze unauthenticated media
   access.

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

* Setting the `Authorization` header is particularly annoying for web clients.
  Service workers are seemingly the best option, though other options include
  locally-cached `blob:` URIs. Clients should note that caching media can lead
  to significant memory usage, particularly for large media. Service workers by
  comparison allow for proxy-like behaviour.

* Users will be unable to copy links to media from web clients to share out of
  band. This is considered a feature, not a bug.

* Over federation, the use of the `Range` request header on `/download` becomes
  unclear as it could affect either or both parts of the response. There does not
  appear to be formal guidance in [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110#field.range)
  either. There are arguments for affecting both and either part equally. Typically,
  such a header would be used to resume failed downloads, though servers are
  already likely to discard received data and fail the associated client requests
  when the federation request fails. Therefore, servers are unlikely to use `Range`
  at all. As such, this proposal does not make a determination on how `Range`
  should be handled, and leaves it as an HTTP specification interpretation problem
  instead.

* [MSC3860](https://github.com/matrix-org/matrix-spec-proposals/pull/3860)-style
  redirects are harder to implement for the federation endpoints. It's presumed
  that CDNs can either cache the multipart type (later to be combined with linked
  media authentication, like [MSC3911](https://github.com/matrix-org/matrix-spec-proposals/pull/3911)),
  or the CDN can be somehow told the parameters it needs to return. For example,
  `Location: https://cdn.example.org/media?mx_json={}`. Popular CDN providers
  support this sort of request rewriting. Relatedly, [MSC4097](https://github.com/matrix-org/matrix-spec-proposals/pull/4097)
  may be of interest to readers.

## Alternatives

* Allow clients to upload media which does not require authentication (for
  example via a `public=true` query parameter). This might be particularly
  useful for IRC/XMPP bridges, which could upload any media they encounter to
  the homeserver's repository.

  The danger with this is that is that there's little stopping clients
  continuing to upload media as "public", negating all of the benefits in this
  MSC. It might be ok if media upload it was restricted to certain privileged
  users, or applied after the fact by a server administrator.

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
  rename, and it is expected that both proposals will be mergeed near to the same
  time as each other (so a double rename will be confusing and unnecessary). However,
  if MSC3911 is delayed or rejected, we should reconsider this.

* Rather than messing with multipart content, have a separate endpoint for
  servers to get the metadata for a media item. That would mean two requests,
  but might make more sense than `/download` providing the info directly.

### Compared to MSC3796 (MSC701)

[MSC701/3796](https://github.com/matrix-org/matrix-spec-proposals/issues/3796)
introduces a concept of "content tokens" which have authentication tie-in to
prevent anonymous users from accessing media. This is a similar problem space
to this proposal, though deals more in the event-to-media linking space instead.
Although the MSC is an early sketch, it's unclear if the problems noted on the
MSC itself are feasibly resolvable.

### Compared to MSC2461

[MSC2461](https://github.com/matrix-org/matrix-spec-proposals/pull/2461) adds
authentication to the existing media endpoints, which as noted here in the
Alternatives is not likely to roll out quickly and leaves an inconsistency in
the spec. MSC2461 also introduces a client-visible flag for which kinds of media
may require authentication, making it similar to the alternative listed above
where on the federation side we could have two endpoints: one for information
and one for the media itself. MSC2461 simply makes the information client-visible
instead of server-visible.

## Unstable prefix

While this proposal is in development, the new endpoints should be named as follows:

* `GET /_matrix/client/unstable/org.matrix.msc3916/media/preview_url`
* `GET /_matrix/client/unstable/org.matrix.msc3916/media/config`
* `GET /_matrix/client/unstable/org.matrix.msc3916/media/download/{serverName}/{mediaId}`
* `GET /_matrix/client/unstable/org.matrix.msc3916/media/download/{serverName}/{mediaId}/{fileName}`
* `GET /_matrix/client/unstable/org.matrix.msc3916/media/thumbnail/{serverName}/{mediaId}`
* `GET /_matrix/federation/unstable/org.matrix.msc3916/media/download/{serverName}/{mediaId}`

In a prior version of this proposal, the federation API included a thumbnail endpoint.
It was removed due to lack of perceived usage. Servers which implemented the unstable
version will have done so under `GET /_matrix/federation/unstable/org.matrix.msc3916/media/thumbnail/{serverName}/{mediaId}`.
The client-server thumbnail endpoint is unaffected by this change.

## Dependencies

None at present.
