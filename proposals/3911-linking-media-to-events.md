# MSC3911: Linking media to events

(An alternative to [MSC3910](https://github.com/matrix-org/matrix-spec-proposals/pull/3910).)

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

After an item of media is uploaded, it must be linked to an event (via
parameters to the `/send` api). A given piece of media is only visible
to a user if the user can see the corresponding event.

### Detailed spec changes

1. A new "media upload" endpoint is defined, `POST
   /_matrix/client/v1/media/upload`.  It is based on the existing
   [`/_matrix/media/v3/upload`](https://spec.matrix.org/v1.4/client-server-api/#post_matrixmediav3upload)
   endpoint, but media uploaded this way is not initially viewable (except to
   the user that uploaded it). This is referred to as a "restricted" media item.

   The existing endpoint is deprecated. Media uploaded via the existing endpoint
   is "unrestricted".

2. Attaching media

   * The methods for sending events
     ([`PUT /_matrix/client/v3/rooms/{roomId}/state/{eventType}/{stateKey}`](PUT /_matrix/client/v3/rooms/{roomId}/state/{eventType}/{stateKey})
     and [`PUT /_matrix/client/v3/rooms/{roomId}/state/{eventType}/{stateKey}`](https://spec.matrix.org/v1.4/client-server-api/#put_matrixclientv3roomsroomidsendeventtypetxnid)
     are extended to take a query parameter `attach_media`, whose value must be a complete `mxc:` URI.

     The `attach_media` parameter may be used several times to attach several
     pieces of media to the same event. The maximium number of pieces of media
     that can be attached to a single event is implementation-defined by servers.

     If any of the `attach_media` parameters do not correspond to known
     restricted media items, or they refer to restricted media items that have
     already been attached, the server responds with a 400 error with
     `M_INVALID_PARAM`.

     Sending an event in this manner associates the media with the sent
     event. From then on, the media can be seen by any user who can see the event
     itself.
   
     Servers should ensure that sending an event remains an idempotent operation: in
     particular, if a client sends an event with a media attachment, and then
     repeats the operation with identical parameters, a 200 response must be returned
     (with the original event ID) even though the media has already been attached.

   * Alternatively, if a restricted media item is referenced in a call to
     [`PUT /_matrix/client/v3/profile/{userId}/avatar_url`](PUT /_matrix/client/v3/profile/{userId}/avatar_url),
     it is instead attached to the user's profile. 

     Again, if the media is already attached, the server responds with a 400 error with
     `M_INVALID_PARAM`.

   If the media is not attached to either an event or a profile within a reasonable period
   (say, ten minutes), then the server is free to assume that the user has changed their
   mind (or the client has gone offline), and may clean up the uploaded media.

4. New download endpoints
     
   The existing download endpoints are to be deprecated, and replaced with new
   endpoints specific to client-server or federation requests:
     
   | Old                                                                                                                                                              | Client-Server                                                             | Federation                                                          |
   | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------- |
   | [`GET /_matrix/media/v3/download/{serverName}/{mediaId}`](https://spec.matrix.org/v1.4/client-server-api/#get_matrixmediav3downloadservernamemediaid)            | `GET /_matrix/client/v1/media/download/{serverName}/{mediaId}`            | `GET /_matrix/federation/v1/media/download/{serverName}/{mediaId}`  |
   | [`GET /_matrix/media/v3/download/{serverName}/{mediaId}/{fileName}`](https://spec.matrix.org/v1.4/client-server-api/#get_matrixmediav3downloadservernamemediaid) | `GET /_matrix/client/v1/media/download/{serverName}/{mediaId}/{fileName}` | N/A                                                                 |
   | [`GET /_matrix/media/v3/thumbnail/{serverName}/{mediaId}`](https://spec.matrix.org/v1.4/client-server-api/#get_matrixmediav3thumbnailservernamemediaid)          | `GET /_matrix/client/v1/media/thumbnail/{serverName}/{mediaId}`           | `GET /_matrix/federation/v1/media/thumbnail/{serverName}/{mediaId}` |

   [Question: should we move `/config`, and `/preview_url` while
   we're at it, per [MSC1902](https://github.com/matrix-org/matrix-spec-proposals/pull/1902)?]

   None of the new endpoints take an `allow_remote` query parameter. (For
   `/_matrix/client`, servers should always attempt to request remote
   media. For `/_matrix/federation`, servers should never attempt to request
   remote media they do not already have cached.)

   All of the new endpoints require an `Authorization` header, which must be
   set in the same way as for any other CSAPI or federation request (ie,
   `Bearer {accessToken}` for `/_matrix/client`, or the signature for
   `/_matrix/federation`).

   When handling a request to the new endpoints, the server must check if the
   requesting user or server has permission to see the corresponding event.
   If not, the server responds with a 403 error and `M_UNAUTHORIZED`.

   * For the new `/_matrix/client` endpoints, the response format is the same as
     the corresponding original endpoints.

   * For the new `/_matrix/federation` endpoints, the response is
     [`multipart/mixed`]https://www.w3.org/Protocols/rfc1341/7_2_Multipart.html)
     content with two parts: the first must be a JSON object
     (and should have a `Content-type: application/json` header), and the second
     is the media item as per the original endpoints. The json object may have
     a property `restrictions`.

     If there is no `restrictions` property, the media is a legacy "unrestricted"
     media. Otherwise, `restrictions` should be a JSON object with one
     of the following properties:

     * `event_id`: the event id of the event to which the media is attached.
     * `profile_user_id`: the user id of the user to whose profile the media is attached.

     It is invalid for both `event_id` and `profile_user_id` to be set.

     The requesting server must check the restrictions list, and only return
     the requested media to users who have permission to view the relevant
     event or profile. If the requesting server caches the media, it must also
     cache the restrictions list.

     If neither `event_id` nor `profile_user_id` are present, the requesting
     user should assume that an unknown restriction is present, and not allow access
     to any user.

     An example response:

     ```
     Content-Type: multipart/mixed; boundary=gc0p4Jq0M2Yt08jU534c0p

     --gc0p4Jq0M2Yt08jU534c0p
     Content-Type: application/json

     { "restrictions": {
         "event_id": "$Rqnc-F-dvnEYJTyHq_iKxU2bZ1CI92-kuZq3a5lr5Zg"
     }}

     --gc0p4Jq0M2Yt08jU534c0p
     Content-Type: text/plain

     This media is plain text. Maybe somebody used it as a paste bin.

     --gc0p4Jq0M2Yt08jU534c0p
     ```     

4. New "media copy" API

   A new endpoint is defined: `POST
   /_matrix/client/v1/media/copy/{serverName}/{mediaId}`. The body of the
   request must be a JSON object, but there are no required parameters.

   Conceptually, the API makes a new copy of a media item. (In practice, the
   server will probably make a new reference to an existing media item, but
   that is an implementation detail). 

   The response is a json object with a required `content_uri` property,
   giving a new MXC URI referring to the media.

   The new media item can be attached to a new event, and generally functions
   in every way the same as uploading a brand new media item.

   This "copy" api is to be used by clients when forwarding events with media
   attachments.

5. Autogenerated `m.room.member` events

   Servers will generate `m.room.member` events with an `avatar_url` whenever
   one of their users joins a room, or changes their profile picture.

   Such events must each use a different copy of the media item, in the same
   way as the "media copy" API described above.

5. Backwards compatibility mechanisms

   a. Backwards compatibility with older servers: if a client or requesting
   server receives a 404 error with a non-JSON response, or a 400 error with
   `{"errcode": "M_UNRECOGNIZED"}`, in response to a request to one of the new
   endpoints, they may retry the request using the original endpoint.
   
   b. Backwards compatibility with older clients and federating servers:
   servers may for a short time choose to allow unauthenticated access via the
   deprecated endpoints, even for restricted media.

6. URL preview

   The
   [`/preview_url`](https://spec.matrix.org/v1.4/client-server-api/#get_matrixmediav3preview_url)
   endpoint returns an object that references an image for the previewed
   site.

   It is expected that servers will continue to treat such media as unrestricted
   (at least for local users), but it would be legitimate for them to, for example,
   return a different `mxc:` URI for each requesting user, and only allow each user
   access to the corresponding `mxc:` URI.

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

In this scenario, the bridge would have a secret HMAC key. When it
receives a matrix event referencing a piece of media, it should create a new URI
referencing the media, include an HMAC to prevent tampering. For example:

```
https://<bridge_server>/media/{originServerName}/{mediaId}?mac={hmac}
```

When the bridge later receives a request to that URI, it checks the hmac,
and proxies the request to the homeserver, using its AS access
token in the `Authorization` header.

This mechanism also works for a secondary use of the content repository in
bridges: as a paste-bin. In this case, the bridge simply generates a link
referencing its own media.

The bridge might also choose to embed information such as the room that
referenced the media, and the time that the link was generated, in the URL.
This could be used to help control access to the media.

Such mechanisms would allow the bridge to impose controls such as:

* Limiting the time a media link is valid for. Doing so would help prevent
  visibility to users who weren't participating in the chat.

* Rate-limiting the amount of media being shared in a particular room (in other
  words, avoiding the use of Matrix as a Warez distribution system).

#### Redacting events

Under this proposal, servers can determine which media is referenced by an
event that is redacted, and add that media to a list to be cleaned up.

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
specifically for access to these icon.

We also need to ensure that the icons are not deleted from the content
repository even though they have not been attached to any event or profile. It
would be wise for servers to provide administrators with a mechanism to upload
media without attaching it to anything.

(This was previously discussed in
[MSC2858](https://github.com/matrix-org/matrix-spec-proposals/pull/2858#discussion_r543513811).)

## Potential issues

* Setting the `Authorization` header is going to be annoying for web clients. Service workers
  might be needed.

* Users will be unable to copy links to media from web clients to share out of
  band. This is considered a feature, not a bug.

* Since each `m.room.member` references the avatar separately, changing your
  avatar will cause an even bigger traffic storm if you're in a lot of rooms.

## Alternatives

* Use some sort of "content token" for each piece of media, and require clients to
  provide it, per [MSC3910](https://github.com/matrix-org/matrix-spec-proposals/pull/3910).

* Allow clients to upload media which does not require authentication (for
  example via a `public=true` query parameter). This might be particularly
  useful for IRC/XMPP bridges, which could upload any media they encounter to
  the homeserver's repository.

  The danger with this is that is that there's little stopping clients
  continuing to upload media as "public", negating all of the benefits in this
  MSC. It might be ok if media upload it was restricted to certain privileged
  users.

* Have the "upload" endpoint return a nonce, which can then be used in the
  "send" endpoint in place of the `mxc` uri. It's hard to see what advantage
  this gives, beyond the fact a nonce could be smaller so marginally fewer
  bytes to send.

## Security considerations

* Letting servers track the relationship between events and media is a metadata
  leak, especially for e2ee rooms.

## Unstable prefix

TODO

## Dependencies

None at present.

## Prior art

* Credit: this is based on ideas from @jcgruenhage and @anoadragon453 at
  https://cryptpad.fr/code/#/2/code/view/oWjZciD9N1aWTr1IL6GRZ0k1i+dm7wJQ7juLf4tJRoo/

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
  
  
