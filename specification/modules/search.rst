Server Side Search
==================

.. _module:search:

The search API allows clients to perform full text search across events in
their rooms without having to download the entire histories.

Client behaviour
----------------
{{search_http_api}}

Search Categories
-----------------

The search API allows clients to search in different categories of items.
Currently the only specified category is ``room_events``.

``room_events``
~~~~~~~~~~~~~~~

This category covers all events in rooms that the user has joined. The search
is performed on certain keys of certain event types.

The supported keys to search over are:

- ``content.body`` in ``m.room.message``
- ``content.name`` in ``m.room.name``
- ``content.topic`` in ``m.room.topic``

Security considerations
-----------------------
The server must only return results that the user has permission to see.

