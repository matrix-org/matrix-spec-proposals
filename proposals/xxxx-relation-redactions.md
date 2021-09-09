# MSCXXXX: Redaction changes for events with a relation

[MSC2674](https://github.com/matrix-org/matrix-doc/pull/2674) defines a
standard shape for indicating events which relate to other events.

When redacting events relating to other events, some information needs to be
preserved for the best user experience. Given that this will require
a room version change, it was split up into a separate MSC here.

## Proposal

Events with a relation may be redacted like any other event.

The `m.relates_to`.`rel_type` and `m.relates_to`.`event_id` fields should
be preserved over redactions, so that clients can still distinguish
redacted relations from other redacted events of the same event type.
If `m.relates_to` is not an object, or `m._relates_to` would be
an empty object after redacting any other keys, then `m.relates_to`
should also be removed from `content`.

One example is telling redacted edits (as proposed in
[MSC 2676](https://github.com/matrix-org/matrix-doc/pull/2676)) apart from
from normal redacted messages, and maintain reply ordering.

This modification to the redaction algorithm requires a new room version.
However, event relationships can still be used in existing room versions, but
the user experience may be worse if redactions are performed.