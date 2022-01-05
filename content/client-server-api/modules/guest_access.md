---
type: module
---

### Guest Access

There are times when it is desirable for clients to be able to interact
with rooms without having to fully register for an account on a
homeserver or join the room. This module specifies how these clients
should interact with servers in order to participate in rooms as guests.

Guest users retrieve access tokens from a homeserver using the ordinary
[register
endpoint](#post_matrixclientv3register),
specifying the `kind` parameter as `guest`. They may then interact with
the client-server API as any other user would, but will only have access
to a subset of the API as described the Client behaviour subsection
below. Homeservers may choose not to allow this access at all to their
local users, but have no information about whether users on other
homeservers are guests or not.

Guest users can also upgrade their account by going through the ordinary
`register` flow, but specifying the additional POST parameter
`guest_access_token` containing the guest's access token. They are also
required to specify the `username` parameter to the value of the local
part of their username, which is otherwise optional.

This module does not fully factor in federation; it relies on individual
homeservers properly adhering to the rules set out in this module,
rather than allowing all homeservers to enforce the rules on each other.

#### Events

{{% event event="m.room.guest_access" %}}

#### Client behaviour

The following API endpoints are allowed to be accessed by guest accounts
for retrieving events:

* [GET /rooms/{roomId}/state](#get_matrixclientv3roomsroomidstate)
* [GET /rooms/{roomId}/context/{eventId}](#get_matrixclientv3roomsroomidcontexteventid)
* [GET /rooms/{roomId}/event/{eventId}](#get_matrixclientv3roomsroomideventeventid)
* [GET /rooms/{roomId}/state/{eventType}/{stateKey}](#get_matrixclientv3roomsroomidstateeventtypestatekey)
* [GET /rooms/{roomId}/messages](#get_matrixclientv3roomsroomidmessages)
* {{< added-in v="1.1" >}} [GET /rooms/{roomId}/members](#get_matrixclientv3roomsroomidmembers)
* [GET /rooms/{roomId}/initialSync](#get_matrixclientv3roomsroomidinitialsync)
* [GET /sync](#get_matrixclientv3sync)
* [GET /events](#get_matrixclientv3events) as used for room previews.

The following API endpoints are allowed to be accessed by guest accounts
for sending events:

* [POST /rooms/{roomId}/join](#post_matrixclientv3roomsroomidjoin)
* [POST /rooms/{roomId}/leave](#post_matrixclientv3roomsroomidleave)
* [PUT /rooms/{roomId}/send/{eventType}/{txnId}](#put_matrixclientv3roomsroomidsendeventtypetxnid)

    * {{< changed-in v="1.2" >}} Guests can now send *any* event type rather than just `m.room.message` events.

* {{< added-in v="1.2" >}} [PUT /rooms/{roomId}/state/{eventType}/{stateKey}](#put_matrixclientv3roomsroomidstateeventtypestatekey)
* [PUT /sendToDevice/{eventType}/{txnId}](#put_matrixclientv3sendtodeviceeventtypetxnid)

The following API endpoints are allowed to be accessed by guest accounts
for their own account maintenance:

* [PUT /profile/{userId}/displayname](#put_matrixclientv3profileuseriddisplayname)
* [GET /devices](#get_matrixclientv3devices)
* [GET /devices/{deviceId}](#get_matrixclientv3devicesdeviceid)
* [PUT /devices/{deviceId}](#put_matrixclientv3devicesdeviceid)
* {{< added-in v="1.2" >}} [GET /account/whoami](#get_matrixclientv3accountwhoami)

The following API endpoints are allowed to be accessed by guest accounts
for end-to-end encryption:

* [POST /keys/upload](#post_matrixclientv3keysupload)
* [POST /keys/query](#post_matrixclientv3keysquery)
* [POST /keys/claim](#post_matrixclientv3keysclaim)

#### Server behaviour

Servers MUST only allow guest users to join rooms if the
`m.room.guest_access` state event is present on the room, and has the
`guest_access` value `can_join`. If the `m.room.guest_access` event is
changed to stop this from being the case, the server MUST set those
users' `m.room.member` state to `leave`.

#### Security considerations

Each homeserver manages its own guest accounts itself, and whether an
account is a guest account or not is not information passed from server
to server. Accordingly, any server participating in a room is trusted to
properly enforce the permissions outlined in this section.

Homeservers may want to enable protections such as captchas for guest
registration to prevent spam, denial of service, and similar attacks.

Homeservers may want to put stricter rate limits on guest accounts,
particularly for sending state events.
