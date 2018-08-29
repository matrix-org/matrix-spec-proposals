Abstract
========

This document proposes a format for human-readable IDs (specifically, room
aliases) within Matrix.

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

The only human-readable IDs currently in Matrix are Room Aliases.  Room aliases
look like ``#localpart:domain``. These aliases point to opaque non
human-readable room IDs. These pointers can change to point at a different room
ID at any time.

Proposal
========

Room aliases have the format::

  #localpart:domain

As with other identifiers using the common identifier format, the ``domain`` is
a `server name`_ - in this case, the server hosting this alias which may be
contacted to resolve the alias to a room ID. The ``domain`` may be an
internationalized domain name, encoded using `punycode`_. When displaying the
alias to users, Matrix clients may optionally decode any punycode-encoded parts
of the domain to unicode.

.. _punycode: https://tools.ietf.org/html/rfc3492
.. _RFC3490: https://tools.ietf.org/html/rfc3490
.. _server name: https://matrix.org/docs/spec/appendices.html#server-name

The ``localpart`` is a UTF-8-encoded, `NFC`_\-normalised unicode string.  The
following constitute invalid localparts for room aliases:

XXX: we need to figure out which of thes things to actually forbid:

- invalid utf8

  - invalid byte sequences
  - utf-16 surrogates U+D800 to U+DFFF
  - codepoints after U+10FFFF
  - overlong encodings

- strings not in NFC
- characters forbidden by NAMEPREP
  https://tools.ietf.org/html/rfc3491#section-5 ?
- strings which contain any of the 107 blacklisted characters listed at
  http://kb.mozillazine.org/Network.IDN.blacklist_chars ?
- strings which do not meet the bidi requirements
  https://tools.ietf.org/html/rfc5893 ?
  https://tools.ietf.org/html/rfc3454#section-6 ?
- Things from more than one language? ["After stripping ``"``, ``0-9``, ``+``, ``-``, ``[``, ``]``, ``_``, and the
  space character `` `` it MUST NOT
  contain characters from more than one language, defined by the `exemplar characters`_
  on http://cldr.unicode.org/ ]
- strings whose first character is a Unicode combining mark?
- strings which include the DISALLOWED code points in `RFC5892`_. (This
  includes a lot fof things which didn't exist in 2010, like emoji, so I don't
  think we should take this list as-is.)
- Complicated rules about CONTEXTO or CONTEXTJ code points in `RFC5892`_.


The total length of the (utf-8 encoded) room alias, including the sigil and the
server name, must not exceed 255 characters.

Servers should not allow clients to create aliases which are considered invalid
according to any of the above rules. Servers should also reject attempts to
resolve such aliases.

Provided an alias is valid, the following rules should be followed to normalise
an alias for storage and lookup:

- Normalise to NFKC
- Remove characters listed in https://tools.ietf.org/html/rfc3454#appendix-B.1
- Case-map according to https://tools.ietf.org/html/rfc3454#appendix-B.2

.. _NFC: http://unicode.org/reports/tr15/
.. _exemplar characters: http://cldr.unicode.org/translation/characters#TOC-Exemplar-Characters
.. _RFC5892: https://tools.ietf.org/html/rfc5892

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

.. _Google Chrome for IDN handling:
  https://www.chromium.org/developers/design-documents/idn-in-google-chrome
