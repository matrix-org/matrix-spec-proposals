Event Context
=============

.. _module:event-context:

This API returns a number of events that happened just before and after the
specified event. This allows clients to get the context surrounding an event.

Client behaviour
----------------

{{event_context_http_api}}

Security considerations
-----------------------

The server must only return results that the user has permission to see.
