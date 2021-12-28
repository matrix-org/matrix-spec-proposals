r0.6.1
======

New Endpoints
-------------

- Added ``/rooms/{roomId}/aliases`` for retrieving local aliases for a room. (`#2562 <https://github.com/matrix-org/matrix-doc/issues/2562>`_)


Backwards Compatible Changes
----------------------------

- Added data structures for defining moderation policies in rooms per `MSC2313 <https://github.com/matrix-org/matrix-doc/pull/2313>`_. (`#2434 <https://github.com/matrix-org/matrix-doc/issues/2434>`_)
- Optionally invalidate other access tokens during password modification per `MSC2457 <https://github.com/matrix-org/matrix-doc/pull/2457>`_. (`#2523 <https://github.com/matrix-org/matrix-doc/issues/2523>`_)
- Add User-Interactive Authentication for SSO-backed homeserver per `MSC2454 <https://github.com/matrix-org/matrix-doc/pull/2454>`_. (`#2532 <https://github.com/matrix-org/matrix-doc/issues/2532>`_)
- Add soft-logout support per `MSC1466 <https://github.com/matrix-org/matrix-doc/issues/1466>`_. (`#2546 <https://github.com/matrix-org/matrix-doc/issues/2546>`_)
- Replaced legacy room alias handling with a more sustainable solution per `MSC2432 <https://github.com/matrix-org/matrix-doc/pull/2432>`_. (`#2562 <https://github.com/matrix-org/matrix-doc/issues/2562>`_)


Spec Clarifications
-------------------

- List available enum values for the room versions capability. (`#2245 <https://github.com/matrix-org/matrix-doc/issues/2245>`_)
- Fix various spelling errors throughout the specification. (`#2351 <https://github.com/matrix-org/matrix-doc/issues/2351>`_, `#2415 <https://github.com/matrix-org/matrix-doc/issues/2415>`_, `#2453 <https://github.com/matrix-org/matrix-doc/issues/2453>`_, `#2524 <https://github.com/matrix-org/matrix-doc/issues/2524>`_, `#2553 <https://github.com/matrix-org/matrix-doc/issues/2553>`_, `#2569 <https://github.com/matrix-org/matrix-doc/issues/2569>`_)
- Minor clarifications to token-based User-Interactive Authentication. (`#2369 <https://github.com/matrix-org/matrix-doc/issues/2369>`_)
- Minor clarification for what the user directory searches. (`#2381 <https://github.com/matrix-org/matrix-doc/issues/2381>`_)
- Fix key export format example to match the specification. (`#2430 <https://github.com/matrix-org/matrix-doc/issues/2430>`_)
- Clarify the IV data type for encrypted files. (`#2492 <https://github.com/matrix-org/matrix-doc/issues/2492>`_)
- Fix the ``.m.rule.contains_user_name`` default push rule to set the highlight tweak. (`#2519 <https://github.com/matrix-org/matrix-doc/issues/2519>`_)
- Clarify that an ``event_id`` is returned when sending events. (`#2525 <https://github.com/matrix-org/matrix-doc/issues/2525>`_)
- Fix some numbers in the specification to match their explanation text. (`#2554 <https://github.com/matrix-org/matrix-doc/issues/2554>`_)
- Move redaction algorithm into the room version specifications. (`#2563 <https://github.com/matrix-org/matrix-doc/issues/2563>`_)
- Clarify signature object structures for encryption. (`#2566 <https://github.com/matrix-org/matrix-doc/issues/2566>`_)
- Clarify which events are created as part of ``/createRoom``. (`#2571 <https://github.com/matrix-org/matrix-doc/issues/2571>`_)
- Remove claims that the homeserver is exclusively responsible for profile information in membership events. (`#2574 <https://github.com/matrix-org/matrix-doc/issues/2574>`_)


r0.6.0
======

Breaking Changes
----------------

- Add ``id_access_token`` as a required request parameter to a few endpoints which require an ``id_server`` parameter as part of `MSC2140 <https://github.com/matrix-org/matrix-doc/pull/2140>`_. (`#2255 <https://github.com/matrix-org/matrix-doc/issues/2255>`_)


New Endpoints
-------------

- Add ``POST /account/3pid/unbind`` for removing a 3PID from an identity server. (`#2282 <https://github.com/matrix-org/matrix-doc/issues/2282>`_)


Backwards Compatible Changes
----------------------------

- Add ``M_USER_DEACTIVATED`` error code. (`#2234 <https://github.com/matrix-org/matrix-doc/issues/2234>`_)
- Remove ``bind_msisdn`` and ``bind_email`` from ``/register`` now that the identity server's bind endpoint requires authentication. (`#2279 <https://github.com/matrix-org/matrix-doc/issues/2279>`_)
- Add ``m.identity_server`` account data for tracking the user's preferred identity server. (`#2281 <https://github.com/matrix-org/matrix-doc/issues/2281>`_)
- Deprecate ``id_server`` and make it optional in several places. (`#2310 <https://github.com/matrix-org/matrix-doc/issues/2310>`_)


Spec Clarifications
-------------------

