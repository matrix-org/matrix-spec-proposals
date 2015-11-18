Client Config
=============

.. _module:client_config:

Clients can store their config on their homeserver. This config will be synced
between different devices and can persist across installations on a particular
device.

The config may be either global or scoped to a particular rooms.

Events
------

The client recieves the config as a event in the ``account_data`` sections
of a v2 /sync.

These events can also be received in a v1 /events response or in the
``account_data`` section of a room in v1 /initialSync. ``m.tag``
events appearing in v1 /events will have a ``room_id`` with the room
the tags are for.

Client Behaviour
----------------

{{v2_client_config_http_api}}
