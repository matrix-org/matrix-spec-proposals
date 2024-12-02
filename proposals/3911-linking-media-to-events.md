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

This proposal builds on
[MSC3916](https://github.com/matrix-org/matrix-spec-proposals/pull/3916) (which
adds authentication to media download), to require that the authenticated
user is *authorised* to access the requested media.

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
     ([`PUT /_matrix/client/v3/rooms/{roomId}/state/{eventType}/{stateKey}`](https://spec.matrix.org/v1.4/client-server-api/#put_matrixclientv3roomsroomidstateeventtypestatekey)
     and [`PUT /_matrix/client/v3/rooms/{roomId}/send/{eventType}/{txnId}`](https://spec.matrix.org/v1.4/client-server-api/#put_matrixclientv3roomsroomidsendeventtypetxnid))
     are extended to take a query parameter `attach_media`, whose value must be a complete `mxc:` URI.

     The `attach_media` parameter may be used several times to attach several
     pieces of media to the same event. The maximum number of pieces of media
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
     [`PUT /_matrix/client/v3/profile/{userId}/avatar_url`](https://spec.matrix.org/v1.4/client-server-api/#put_matrixclientv3profileuseridavatar_url)
     it is instead attached to the user's profile. 

     Again, if the media is already attached, the server responds with a 400 error with
     `M_INVALID_PARAM`.

   If the media is not attached to either an event or a profile within a reasonable period
   (say, ten minutes), then the server is free to assume that the user has changed their
   mind (or the client has gone offline), and may clean up the uploaded media.

3. Additional checks on `/download` and `/thumbnail` endpoints

   The new `/download` and `/thumbnail` endpoints added in
   [MSC3916](https://github.com/matrix-org/matrix-spec-proposals/pull/3916) are
   updated the server must check if the requesting user or server has
   permission to see the corresponding event.  If not, the server responds with
   a 403 error and `M_UNAUTHORIZED`.

4. Federation API returns a `restrictions` property

   The `/_matrix/federation/v1/media/download` and `/_matrix/federation/v1/media/thumbnail`
   endpoints specified by [MSC3916](https://github.com/matrix-org/matrix-spec-proposals/pull/3916)
   are extended: the returned json object may have a property `restrictions`.

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

5. New "media copy" API

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

   (This mechanism, rather than just allowing clients to attach media to multiple
   events, is necessary to ensure that the list of events attached a given piece of
   media does not grow over time, which would make it difficult for servers to
   reliably cache media and impose the correct access restrictions.)

5. Autogenerated `m.room.member` events

   Servers will generate `m.room.member` events with an `avatar_url` whenever
   one of their users joins a room, or changes their profile picture.

   Such events must each use a different copy of the media item, in the same
   way as the "media copy" API described above.

6. Backwards compatibility mechanisms

   For backwards compatibility with older clients and requesting servers:
   servers may for a short time choose to allow unauthenticated access via the
   deprecated `/_matrix/media/v3` endpoints, even for restricted media.

7. URL preview

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

These bridges have previously been discussed in [MSC3916](https://github.com/matrix-org/matrix-spec-proposals/pull/3916), however this proposal adds a new problem.

These bridges currently use the content repository as a paste-bin: large text
messages are uploaded as plain-text media, and a link is then sent to the
remote network. This will become problematic, because servers are entitled
to remove any media that does not get linked to an event.

Solutions might include:
 * the bridge hosting its own content repository for this usecase
 * using an external service
 * special-casing the bridge AS user to permit it to upload media without
   expiry.

#### Icons for "social login" flows

These likewise were previously discussed in
[MSC3916](https://github.com/matrix-org/matrix-spec-proposals/pull/3916).

We need to ensure that the icons are not deleted from the content
repository even though they have not been attached to any event or profile. It
would be wise for servers to provide administrators with a mechanism to upload
media without attaching it to anything.

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

## Potential issues

* Since each `m.room.member` references the avatar separately, changing your
  avatar will cause an even bigger traffic storm if you're in a lot of rooms.

  In addition, this could cause duplication of media in the remote media cache,
  if the implementation does not take steps to deduplicate (eg, storing media
  by content hash rather than media id).

## Alternatives

* Have the "upload" endpoint return a nonce, which can then be used in the
  "send" endpoint in place of the `mxc` uri. It's hard to see what advantage
  this gives, beyond the fact a nonce could be smaller so marginally fewer
  bytes to send.

* Use some sort of "content token" for each piece of media, and require clients to
  provide it, per [MSC3910](https://github.com/matrix-org/matrix-spec-proposals/pull/3910).

## Security considerations

* Letting servers track the relationship between events and media is a metadata
  leak, especially for e2ee rooms.

## Unstable prefix

TODO

## Dependencies

[MSC3916](https://github.com/matrix-org/matrix-spec-proposals/issues/3916) "Authentication for media access, and new endpoint names".

## Prior art

* Credit: this proposal is based on ideas from @jcgruenhage and @anoadragon453 at
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
  
  
