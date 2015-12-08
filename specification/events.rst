Event Structure
===============

All communication in Matrix is expressed in the form of data objects called
Events. These are the fundamental building blocks common to the client-server,
server-server and application-service APIs, and are described below.

Note that the structure of these events may be different than those in the
server-server API.

{{common_event_fields}}

{{common_room_event_fields}}

{{common_state_event_fields}}


Size limits
-----------

The total size of any event MUST NOT exceed 65 KB. There are additional
restrictions on sizes per key:

- ``sender`` MUST NOT exceed 255 bytes (including domain).
- ``room_id`` MUST NOT exceed 255 bytes.
- ``state_key`` MUST NOT exceed 255 bytes.
- ``type`` MUST NOT exceed 255 bytes.
- ``event_id`` MUST NOT exceed 255 bytes.

Some event types have additional size restrictions which are specified in
the description of the event. Additional keys have no limit other than that
implied by the total 65 KB limit on events.

Room Events
-----------
.. NOTE::
  This section is a work in progress.

This specification outlines several standard event types, all of which are
prefixed with ``m.``

{{m_room_aliases_event}}

{{m_room_canonical_alias_event}}

{{m_room_create_event}}

{{m_room_join_rules_event}}

{{m_room_member_event}}

{{m_room_power_levels_event}}

{{m_room_redaction_event}}

