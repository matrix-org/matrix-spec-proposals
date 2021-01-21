---
type: module
weight: 160
---

### Guest Access

There are times when it is desirable for clients to be able to interact
with rooms without having to fully register for an account on a
homeserver or join the room. This module specifies how these clients
should interact with servers in order to participate in rooms as guests.

Guest users retrieve access tokens from a homeserver using the ordinary
[register
endpoint](#post_matrixclientr0register),
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

{{m\_room\_guest\_access\_event}}

#### Client behaviour

The following API endpoints are allowed to be accessed by guest accounts
for retrieving events:

-   [GET /rooms/:room\_id/state](#get_matrixclientr0roomsroomidstate)
-   [GET /rooms/:room\_id/context/:event\_id](#get_matrixclientr0roomsroomidcontexteventid)
-   [GET /rooms/:room\_id/event/:event\_id](#get_matrixclientr0roomsroomideventeventid)
-   [GET /rooms/:room\_id/state/:event\_type/:state\_key](#get_matrixclientr0roomsroomidstateeventtypestatekey)
-   [GET /rooms/:room\_id/messages](#get_matrixclientr0roomsroomidmessages)
-   [GET /rooms/:room\_id/members](#get_matrixclientr0roomsroomidmembers)
-   [GET /rooms/:room\_id/initialSync](#get_matrixclientr0roomsroomidinitialsync)
-   [GET /sync](#get_matrixclientr0sync)
-   [GET /events](#get_matrixclientr0events) as used for room previews.

The following API endpoints are allowed to be accessed by guest accounts
for sending events:

-   [POST /rooms/:room\_id/join](#post_matrixclientr0roomsroomidjoin)
-   [POST /rooms/:room\_id/leave](#post_matrixclientr0roomsroomidleave)
-   [PUT /rooms/:room\_id/send/m.room.message/:txn\_id](#put_matrixclientr0roomsroomidsendeventtypetxnid)
-   [PUT /sendToDevice/{eventType}/{txnId}](#put_matrixclientr0sendtodeviceeventtypetxnid)

The following API endpoints are allowed to be accessed by guest accounts
for their own account maintenance:

-   [PUT /profile/:user\_id/displayname](#put_matrixclientr0profileuseriddisplayname)
-   [GET /devices](#get_matrixclientr0devices)
-   [GET /devices/{deviceId}](#get_matrixclientr0devicesdeviceid)
-   [PUT /devices/{deviceId}](#put_matrixclientr0devicesdeviceid)

The following API endpoints are allowed to be accessed by guest accounts
for end-to-end encryption:

-   [POST /keys/upload](#post_matrixclientr0keysupload)
-   [POST /keys/query](#post_matrixclientr0keysquery)
-   [POST /keys/claim](#post_matrixclientr0keysclaim)

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
