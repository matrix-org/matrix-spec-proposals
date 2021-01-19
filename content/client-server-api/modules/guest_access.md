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
endpoint](#post-matrix-client-%CLIENT_MAJOR_VERSION%-register),
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

-   [GET
    /rooms/:room\_id/state](#get-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-state)
-   [GET
    /rooms/:room\_id/context/:event\_id](#get-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-context-eventid)
-   [GET
    /rooms/:room\_id/event/:event\_id](#get-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-event-eventid)
-   [GET
    /rooms/:room\_id/state/:event\_type/:state\_key](#get-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-state-eventtype-statekey)
-   [GET
    /rooms/:room\_id/messages](#get-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-messages)
-   [GET
    /rooms/:room\_id/members](#get-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-members)
-   [GET
    /rooms/:room\_id/initialSync](#get-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-initialsync)
-   [GET /sync](#get-matrix-client-%CLIENT_MAJOR_VERSION%-sync)
-   [GET /events]() as used for room previews.

The following API endpoints are allowed to be accessed by guest accounts
for sending events:

-   [POST
    /rooms/:room\_id/join](#post-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-join)
-   [POST
    /rooms/:room\_id/leave](#post-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-leave)
-   [PUT
    /rooms/:room\_id/send/m.room.message/:txn\_id](#put-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-send-eventtype-txnid)
-   [PUT
    /sendToDevice/{eventType}/{txnId}](#put-matrix-client-%CLIENT_MAJOR_VERSION%-sendtodevice-eventtype-txnid)

The following API endpoints are allowed to be accessed by guest accounts
for their own account maintenance:

-   [PUT
    /profile/:user\_id/displayname](#put-matrix-client-%CLIENT_MAJOR_VERSION%-profile-userid-displayname)
-   [GET /devices](#get-matrix-client-%CLIENT_MAJOR_VERSION%-devices)
-   [GET
    /devices/{deviceId}](#get-matrix-client-%CLIENT_MAJOR_VERSION%-devices-deviceid)
-   [PUT
    /devices/{deviceId}](#put-matrix-client-%CLIENT_MAJOR_VERSION%-devices-deviceid)

The following API endpoints are allowed to be accessed by guest accounts
for end-to-end encryption:

-   [POST
    /keys/upload](#post-matrix-client-%CLIENT_MAJOR_VERSION%-keys-upload)
-   [POST
    /keys/query](#post-matrix-client-%CLIENT_MAJOR_VERSION%-keys-query)
-   [POST
    /keys/claim](#post-matrix-client-%CLIENT_MAJOR_VERSION%-keys-claim)

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
