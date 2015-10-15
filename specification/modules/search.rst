Server Side Search
==================

.. _module:search:

The search API allows clients to perform full text search across events in
their rooms without having to download the entire histories.

Client behaviour
----------------
{{search_http_api}}

Search Categories
~~~~~~~~~~~~~~~~~

The search API allows clients to search in different categories of items.
Currently the only specified category is ``room_events``, which include
events in rooms the user had joined.

Security considerations
-----------------------
The server must only return results that the user has permission to see.