- Add missing format fields to ``m.room.message$m.notice`` schema. (`#2125 <https://github.com/matrix-org/matrix-doc/issues/2125>`_)
- Remove "required" designation from the ``url`` field of certain ``m.room.message`` msgtypes. (`#2129 <https://github.com/matrix-org/matrix-doc/issues/2129>`_)
- Fix various typos throughout the specification. (`#2131 <https://github.com/matrix-org/matrix-doc/issues/2131>`_, `#2136 <https://github.com/matrix-org/matrix-doc/issues/2136>`_, `#2148 <https://github.com/matrix-org/matrix-doc/issues/2148>`_, `#2215 <https://github.com/matrix-org/matrix-doc/issues/2215>`_)
- Clarify the distinction between ``m.key.verification.start`` and its ``m.sas.v1`` variant. (`#2132 <https://github.com/matrix-org/matrix-doc/issues/2132>`_)
- Fix link to Olm signing specification. (`#2133 <https://github.com/matrix-org/matrix-doc/issues/2133>`_)
- Clarify the conditions for the ``.m.rule.room_one_to_one`` push rule. (`#2152 <https://github.com/matrix-org/matrix-doc/issues/2152>`_)
- Clarify the encryption algorithms supported by the device of the device keys example. (`#2157 <https://github.com/matrix-org/matrix-doc/issues/2157>`_)
- Clarify that ``/rooms/:roomId/event/:eventId`` returns a Matrix error. (`#2204 <https://github.com/matrix-org/matrix-doc/issues/2204>`_)
- Add a missing ``state_key`` check on ``.m.rule.tombstone``. (`#2223 <https://github.com/matrix-org/matrix-doc/issues/2223>`_)
- Fix the ``m.room_key_request`` ``action`` value, setting it from ``cancel_request`` to ``request_cancellation``. (`#2247 <https://github.com/matrix-org/matrix-doc/issues/2247>`_)
- Clarify that the ``submit_url`` field is without authentication. (`#2341 <https://github.com/matrix-org/matrix-doc/issues/2341>`_)
- Clarify the expected phone number format. (`#2342 <https://github.com/matrix-org/matrix-doc/issues/2342>`_)
- Clarify that clients should consider not requesting URL previews in encrypted rooms. (`#2343 <https://github.com/matrix-org/matrix-doc/issues/2343>`_)
- Add missing information on how filters are meant to work with ``/context``. (`#2344 <https://github.com/matrix-org/matrix-doc/issues/2344>`_)
- Clarify what the keys are for rooms in ``/sync``. (`#2345 <https://github.com/matrix-org/matrix-doc/issues/2345>`_)


r0.5.0
======

Breaking Changes
----------------

- Add a new ``submit_url`` field to the responses of ``/requestToken`` which older clients will not be able to handle correctly. (`#2101 <https://github.com/matrix-org/matrix-doc/issues/2101>`_)


Deprecations
------------

- Remove references to presence lists. (`#1817 <https://github.com/matrix-org/matrix-doc/issues/1817>`_)


New Endpoints
-------------

- ``GET /account_data`` routes. (`#1873 <https://github.com/matrix-org/matrix-doc/issues/1873>`_)


Backwards Compatible Changes
----------------------------

- Add megolm session export format. (`#1701 <https://github.com/matrix-org/matrix-doc/issues/1701>`_)
- Add support for advertising experimental features to clients. (`#1786 <https://github.com/matrix-org/matrix-doc/issues/1786>`_)
- Add a generic SSO login API. (`#1789 <https://github.com/matrix-org/matrix-doc/issues/1789>`_)
- Add a mechanism for servers to redirect clients to an alternative homeserver after logging in. (`#1790 <https://github.com/matrix-org/matrix-doc/issues/1790>`_)
- Add room version upgrades. (`#1791 <https://github.com/matrix-org/matrix-doc/issues/1791>`_, `#1875 <https://github.com/matrix-org/matrix-doc/issues/1875>`_)
- Support optional features by having clients query for capabilities. (`#1829 <https://github.com/matrix-org/matrix-doc/issues/1829>`_, `#1879 <https://github.com/matrix-org/matrix-doc/issues/1879>`_)
- Add ``M_RESOURCE_LIMIT_EXCEEDED`` as an error code for when homeservers exceed limits imposed on them. (`#1874 <https://github.com/matrix-org/matrix-doc/issues/1874>`_)
- Emit ``M_UNSUPPORTED_ROOM_VERSION`` error codes where applicable on ``/createRoom`` and ``/invite`` APIs. (`#1908 <https://github.com/matrix-org/matrix-doc/issues/1908>`_)
- Add a ``.m.rule.tombstone`` default push rule for room upgrade notifications. (`#2020 <https://github.com/matrix-org/matrix-doc/issues/2020>`_)
- Add support for sending server notices to clients. (`#2026 <https://github.com/matrix-org/matrix-doc/issues/2026>`_)
- Add MSISDN (phone number) support to User-Interactive Authentication. (`#2030 <https://github.com/matrix-org/matrix-doc/issues/2030>`_)
- Add the option to lazy-load room members for increased client performance. (`#2035 <https://github.com/matrix-org/matrix-doc/issues/2035>`_)
- Add ``id_server`` to ``/deactivate`` and ``/3pid/delete`` endpoints to unbind from a specific identity server. (`#2046 <https://github.com/matrix-org/matrix-doc/issues/2046>`_)
- Add support for Olm sessions becoming un-stuck. (`#2059 <https://github.com/matrix-org/matrix-doc/issues/2059>`_)
- Add interactive device verification, including a common framework for device verification. (`#2072 <https://github.com/matrix-org/matrix-doc/issues/2072>`_)


