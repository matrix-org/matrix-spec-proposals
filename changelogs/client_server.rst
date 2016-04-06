<Next release>
==============

- Spec clarifications:

  - Clarify the behaviour of the "Room History Visibility" module; in particular, the behaviour of the ``shared`` history visibilty, and how events at visibility boundaries should be handled.

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
