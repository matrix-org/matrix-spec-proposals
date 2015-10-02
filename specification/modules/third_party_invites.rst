Third party invites
===================

.. _module:third_party_invites:

This module adds in support for inviting new members to a room where their
Matrix user ID is not known, instead addressing them by a third party identifier
such as an email address.

Events
------

{{m_room_third_party_invite_event}}

Client behaviour
----------------

A client asks a server to invite a user by their third party identifier.

See the documentation for /invite for more information.

Server behaviour
----------------

All homeservers MUST verify that sign(``token``, ``public_key``) = ``signature``.

If a client of the current homeserver is joining by an
``m.room.third_party_invite``, that homesever MUST validate that the public
key used for signing is still valid, by checking ``key_validity_url``.

If a homeserver is joining a room for the first time because of an
``m.room.third_party_invite``, the server which is already participating in the
room MUST validate that the public key used for signing is still valid, by
checking ``key_validity_url``.

No other homeservers may reject the joining of the room on the basis of
``key_validity_url``, this is so that all homeservers have a consistent view of
the room.

