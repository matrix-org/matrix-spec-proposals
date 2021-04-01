.. Copyright 2016 OpenMarket Ltd
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..     http://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.

Guest Access
============

.. _module:guest-access:

There are times when it is desirable for clients to be able to interact with
rooms without having to fully register for an account on a homeserver or join
the room. This module specifies how these clients should interact with servers
in order to participate in rooms as guests.

Guest users retrieve access tokens from a homeserver using the ordinary
`register endpoint <#post-matrix-client-%CLIENT_MAJOR_VERSION%-register>`_, specifying
the ``kind`` parameter as ``guest``. They may then interact with the
client-server API as any other user would, but will only have access to a subset
of the API as described the Client behaviour subsection below.
Homeservers may choose not to allow this access at all to their local users, but
have no information about whether users on other homeservers are guests or not.

Guest users can also upgrade their account by going through the ordinary
``register`` flow, but specifying the additional POST parameter
``guest_access_token`` containing the guest's access token. They are also
required to specify the ``username`` parameter to the value of the local part of
their username, which is otherwise optional.

This module does not fully factor in federation; it relies on individual
homeservers properly adhering to the rules set out in this module, rather than
allowing all homeservers to enforce the rules on each other.

Events
------
{{m_room_guest_access_event}}

Client behaviour
----------------
The following API endpoints are allowed to be accessed by guest accounts for
retrieving events:

* `GET /rooms/:room_id/state <#get-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-state>`_
* `GET /rooms/:room_id/context/:event_id <#get-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-context-eventid>`_
* `GET /rooms/:room_id/event/:event_id <#get-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-event-eventid>`_
* `GET /rooms/:room_id/state/:event_type/:state_key <#get-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-state-eventtype-statekey>`_
* `GET /rooms/:room_id/messages <#get-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-messages>`_
* `GET /rooms/:room_id/members <#get-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-members>`_
* `GET /rooms/:room_id/initialSync <#get-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-initialsync>`_
* `GET /sync <#get-matrix-client-%CLIENT_MAJOR_VERSION%-sync>`_
* `GET /events`__ as used for room previews.

__  `peeking_events_api`_

The following API endpoints are allowed to be accessed by guest accounts for
sending events:

* `POST /rooms/:room_id/join <#post-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-join>`_
* `POST /rooms/:room_id/leave <#post-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-leave>`_
* `PUT /rooms/:room_id/send/m.room.message/:txn_id <#put-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-send-eventtype-txnid>`_
* `PUT /sendToDevice/{eventType}/{txnId} <#put-matrix-client-%CLIENT_MAJOR_VERSION%-sendtodevice-eventtype-txnid>`_

The following API endpoints are allowed to be accessed by guest accounts for
their own account maintenance:

* `PUT /profile/:user_id/displayname <#put-matrix-client-%CLIENT_MAJOR_VERSION%-profile-userid-displayname>`_
* `GET /devices <#get-matrix-client-%CLIENT_MAJOR_VERSION%-devices>`_
* `GET /devices/{deviceId} <#get-matrix-client-%CLIENT_MAJOR_VERSION%-devices-deviceid>`_
* `PUT /devices/{deviceId} <#put-matrix-client-%CLIENT_MAJOR_VERSION%-devices-deviceid>`_

The following API endpoints are allowed to be accessed by guest accounts for
end-to-end encryption:

* `POST /keys/upload <#post-matrix-client-%CLIENT_MAJOR_VERSION%-keys-upload>`_
* `POST /keys/query <#post-matrix-client-%CLIENT_MAJOR_VERSION%-keys-query>`_
* `POST /keys/claim <#post-matrix-client-%CLIENT_MAJOR_VERSION%-keys-claim>`_

Server behaviour
----------------
Servers MUST only allow guest users to join rooms if the ``m.room.guest_access``
state event is present on the room, and has the ``guest_access`` value
``can_join``. If the ``m.room.guest_access`` event is changed to stop this from
being the case, the server MUST set those users' ``m.room.member`` state to
``leave``.

Security considerations
-----------------------
Each homeserver manages its own guest accounts itself, and whether an account
is a guest account or not is not information passed from server to server.
Accordingly, any server participating in a room is trusted to properly enforce
the permissions outlined in this section.

Homeservers may want to enable protections such as captchas for guest
registration to prevent spam, denial of service, and similar attacks.
