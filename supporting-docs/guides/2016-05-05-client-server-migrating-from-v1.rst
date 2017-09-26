---
layout: post
title: Migrating from Client Server API v1
categories: guides
---

Migrating from client-server API v1
===================================

This guide assists developers of API clients that target the ``v1`` version of
the API to migrate their code to the later ``r0``. It does not aim to introduce
new concepts that were added in ``r0`` except where these replace things that
were removed since ``v1``.

Updated Version In Path
=======================

The new version of the API is ``r0``; this should be used in paths where
``v1`` used to appear. Additionally, the ``/api`` path component has now been
removed. API endpoint paths are now::

  POST /_matrix/client/r0/register
  GET /_matrix/client/r0/login
  etc...

New Registration and Login Endpoints
====================================

The ``r0`` version of the ``/register`` and ``/login`` endpoints is different
to the ``v1`` version. See the updated API documentation for details on how the
new API works. In brief, the changes are that the new version returns extra
information in the form of the ``params`` object, and that a sequence of
multiple calls may be statefully chained together by the ``session`` parameter.

Additionally, whereas in ``v1`` the client performed a ``GET`` request to
discover the list of supported flows for ``/register``, in ``r0`` this is done
by sending a ``POST`` request with an empty data body. The ``/login`` endpoint
continues to use the ``GET`` method as before.

Deprecated Endpoints
====================

The following endpoints are now deprecated and replaced by the ``/sync`` API::

  /initialSync
  /events
  /rooms/:roomId/initialSync

The new ``/sync`` API takes an optional ``since`` parameter to distinguish the
initial sync from subsequent updates for more events.

The return value takes a different structure to that from the previous
``/initialSync`` API. For full details see the API documentation, but the
following summary may be useful to compare with ``v1``:

 * ``/initialSync`` returned a ``state`` key containing the most recent state
   in the room, whereas the new ``/sync`` API's ``state`` corresponds to the
   room state at the start of the returned timeline. This makes it easier for
   clients to represent state changes that occur within the region of returned
   timeline.

 * In ``/events``, if more events occurred since the ``since`` token than the
   ``limit`` parameter allowed, then events from the start of this range were
   returned and the client had to perform another fetch to incrementally obtain
   more of them. In the ``/sync`` API the result always contains the most
   recent events, creating a gap if this would be more events than the
   requested limit. If this occurs then the client can use the ``prev_batch``
   token as a reference to obtaining more.

 * The ``state`` contained in the response to a ``/sync`` request that has a
   ``since`` parameter will contain only keys that have changed since the
   basis given in the ``since`` parameter, rather than containing a full set
   values.

The ``/initialSync`` API allowed a parameter called ``limit`` to limit the
number of events returned. To apply this limit to the new ``/sync`` API, you
can supply an ad-hoc filter::

  GET .../sync?filter={"room":{"timeline":{"limit:$limit}}}

There is no direct replacement for the per-room ``/rooms/:roomId/initialSync``
endpoint, but the behaviour can be recreated by applying an ad-hoc filter using
the ``filter`` parameter to ``/sync`` that selects only the required room ID::

  GET .../sync?filter={"room":{"rooms":[$room_id]}}

However, the way that the new ``/sync`` API works should remove any need to do
this kind of query, in the situations where the ``v1`` API needed it.
Specifically, on joining a new room the initial information about that room is
sent in the next ``/sync`` batch, so it should not be necessary to query that
one room specially.

The following endpoint is deprecated and has no direct replacement:: 

  /events/:eventId

However, if the client knows the room ID of the room that the event is in, it
can use the ``/rooms/:roomId/context/:eventId`` request to fetch the event
itself. By giving the ``limit`` parameter of ``0`` the client can save using
extra bandwidth by actually returning additional context events around the
requested one.

Removed POST Endpoint
=====================

The room message sending API endpoint in ``v1`` accepted both ``PUT`` and
``POST`` methods, where the client could specify a message ID in the ``PUT``
path for de-duplication purposes, or have the server allocate one during
``POST``. In ``r0`` this latter form no longer exists. Clients will now have
to generate these IDs locally.

The following URLs have therefore been removed::

  POST .../rooms/:roomId/send/:messageType