Spec Clarifications
-------------------

- Change examples to use example.org instead of a real domain. (`#1650 <https://github.com/matrix-org/matrix-doc/issues/1650>`_)
- Clarify that ``state_default`` in ``m.room.power_levels`` always defaults to 50. (`#1656 <https://github.com/matrix-org/matrix-doc/issues/1656>`_)
- Add missing ``status_msg`` to ``m.presence`` schema. (`#1744 <https://github.com/matrix-org/matrix-doc/issues/1744>`_)
- Fix various spelling mistakes throughout the specification. (`#1838 <https://github.com/matrix-org/matrix-doc/issues/1838>`_, `#1853 <https://github.com/matrix-org/matrix-doc/issues/1853>`_, `#1860 <https://github.com/matrix-org/matrix-doc/issues/1860>`_, `#1933 <https://github.com/matrix-org/matrix-doc/issues/1933>`_, `#1969 <https://github.com/matrix-org/matrix-doc/issues/1969>`_, `#1988 <https://github.com/matrix-org/matrix-doc/issues/1988>`_, `#1989 <https://github.com/matrix-org/matrix-doc/issues/1989>`_, `#1991 <https://github.com/matrix-org/matrix-doc/issues/1991>`_, `#1992 <https://github.com/matrix-org/matrix-doc/issues/1992>`_)
- Add the missing ``m.push_rules`` event schema. (`#1889 <https://github.com/matrix-org/matrix-doc/issues/1889>`_)
- Clarify how modern day local echo is meant to be solved by clients. (`#1891 <https://github.com/matrix-org/matrix-doc/issues/1891>`_)
- Clarify that ``width`` and ``height`` are required parameters on ``/_matrix/media/r0/thumbnail/{serverName}/{mediaId}``. (`#1975 <https://github.com/matrix-org/matrix-doc/issues/1975>`_)
- Clarify how ``m.login.dummy`` can be used to disambiguate login flows. (`#1999 <https://github.com/matrix-org/matrix-doc/issues/1999>`_)
- Remove ``prev_content`` from the redaction algorithm's essential keys list. (`#2016 <https://github.com/matrix-org/matrix-doc/issues/2016>`_)
- Fix the ``third_party_signed`` definitions for the join APIs. (`#2025 <https://github.com/matrix-org/matrix-doc/issues/2025>`_)
- Clarify why User Interactive Auth is used on password changes and how access tokens are handled. (`#2027 <https://github.com/matrix-org/matrix-doc/issues/2027>`_)
- Clarify that devices are deleted upon logout. (`#2028 <https://github.com/matrix-org/matrix-doc/issues/2028>`_)
- Add ``M_NOT_FOUND`` error definition for deleting room aliases. (`#2029 <https://github.com/matrix-org/matrix-doc/issues/2029>`_)
- Add missing ``reason`` to ``m.call.hangup``. (`#2031 <https://github.com/matrix-org/matrix-doc/issues/2031>`_)
- Clarify how redactions affect room state. (`#2032 <https://github.com/matrix-org/matrix-doc/issues/2032>`_)
- Clarify that ``FAIL_ERROR`` in autodiscovery is not limited to just homeservers. (`#2036 <https://github.com/matrix-org/matrix-doc/issues/2036>`_)
- Fix example ``Content-Type`` for ``/media/upload`` request. (`#2041 <https://github.com/matrix-org/matrix-doc/issues/2041>`_)
- Clarify that login flows are meant to be completed in order. (`#2042 <https://github.com/matrix-org/matrix-doc/issues/2042>`_)
- Clarify that clients should not send read receipts for their own messages. (`#2043 <https://github.com/matrix-org/matrix-doc/issues/2043>`_)
- Use consistent examples of events throughout the specification. (`#2051 <https://github.com/matrix-org/matrix-doc/issues/2051>`_)
- Clarify which push rule condition kinds exist. (`#2052 <https://github.com/matrix-org/matrix-doc/issues/2052>`_)
- Clarify the required fields on ``m.file`` (and similar) messages. (`#2053 <https://github.com/matrix-org/matrix-doc/issues/2053>`_)
- Clarify that User-Interactive Authentication stages cannot be attempted more than once. (`#2054 <https://github.com/matrix-org/matrix-doc/issues/2054>`_)
- Clarify which parameters apply in what scenarios on ``/register``. (`#2055 <https://github.com/matrix-org/matrix-doc/issues/2055>`_)
- Clarify how to interpret changes of ``membership`` over time. (`#2056 <https://github.com/matrix-org/matrix-doc/issues/2056>`_)
- Clarify exactly what invite_room_state consists of. (`#2067 <https://github.com/matrix-org/matrix-doc/issues/2067>`_)
- Clarify how the content repository works, and what it is used for. (`#2068 <https://github.com/matrix-org/matrix-doc/issues/2068>`_)
- Clarify the order events in chunk are returned in for ``/messages``. (`#2069 <https://github.com/matrix-org/matrix-doc/issues/2069>`_)
- Clarify the key object definition for the key management API. (`#2083 <https://github.com/matrix-org/matrix-doc/issues/2083>`_)
- Reorganize information about events into a common section. (`#2087 <https://github.com/matrix-org/matrix-doc/issues/2087>`_)
- De-duplicate ``/state/<event_type>`` endpoints, clarifying that the ``<state_key>`` is optional. (`#2088 <https://github.com/matrix-org/matrix-doc/issues/2088>`_)
- Clarify when and where CORS headers should be returned. (`#2089 <https://github.com/matrix-org/matrix-doc/issues/2089>`_)
- Clarify when authorization and rate-limiting are not applicable. (`#2090 <https://github.com/matrix-org/matrix-doc/issues/2090>`_)
- Clarify that ``/register`` must produce valid Matrix User IDs. (`#2091 <https://github.com/matrix-org/matrix-doc/issues/2091>`_)
- Clarify how ``unread_notifications`` is calculated. (`#2097 <https://github.com/matrix-org/matrix-doc/issues/2097>`_)
- Clarify what a "module" is and update feature profiles for clients. (`#2098 <https://github.com/matrix-org/matrix-doc/issues/2098>`_)


