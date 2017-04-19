<Unreleased changes>
====================

- Breaking changes:

  - Change the rule kind of `.m.rule.contains_display_name` from
    `underride` to `override`. This works with all known clients
    which support push rules, but any other clients implementing
    the push rules API should be aware of this change. This
    makes it simple to mute rooms correctly in the API
    (`#373 <https://github.com/matrix-org/matrix-doc/pull/373>`_).
  - Remove ``/tokenrefresh`` from the API
    (`#395 <https://github.com/matrix-org/matrix-doc/pull/395>`_).
  - Remove requirement that tokens used in token-based login be macaroons
    (`#395 <https://github.com/matrix-org/matrix-doc/pull/395>`_).

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

- Spec clarifications:

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
    particular, the behaviour of the ``shared`` history visibilty, and how
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
