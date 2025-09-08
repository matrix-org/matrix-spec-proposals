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
   | [`GET /_matrix/media/v3/download/{serverName}/{mediaId}`](https://spec.matrix.org/v1.6/client-server-api/#get_matrixmediav3downloadservernamemediaid)            | `GET /_matrix/client/v1/media/download/{serverName}/{mediaId}`            | `GET /_matrix/federation/v1/media/download/{mediaId}`  |
   | [`GET /_matrix/media/v3/download/{serverName}/{mediaId}/{fileName}`](https://spec.matrix.org/v1.6/client-server-api/#get_matrixmediav3downloadservernamemediaidfilename) | `GET /_matrix/client/v1/media/download/{serverName}/{mediaId}/{fileName}` | -                                                                 |
   | [`GET /_matrix/media/v3/thumbnail/{serverName}/{mediaId}`](https://spec.matrix.org/v1.6/client-server-api/#get_matrixmediav3thumbnailservernamemediaid)          | `GET /_matrix/client/v1/media/thumbnail/{serverName}/{mediaId}`           | `GET /_matrix/federation/v1/media/thumbnail/{mediaId}` |

   **Note**: [`POST /_matrix/media/v3/upload`](https://spec.matrix.org/v1.6/client-server-api/#post_matrixmediav3upload)
   and [`POST /_matrix/media/v1/create`](https://spec.matrix.org/v1.10/client-server-api/#post_matrixmediav1create)
   are **not** modified or deprecated by this MSC: it is intended that they be brought into line with the other
   endpoints by a future MSC, such as [MSC3911](https://github.com/matrix-org/matrix-spec-proposals/pull/3911).

2. Removal of `allow_remote` parameter from `/download` and `/thumbnail`

   The current
   [`/download`](https://spec.matrix.org/v1.6/client-server-api/#get_matrixmediav3downloadservernamemediaid)
   and
   [`/thumbnail`](https://spec.matrix.org/v1.6/client-server-api/#get_matrixmediav3thumbnailservernamemediaid)
   endpoints take an `allow_remote` query parameter, indicating whether the
   server should request remote media from other servers. This is redundant
   with the new endpoints, so will not be supported.

   Servers MUST NOT return remote media from `GET /_matrix/federation/v1/media/download` or
   `GET /_matrix/federation/v1/media/thumbnail`. The `serverName` is omitted from
   the endpoint's path to strongly enforce this - the `mediaId` in a request is
   assumed to be scoped to the target server.

   `/_matrix/client/v1/media/download` and
   `/_matrix/client/v1/media/thumbnail` return remote media as normal.

3. Authentication on all endpoints

   Currently, the `/download` and `/thumbnail` endpoints have no authentication
   requirements. Under this proposal, the new endpoints will be authenticated
   the same way as other endpoints: they will require an `Authorization` header
   which must be `Bearer {accessToken}` for `/_matrix/client`, or the signature
   for `/_matrix/federation`.

   Clients SHOULD NOT use the [deprecated](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/4126-deprecate-query-string-auth.md)
   `?access_token` query string authentication mechanism. The method is [pending removal](https://github.com/matrix-org/matrix-spec-proposals/pull/4127)
   and is generally unsafe. See those MSCs for further details.

   **Note**: This fixes [matrix-spec#313](https://github.com/matrix-org/matrix-spec/issues/313).

4. Updated response format

   * For the new `/_matrix/client` endpoints, the response format is the same as
     the corresponding original endpoints.

   * To enable future expansion, for the new `/_matrix/federation` endpoints,
     the response is
     [`multipart/mixed`](https://www.w3.org/Protocols/rfc1341/7_2_Multipart.html)
     content with exactly two parts: the first MUST be a JSON object (and should have a
     `Content-type: application/json` header), and the second MUST be the media item.
     The media item may be served inline, as shown in the first example below, or
     be a pointer to a URL containing the media item's bytes instead, represented
     by the `Location` header described further below.

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

     The second part (media item bytes) MAY include a [`Location` header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Location)
     to point to the raw media object instead of having bytes itself. Servers
     SHOULD NOT cache the `Location` header's value as the responding server may
     have applied time limits on its validity. Servers which don't immediately
     download the media from the provided URL should re-request the media and
     metadata from the `/download` endpoint when ready for the media bytes.

     The `Location` header's URL does *not* require authentication, as it will
     typically be served by a CDN or other non-matrix server (thus being unable
     to verify any `X-Matrix` signatures, for example).

     Note that all other headers besides `Location` for the media item part are
     ignored when `Location` is present. The `Content-Type`, `Content-Disposition`,
     etc headers will be served from the `Location`'s URL instead. Similarly,
     the body for the media item part is ignored and SHOULD be empty.

     An example response with a `Location` redirect would be:

     ```
     Content-Type: multipart/mixed; boundary=gc0p4Jq0M2Yt08jU534c0p

     --gc0p4Jq0M2Yt08jU534c0p
     Content-Type: application/json

     {}

     --gc0p4Jq0M2Yt08jU534c0p
     Location: https://cdn.example.org/ab/c1/2345.txt

     --gc0p4Jq0M2Yt08jU534c0p
     ```

     If the server were to `curl https://cdn.example.org/ab/c1/2345.txt`, it'd
     get something similar to the following:

     ```
     Content-Type: text/plain

     This media is plain text. Maybe somebody used it as a paste bin.
     ```

     **Note**: For clarity, the above applies to the federation `/thumbnail` endpoint
     as well as `/download`.

5. Backwards compatibility mechanisms

   Servers SHOULD *stop* serving new media as unauthenticated within 1 spec release
   of this proposal being released itself using a standard `404 M_NOT_FOUND` response.
   Existing media should continue to be served from the unauthenticated endpoints
   indefinitely for backwards compatibility. For example, if this proposal is
   released in Matrix 1.11, then by Matrix 1.12 servers should freeze the old
   unauthenticated endpoints by only serving media known to exist from before the
   freeze.

   "New media" is any media which local users upload after the freeze is put in
   place, and any remote media which becomes cached after the freeze as well. This
   could be marked by a configuration option within the server software, or as part
   of a scheduled/dedicated release which enacts the freeze for everyone who updates
   to that version.

   This freeze schedule will have some undesirable side effects, particularly for
   clients and servers which are slow to update or support the new endpoints. Newly
   uploaded images, files, avatars, etc may appear "broken" or missing to users on
   older software. Existing media should continue to work, however, reducing the
   impact from 100% of media to a smaller percentage.

   Servers SHOULD consider whether their users' typical clients will break as
   part of the freeze before enacting the freeze. Clients SHOULD update as soon
   as reasonably possible to support authenticated media, particularly following
   the spec release containing this MSC. Other considerations may include bridges,
   deployment-specific use cases, and patch availability.

   It is worth noting that the matrix.org homeserver plans to freeze media relatively
   quickly following this proposal's release in the specification. Details will be
   published to the matrix.org blog closer to the spec release date.

   The following are specific backwards compatibility cases:

   a. New clients & servers with older servers: The [`M_UNRECOGNIZED`](https://spec.matrix.org/v1.10/client-server-api/#common-error-codes)
      error behaviour should be followed to indicate that the server does not
      support the new endpoints, particularly when partnered with a 404 HTTP status
      code. Clients and servers should use the unauthenticated endpoints in this
      case. The endpoints will not be frozen by the server, so should work for
      'new' media.

   b. Older clients & servers with newer servers: Mentioned above, servers are
      strongly encouraged to freeze unauthenticated media access within a relatively
      quick timeframe. Though media before the freeze should remain accessible,
      clients and older federating servers may still see errors when accessing
      new media, leading to client UI feeling "broken" or missing avatars. The
      various considerations above are meant to reduce the impact of this case.

6. Removal of `allow_redirect` parameter from `/download` and `/thumbnail`

   Clients MUST expect a 307 or 308 redirect when calling the new `/download`
   and `/thumbnail` Client-Server API endpoints.

   Servers MUST expect the `Location` header in the media part of the new Server-Server
   API `/download` and `/thumbnail` endpoints. Servers MUST NOT respond with a 307 or 308 redirect at
   the top level for the endpoint - they can only redirect within the media part
   itself.

   See [this comment on MSC3860](https://github.com/matrix-org/matrix-spec-proposals/pull/3860/files#r1005176480)
   for further context on this change.

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

Servers MAY flag the media as exceptions to the freeze described in part 5 of
this proposal ("Backwards compatibility mechanisms"). Clients SHOULD continue to
use the unauthenticated media download/thumbnail endpoints to access these icons
until a future MSC can improve the situation.

The proposal author expects that the spec's transition to OIDC will ultimately
replace this mechanism, or that an MSC could be opened to allow HTTP(S) URLs in
place of `mxc:` URIs.

(This was previously discussed in
[MSC2858](https://github.com/matrix-org/matrix-spec-proposals/pull/2858#discussion_r543513811).)

## Potential issues

* Setting the `Authorization` header is particularly annoying for web clients.
  Service workers are seemingly the best option, though other options include
  locally-cached `blob:` URIs. Clients should note that caching media can lead
  to significant memory usage, particularly for large media. Service workers by
  comparison allow for proxy-like behaviour.

  Cookies are a plausible mechanism for sharing session information between
  requests without having to set headers, though would be a relatively bespoke
  authentication method for Matrix. Additionally, many Matrix users have cookies
  disabled due to the advertising and tracking use cases common across the web.

* Users will be unable to copy links to media from web clients to share out of
  band. This is considered a feature, not a bug.

* Over federation, the use of the `Range` request header on the federation endpoints becomes
  unclear as it could affect either or both parts of the response. There does not
  appear to be formal guidance in [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110#field.range)
  either. There are arguments for affecting both and either part equally. Typically,
  such a header would be used to resume failed downloads, though servers are
  already likely to discard received data and fail the associated client requests
  when the federation request fails. Therefore, servers are unlikely to use `Range`
  at all. As such, this proposal does not make a determination on how `Range`
  should be handled, and leaves it as an HTTP specification interpretation problem
  instead.

* The `Location` header support on the new federation endpoints could add a bit
  of complexity to servers, though given the alternative of supporting CDNs and
  similar is to place complexity into "edge workers" to mutate the response value.
  Though the Matrix spec would be "simpler", the edge worker setup would be
  fragmented where we have an opportunity for a common standard.

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

  Conversely, we should make sure to rename `POST /_matrix/media/v3/upload`
  and `GET /_matrix/media/v3/create`. The reason to
  delay doing so is because MSC3911 will make more substantial changes to these
  endpoints, requiring another rename, and it is expected that both proposals
  will be merged near to the same time as each other (so a double rename will
  be confusing and unnecessary). However, if MSC3911 is delayed or rejected, we
  should reconsider this.

* Rather than messing with multipart content, have a separate endpoint for
  servers to get the metadata for a media item. That would mean two requests,
  but might make more sense than the federation endpoints providing the info directly.

  This is a plausible approach with no significant upsides or downsides when
  compared to multipart responses.

  Similarly, custom headers could be used to carry the metadata on the response,
  though again, there are no significant upsides or downsides to doing so.

  Readers may wish to refer to [this thread](https://github.com/matrix-org/matrix-spec-proposals/pull/3916/files#r1586878787)
  on the MSC which covers the majority of the pros and cons for all 3 approaches.

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
* `GET /_matrix/federation/unstable/org.matrix.msc3916.v2/media/download/{mediaId}`
  * **Note**: This endpoint has a `.v2` in its unstable identifier due to the MSC changing after
    initial implementation. The original unstable endpoint has a `serverName` and may still be
    supported by some servers: `GET /_matrix/federation/unstable/org.matrix.msc3916/media/download/{serverName}/{mediaId}`

    The `serverName` was later dropped in favour of explicit scoping. See `allow_remote` details
    in the MSC body for details.
* `GET /_matrix/federation/unstable/org.matrix.msc3916.v2/media/thumbnail/{mediaId}`
  * **Note**: This endpoint has a `.v2` in its unstable identifier due to the MSC changing after
    initial implementation. The original unstable endpoint has a `serverName` and may still be
    supported by some servers: `GET /_matrix/federation/unstable/org.matrix.msc3916/media/thumbnail/{serverName}/{mediaId}`

    The `serverName` was later dropped in favour of explicit scoping. See `allow_remote` details
    in the MSC body for details.

## Stable flag

After the proposal is accepted servers may advertise support for the stable
endpoints by setting `org.matrix.msc3916.stable` to `true` in the
`unstable_features` section of the
[versions endpoint](https://spec.matrix.org/v1.11/client-server-api/#get_matrixclientversions)
in addition to the usual version-based feature support. This option is provided
to encourage a faster rollout in the wider Matrix ecosystem until servers
support the full feature set of the respective version of the Matrix
specification.

## Dependencies

None.
