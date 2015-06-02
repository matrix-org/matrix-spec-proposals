This repository contains the documentation for Matrix.

Structure
=========

- ``api`` : Contains the HTTP API specification.
- ``drafts`` : Contains documents which will make it into the specification
  and/or supporting documentation at some point in the future.
- ``event-schemas`` : Contains the `JSON Schema`_ for all Matrix events
  contained in the specification, along with example JSON files.
- ``meta`` : Contains documents outlining the processes involved when writing
  documents, e.g. documentation style, guidelines.
- ``scripts`` : Contains scripts to generate formatted versions of the
  documentation, typically HTML.
- ``specification`` : Contains the specification split up into sections.
- ``supporting-docs`` : Contains additional documents which explain design 
  decisions, examples, use cases, etc.
- ``templating`` : Contains the templates and templating system used to
  generate the spec.

Contributing
============

Known issues with the specification are represented as JIRA issues at
https://matrix.org/jira/browse/SPEC

If you want to ask more about the specification, or have suggestions for
improvements, join us on ``#matrix-dev:matrix.org`` via https://matrix.org/beta.

.. _JSON Schema: http://json-schema.org/
