Presence
========

.. _module:presence:

Each user has the concept of presence information. This encodes:

* Whether the user is currently online
* How recently the user was last active (as seen by the server)
* Whether a given client considers the user to be currently idle
* Arbitrary information about the user's current status (e.g. "in a meeting").

This information is collated from both per-device (``online``, ``idle``,
``last_active``) and per-user (status) data, aggregated by the user's homeserver
and transmitted as an ``m.presence`` event. This is one of the few events which
are sent *outside the context of a room*. Presence events are sent to all users
who subscribe to this user's presence through a presence list or by sharing
membership of a room.

A presence list is a list of user IDs whose presence the user wants to follow.
To be added to this list, the user being added must be invited by the list owner
who must accept the invitation.
 
User's presence state is represented by the ``presence`` key, which is an enum
of one of the following:

- ``online`` : The default state when the user is connected to an event
  stream.
- ``unavailable`` : The user is not reachable at this time e.g. they are
  idle.
- ``offline`` : The user is not connected to an event stream or is
  explicitly suppressing their profile information from being sent.
- ``free_for_chat`` : The user is generally willing to receive messages
  moreso than default.

Events
------

{{presence_events}}

Client behaviour
----------------

Clients can manually set/get their presence/presence list using the HTTP APIs
listed below.

{{presence_cs_http_api}}

Idle timeout
~~~~~~~~~~~~

Clients SHOULD implement an "idle timeout". This is a timer which fires after
a period of inactivity on the client. The definition of inactivity varies
depending on the client. For example, web implementations may determine
inactivity to be not moving the mouse for a certain period of time. When this
timer fires it should set the presence state to ``unavailable``. When the user
becomes active again (e.g. by moving the mouse) the client should set the
presence state to ``online``. A timeout value between 1 and 5 minutes is
recommended. 

Server behaviour
----------------

Each user's homeserver stores a "presence list" per user. Once a user accepts
a presence list, both user's HSes must track the subscription.

Propagating profile information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Because the profile display name and avatar information are likely to be used in
many places of a client's display, changes to these fields SHOULD cause an
automatic propagation event to occur, informing likely-interested parties of the
new values. One of these change mechanisms SHOULD be via ``m.presence`` events.
These events should set ``displayname`` and ``avatar_url`` to the new values
along with the presence-specific keys. This SHOULD be done automatically by the
homeserver when a user successfully changes their display name or avatar URL.

.. admonition:: Rationale

  The intention for sending this information in ``m.presence`` is so that any
  "user list" can display the *current* name/presence for a user ID outside the
  scope of a room e.g. for a user page. This is bundled into a single event for
  several reasons. The user's display name can change per room. This
  event provides the "canonical" name for the user. In addition, the name is
  bundled into a single event for the ease of client implementations. If this
  was not done, the client would need to search all rooms for their own
  membership event to pull out the display name.


Last active ago
~~~~~~~~~~~~~~~
The server maintains a timestamp of the last time it saw a
pro-active event from the user. A pro-active event may be sending a message to a
room or changing presence state to a higher level of availability. Levels of
availability are defined from low to high as follows:

- ``offline``
- ``unavailable``
- ``online``
- ``free_for_chat``

Based on this list, changing state from ``unavailable`` to ``online`` counts as
a pro-active event, whereas ``online`` to ``unavailable`` does not. This
timestamp is presented via a key called ``last_active_ago`` which gives the
relative number of milliseconds since the pro-active event.

Security considerations
-----------------------
    
Presence information is shared with all users who share a room with the target
user. In large public rooms this could be undesirable.

