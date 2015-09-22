Room History Visibility
-----------------------

Whether a member of a room can see the events that happened in a room from
before they joined the room is controlled by the ``history_visibility`` key
of the ``m.room.history_visibility`` state event. The valid values for
``history_visibility`` are:

- ``shared``
- ``invited``
- ``joined``

By default if no ``history_visibility`` is set it is assumed to be ``shared``.

The rules governing whether a user is allowed to see an event depend solely on
the state of the room at that event:

1. If the user was joined, allow.
2. If the user was invited and the ``history_visibility`` was set to
   ``invited`` or ``shared``, allow.
3. If the user was neither invited nor joined but the ``history_visibility``
   was set to ``shared``, allow.
4. Otherwise, deny.

