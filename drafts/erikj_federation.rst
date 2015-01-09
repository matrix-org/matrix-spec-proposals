Federation
==========

Constructing a new event
------------------------

**TODO**

Signing and Hashes
~~~~~~~~~~~~~~~~~~

**TODO**

Authorization
-------------

When receiving new events from remote servers, or creating new events, a server 
must know whether that event is allowed by the authorization rules. These rules
depend solely on the state at that event. The types of state events that affect
authorization are:

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
   
   
Definitions
~~~~~~~~~~~

Required Power Level
  A given event type has an associated *required power level*. This is given
  by the current ``m.room.power_levels`` event, it is either listed explicitly
  in the ``events`` section or given by either ``state_default`` or 
  ``events_default`` depending on if the event type is a state event or not.
  



Appendix
========