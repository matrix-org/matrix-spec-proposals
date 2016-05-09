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
