Room Tagging
============

.. _module:tagging:

Users can add tags to rooms. Tags are short strings used to label rooms, e.g.
"work", "familly". A room may have multiple tags. Tags are only visible to the
user that set them but are shared across all their devices.

Events
------

The tags on a room are passed as single ``m.tag`` event in the
``private_user_data`` section of a room in v2 sync.

{{m_tag_event}}

Client Behaviour
----------------

{{v2_tags_http_api}}
