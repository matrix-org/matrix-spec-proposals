Migrating from client-server API v1
===================================

This guide assists developers of API clients that target the ``v1`` version of
the API to migrate their code to the later ``r0``. It does not aim to introduce
new concepts that were added in ``r0`` except where these replace things that
were removed since ``v1``.

New Registration and Login Endpoints
====================================

The ``r0`` version of the ``/register`` and ``/login`` endpoints is different
to the ``v1`` version. See the updated API documentation for details on how the
new API works. In brief, the changes are that the new version returns extra
information in the form of the ``params`` object, and that a sequence of
multiple calls may be statefully chained together by the ``session`` parameter.

Deprecated Endpoints
====================

The following endpoints are now deprecated and replaced by the ``/sync`` API::

  /initialSync
  /events
  /rooms/:roomId/initialSync

The new ``/sync`` API takes an optional ``since`` parameter to distinguish the
initial sync from subsequent updates for more events. These return data in a
different format.

There is no direct replacement for the per-room ``/rooms/:roomId/initialSync``
endpoint, but the behaviour can be recreated by applying an ad-hoc filter using
the ``filter`` parameter to ``/sync`` that selects only the required room ID.

See the new API documentation for details on the new return
value.

The following endpoint is deprecated and has no direct replacement:: 

  /events/:eventId

However, if the client is aware of the room ID the event is in, it can use the
``/rooms/:roomId/context/:eventId`` request to fetch the event itself. By
giving the ``limit`` parameter of ``0`` the client can save using extra
bandwidth by actually returning additional context events around the requested
one.

Removed POST Endpoint
=====================

The room message sending API endpoint in ``v1`` accepted both ``PUT`` and
``POST`` methods, where the client could specify a message ID in the ``PUT``
path for de-duplication purposes, or have the server allocate one during
``POST``. In ``r0`` this latter form no longer exists. Clients will now have
to generate these IDs locally.

The following URLs have therefore been removed::

  POST .../rooms/:roomId/send/:messageType

Updated Version In Path
=======================

The new version of the API is ``r0``; this should be used in paths where
``v1`` appears::

  POST /_matrix/client/api/r0/register
  GET /_matrix/client/api/r0/login
  etc...
