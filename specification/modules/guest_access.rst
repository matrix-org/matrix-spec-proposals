Guest access
============

.. _module:guest-access:

There are times when it is desirable for clients to be able to interact with
rooms without having to fully register for an account on a homeserver or join
the room. This module specifies how these clients should interact with servers
in order to participate in rooms as guests.

Guest users retrieve access tokens from a homeserver using the ordinary
`register endpoint <#post-matrix-client-api-v2-alpha-register>`_, specifying
the ``kind`` parameter as ``guest``. They may then interact with the
client-server API as any other user would, but will only have access to a subset
of the API as described the Client behaviour subsection below.
Homeservers may choose not to allow this access at all to their local users, but
have no information about whether users on other homeservers are guests or not.

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

* `GET /rooms/:room_id/state <#get-matrix-client-api-v1-rooms-roomid-state>`_
* `GET /rooms/:room_id/state/:event_type/:state_key <#get-matrix-client-api-v1-rooms-roomid-state-eventtype-statekey>`_
* `GET /rooms/:room_id/messages <#get-matrix-client-api-v1-rooms-roomid-messages>`_

There is also a special version of the
`GET /events <#get-matrix-client-api-v1-events>`_ endpoint:

{{guest_events_http_api}}

They will only return events which happened while the room state had the
``m.room.history_visibility`` state event present with ``history_visibility``
value ``world_readable``. Guest clients do not need to join rooms in order to
receive events for them.

The following API endpoints are allowed to be accessed by guest accounts for
sending events:

* `POST /rooms/:room_id/join <#post-matrix-client-api-v1-rooms-roomid-join>`_
* `PUT /rooms/:room_id/send/m.room.message/:txn_id <#put-matrix-client-api-v1-rooms-roomid-send-eventtype-txnid>`_

Guest clients *do* need to join rooms in order to send events to them.

Server behaviour
----------------
Servers are required to only return events to guest accounts for rooms where
the room state at the event had the  ``m.room.history_visibility`` state event
present with ``history_visibility`` value ``world_readable``. These events may
be returned even if the anonymous user is not joined to the room.

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

Clients may wish to display to their users that rooms which are
``world_readable`` *may* be showing messages to non-joined users. There is no
way using this module to find out whether any non-joined guest users *do* see
events in the room, or to list or count any guest users.

Homeservers may want to enable protections such as captchas for guest
registration to prevent spam, denial of service, and similar attacks.

