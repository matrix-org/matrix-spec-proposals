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

Third party invites
===================

.. _module:third-party-invites:

This module adds in support for inviting new members to a room where their
Matrix user ID is not known, instead addressing them by a third party identifier
such as an email address.
There are two flows here; one if a Matrix user ID is known for the third party
identifier, and one if not. Either way, the client calls ``/invite`` with the
details of the third party identifier.

The homeserver asks the identity server whether a Matrix user ID is known for
that identifier:

- If it is, an invite is simply issued for that user.

- If it is not, the homeserver asks the identity server to record the details of
  the invitation, and to notify the invitee's homeserver of this pending invitation if it gets
  a binding for this identifier in the future. The identity server returns a token
  and public key to the inviting homeserver.

When the invitee's homeserver receives the notification of the binding, it
should insert an ``m.room.member`` event into the room's graph for that user,
with ``content.membership`` = ``invite``, as well as a
``content.third_party_invite`` property which contains proof that the invitee
does indeed own that third party identifier.

Events
------

{{m_room_third_party_invite_event}}

Client behaviour
----------------

A client asks a server to invite a user by their third party identifier.

{{third_party_membership_cs_http_api}}

Server behaviour
----------------

All homeservers MUST verify the signature in the event's
``content.third_party_invite.signed`` object.

When a homeserver inserts an ``m.room.member`` ``invite`` event into the graph
because of an ``m.room.third_party_invite`` event,
that homesever MUST validate that the public
key used for signing is still valid, by checking ``key_validity_url`` from the ``m.room.third_party_invite``. It does
this by making an HTTP GET request to ``key_validity_url``:

.. TODO: Link to identity server spec when it exists

Schema::

    => GET $key_validity_url?public_key=$public_key
    <= HTTP/1.1 200 OK
    {
        "valid": true|false
    }


Example::

    key_validity_url = https://identity.server/is_valid
    public_key = ALJWLAFQfqffQHFqFfeqFUOEHf4AIHfefh4
    => GET https://identity.server/is_valid?public_key=ALJWLAFQfqffQHFqFfeqFUOEHf4AIHfefh4
    <= HTTP/1.1 200 OK
    {
        "valid": true
    }

with the querystring
?public_key=``public_key``. A JSON object will be returned.
The invitation is valid if the object contains a key named ``valid`` which is
``true``. Otherwise, the invitation MUST be rejected. This request is
idempotent and may be retried by the homeserver.

If a homeserver is joining a room for the first time because of an
``m.room.third_party_invite``, the server which is already participating in the
room (which is chosen as per the standard server-server specification) MUST
validate that the public key used for signing is still valid, by checking
``key_validity_url`` in the above described way.

No other homeservers may reject the joining of the room on the basis of
``key_validity_url``, this is so that all homeservers have a consistent view of
the room. They may, however, indicate to their clients that a member's'
membership is questionable.

For example:

#. Room R has two participating homeservers, H1, H2

#. User A on H1 invites a third party identifier to room R

#. H1 asks the identity server for a binding to a Matrix user ID, and has none,
   so issues an ``m.room.third_party_invite`` event to the room.

#. When the third party user validates their identity, their homeserver H3
   is notified and attempts to issue an ``m.room.member`` event to participate
   in the room.

#. H3 validates the signature given to it by the identity server.

#. H3 then asks H1 to join it to the room. H1 *must* validate the ``signed``
   property *and* check ``key_validity_url``.

#. Having validated these things, H1 writes the invite event to the room, and H3
   begins participating in the room. H2 *must* accept this event.

The reason that no other homeserver may reject the event based on checking
``key_validity_url`` is that we must ensure event acceptance is deterministic.
If some other participating server doesn't have a network path to the keyserver,
or if the keyserver were to go offline, or revoke its keys, that other server
would reject the event and cause the participating servers' graphs to diverge.
This relies on participating servers trusting each other, but that trust is
already implied by the server-server protocol. Also, the public key signature
verification must still be performed, so the attack surface here is minimized.

Security considerations
-----------------------

There are a number of privary and trust implications to this module.

It is important for user privacy that leaking the mapping between a matrix user
ID and a third party identifier is hard. In particular, being able to look up
all third party identifiers from a matrix user ID (and accordingly, being able
to link each third party identifier) should be avoided wherever possible.
To this end, the third party identifier is not put in any event, rather an
opaque display name provided by the identity server is put into the events.
Clients should not remember or display third party identifiers from invites,
other than for the use of the inviter themself.

Homeservers are not required to trust any particular identity server(s). It is
generally a client's responsibility to decide which identity servers it trusts,
not a homeserver's. Accordingly, this API takes identity servers as input from
end users, and doesn't have any specific trusted set. It is possible some
homeservers may want to supply defaults, or reject some identity servers for
*its* users, but no homeserver is allowed to dictate which identity servers
*other* homeservers' users trust.

There is some risk of denial of service attacks by flooding homeservers or
identity servers with many requests, or much state to store. Defending against
these is left to the implementer's discretion.

