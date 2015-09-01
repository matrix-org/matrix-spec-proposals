Room History Visibility
=======================

The visibility of events to users before they joined can be controlled by the
``m.room.history_visibility`` state event.

More specifically, the string value of the content key ``history_visibility``
controls the visibility of events. The valid values are:

- ``shared``
- ``invited``
- ``joined``

By default, ``history_visibility`` is set to ``shared``.

The rules governing whether a user is allowed to see an event depend solely on
the state at that event:

1. If the user was joined, allow.
2. If the user was invited and the ``history_visibility`` was set to
   ``invited`` or ``shared``, allow.
3. If the user was neither invited nor joined but the ``history_visibility``
   was set to ``shared``, allow.
4. Otherwise, deny.

