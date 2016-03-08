Event Context
=============

.. _module:event-context:

This API returns a number of events that happened just before and after the
specified event. This allows clients to get the context surrounding an event.

Client behaviour
----------------

There is a single HTTP API for retrieving event context, documented below.

{{event_context_cs_http_api}}

Security considerations
-----------------------

The server must only return results that the user has permission to see.
