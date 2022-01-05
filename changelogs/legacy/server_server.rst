r0.1.4
======

New Endpoints
-------------

- Add new ``POST /publicRooms`` endpoint for filtering the room directory. (`#2305 <https://github.com/matrix-org/matrix-doc/issues/2305>`_)
- Add new v2 ``/send_join`` and ``/send_leave`` endpoints per `MSC1802 <https://github.com/matrix-org/matrix-doc/pull/1802>`_. (`#2547 <https://github.com/matrix-org/matrix-doc/issues/2547>`_)


Removed Endpoints
-----------------

- Remove the unused ``query_auth`` API per `MSC2451 <https://github.com/matrix-org/matrix-doc/pull/2451>`_. (`#2470 <https://github.com/matrix-org/matrix-doc/issues/2470>`_)


Spec Clarifications
-------------------

- Move auth event selection to a more obvious location. (`#2392 <https://github.com/matrix-org/matrix-doc/issues/2392>`_)
- Fix typo in Request Authentication python example. (`#2510 <https://github.com/matrix-org/matrix-doc/issues/2510>`_)
- Clarify which fields are required on the key server endpoints. (`#2527 <https://github.com/matrix-org/matrix-doc/issues/2527>`_)
- Clarify the limits of ``prev_events`` and ``auth_events`` for PDUs. (`#2538 <https://github.com/matrix-org/matrix-doc/issues/2538>`_)
- Clarify which events are targeted by backfill. (`#2559 <https://github.com/matrix-org/matrix-doc/issues/2559>`_)
- Fix the response format of the ``/send`` endpoint. (`#2560 <https://github.com/matrix-org/matrix-doc/issues/2560>`_)
- Clarify signature object structures for encryption. (`#2566 <https://github.com/matrix-org/matrix-doc/issues/2566>`_)
- Clarify the server names to use when signing requests. (`#2570 <https://github.com/matrix-org/matrix-doc/issues/2570>`_)
- Clarify the state/auth chain requirements for ``/send_join``. (`#2575 <https://github.com/matrix-org/matrix-doc/issues/2575>`_)
- Fix various spelling errors throughout the specification. (`#2577 <https://github.com/matrix-org/matrix-doc/issues/2577>`_)


r0.1.3
======

Spec Clarifications
-------------------

- Clarify the encryption algorithms supported by the device of the user keys query example. (`#2157 <https://github.com/matrix-org/matrix-doc/issues/2157>`_)
- Clarify the purpose of reference hashes. (`#2159 <https://github.com/matrix-org/matrix-doc/issues/2159>`_)


r0.1.2
======

Spec Clarifications
-------------------

- Change examples to use example.org instead of a real domain. (`#1650 <https://github.com/matrix-org/matrix-doc/issues/1650>`_)
- Fix the ``access_token`` parameter in the open_id endpoint. (`#1906 <https://github.com/matrix-org/matrix-doc/issues/1906>`_)
- Fix various spelling mistakes throughout the specification. (`#1991 <https://github.com/matrix-org/matrix-doc/issues/1991>`_)
- Clarify exactly what invite_room_state consists of. (`#2067 <https://github.com/matrix-org/matrix-doc/issues/2067>`_)
- Clarify how ``valid_until_ts`` behaves with respect to room version. (`#2080 <https://github.com/matrix-org/matrix-doc/issues/2080>`_)
- Clarify which servers are supposed to sign events. (`#2081 <https://github.com/matrix-org/matrix-doc/issues/2081>`_)
- Clarify the key object definition for the key management API. (`#2083 <https://github.com/matrix-org/matrix-doc/issues/2083>`_)
- Clarify how many PDUs are contained in transaction objects for various endpoints. (`#2095 <https://github.com/matrix-org/matrix-doc/issues/2095>`_)
- Clarify that the trailing slash is optional on ``/keys/*`` endpoints when no key ID is requested. (`#2097 <https://github.com/matrix-org/matrix-doc/issues/2097>`_)


r0.1.1
======

Spec Clarifications
-------------------

- Remove legacy references to TLS fingerprints. (`#1844 <https://github.com/matrix-org/matrix-doc/issues/1844>`_)
- Clarify that servers should not fail to contact servers if ``/.well-known`` fails. (`#1855 <https://github.com/matrix-org/matrix-doc/issues/1855>`_)


r0.1.0
======

This is the first release of the Server Server (Federation) specification.
It includes support for homeservers being able to interact with other
homeservers in a decentralized and standard way.
