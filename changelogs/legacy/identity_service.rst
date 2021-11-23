r0.3.0
======

New Endpoints
-------------

- Add ``/account``, ``/account/register``, and ``/account/logout`` to authenticate with the identity server. (`#2255 <https://github.com/matrix-org/matrix-doc/issues/2255>`_)
- Add endpoints for accepting and handling terms of service. (`#2258 <https://github.com/matrix-org/matrix-doc/issues/2258>`_)
- Add ``/hash_details`` and a new ``/lookup`` endpoint for performing hashed association lookups. (`#2287 <https://github.com/matrix-org/matrix-doc/issues/2287>`_)


Backwards Compatible Changes
----------------------------

- Deprecate the v1 API in favour of an authenticated v2 API. (`#2254 <https://github.com/matrix-org/matrix-doc/issues/2254>`_)


r0.2.1
======

Spec Clarifications
-------------------

- Remove incorrect ``id_server`` parameter from ``/requestToken`` endpoints. (`#2124 <https://github.com/matrix-org/matrix-doc/issues/2124>`_)
- Clarify that identity servers can return 403 for unbind requests. (`#2126 <https://github.com/matrix-org/matrix-doc/issues/2126>`_)


r0.2.0
======

New Endpoints
-------------

- Add ``/3pid/unbind`` for removing 3PIDs. (`#2046 <https://github.com/matrix-org/matrix-doc/issues/2046>`_)


Spec Clarifications
-------------------

- Fix various spelling mistakes throughout the specification. (`#1853 <https://github.com/matrix-org/matrix-doc/issues/1853>`_)
- Fix route for ``/3pid/bind``. (`#1967 <https://github.com/matrix-org/matrix-doc/issues/1967>`_)
- Add missing aesthetic parameters to ``/store-invite``. (`#2049 <https://github.com/matrix-org/matrix-doc/issues/2049>`_)
- Clarify what the client should receive upon sending an identical email validation request multiple times. (`#2057 <https://github.com/matrix-org/matrix-doc/issues/2057>`_)
- Clarify that the default transport is JSON over HTTP. (`#2086 <https://github.com/matrix-org/matrix-doc/issues/2086>`_)


r0.1.0
======

This is the first release of the Identity Service API. With this API, clients and
homeservers can store bindings between third party identifiers such as email addresses
and phone numbers, associating them with Matrix user IDs. Additionally, identity
servers offer the ability to invite third party users to Matrix rooms by storing
the invite until the identifier is bound.
