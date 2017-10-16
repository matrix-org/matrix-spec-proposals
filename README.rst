This repository contains the documentation for Matrix.

Primarily, that means the Matrix protocol specifcation, but this repo also
comtains a lot of supporting documents, including some introductions to Matrix,
and, notably, a list of projects using Matrix which is visible on the
`matrix.org website <https://matrix.org/docs/projects/try-matrix-now.html>`_.

Issue tracking
==============

Issues with the Matrix specification and supporting documentation are tracked
in `GitHub <https://github.com/matrix-org/matrix-doc/issues>`_.

The following labels are used to help categorize issues:

`spec-omission <https://github.com/matrix-org/matrix-doc/labels/spec-omission>`_
--------------------------------------------------------------------------------

Things which have been implemented but not currently specified. These may range
from entire API endpoints, to particular options or return parameters.

Issues with this label will have been implemented in `Synapse
<https://github.com/matrix-org/synapse>`_. Normally there will be a design
document in Google Docs or similar which describes the feature.

Examples:

* `Spec PUT /directory/list <https://github.com/matrix-org/matrix-doc/issues/417>`_
* `Unspec'd server_name request param for /join/{roomIdOrAlias}
  <https://github.com/matrix-org/matrix-doc/issues/904>`_

`clarification <https://github.com/matrix-org/matrix-doc/labels/clarification>`_
--------------------------------------------------------------------------------

An area where the spec could do with being more explicit.

Examples:

* `Spec the implicit limit on /syncs
  <https://github.com/matrix-org/matrix-doc/issues/708>`_

* `Clarify the meaning of the currently_active flags in presence events
  <https://github.com/matrix-org/matrix-doc/issues/686>`_

`bug <https://github.com/matrix-org/matrix-doc/labels/bug>`_
------------------------------------------------------------

Something which is in the spec, but is wrong.

Note: this is *not* for things that are badly designed or don't work well
(for which see 'improvement' or 'feature') - it is for places where the
spec doesn't match reality.

Examples:

* `swagger is wrong for directory PUT
  <https://github.com/matrix-org/matrix-doc/issues/933>`_

* `receipts section still refers to initialSync
  <https://github.com/matrix-org/matrix-doc/issues/695>`_

`improvement <https://github.com/matrix-org/matrix-doc/labels/improvement>`_
----------------------------------------------------------------------------

A suggestion for a relaatively simple improvement to the protocol.

Examples:

* `We need a 'remove 3PID' API so that users can remove mappings
  <https://github.com/matrix-org/matrix-doc/issues/620>`_
* `We should mandate that /publicRooms requires an access_token
  <https://github.com/matrix-org/matrix-doc/issues/612>`_

`feature <https://github.com/matrix-org/matrix-doc/labels/feature>`_
--------------------------------------------------------------------

A suggestion for a significant extension to the matrix protocol which
needs considerable consideration before implementation.

Examples:

* `Peer-to-peer Matrix <https://github.com/matrix-org/matrix-doc/issues/710>`_
* `Specify a means for clients to "edit" previous messages
  <https://github.com/matrix-org/matrix-doc/issues/682>`_

`projects <https://github.com/matrix-org/matrix-doc/labels/projects>`_
----------------------------------------------------------------------

A project which needs adding to the 'Try Matrix Now' page.

Examples:

* `add https://gitlab.com/uhoreg/matrix-appservice-prosody
  <https://github.com/matrix-org/matrix-doc/issues/1016>`_

* `add https://github.com/tavoda/matrix-java project
  <https://github.com/matrix-org/matrix-doc/issues/956>`_

`site <https://github.com/matrix-org/matrix-doc/labels/site>`_
--------------------------------------------------------------

Ideas for things to help document or sell matrix more generally.
(Probably these would be better filed under 
https://github.com/matrix-org/matrix.org, but they tend to end up here.)

Structure of this repository
============================

- ``api`` : `OpenAPI`_ (swagger) specifications for the the HTTP APIs.
- ``attic``: historical sections of specification for reference
  purposes.
- ``changelogs``: change logs for the various parts of the
  specification.
- ``drafts``: Previously, contained documents which were under discussion for
  future incusion into the specification and/or supporting documentation. This
  is now historical, as we use separate discussion documents (see
  `<CONTRIBUTING.rst>`_).
- ``event-schemas``: the `JSON Schema`_ for all Matrix events
  contained in the specification, along with example JSON files.
- ``meta``: documents outlining the processes involved when writing
  documents, e.g. documentation style, guidelines.
- ``scripts``: scripts to generate formatted versions of the
  documentation, typically HTML.
- ``specification``: the specification split up into sections.
- ``supporting-docs``: additional documents which explain design
  decisions, examples, use cases, etc.
- ``templating``: the templates and templating system used to
  generate the spec.

.. _OpenAPI: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md
.. _JSON Schema: http://json-schema.org/

Contributing
============

If you want to ask more about the specification, join us on
`#matrix-dev:matrix.org <http://matrix.to/#/#matrix-dev:matrix.org>`_.

If you would like to contribute to the specification or supporting
documentation, see `<CONTRIBUTING.rst>`_.
