Abstract
========

This document outlines a proposed format for human-readable IDs within Matrix.
For status see https://github.com/matrix-org/matrix-doc/pull/3/files

Background
----------
UTF-8 is the dominant character encoding for Unicode on the web. However,
using Unicode as the character set for human-readable IDs is troublesome. There
are many different characters which appear identical to each other, but would
produce different IDs. In addition, there are non-printable characters which
cannot be rendered by the end-user. This creates an opportunity for
phishing/spoofing of IDs, commonly known as a homograph attack.

Web browsers encountered this problem when International Domain Names were
introduced. A variety of checks were put in place in order to protect users. If
an address failed the check, the raw punycode would be displayed to
disambiguate the address.

The human-readable IDs in Matrix are Room Aliases and User IDs.
Room aliases look like ``#localpart:domain``. These aliases point to opaque
non human-readable room IDs. These pointers can change to point at a different
room ID at any time. User IDs look like ``@localpart:domain``. These represent
actual end-users (there is no indirection).

Proposal
========

User IDs and Room Aliases MUST be Unicode as UTF-8. Checks are performed on
these IDs by homeservers to protect users from phishing/spoofing attacks.
These checks are:

User ID Localparts:
 - MUST NOT contain a ``:`` or start with a ``@`` or ``.``
 - MUST NOT contain one of the 107 blacklisted characters on this list:
     http://kb.mozillazine.org/Network.IDN.blacklist_chars
 - After stripping " 0-9, +, -, [, ], _, and the space character it MUST NOT
   contain characters from >1 language, defined by the `exemplar characters`_
   on http://cldr.unicode.org/

.. _exemplar characters: http://cldr.unicode.org/translation/characters#TOC-Exemplar-Characters

Room Alias Localparts:
 - MUST NOT contain a ``:``
 - MUST NOT contain one of the 107 blacklisted characters on this list:
   http://kb.mozillazine.org/Network.IDN.blacklist_chars
 - After stripping " 0-9, +, -, [, ], _, and the space character it MUST NOT
   contain characters from >1 language, defined by the `exemplar characters`_
   on http://cldr.unicode.org/

.. _exemplar characters: http://cldr.unicode.org/translation/characters#TOC-Exemplar-Characters

In the event of a failed user ID check, well behaved homeservers MUST:
 - Rewrite user IDs in the offending events to be punycode with an additional ``@``
   prefix **before** delivering them to clients. There are no guarantees for
   consistency between homeserver ID checking implementations. As a result, user
   IDs MUST be sent in their *original* form over federation. This can be done in
   a stateless manner as the punycode form has no information loss.

In the event of a failed room alias check, well behaved homeservers MUST:
 - Send an HTTP status code 400 with an ``errcode`` of ``M_FAILED_HUMAN_ID_CHECK``
   to the client if the client is attempting to *create* this alias.
 - Send an HTTP status code 400 with an ``errcode`` of ``M_FAILED_HUMAN_ID_CHECK``
   to the client if the client is attempting to *join* a room via this alias.

Examples::

  @ebаy:example.org (Cyrillic 'a', everything else English)
  @@xn--eby-7cd:example.org (Punycode with additional '@')

Homeservers SHOULD NOT allow two user IDs that differ only by case. This
SHOULD be applied based on the capitalisation rules in the CLDR dataset:
http://cldr.unicode.org/

This check SHOULD be applied when the user ID is created, in order to prevent
registration with the same name and different capitalisations, e.g.
``@foo:bar`` vs ``@Foo:bar`` vs ``@FOO:bar``. Homeservers MAY canonicalise
the user ID to be completely lower-case if desired.

Rationale
=========

Each ID is split into segments (localpart/domain) around the ``:``. For
this reason, ``:`` is a reserved character and cannot be a localpart character.
The 107 blacklisted characters are used to prevent non-printable characters and
spaces from being used. The decision to ban characters from more than 1 language
matches the behaviour of `Google Chrome for IDN handling`_. This is to protect
against common homograph attacks such as ebаy.com (Cyrillic "a", rest is
English). This would always result in a failed check. Even with this though
there are limitations. For example, сахар is entirely Cyrillic, whereas caxap is
entirely Latin.

.. _Google Chrome for IDN handling: https://www.chromium.org/developers/design-documents/idn-in-google-chrome

User ID localparts cannot start with ``@`` so that a namespace of localparts
beginning with ``@`` can be created. This namespace is used for user IDs which
fail the ID checks. A failed ID could look like ``@@xn--c1yn36f:example.org``.

If a user ID fails the check, the user ID on the event is renamed. This doesn't
require extra work for clients, and users will see an odd user ID rather than a
spoofed name. Renaming is done in order to protect users of a given HS, so if a
malicious HS doesn't rename their IDs, it doesn't affect any other HS.

Room aliases cannot be rewritten as punycode and sent to the HS the alias is
referring to as the HS will not necessarily understand the rewritten alias.

Other rejected solutions for failed checks
------------------------------------------
- Additional key: Informational key on the event attached by HS to say "unsafe
  ID". Problem: clients can just ignore it, and since it will appear only very
  rarely, easy to forget when implementing clients.
- Require client handshake: Forces clients to implement
  a check, else they cannot communicate with the misleading ID. However, this
  is extra overhead in both client implementations and round-trips.
- Reject event: Outright rejection of the ID at the point of creation /
  receiving event. Point of creation rejection is preferable to avoid the ID
  entering the system in the first place. However, malicious HSes can just
  allow the ID. Hence, other homeservers must reject them if they see them in
  events. Client never sees the problem ID, provided the HS is correctly
  implemented. However, it is difficult to ensure that ALL HSes will come to the
  same conclusion (given the CLDR dataset does come out with new versions).

Outstanding Problems
====================

Capitalisation
--------------

The capitalisation rules outlined above are nice but do not fully resolve issues
where ``@alice:example.com`` tries to speak with ``@bob:example.org`` using
``@Bob:example.org``. It is up to ``example.org`` to map ``Bob`` to ``bob`` in
a sensible way.
