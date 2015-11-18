.. This file is automatically processed by the templating system. To make it
.. happy, you MUST use '=' as the title underline and you MUST stick the version
.. in the title. The version MUST follow the numbering format 
.. "v<num>.<num>.<num>" - You cannot use a-z. If the templating system fails to
.. find the right info, it will be treated as a test failure and so will show up
.. in Jenkins. Comments like this are ignored by both RST and the templating
.. system. Add the newest release notes beneath this comment.

Specification changes in v0.3.0 (2015-11-18)
============================================

Many sections have been filled in, or added to reflect long-standing status
quos. Several API endpoints have also been converted to Swagger. Several
presentation improvements (e.g. syntax highlighting) have also been added.

Additions:
 - Extensive narrative on instant messaging
 - Documentation of event sending
 - Documentation of state event retrieval
 - Redaction algorithm
 - Algorithm for calculating display names for rooms and users
 - New endpoint: ``/publicRooms``
 - New event: ``m.room.avatar``
 - invite_room_state on ``m.room.member`` events
 - New section: Third party invitations
 - Ability to reject invitations
 - New API: Search
 - Guest access to rooms
 - Descriptions of server-server API endpoints for joining rooms
 - Sample expected crypto output
 - Several security warnings

 Modifications:
  - Fixed errors in parameters of /login
  - Significant clarification and improvements to description of pagination
  - Changes to v2_alpha/sync API (Note: this API is still not stable)

Specification changes in v0.2.0 (2015-10-02)
============================================

This update fundamentally restructures the specification. The specification has
been split into more digestible "modules" which each describe a particular
function (e.g. typing). This was done in order make the specification easier to
maintain and help define which modules are mandatory for certain types
of clients. Types of clients along with the mandatory modules can be found in a
new "Feature Profiles" section. This update also begins to aggressively
standardise on using Swagger and JSON Schema to document HTTP endpoints and
Events respectively. It also introduces a number of new concepts to Matrix.

Additions:
 - New section: Feature Profiles.
 - New section: Receipts.
 - New section: Room history visibility.
 - New event: ``m.receipt``.
 - New event: ``m.room.canonical_alias``
 - New event: ``m.room.history_visibility``
 - New keys: ``/createRoom`` - allows room "presets" using ``preset`` and
   ``initial_state`` keys.
 - New endpoint: ``/tokenrefresh`` - Related to refreshing access tokens.

Modifications:
 - Convert most of the older HTTP APIs to Swagger documentation.
 - Convert most of the older event formats to JSON Schema.
 - Move selected client-server sections to be "Modules".

Specification changes in v0.1.0 (2015-06-01)
============================================
- First numbered release.
- Restructure the format of Event information. Add more information.
- Restructure the format of the Client-Server HTTP APIs.
