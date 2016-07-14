This repository contains the documentation for Matrix.

Structure
=========

- ``api`` : Contains the HTTP API specification.
- ``attic``: Contains historical sections of specification for reference
  purposes.
- ``changelogs``: Contains change logs for the various parts of the
  specification.
- ``drafts``: Previously, contained documents which were under discussion for
  future incusion into the specification and/or supporting documentation. This
  is now historical, as we use separate discussion documents (see
  `<CONTRIBUTING.rst>`_).
- ``event-schemas``: Contains the `JSON Schema`_ for all Matrix events
  contained in the specification, along with example JSON files.
- ``meta``: Contains documents outlining the processes involved when writing
  documents, e.g. documentation style, guidelines.
- ``scripts``: Contains scripts to generate formatted versions of the
  documentation, typically HTML.
- ``specification``: Contains the specification split up into sections.
- ``supporting-docs``: Contains additional documents which explain design
  decisions, examples, use cases, etc.
- ``templating``: Contains the templates and templating system used to
  generate the spec.

Contributing
============

Known issues with the specification are represented as JIRA issues at
`<https://matrix.org/jira/browse/SPEC>`_.

If you want to ask more about the specification, join us on
`#matrix-dev:matrix.org <http://matrix.to/#/#matrix-dev:matrix.org>`_.

If you would like to contribute to the specification or supporting
documentation, see `<CONTRIBUTING.rst>`_.

.. _JSON Schema: http://json-schema.org/
