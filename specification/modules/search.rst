Server Side Search
==================

.. _module:search:

The search API allows clients to perform full text search across events in
their rooms without having to download the entire histories.

Client behaviour
----------------
{{search_http_api}}

Security considerations
-----------------------
The server must only return results that the user has permission to see.

