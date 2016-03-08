Client Config
=============

.. _module:account_data:

Clients can store custom config data for their account on their homeserver.
This account data will be synced between different devices and can persist
across installations on a particular device. Users may only view the account
data for their own account

The account_data may be either global or scoped to a particular rooms.

Events
------

The client recieves the account data as events in the ``account_data`` sections
of a ``/sync``.

These events can also be received in a ``/events`` response or in the
``account_data`` section of a room in ``/initialSync``. ``m.tag``
events appearing in ``/events`` will have a ``room_id`` with the room
the tags are for.

Client Behaviour
----------------

{{account_data_cs_http_api}}
