Server Side Search
==================

.. _module:search:

The search API allows clients to perform full text search across events in all
rooms that the user has been in, including those that they have left. Only
events that the user is allowed to see will be searched.

Client behaviour
----------------
{{search_http_api}}

Search Categories
-----------------

The search API allows clients to search in different categories of items.
Currently the only specified category is ``room_events``.

``room_events``
~~~~~~~~~~~~~~~

This category covers all events that the user is allowed to see, including
events in rooms that they have left. The search is performed on certain keys of
certain event types.

The supported keys to search over are:

- ``content.body`` in ``m.room.message``
- ``content.name`` in ``m.room.name``
- ``content.topic`` in ``m.room.topic``

The search will *not* include rooms that are end to end encrypted.

The results include a ``rank`` key that can be used to sort the results by
revelancy. The higher the ``rank`` the more relevant the result is.

The value of ``count`` may not match the number of results. For example due to
the search query matching 1000s of results and the server truncating the
response.

Security considerations
-----------------------
The server must only return results that the user has permission to see.

