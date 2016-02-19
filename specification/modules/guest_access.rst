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
* `GET /rooms/:room_id/state/:event_type/:state_key <#get-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-state-eventtype-statekey>`_
* `GET /rooms/:room_id/messages <#get-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-messages>`_
* `GET /rooms/:room_id/initialSync <#get-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-initialsync>`_
* `GET /sync <#get-matrix-client-%CLIENT_MAJOR_VERSION%-sync>`_
* `GET /events`__ as used for room previews.

__  `peeking_events_api`_

The following API endpoints are allowed to be accessed by guest accounts for
sending events:

* `POST /rooms/:room_id/join <#post-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-join>`_
* `POST /rooms/:room_id/leave <#post-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-leave>`_
* `PUT /rooms/:room_id/send/m.room.message/:txn_id <#put-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-send-eventtype-txnid>`_

The following API endpoints are allowed to be accessed by guest accounts for
their own account maintenance:

* `PUT /profile/:user_id/displayname <#put-matrix-client-%CLIENT_MAJOR_VERSION%-profile-userid-displayname>`_

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

