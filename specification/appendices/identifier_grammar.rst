.. Copyright 2016 Openmarket Ltd.
.. Copyright 2017 New Vector Ltd.
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..     http://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.

Identifier Grammar
------------------

Server Name
~~~~~~~~~~~

A homeserver is uniquely identified by its server name. This value is used in a
number of identifiers, as described below.

The server name represents the address at which the homeserver in question can
be reached by other homeservers. The complete grammar is::

    server_name = dns_name [ ":" port]
    dns_name = host
    port = *DIGIT

where ``host`` is as defined by `RFC3986, section 3.2.2
<https://tools.ietf.org/html/rfc3986#section-3.2.2>`_.

Examples of valid server names are:

* ``matrix.org``
* ``matrix.org:8888``
* ``1.2.3.4`` (IPv4 literal)
* ``1.2.3.4:1234`` (IPv4 literal with explicit port)
* ``[1234:5678::abcd]`` (IPv6 literal)
* ``[1234:5678::abcd]:5678`` (IPv6 literal with explicit port)


Common Identifier Format
~~~~~~~~~~~~~~~~~~~~~~~~

The Matrix protocol uses a common format to assign unique identifiers to a
number of entities, including users, events and rooms. Each identifier takes
the form::

  &localpart:domain

where ``&`` represents a 'sigil' character; ``domain`` is the `server name`_ of
the homeserver which allocated the identifier, and ``localpart`` is an
identifier allocated by that homeserver.

The sigil characters are as follows:

* ``@``: User ID
* ``!``: Room ID
* ``$``: Event ID
* ``#``: Room alias

The precise grammar defining the allowable format of an identifier depends on
the type of identifier.

User Identifiers
++++++++++++++++

Users within Matrix are uniquely identified by their Matrix user ID. The user
ID is namespaced to the homeserver which allocated the account and has the
form::

  @localpart:domain

The ``localpart`` of a user ID is an opaque identifier for that user. It MUST
NOT be empty, and MUST contain only the characters ``a-z``, ``0-9``, ``.``,
``_``, ``=``, ``-``, and ``/``.

The ``domain`` of a user ID is the `server name`_ of the homeserver which
allocated the account.

The length of a user ID, including the ``@`` sigil and the domain, MUST NOT
exceed 255 characters.

The complete grammar for a legal user ID is::

  user_id = "@" user_id_localpart ":" server_name
  user_id_localpart = 1*user_id_char
  user_id_char = DIGIT
               / %x61-7A                   ; a-z
               / "-" / "." / "=" / "_" / "/"

.. admonition:: Rationale

  A number of factors were considered when defining the allowable characters
  for a user ID.

  Firstly, we chose to exclude characters outside the basic US-ASCII character
  set. User IDs are primarily intended for use as an identifier at the protocol
  level, and their use as a human-readable handle is of secondary
  benefit. Furthermore, they are useful as a last-resort differentiator between
  users with similar display names. Allowing the full unicode character set
  would make very difficult for a human to distinguish two similar user IDs. The
  limited character set used has the advantage that even a user unfamiliar with
  the Latin alphabet should be able to distinguish similar user IDs manually, if
  somewhat laboriously.

  We chose to disallow upper-case characters because we do not consider it
  valid to have two user IDs which differ only in case: indeed it should be
  possible to reach ``@user:matrix.org`` as ``@USER:matrix.org``. However,
  user IDs are necessarily used in a number of situations which are inherently
  case-sensitive (notably in the ``state_key`` of ``m.room.member``
  events). Forbidding upper-case characters (and requiring homeservers to
  downcase usernames when creating user IDs for new users) is a relatively simple
  way to ensure that ``@USER:matrix.org`` cannot refer to a different user to
  ``@user:matrix.org``.

  Finally, we decided to restrict the allowable punctuation to a very basic set
  to reduce the possibility of conflicts with special characters in various
  situations. For example, "*" is used as a wildcard in some APIs (notably the
  filter API), so it cannot be a legal user ID character.

  The length restriction is derived from the limit on the length of the
  ``sender`` key on events; since the user ID appears in every event sent by the
  user, it is limited to ensure that the user ID does not dominate over the actual
  content of the events.

Matrix user IDs are sometimes informally referred to as MXIDs.

Historical User IDs
<<<<<<<<<<<<<<<<<<<

Older versions of this specification were more tolerant of the characters
permitted in user ID localparts. There are currently active users whose user
IDs do not conform to the permitted character set, and a number of rooms whose
history includes events with a ``sender`` which does not conform. In order to
handle these rooms successfully, clients and servers MUST accept user IDs with
localparts from the expanded character set::

  extended_user_id_char = %x21-39 / %x3B-7F  ; all ascii printing chars except :

Mapping from other character sets
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

In certain circumstances it will be desirable to map from a wider character set
onto the limited character set allowed in a user ID localpart. Examples include
a homeserver creating a user ID for a new user based on the username passed to
``/register``, or a bridge mapping user ids from another protocol.

.. TODO-spec

   We need to better define the mechanism by which homeservers can allow users
   to have non-Latin login credentials. The general idea is for clients to pass
   the non-Latin in the ``username`` field to ``/register`` and ``/login``, and
   the HS then maps it onto the MXID space when turning it into the
   fully-qualified ``user_id`` which is returned to the client and used in
   events.

Implementations are free to do this mapping however they choose. Since the user
ID is opaque except to the implementation which created it, the only
requirement is that the implemention can perform the mapping
consistently. However, we suggest the following algorithm:

1. Encode character strings as UTF-8.

2. Convert the bytes ``A-Z`` to lower-case.

   * In the case where a bridge must be able to distinguish two different users
     with ids which differ only by case, escape upper-case characters by
     prefixing with ``_`` before downcasing. For example, ``A`` becomes
     ``_a``. Escape a real ``_`` with a second ``_``.

3. Encode any remaining bytes outside the allowed character set, as well as
   ``=``, as their hexadecimal value, prefixed with ``=``. For example, ``#``
   becomes ``=23``; ``á`` becomes ``=c3=a1``.

.. admonition:: Rationale

  The suggested mapping is an attempt to preserve human-readability of simple
  ASCII identifiers (unlike, for example, base-32), whilst still allowing
  representation of *any* character (unlike punycode, which provides no way to
  encode ASCII punctuation).


Room IDs and Event IDs
++++++++++++++++++++++

A room has exactly one room ID. A room ID has the format::

  !opaque_id:domain

An event has exactly one event ID. An event ID has the format::

  $opaque_id:domain

The ``domain`` of a room/event ID is the `server name`_ of the homeserver which
created the room/event. The domain is used only for namespacing to avoid the
risk of clashes of identifiers between different homeservers. There is no
implication that the room or event in question is still available at the
corresponding homeserver.

Event IDs and Room IDs are case-sensitive. They are not meant to be human
readable.

.. TODO-spec
  What is the grammar for the opaque part? https://matrix.org/jira/browse/SPEC-389

Room Aliases
++++++++++++

A room may have zero or more aliases. A room alias has the format::

      #room_alias:domain

The ``domain`` of a room alias is the `server name`_ of the homeserver which
created the alias. Other servers may contact this homeserver to look up the
alias.

Room aliases MUST NOT exceed 255 bytes (including the ``#`` sigil and the
domain).

.. TODO-spec
  - Need to specify precise grammar for Room Aliases. https://matrix.org/jira/browse/SPEC-391
