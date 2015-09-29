Presence
========
 
Each user has presence information associated with them. This encodes the
"availability" of that user, suitable for display on other clients.
This is transmitted as an ``m.presence`` event and is one of the few events
which are sent *outside the context of a room*. Their presence state is
represented by the ``presence`` key, which is an enum of one of the following:

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

Clients can manually set/get their presence using the HTTP APIs listed below.

{{presence_http_api}}

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

Propagating profile information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Because the profile display name and avatar information are likely to be used in
many places of a client's display, changes to these fields SHOULD cause an
automatic propagation event to occur, informing likely-interested parties of the
new values. One of these change mechanisms SHOULD be via ``m.presence`` events.
These events should set ``displayname`` and ``avatar_url`` to the new values
along with the presence-specific keys. This SHOULD be done automatically by the
home server when a user successfully changes their display name or avatar URL.

.. admonition:: Rationale

  The intention for sending this information in ``m.presence`` is so that any
  "user list" can display the *current* name/presence for a user ID outside the
  scope of a room (e.g. a user page which has a "start conversation" button).
  This is bundled into a single event to avoid "flickering" on this page which
  can occur if you received presence first and then display name later (the
  user's name would flicker from their user ID to the display name).


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

