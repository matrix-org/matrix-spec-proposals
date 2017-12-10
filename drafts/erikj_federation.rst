Federation
==========
.. sectnum::
.. contents:: Table of Contents


Auth chain
~~~~~~~~~~

The *auth chain* for an event is the recursive list of auth events and the auth
chain for those auth events.

.. Note:: The auth chain for an event gives all the information a server needs
          to accept an event. However, being given an auth chain for an event
          that appears valid does not mean that the event might not later be
          rejected. For example if we discover that the sender had been banned
          between the join event listed in the auth events and the event being
          authed.

**TODO**: Clean the above explanations up a bit.


Auth chain resolution
~~~~~~~~~~~~~~~~~~~~~

If an auth check fails, or if we get told something we accepted should have
been rejected, we need to try and determine who is right.

If two servers disagree about the validity of the auth events, both should
inform the other of what they think the current auth chain is. If either are
missing auth events that they know are valid (through authorization and state
resolution) they process the missing events as usual.

If either side notice that the other has accepted an auth events we think
should be rejected (for reasons *not* in their auth chain), that server should
inform the other with suitable proof.

The proofs can be:

- An *event chain* that shows an auth event is *not* an ancestor of the event.
  This can be done by giving the full ancestor chains up to the depth of the
  invalid auth event.
- Given an event (and event chain?) showing that authorization had been revoked.

If a server discovers it cannot prove the other side is wrong, then it accepts
that the other is correct; i.e. we always accept that the other side is correct
unless we can prove otherwise.


Constructing a new event
------------------------

    **TODO**

When constructing a new event, the server should insert the following fields:

- ``prev_events``: The list of event ids of what the server believes are the
  current leaf nodes of the event graph (i.e., nodes that have been received
  but are yet to be referenced by another event).
- ``depth``: An integer one greater than the maximum depth of the event's
  previous events.
- ``auth_events``: The list of event ids that authorizes this event. This
  should be a subset of the current state.
- ``origin_server_ts``: The time the server created the event.
- ``origin``: The name of the server.


Signing and Hashes
~~~~~~~~~~~~~~~~~~

    **TODO**

Validation
----------

    **TODO**

Domain specific string
    A string of the form ``<prefix><localpart>:<domain>``, where <prefix> is a
    single character, ``<localpart>`` is an arbitrary string that does not
    include a colon, and `<domain>` is a valid server name.

``room_id``
    A domain specific string with prefix ``!`` that is static across all events
    in a graph and uniquely identifies it. The ``domain`` should be that of the
    homeserver that created the room (i.e., the server that generated the
    first ``m.room.create`` event).

``sender``
    The entity that logically sent the event. This is usually a user id, but
    can also be a server name.

User Id
    A domain specific string with prefix ``@`` representing a user account. The
    ``domain`` is the homeserver of the user and is the server used to contact
    the user.

Joining a room
--------------

If a user requests to join a room that the server is already in (i.e. the a
user on that server has already joined the room) then the server can simply
generate a join event and send it as normal.

If the server is not already in the room it needs to will need to join via
another server that is already in the room. This is done as a two step process.

First, the local server requests from the remote server a skeleton of a join
event. The remote does this as the local server does not have the event graph
to use to fill out the ``prev_events`` key in the new event. Critically, the
remote server does not process the event it responded with.

Once the local server has this event, it fills it out with any extra data and
signs it. Once ready the local server sends this event to a remote server
(which could be the same or different from the first remote server), this
remote server then processes the event and distributes to all the other
participating servers in that room. The local server is told about the
current state and complete auth chain for the join event. The local server
can then process the join event itself.


.. Note::
   Finding which server to use to join any particular room is not specified.


Inviting a user
---------------

To invite a remote user to a room we need their homeserver to sign the invite
event. This is done by sending the event to the remote server, which then signs
the event, before distributing the invite to other servers.


Handling incoming events
------------------------

When a server receives an event, it should:

#. Check if it knows about the room. If it doesn't, then it should get the
   current state and auth events to determine whether the server *should* be in
   the room. If so continue, if not drop or reject the event
#. If the server already knew about the room, check the prev events to see if
   it is missing any events. If it is, request them. Servers should limit how
   far back they will walk the event graph for missing events.
#. If the server does not have all the prev events, then it should request the
   current state and auth events from a server.


Failures
--------

A server can notify a remote server about something it thinks it has done
wrong using the failures mechanism. For example, the remote accepted an event
the local think it shouldn't have.

A failure has a severity level depending on the action taken by the local
server. These levels are:

``FATAL``
    The local server could not parse the event, for example due to a missing
    required field.

``ERROR``
    The local server *could* parse the event, but it was rejected. For example,
    the event may have failed an authorization check.

``WARN``
    The local server accepted the event, but something was unexpected about it.
    For example, the event may have referenced another event the local server
    thought should be rejected.

A failure also includes several other fields:

``code``
    A numeric code (to be defined later) indicating a particular type of
    failure.

``reason``
    A short string indicating what was wrong, for diagnosis purposes on the
    remote server.

``affected``
    The event id of the event this failure is responding to. For example, if
    an accepted event referenced a rejected event, this would point to the
    accepted one.

``source``
    The event id of the event that was the source of this unexpected behaviour.
    For example, if an accepted event referenced a rejected event, this would
    point to the rejected one.


Appendix
========

    **TODO**

Example event:

.. code::

    {
        "auth_events": [
            [
                "$14187571482fLeia:localhost:8480",
                {
                    "sha256": "kiZUclzzPetHfy0rVoYKnYXnIv5VxH8a4996zVl8xbw"
                }
            ],
            [
                "$14187571480odWTd:localhost:8480",
                {
                    "sha256": "GqtndjviW9yPGaZ6EJfzuqVCRg5Lhoyo4YYv1NFP7fw"
                }
            ],
            [
                "$14205549830rrMar:localhost:8480",
                {
                    "sha256": "gZmL23QdWjNOmghEZU6YjqgHHrf2fxarKO2z5ZTbkig"
                }
            ]
        ],
        "content": {
            "body": "Test!",
            "msgtype": "m.text"
        },
        "depth": 250,
        "event_id": "$14207181140uTFlx:localhost:8480",
        "hashes": {
            "sha256": "k1nuafFdFvZXzhb5NeTE0Q2Jkqu3E8zkh3uH3mqwIxc"
        },
        "origin": "localhost:8480",
        "origin_server_ts": 1420718114694,
        "prev_events": [
            [
                "$142071809077XNNkP:localhost:8480",
                {
                    "sha256": "xOnU1b+4LOVz5qih0dkNFrdMgUcf35fKx9sdl/gqhjY"
                }
            ]
        ],
        "room_id": "!dwZDafgDEFTtpPKpLy:localhost:8480",
        "sender": "@bob:localhost:8480",
        "signatures": {
            "localhost:8480": {
                "ed25519:auto": "Nzd3D+emFBJJ4LCTzQEZaKO0Sa3sSTR1fGpu8OWXYn+7XUqke9Q1jYUewrEfxb3lPxlYWm/GztVUJizLz1K5Aw"
            }
        },
        "type": "m.room.message",
        "unsigned": {
            "age": 500
        }
    }
