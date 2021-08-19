Documentation Style
===================

Each document should begin with a brief single sentence to describe what this
file contains: in this case a description of the style to write documentation
in.

Format
------

Documentation is written in Commonmark markdown.

Sections
--------

Markdown supports headings through the `#` prefix on text. Please avoid heavily
nested titles (h6, or 6 `#` characters) and instead re-evaluate the document structure.

Correct capitalisation for long section names
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Headings should start with a capital letter, and use lower-case otherwise. This
document is an example of what we mean.

TODOs
-----

Any file in this repository might make it onto the matrix.org site, and as such
we do not want ``TODO`` markers visible there. For internal comments, notes, TODOs,
etc please use standard markdown comments (`<!-- TODO TravisR: Fix this -->`). Please
include your name in the TODO comment so we know who to ask about it in the future.

Line widths
-----------

We use 80 characters for line widths. This is a guideline and can be ignored IF
AND ONLY IF it makes reading more legible. Use common sense.

For proposals, please use 120 characters as a guide.

Stylistic notes
---------------

General
~~~~~~~

Try to write clearly and unambiguously. Remember that many readers will not
have English as their first language.

Prefer British English (colour, -ise) to American English.

The word "homeserver" is spelt thus (rather than "home server", "Homeserver",
or (argh) "Home Server"). However, an identity server is two words.

An "identity server" (spelt thus) implements the Identity Service API (also spelt
thus). However, "Application Services" (spelt thus) implement the Application Service
API. Application Services should not be called "appservices" in documentation.

.. Rationale: "homeserver" distinguishes from a "home server" which is a server
   you have at home. "identity server" is clear, whereas "identityserver" is
   horrible.

Lists should:

* Be introduced with a colon.
* Be used where they provide clarity.
* Contain entries which start with a capital and end with a full stop.

OpenAPI
~~~~~~~

When writing OpenAPI specifications for the API endpoints, follow these rules:

* ``summary``: a phrase summarising what this API does. Start with a capital,
  end with a full stop. Examples: "Sends an event."; "Searches the directory."

* ``description``: a longer description of the behaviour of this API, written
  in complete sentences. Use multiple paragraphs if necessary.

  Example:

      This API sends an event to the room. The server must ensure that the user
      has permission to post events to this room.

* ``operationId``: a camelCased unique identifier for this endpoint. This will
  be used to automatically generate bindings for the endpoint.

* Parameter and property ``description``\s: a phrase summarising the behaviour
  of this parameter or property, optionally followed by sentences giving more
  detailed explanations. Start with a capital, end with a full stop.

  The description is also the place to define default values for optional
  properties. Use the wording "Defaults to X [if unspecified]."

  Some descriptions start with the word "Optional" to explicitly mark optional
  properties and parameters. This is redundant. Instead, use the ``required``
  property to mark those that are required.