r0.4.0
======

New Endpoints
-------------

- ``POST /user_directory/search`` (`#1096 <https://github.com/matrix-org/matrix-doc/issues/1096>`_)
- ``GET /rooms/{roomId}/event/{eventId}`` (`#1110 <https://github.com/matrix-org/matrix-doc/issues/1110>`_)
- ``POST /delete_devices`` (`#1239 <https://github.com/matrix-org/matrix-doc/issues/1239>`_)
- ``GET /thirdparty/*`` Endpoints (`#1353 <https://github.com/matrix-org/matrix-doc/issues/1353>`_)
- ``POST /account/3pid/msisdn/requestToken``, ``POST /register/msisdn/requestToken``, and ``POST /account/password/msisdn/requestToken`` (`#1507 <https://github.com/matrix-org/matrix-doc/issues/1507>`_)
- ``POST /account/3pid/delete`` (`#1567 <https://github.com/matrix-org/matrix-doc/issues/1567>`_)
- ``POST /rooms/{roomId}/read_markers`` (`#1635 <https://github.com/matrix-org/matrix-doc/issues/1635>`_)


Backwards Compatible Changes
----------------------------

- Add more presence options to the ``set_presence`` parameter of ``/sync``. (Thanks @mujx!) (`#780 <https://github.com/matrix-org/matrix-doc/issues/780>`_)
- Add ``token`` parameter to the ``/keys/query`` endpoint (`#1104 <https://github.com/matrix-org/matrix-doc/issues/1104>`_)
- Add the room visibility options for the room directory (`#1141 <https://github.com/matrix-org/matrix-doc/issues/1141>`_)
- Add spec for ignoring users (`#1142 <https://github.com/matrix-org/matrix-doc/issues/1142>`_)
- Add the ``/register/available`` endpoint for username availability (`#1151 <https://github.com/matrix-org/matrix-doc/issues/1151>`_)
- Add sticker messages (`#1158 <https://github.com/matrix-org/matrix-doc/issues/1158>`_)
- Specify how to control the power level required for ``@room`` (`#1176 <https://github.com/matrix-org/matrix-doc/issues/1176>`_)
- Document ``/logout/all`` endpoint (`#1263 <https://github.com/matrix-org/matrix-doc/issues/1263>`_)
- Add report content API (`#1264 <https://github.com/matrix-org/matrix-doc/issues/1264>`_)
- Add ``allow_remote`` to the content repo to avoid routing loops (`#1265 <https://github.com/matrix-org/matrix-doc/issues/1265>`_)
- Document `highlights` field in /search response (`#1274 <https://github.com/matrix-org/matrix-doc/issues/1274>`_)
- End-to-end encryption for group chats:

  * Olm and Megolm messaging algorithms.
  * ``m.room.encrypted``, ``m.room.encryption``, ``m.room_key`` events.
  * Device verification process.
  * ``device_one_time_keys_count`` sync parameter.
  * ``device_lists:left`` sync parameter. (`#1284 <https://github.com/matrix-org/matrix-doc/issues/1284>`_)
- Add ``.well-known`` server discovery method (`#1359 <https://github.com/matrix-org/matrix-doc/issues/1359>`_)
- Document the GET version of ``/login`` (`#1361 <https://github.com/matrix-org/matrix-doc/issues/1361>`_)
- Document the ``server_name`` parameter on ``/join/{roomIdOrAlias}`` (`#1364 <https://github.com/matrix-org/matrix-doc/issues/1364>`_)
- Document the CORS/preflight headers (`#1365 <https://github.com/matrix-org/matrix-doc/issues/1365>`_)
- Add new user identifier object for logging in (`#1390 <https://github.com/matrix-org/matrix-doc/issues/1390>`_)
- Document message formats on ``m.text`` and ``m.emote`` messages (`#1397 <https://github.com/matrix-org/matrix-doc/issues/1397>`_)
- Encrypt file attachments (`#1420 <https://github.com/matrix-org/matrix-doc/issues/1420>`_)
- Share room decryption keys between devices (`#1465 <https://github.com/matrix-org/matrix-doc/issues/1465>`_)
- Document and improve client interaction with pushers. (`#1506 <https://github.com/matrix-org/matrix-doc/issues/1506>`_)
- Add support for Room Versions. (`#1516 <https://github.com/matrix-org/matrix-doc/issues/1516>`_)
- Guests can now call /context and /event to fetch events (`#1542 <https://github.com/matrix-org/matrix-doc/issues/1542>`_)
- Add a common standard for user, room, and group mentions in messages. (`#1547 <https://github.com/matrix-org/matrix-doc/issues/1547>`_)
- Add server ACLs as an option for controlling federation in a room. (`#1550 <https://github.com/matrix-org/matrix-doc/issues/1550>`_)
- Add new push rules for encrypted events and ``@room`` notifications. (`#1551 <https://github.com/matrix-org/matrix-doc/issues/1551>`_)
- Add third party network room directories, as provided by application services. (`#1554 <https://github.com/matrix-org/matrix-doc/issues/1554>`_)
- Document the ``validated_at`` and ``added_at`` fields on ``GET /acount/3pid``. (`#1567 <https://github.com/matrix-org/matrix-doc/issues/1567>`_)
- Add an ``inhibit_login`` registration option. (`#1589 <https://github.com/matrix-org/matrix-doc/issues/1589>`_)
- Recommend that servers set a Content Security Policy for the content repository. (`#1600 <https://github.com/matrix-org/matrix-doc/issues/1600>`_)
- Add "rich replies" - a way for users to better represent the conversation thread they are referencing in their messages. (`#1617 <https://github.com/matrix-org/matrix-doc/issues/1617>`_)
- Add support for read markers. (`#1635 <https://github.com/matrix-org/matrix-doc/issues/1635>`_)


Spec Clarifications
-------------------

- Mark ``home_server`` return field for ``/login`` and ``/register`` endpoints as deprecated (`#1097 <https://github.com/matrix-org/matrix-doc/issues/1097>`_)
- Fix response format of ``/keys/changes`` endpoint (`#1106 <https://github.com/matrix-org/matrix-doc/issues/1106>`_)
- Clarify default values for some fields on the ``/search`` API (`#1109 <https://github.com/matrix-org/matrix-doc/issues/1109>`_)
- Fix the representation of ``m.presence`` events (`#1137 <https://github.com/matrix-org/matrix-doc/issues/1137>`_)
- Clarify that ``m.tag`` ordering is done with numbers, not strings (`#1139 <https://github.com/matrix-org/matrix-doc/issues/1139>`_)
- Clarify that ``/account/whoami`` should consider application services (`#1152 <https://github.com/matrix-org/matrix-doc/issues/1152>`_)
- Update ``ImageInfo`` and ``ThumbnailInfo`` dimension schema descriptions to clarify that they relate to intended display size, as opposed to the intrinsic size of the image file. (`#1158 <https://github.com/matrix-org/matrix-doc/issues/1158>`_)
- Mark ``GET /rooms/{roomId}/members`` as requiring authentication (`#1245 <https://github.com/matrix-org/matrix-doc/issues/1245>`_)
- Clarify ``changed`` field behaviour in device tracking process (`#1284 <https://github.com/matrix-org/matrix-doc/issues/1284>`_)
- Describe ``StateEvent`` for ``/createRoom`` (`#1329 <https://github.com/matrix-org/matrix-doc/issues/1329>`_)
- Describe how the ``reason`` is handled for kicks/bans (`#1362 <https://github.com/matrix-org/matrix-doc/issues/1362>`_)
- Mark ``GET /presence/{userId}/status`` as requiring authentication (`#1371 <https://github.com/matrix-org/matrix-doc/issues/1371>`_)
- Describe the rate limit error response schema (`#1373 <https://github.com/matrix-org/matrix-doc/issues/1373>`_)
- Clarify that clients must leave rooms before forgetting them (`#1378 <https://github.com/matrix-org/matrix-doc/issues/1378>`_)
- Document guest access in ``/createRoom`` presets (`#1379 <https://github.com/matrix-org/matrix-doc/issues/1379>`_)
- Define what a ``RoomEvent`` is on ``/rooms/{roomId}/messages`` (`#1380 <https://github.com/matrix-org/matrix-doc/issues/1380>`_)
- Clarify the request and result types on ``/search`` (`#1381 <https://github.com/matrix-org/matrix-doc/issues/1381>`_)
- Clarify some of the properties on the search result (`#1400 <https://github.com/matrix-org/matrix-doc/issues/1400>`_)
- Clarify how access tokens are meant to be supplied to the homeserver. (`#1517 <https://github.com/matrix-org/matrix-doc/issues/1517>`_)
- Document additional parameters on the ``/createRoom`` API. (`#1518 <https://github.com/matrix-org/matrix-doc/issues/1518>`_)
- Clarify that new push rules should be enabled by default, and that unrecognised conditions should not match. (`#1551 <https://github.com/matrix-org/matrix-doc/issues/1551>`_)
- Update all event examples to be accurate representations of their associated events. (`#1558 <https://github.com/matrix-org/matrix-doc/issues/1558>`_)
- Clarify the supported HTML features for room messages. (`#1562 <https://github.com/matrix-org/matrix-doc/issues/1562>`_)
- Move the ``invite_room_state`` definition under ``unsigned`` where it actually resides. (`#1568 <https://github.com/matrix-org/matrix-doc/issues/1568>`_)
- Clarify the homeserver's behaviour for searching users. (`#1569 <https://github.com/matrix-org/matrix-doc/issues/1569>`_)
- Clarify the object structures and defaults for Filters. (`#1570 <https://github.com/matrix-org/matrix-doc/issues/1570>`_)
- Clarify instances of ``type: number`` in the swagger/OpenAPI schema definitions. (`#1571 <https://github.com/matrix-org/matrix-doc/issues/1571>`_)
- Clarify that left rooms also have account data in ``/sync``. (`#1572 <https://github.com/matrix-org/matrix-doc/issues/1572>`_)
- Clarify the event fields used in the ``/sync`` response. (`#1573 <https://github.com/matrix-org/matrix-doc/issues/1573>`_)
- Fix naming of the body field in ``PUT /directory/room``. (`#1574 <https://github.com/matrix-org/matrix-doc/issues/1574>`_)
- Clarify the filter object schema used in room searching. (`#1577 <https://github.com/matrix-org/matrix-doc/issues/1577>`_)
- Document the 403 error for sending state events. (`#1590 <https://github.com/matrix-org/matrix-doc/issues/1590>`_)
- specify how to handle multiple olm sessions with the same device (`#1596 <https://github.com/matrix-org/matrix-doc/issues/1596>`_)
- Add the other keys that redactions are expected to preserve. (`#1602 <https://github.com/matrix-org/matrix-doc/issues/1602>`_)
- Clarify that clients should not be generating invalid HTML for formatted events. (`#1605 <https://github.com/matrix-org/matrix-doc/issues/1605>`_)
- Clarify the room tag structure (thanks @KitsuneRal!) (`#1606 <https://github.com/matrix-org/matrix-doc/issues/1606>`_)
- Add a note that clients may use the transaction ID to avoid flickering when doing local echo. (`#1619 <https://github.com/matrix-org/matrix-doc/issues/1619>`_)
- Include the request and response structures for the various ``/requestToken`` endpoints. (`#1636 <https://github.com/matrix-org/matrix-doc/issues/1636>`_)
- Clarify the available error codes, and when to prefer the HTTP status code over the ``errcode``. (`#1637 <https://github.com/matrix-org/matrix-doc/issues/1637>`_)
- Clarify and generalise the language used for describing pagination. (`#1642 <https://github.com/matrix-org/matrix-doc/issues/1642>`_)


r0.3.0
======

- Breaking changes:

  - Change the rule kind of ``.m.rule.contains_display_name`` from
    ``underride`` to ``override``. This works with all known clients
    which support push rules, but any other clients implementing
    the push rules API should be aware of this change. This
    makes it simple to mute rooms correctly in the API
    (`#373 <https://github.com/matrix-org/matrix-doc/pull/373>`_).
  - Remove ``/tokenrefresh`` from the API
    (`#395 <https://github.com/matrix-org/matrix-doc/pull/395>`_).
  - Remove requirement that tokens used in token-based login be macaroons
    (`#395 <https://github.com/matrix-org/matrix-doc/pull/395>`_).
  - Move ``thumbnail_url`` and ``thumbnail_info`` members of json objects
    for ``m.room.message`` events with msgtypes ``m.image``, ``m.file``
    and ``m.location``, inside the ``info`` member, to match ``m.video``
    events
    (`#723 <https://github.com/matrix-org/matrix-doc/pull/723>`_).

- Changes to the API which will be backwards-compatible for clients:

  - Add ``filename`` parameter to ``POST /_matrix/media/r0/upload``
    (`#364 <https://github.com/matrix-org/matrix-doc/pull/364>`_).
  - Document CAS-based client login and the use of ``m.login.token`` in
    ``/login`` (`#367 <https://github.com/matrix-org/matrix-doc/pull/367>`_).
  - Make ``origin_server_ts`` a mandatory field of room events
    (`#379 <https://github.com/matrix-org/matrix-doc/pull/370>`_).
  - Add top-level ``account_data`` key to the responses to ``GET /sync`` and
    ``GET /initialSync``
    (`#380 <https://github.com/matrix-org/matrix-doc/pull/380>`_).
  - Add ``is_direct`` flag to ``POST /createRoom`` and invite member event.
    Add 'Direct Messaging' module
    (`#389 <https://github.com/matrix-org/matrix-doc/pull/389>`_).
  - Add ``contains_url`` option to ``RoomEventFilter``
    (`#390 <https://github.com/matrix-org/matrix-doc/pull/390>`_).
  - Add ``filter`` optional query param to ``/messages``
    (`#390 <https://github.com/matrix-org/matrix-doc/pull/390>`_).
  - Add 'Send-to-Device messaging' module
    (`#386 <https://github.com/matrix-org/matrix-doc/pull/386>`_).
  - Add 'Device management' module
    (`#402 <https://github.com/matrix-org/matrix-doc/pull/402>`_).
  - Require that User-Interactive auth fallback pages call
    ``window.postMessage`` to notify apps of completion
    (`#398 <https://github.com/matrix-org/matrix-doc/pull/398>`_).
  - Add pagination and filter support to ``/publicRooms``. Change response to
    omit fields rather than return ``null``. Add estimate of total number of
    rooms in list.
    (`#388 <https://github.com/matrix-org/matrix-doc/pull/388>`_).
  - Allow guest accounts to use a number of endpoints which are required for
    end-to-end encryption.
    (`#751 <https://github.com/matrix-org/matrix-doc/pull/751>`_).
  - Add key distribution APIs, for use with end-to-end encryption.
    (`#894 <https://github.com/matrix-org/matrix-doc/pull/894>`_).
  - Add ``m.room.pinned_events`` state event for rooms.
    (`#1007 <https://github.com/matrix-org/matrix-doc/pull/1007>`_).
  - Add mention of ability to send Access Token via an Authorization Header.
  - Add ``guest_can_join`` parameter to ``POST /createRoom``
    (`#1093 <https://github.com/matrix-org/matrix-doc/pull/1093>`_).

  - New endpoints:

    - ``GET /joined_rooms``
      (`#999 <https://github.com/matrix-org/matrix-doc/pull/999>`_).

    - ``GET /rooms/{roomId}/joined_members``
      (`#999 <https://github.com/matrix-org/matrix-doc/pull/999>`_).

    - ``GET /account/whoami``
      (`#1063 <https://github.com/matrix-org/matrix-doc/pull/1063>`_).

    - ``GET /media/{version}/preview_url``
      (`#1064 <https://github.com/matrix-org/matrix-doc/pull/1064>`_).

- Spec clarifications:

  - Add endpoints and logic for invites and third-party invites to the federation
    spec and update the JSON of the request sent by the identity server upon 3PID
    binding
    (`#997 <https://github.com/matrix-org/matrix-doc/pull/997>`_)
  - Fix "membership" property on third-party invite upgrade example
    (`#995 <https://github.com/matrix-org/matrix-doc/pull/995>`_)
  - Fix response format and 404 example for room alias lookup
    (`#960 <https://github.com/matrix-org/matrix-doc/pull/960>`_)
  - Fix examples of ``m.room.member`` event and room state change,
    and added a clarification on the membership event sent upon profile update
    (`#950 <https://github.com/matrix-org/matrix-doc/pull/950>`_).
  - Spell out the way that state is handled by ``POST /createRoom``
    (`#362 <https://github.com/matrix-org/matrix-doc/pull/362>`_).
  - Clarify the fields which are applicable to different types of push rule
    (`#365 <https://github.com/matrix-org/matrix-doc/pull/365>`_).
  - A number of clarifications to authentication
    (`#371 <https://github.com/matrix-org/matrix-doc/pull/371>`_).
  - Correct references to ``user_id`` which should have been ``sender``
    (`#376 <https://github.com/matrix-org/matrix-doc/pull/376>`_).
  - Correct inconsistent specification of ``redacted_because`` fields and their
    values (`#378 <https://github.com/matrix-org/matrix-doc/pull/378>`_).
  - Mark required fields in response objects as such
    (`#394 <https://github.com/matrix-org/matrix-doc/pull/394>`_).
  - Make ``m.notice`` description a bit harder in its phrasing to try to
    dissuade the same issues that occurred with IRC
    (`#750 <https://github.com/matrix-org/matrix-doc/pull/750>`_).
  - ``GET /user/{userId}/filter/{filterId}`` requires authentication
    (`#1003 <https://github.com/matrix-org/matrix-doc/pull/1003>`_).
  - Add some clarifying notes on the behaviour of rooms with no
    ``m.room.power_levels`` event
    (`#1026 <https://github.com/matrix-org/matrix-doc/pull/1026>`_).
  - Clarify the relationship between ``username`` and ``user_id`` in the
    ``/register`` API
    (`#1032 <https://github.com/matrix-org/matrix-doc/pull/1032>`_).
  - Clarify rate limiting and security for content repository.
    (`#1064 <https://github.com/matrix-org/matrix-doc/pull/1064>`_).

r0.2.0
======

- Spec clarifications:

  - Room aliases (`#337 <https://github.com/matrix-org/matrix-doc/pull/337>`_):

    - Make it clear that ``GET /directory/room/{roomAlias}`` must work for
      federated aliases.

    - ``GET /directory/room/{roomAlias}`` cannot return a 409; the ``PUT``
      endpoint can, however.

  - Power levels:

    - Clarify the defaults to be used for various fields of the
      ``m.room.power_levels`` event
      (`#286 <https://github.com/matrix-org/matrix-doc/pull/286>`_,
      `#341 <https://github.com/matrix-org/matrix-doc/pull/341>`_).

    - Add suggestions for mapping of names to power levels
      (`#336 <https://github.com/matrix-org/matrix-doc/pull/336>`_).

  - Clarify the room naming algorithm in certain edge cases
    (`#351 <https://github.com/matrix-org/matrix-doc/pull/351>`_).

  - Remove outdated references to the pre-r0 ``/events`` API, and clarify the
    section on syncing
    (`#352 <https://github.com/matrix-org/matrix-doc/pull/352>`_).


- Changes to the API which will be backwards-compatible for clients:

  - New endpoints:

    - ``POST /register/email/requestToken``
      (`#343 <https://github.com/matrix-org/matrix-doc/pull/343>`_).

    - ``POST /account/3pid/email/requestToken``
      (`#346 <https://github.com/matrix-org/matrix-doc/pull/346>`_).

    - ``POST /account/password/email/requestToken``
      (`#346 <https://github.com/matrix-org/matrix-doc/pull/346>`_).

    - ``POST /account/deactivate``
      (`#361 <https://github.com/matrix-org/matrix-doc/pull/361>`_).

  - Updates to the Presence module
    (`#278 <https://github.com/matrix-org/matrix-doc/pull/278>`_,
    `#342 <https://github.com/matrix-org/matrix-doc/pull/342>`_):

    - Remove unused ``free_for_chat`` presence state
    - Add ``currently_active`` flag to the ``m.presence`` event and the ``GET
      /presence/{userId}/status`` response.
    - Make idle timeout the responsibility of the server
    - Remove requirements on servers to propagate profile information via
      ``m.presence`` events.

  - Add new predefined push rules
    (`#274 <https://github.com/matrix-org/matrix-doc/pull/274>`_,
    `#340 <https://github.com/matrix-org/matrix-doc/pull/340/files>`_).

  - ``/sync`` should always return a ``prev_batch`` token
    (`#345 <https://github.com/matrix-org/matrix-doc/pull/345>`_).

  - add ``to`` parameter to ``GET /rooms/{roomId}/messages`` API
    (`#348 <https://github.com/matrix-org/matrix-doc/pull/348>`_).

r0.1.0
======

This release includes the following changes since r0.0.1:

- Breaking changes to the API [#]_:

  - ``POST /rooms/{roomId}/join`` no longer permits use of a room alias instead
    of a room id. (``POST /join/{roomIdOrAlias}`` continues to allow either.)
  - ``POST /account/3pid``: correct the name of the ``three_pid_creds``
    parameter
  - The "Push Rules" module no longer supports device-specific rules:

    - ``GET /pushrules`` no longer returns a ``device`` property
    - ``device/{profile_tag}`` is no longer a valid ``scope`` for push rules
    - ``profile_tag`` is no longer a valid kind of condition on push rules.

    (Device-specific push rules will be reintroduced in the future; in the
    meantime, their specification has been moved to a `draft branch`__.)

    __ https://matrix.org/speculator/spec/drafts%2Freinstate_device_push_rules/

- Changes to the API which will be backwards-compatible for clients:

  - New endpoints:

    - ``POST /logout``
    - ``POST /rooms/{roomId}/unban``
    - ``POST /rooms/{roomId}/kick``
    - ``GET /pushers``
    - ``GET /pushrules/{scope}/{kind}/{ruleId}/enabled``
      (previously ``PUT``-only)
    - ``GET`` and ``PUT /pushrules/{scope}/{kind}/{ruleId}/actions``

  - Add ``third_party_signed`` parameter to ``POST /rooms/{roomId}/join``
  - Add ``M_INVALID_USERNAME`` as valid response to ``POST /register``
  - Add ``unread_notifications`` field to ``GET /sync`` response
  - Add optional ``invite`` property to ``m.room.power_levels`` state event
  - Add optional ``public_key`` and ``public_keys`` to
    ``m.room.third_party_invite`` state event
  - Password-based ``/login`` may now use a third-party identifier instead of
    a matrix user id.

- Spec clarifications

  - Make the state diagram for room membership explicit
  - Note that a user may not be invited to a room while banned
  - Clarify the expected order of events in the response to
    ``GET /rooms/{roomId}/context/{eventId}``, as well as correcting the
    example for that API
  - Clarify the behaviour of the "Room History Visibility" module; in
    particular, the behaviour of the ``shared`` history visibility, and how
    events at visibility boundaries should be handled
  - Separate the "Room Previews" module from "Guest access"
  - Reword the description of the ``profile_tag`` property in
    ``PUT /pushers/set``, and note that it is not mandatory.


.. [#] Our `versioning policy <../index.html#specification-versions>`_ would
   strictly require that a breaking change be denoted by a new major
   specification version. However we are not aware of any clients which
   rely on the old behaviour here, nor server implementations which offer
   it, so we have chosen to retain the r0 designation on this occasion.

r0.0.1
======

This release includes the following changes since r0.0.0:

- API changes:
  - Added new ``/versions`` API
  - ``/createRoom`` takes an optional ``invite_3pid`` parameter
  - ``/publicRooms`` returns an ``avatar_url`` result
- The following APIs are now deprecated:
  - ``/initialSync``
  - ``/events``
  - ``/events/:eventId``
  - ``/rooms/:roomId/initialSync``
- Spec clarifications
  - Document inter-version compatibility
  - Document the parameters to the ``/user/:userId/filter`` API
  - Document the ``next_batch`` parameter on ``/search``
  - Document the membership states on ``m.room.member`` events
  - Minor clarifications/corrections to:
    - Guest access module
    - Search module
    - ``/login`` API
    - ``/rooms/:roomId/send/:eventType/:txnId`` API
    - ``/rooms/:roomId/context/:eventId`` API

r0.0.0
======

This is the first release of the client-server specification. It is largely a dump of what has currently been implemented, and there are several inconsistencies.

An upcoming minor release will deprecate many of these inconsistencies, and they will be removed in the next major release.

Since the draft stage, the following major changes have been made:
- /api/v1 and /v2_alpha path segments have been replaced with the major version of the release (i.e. 'r0').
- Some POST versions of APIs with both POST and PUT have been removed.
- The specification has been split into one specification per API. This is the client-server API. The server-server API can be found documented separately.
- All APIs are now documented using Swagger
- The following modules have been added:
  - Content repository
  - Instant messaging
  - Push notification
  - History visibility
  - Search
  - Invites based on third party identifiers
  - Room tagging
  - Guest access
  - Client config
- The following APIs were added:
  - ``/sync``
  - ``/publicRooms``
  - ``/rooms/{roomId}/forget``
  - ``/admin/whois``
  - ``/rooms/{roomId}/redact``
  - ``/user/{userId}/filter``
- The following APIs have been significantly modified:
  - Invitations now contain partial room state
  - Invitations can now be rejected
  - ``/directory``
- The following events have been added:
  - ``m.room.avatar``
- Example signed json is included for reference
- Commentary on display name calculation was added
