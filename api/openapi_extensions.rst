OpenAPI Extensions
==================

For some functionality that is not directly provided by the OpenAPI v2
specification, some extensions have been added that are to be consistent
across the specification. The defined extensions are listed below. Extensions
should not break parsers, however if extra functionality is required, aware
parsers should be able to take advantage of the added syntax.

Extensible Query Parameters
---------------------------

If a unknown amount of query parameters can be added to a request, the
``name`` should be in form of ``something...``, with the trailing ellipses
representing the possibility of more fields.

Example:

.. code-block::

  - in: query
    name: fields...
    type: string