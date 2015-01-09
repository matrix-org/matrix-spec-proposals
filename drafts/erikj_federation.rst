Federation
==========

Constructing a new event
------------------------

    **TODO**


Signing and Hashes
~~~~~~~~~~~~~~~~~~

    **TODO**

Validation
----------

    **TODO**

Authorization
-------------

When receiving new events from remote servers, or creating new events, a server 
must know whether that event is allowed by the authorization rules. These rules
depend solely on the state at that event. The types of state events that affect
authorization are:

- ``m.room.create``
- ``m.room.member``
- ``m.room.join_rules``
- ``m.room.power_levels``

Servers should not create new events that reference unauthorized events. 
However, any event that does reference an unauthorized event is not itself
automatically considered unauthorized. 

Unauthorized events that appear in the event graph do *not* have any effect on 
the state of the graph. 

.. Note:: This is in contrast to redacted events which can still affect the 
          state of the graph. For example, a redacted *"join"* event will still
          result in the user being considered joined.
          

Rules
~~~~~

The following are the rules to determine if an event is authorized (this does
include validation).

1. If type is ``m.room.create`` allow.
#. If type is ``m.room.member``:
  
   a. If ``membership`` is ``join``:
    
      i. If the previous event is an ``m.room.create``, the depth is 1 and 
         the ``state_key`` is the creator, then allow.
      #. If the ``state_key`` does not match ``sender`` key, reject.
      #. If the current state has ``membership`` set to ``join``.
      #. If the ``sender`` is in the ``m.room.may_join`` list. [Not currently 
         implemented]
      #. If the ``join_rules`` is:
      
         - ``public``:  allow.
         - ``invite``: allow if the current state has ``membership`` set to 
           ``invite``
         - ``knock``: **TODO**.
         - ``private``: Reject.
         
      #. Reject

   #. If ``membership`` is ``invite`` then allow if ``sender`` is in room, 
      otherwise reject.
   #. If ``membership`` is ``leave``:
   
      i. If ``sender`` matches ``state_key`` allow.
      #. If ``sender``'s power level is greater than the the ``kick_level``
         given in the current ``m.room.power_levels`` state (defaults to 50),
         and the ``state_key``'s power level is less than or equal to the
         ``sender``'s power level, then allow.
      #. Reject.
      
   #. If ``membership`` is ``ban``:
   
      i. **TODO**.
   
   #. Reject.

#. Reject the event if the event type's required power level is less that the
   ``sender``'s power level.
#. If the ``sender`` is not in the room, reject.
#. If the type is ``m.room.power_levels``:

   a. **TODO**.

#. Allow.


Auth events
~~~~~~~~~~~

The auth events of an event are the set of events used by the authorization 
algorithm to accept the event. These should be a subset of the current state.

A server is required to store the complete chain of auth events for all events
it serves to remote servers.

.. todo
    We probably should probably give a lower band of how long auth events
    should be kept around for.


Definitions
~~~~~~~~~~~

Required Power Level
  A given event type has an associated *required power level*. This is given
  by the current ``m.room.power_levels`` event, it is either listed explicitly
  in the ``events`` section or given by either ``state_default`` or 
  ``events_default`` depending on if the event type is a state event or not.
  

State Resolution
----------------

    **TODO**

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

