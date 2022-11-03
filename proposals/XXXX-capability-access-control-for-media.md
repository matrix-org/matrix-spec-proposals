# MSCxxxx: Capability-Style Access Control for Media

(An alternative to [MSC3910](https://github.com/matrix-org/matrix-spec-proposals/pull/3910), [MSC3911](https://github.com/matrix-org/matrix-spec-proposals/pull/3911), and [MSC3916](https://github.com/matrix-org/matrix-spec-proposals/pull/3916).)

## Motivation

In Matrix, "everything happens in a room," yet media exists outside of rooms.
Anyone who knows the `media_id` for a media object can request (and receive)
that object from the homeserver.
This leads to a number of issues, which MSC3910 and MSC3911 describe succinctly:

> Currently, access to media in Matrix has the following problems:
> 
> * The only protection for media is the obscurity of the URL, and URLs are
>   easily leaked (eg accidental sharing, access
>   logs). [synapse#2150](https://github.com/matrix-org/synapse/issues/2150)
> * Anybody (including non-matrix users) can cause a homeserver to copy media
>   into its local
>   store. [synapse#2133](https://github.com/matrix-org/synapse/issues/2133)
> * When a media event is redacted, the media it used remains visible to all.
>   [synapse#1263](https://github.com/matrix-org/synapse/issues/1263)
> * There is currently no way to delete
>   media. [matrix-spec#226](https://github.com/matrix-org/matrix-spec/issues/226)
> * If a user requests GDPR erasure, their media remains visible to all.
> * When all users leave a room, their media is not deleted from the server.


## Proposal

### Overview

In this proposal, we borrow an idea from capability-based access control
systems: "No ambient authority."
Instead, every request for a resource must include a "reason" for why
the request should be granted.

We begin with the observation that there are only two legitimate reasons for
downloading a Matrix media object:
1. The media object is part of a room, either as part of a message sent to
  the room, or as the avatar image for the room.
2. The media object is the avatar image for some user's profile.

Therefore in the proposed system, user grant access to their media to rooms
or to their user profile, and media uploaded under the new system cannot be
downloaded without specifying the room or the user profile that justifies
the access.
(See below for an alternative approach, where access to media is granted on
individual events, rather than on rooms.)

In brief, the proposed approach is to change the URL path for `GET /media/media_id`
requests to include either the room id or, for user avatars, the user id,
that motivated the request.

To download media that was shared with a room:

`GET /_matrix/client/{version}/rooms/{roomId}/media/{mediaId}/{serverName}`

To download media that was shared via the user's profile:

`GET /matrix/client/{version}/profile/{userId}/media/{mediaId}`

Once clients transition to using the new URL paths, the "legacy" URLs
without room id or user id can be deprecated and eventually removed.


### Uploading Media

The request is unchanged from the previous system

* `POST /_matrix/media/{version}/upload`

However the returned MXC URL must be different, to indicate to clients
that the new media object can only be accessed via the new API.

`mxc://{serverId}/user/{userId}/{mediaId}`


### Granting a Room access to Media

* `PUT /_matrix/client/{version}/rooms/{roomId}/media/{mediaId}/{serverName}`

The server must verify that
1. The given media id exists
2. The given media id is owned by the user making the request

Note: This operation only grants permission for the room to access the media.
For other users to see the media, it must still be posted in some event in 
the room, e.g. a room message of type `m.image` or `m.video` etc.

The media object can then be referenced as

`mxc://{serverName}/room/{roomId}/{mediaId}`

Clients should grant permission to the room before sending the room message,
in case one of the requests fails.

If media id's are content id's, then this operation is idempotent.
It is OK if multiple users upload identical content and grant the same room access to it.
Homeservers should remember which user(s) granted the room access to which media,
and the homeserver must take care when revoking access -- see below.


### Downloading Media from a Room

Downloading a single media object

* `GET /_matrix/client/{version}/rooms/{roomId}/media/{mediaId}/{serverName}`

Note: Here the server name was put last so that it might be made optional
in the future, e.g. if the Matrix federation protocol gains some new P2P
file sharing capability.

### Listing the media for a room

* `GET /_matrix/client/{version}/rooms/{roomId}/media`
* `GET /_matrix/client/{version}/rooms/{roomId}/media/{serverName}`

### Revoking a Room's Access to Media

To revoke a room's access to media, the client calls

* `DELETE /_matrix/client/{version}/rooms/{roomId}/media/{mediaId}`

The server MUST verify that the user owns the given media.
(FIXME: Or that the user is an admin in the room?)

Then the server revokes any access granted to the given room by the user making the request.
Note that other users may have also granted the room access to identical content
having the same media id; in this case, the server should only revoke the room's
access to the content if the requesting user is the only remaining user who had
granted access.
(In other words, the server needs to keep a list of all users who have granted
access to a given media id.)

### Granting Media Access to your User Profile

The client-server API endpoint URL is unchanged:

* `PUT /_matrix/client/{version}/profile/{userId}/avatar_url`

The server
1. Verifies that the user making the request is the owner of the given media id
2. Makes the media available for retrieval under the user's profile (see below)

The server returns an MXC URL of the form

`mxc://{server}/profile/{userId}/{mediaId}`

### Downloading Media from a User Profile

The client first looks up the user's avatar URL, as before.

* `GET /_matrix/client/{version}/profile/{userId}/avatar_url`

The server responds with a URL of the form

`mxc://{server}/profile/{userId}/{mediaId}`

which is translated into the request

`GET /_matrix/client/{version}/profile/{userId}/media/{mediaId}`

The domain part of the user id serves as the server id here.
Media for a local user must be local media.
Media for a remote user must reside on that user's homeserver.

### Revoking Access for an Avatar Image

* `DELETE /_matrix/client/{version}/profile/{userId}/media/{mediaId}`

### Purging Unused Media

Servers MAY remove any local media that is both
(1) older than a certain minimum threshold (e.g. 24 hours) AND
(2) not currently available in any non-empty rooms or under any currently active (ie, not deactivated) user profiles

### Listing Media owned by the current User

* `GET /_matrix/client/{version}/users/{userId}/media`

### Deactivating the current user Account

The client sends a request to

`POST /_matrix/client/v3/account/deactivate`

We add one new member to the JSON request body:

`delete_media: bool` (defaults to `false`)


### Deleting Media

The owner of a media object can revoke all access to it by calling

`DELETE /_matrix/client/{version}/users/{userId}/media/{mediaId}`

The server should revoke any access to the given media that was granted
by the user to all rooms as well as to the user's profile.



## Potential issues

### Backwards Compatibility

Changing all media download paths would break older legacy clients and servers.
(The same is also true for any new acccess control enforcement scheme.)

A new room version may be necessary in order to keep track of which rooms
support the new style media access and which do not.

A phased roll-out could look something like this:

1. Update servers to provide the new API endpoints
2. Update clients to start using the new API endpoints and new media URLs
3. Deprecate the old style media URLs, but do not disable them.
4. Make backwards compatibility optional

### Access to media is lost after leaving a room

The Matrix spec says that when users leave (or are kicked/banned from)
a room, they should retain their access to messages in the room from the
period when they were members.

The approach proposed above does not fit well with this requirement.
When a user leaves a room, they lose their access to all media in that
room.

In the following section, this proposal outlines an alternative approach
that addresses this issue by granting media access to events rather than
to rooms.

## Modified Approach: Granting Access via Events Instead of via Rooms

Matrix already has a well-defined scheme for determining which users
should have access to which events.

We can leverage this to create a more precise access control scheme where
users' requests to download media are justified by their access to events
rather than to rooms.
In this scheme, if access has been granted to some media via some event,
and the user has access to the event, then the user is allowed access to
that media.

### Granting Access to an Event
* `PUT /_matrix/client/{version}/rooms/{roomId}/event/{eventId}/media/{mediaId}`

### Listing the media associated with an Event
* `GET /_matrix/client/{version}/rooms/{roomId}/event/{eventId}/media`

### Downloading Media, authorized by an event
* `GET /_matrix/client/{version}/rooms/{roomId}/event/{eventId}/media/{mediaId}`

### Revoking Access from an Event
* `DELETE /_matrix/client/{version}/rooms/{roomId}/event/{eventId}/media/{mediaId}`

## Alternatives

[MSC3910](https://github.com/matrix-org/matrix-spec-proposals/pull/3910)

[MSC3911](https://github.com/matrix-org/matrix-spec-proposals/pull/3911) and [MSC3916](https://github.com/matrix-org/matrix-spec-proposals/pull/3916)


## Security considerations

### Security improvements

This proposal addresses all of the problems identified in 
[MSC3910](https://github.com/matrix-org/matrix-spec-proposals/pull/3910)
/
[MSC3911](https://github.com/matrix-org/matrix-spec-proposals/pull/3911)
and copied [above](#motivation).

* Knowledge of the media id or URL is no longer sufficient to download the media.
  [synapse#2150](https://github.com/matrix-org/synapse/issues/2150)
* No one except an authorized Matrix user who is a member of the relevant
  room can cause a homeserver to copy media into its local store.
  [synapse#2133](https://github.com/matrix-org/synapse/issues/2133)
* When a media event is redacted, the access to its media can also be revoked.
  [synapse#1263](https://github.com/matrix-org/synapse/issues/1263)
* Media can now be deleted
  [matrix-spec#226](https://github.com/matrix-org/matrix-spec/issues/226)
* Users who request GDPR erasure can elect to have their media deleted and
  all access to it revoked.
* After all users have left a room, its media can optionally be deleted by
  the server.

### Security Trade-Off: Media and Message Linkability

The current system appears to offer some protection for hiding the relationship
between enrypted room messages and the media that they reference.
Given a static snapshot of a set of encrypted rooms and a set of encrypted
media objects, it is not immediately obvious which media go with which room.

This proposal would weaken whatever protections the current system provides,
by making explicit which encrypted media go with which rooms, or with which
event(s).

However, it should be understood that the current protections are quite weak
already and do not provide meaningful protection against an adversary who 
can watch as messages are uploaded and downloaded.
(And, if the homeserver maintains internal timestamps for media uploads,
then the adversary can perform the same analysis offline from a static snapshot.)

The origin homeserver for an encrypted message can use very simple timing
analysis to reconstruct the linkage:

* When a client uploads an encrypted media object and then immediately sends
an encrypted message, it is obvious that the two go together.

* Similarly, when a client uploads two encrypted media objects, one much
smaller than the other, and then immediately sends an encrypted image,
it is obvious to the server that the smaller object is the thumbnail and
the larger object is the main media in the message.

Other homeservers in the room can perform a similar timing analysis
when their clients first receive some encrypted messages and then fetch
a set of encrypted media objects immediately afterward.

## Unstable prefix



## Dependencies

This proposal should be used together with a content-addressable scheme for generating media id's,
for example MSCxxxx or MSCxxxx.
