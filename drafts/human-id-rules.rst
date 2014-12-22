This document outlines the format for human-readable IDs within matrix.

Summary
-------
- Human-readable IDs are Room Aliases and User IDs.
- They MUST be Unicode as UTF-8.
- If spoof checks fail, the user ID in question MUST be rewritten to be punycode
  with an additional ``@`` prefix.
  Room aliases cannot be rewritten.
- Spoof Checks:
   - MUST NOT contain one of the 107 blacklisted characters on this list: 
     http://kb.mozillazine.org/Network.IDN.blacklist_chars
   - MUST NOT contain characters from >1 language, defined by
     http://cldr.unicode.org/
- User IDs MUST NOT contain a ``:`` or start with a ``@`` or ``.``
- Room aliases MUST NOT contain a ``:``
- User IDs SHOULD be case-insensitive.

Overview
--------
UTF-8 is quickly becoming the standard character encoding set on the web. As
such, Matrix requires that all strings MUST be encoded as UTF-8. However,
using Unicode as the character set for human-readable IDs is troublesome. There
are many different characters which appear identical to each other, but would
identify different users. In addition, there are non-printable characters which
cannot be rendered by the end-user. This opens up a security vulnerability with
phishing/spoofing of IDs, commonly known as a homograph attack.

Web browsers encountered this problem when International Domain Names were
introduced. A variety of checks were put in place in order to protect users. If
an address failed the check, the raw punycode would be displayed to
disambiguate the address. Similar checks are performed by home servers in
Matrix in order to protect users. In the event of a failed check, the raw
punycode is displayed as the user ID along with a special escape sequence to
indicate the change.

Types of human-readable IDs
~~~~~~~~~~~~~~~~~~~~~~~~~~~
There are two main human-readable IDs in question:

- Room aliases
- User IDs

Room aliases look like ``#localpart:domain``. These aliases point to opaque
non human-readable room IDs. These pointers can change, so there is already an
issue present with the same ID pointing to a different destination at a later
date. Checks SHOULD be applied to room aliases, but they cannot be renamed in
punycode as that would break the alias. As a result, the checks in this document
apply to user IDs, although HSes may wish to enforce them on room alias 
creation.

User IDs look like ``@localpart:domain``. These represent actual end-users, and
unlike room aliases, there is no layer of indirection. This presents a much
greater concern with homograph attacks. Checks MUST be applied to user IDs.

Spoof Checks
------------
First, each ID is split into segments (localpart/domain) around the ``:``. For 
this reason, ``:`` is a reserved character and cannot be a localpart or domain 
character. 

User IDs which start with an ``@`` are used as an escape sequence for failed 
user IDs. As a result, the localpart MUST NOT start with an ``@`` in order to 
avoid namespace clashes.

The checks are similar to web browsers for IDNs. The first check is that the 
segment MUST NOT contain a blacklisted character on this list: 
http://kb.mozillazine.org/Network.IDN.blacklist_chars - NB: Even though 
this is Mozilla, Chrome follows the same list as per 
http://www.chromium.org/developers/design-documents/idn-in-google-chrome

The second check is that it MUST NOT contain characters from more than 1 
language. This is defined by this dataset http://cldr.unicode.org/ and is 
applied after stripping " 0-9, +, -, [, ], _, and the space character" 
( http://www.chromium.org/developers/design-documents/idn-in-google-chrome )


Consequences of a failed check
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If a user ID fails the check, the user ID on the event is renamed. This is 
possible because user IDs contain routing information. This doesn't require 
extra work for clients, and users will see an odd user ID rather than a spoofed 
name. Renaming is done in order to protect users of a given HS, so if a 
malicious HS doesn't rename their IDs, it doesn't affect any other HS.

- The HS MAY reject the creation of the room alias or user ID. This is the 
  preferred choice but it is entirely benevolent: other HSes may not apply this
  rule so checks on incoming events MUST still be applied. The error code returned
  for the rejection is ``M_FAILED_HUMAN_ID_CHECK``, which is generic enough for 
  both failing due to homograph attacks, and failing due to including ``:`` s. 
  Error message MAY go into further information about which characters were 
  rejected and why.

- The HS MUST rename the localpart which failed the check. It SHOULD be 
  represented as punycode. The HS MUST prefix the punycode with the escape 
  sequence ``@`` on user ID localparts, e.g. ``@@somepunycode:domain``. Room 
  aliases do not need to be escaped, and indeed they cannot be, as the originating
  HS will not understand the rewritten alias. If a HS renames a user ID, it MUST 
  be able to apply the reverse mapping in case the user wishes to communicate with
  the ID which failed the check.

Other rejected solutions for failed checks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Additional key: Informational key on the event attached by HS to say "unsafe
  ID". Problem: clients can just ignore it, and since it will appear only very
  rarely, easy to forget when implementing clients.
- Require client handshake: Forces clients to implement
  a check, else they cannot communicate with the misleading ID. However, this
  is extra overhead in both client implementations and round-trips.
- Reject event: Outright rejection of the ID at the point of creation /
  receiving event. Point of creation rejection is preferable to avoid the ID
  entering the system in the first place. However, malicious HSes can just
  allow the ID. Hence, other home servers must reject them if they see them in
  events. Client never sees the problem ID, provided the HS is correctly
  implemented. However, it is difficult to ensure that ALL HSes will come to the
  same conclusion (given the CLDR dataset does come out with new versions).

Namespacing
-----------

Bots
~~~~
User IDs representing real users SHOULD NOT start with a ``.``. User IDs which
act on behalf of a real user (e.g. an IRC/XMPP bot) SHOULD start with a ``.``.
This namespaces real/generated user IDs. Further namespacing SHOULD be applied
based on the service being used, getting progressively more specific, similar to
event types: e.g. ``@.irc.freenode.matrix.<username>:domain``. Ultimately, the 
HS in question has control over their user ID namespace, so this is just a 
recommendation.

Additional recommendations
--------------------------

Capitalisation
~~~~~~~~~~~~~~
The home server SHOULD NOT allow two user IDs that differ only by case. This SHOULD be applied based on the 
capitalisation rules in the CLDR dataset: http://cldr.unicode.org/

This check SHOULD be applied when the user ID is created, in order to prevent
registration with the same name and different capitalisations, e.g.
``@foo:bar`` vs ``@Foo:bar`` vs ``@FOO:bar``. Home servers MAY canonicalise
the user ID to be completely lower-case if desired.

