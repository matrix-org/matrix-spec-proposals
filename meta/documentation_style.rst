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

Headings should be in `sentence case <https://apastyle.apa.org/style-grammar-guidelines/capitalization/sentence-case>`,
as represented by this document.

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

When talking about properties in JSON objects, prefer the word "property" to "field",
"member", or various other alternatives. For example: "this property will be set to
X if ...". Also avoid the term "key" unless you are specifically talking about the
*name* of a property - and be mindful of the scope for confusion with cryptographic
keys.

Changes between spec versions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sections should reference the Matrix spec version they were added/changed in. This
is often a guess at what the next version will be - please use the currently released
version with a minor version bump as the referenced version. For example, if the
current version is `v1.1` then annotate your changes with `v1.2`.

"Added/changed in" tags can be documented as the following:

* `{{% added-in v="1.2" %}}` or `{{% changed-in v="1.2" %}}` within Markdown documents.
* `x-addedInMatrixVersion` and `x-changedInMatrixVersion` within OpenAPI.

In rare cases, `this=true` can be used on the Markdown syntax to adjust the wording.
This is most commonly used in room version specifications.

**Tip**: If you're trying to inline the Markdown version and getting unexpected results,
try replacing the `%` symbols with `<` and `>`, changing how Hugo renders the shortcode.

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

Room versions
~~~~~~~~~~~~~

Room versions are fully specified to cover the entirety of their composition for
client and server implementations to reference. As such, they have a relatively
strict format that must be followed, described below.

These rules do not affect MSCs.

The introduction must cover:

* The version the new room version builds on, if any.
* A brief (one or two line) description of what the room version is expected to
  consist of. For example, "..., adding new redaction rules to cover memberships".

The next section must then be "Client considerations" to help client developers avoid
the naturally complex "Server implementation components" later on. This section must:

* Clearly describe any and all changes which affect users of the Client-Server API.
* Clearly make reference to the redaction rules. A copy/paste example of this is in
  Room Version 3: "Though unchanged in this room version, clients which implement the
  redaction algorithm locally should refer to the [redactions] section below for a full
  overview."

The next section must then be "Server implementation components". This section must:

* Start with the copy/pasted warning that clients should skip or ignore the section.
* Repeat the introduction using server-focused language. This includes repeating which
  room version, if any, the room version builds upon.
* Clearly describe any and all changes which affect server implementations. This
  includes a "Redactions" section, even if covered by the client considerations section.
  See Room Version 9 for an example.

Finally, the last section must then be an "Unchanged since vX" section, where ``vX``
is the room version the version builds upon. If the room version doesn't build upon
another room version, this section is excluded.

In each of the client, server, and unchanged sections the subheadings must be in the
following order:

* Redactions
* Handling redactions (if applicable)
* Event IDs (if applicable)
* Event format
* Authorization rules
* State resolution
* Canonical JSON
* Signing key validity period (if applicable)

Within a given room version, these subheadings must appear at least once. Applicability
of the headings depends on the room version a new version builds upon: if the underlying
room version contains the subheading, the new room version must also contain the subheading.

The subheadings which are always deemed as client-affecting are:

* Redactions

When a new subheading is added, it must be referenced and ordered in this document.
