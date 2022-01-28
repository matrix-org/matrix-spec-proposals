---
toc_hide: true
---

{{% added-in this=true %}} In room versions 1 and 2, redactions were
explicitly part of the [authorization rules](/rooms/v1/#authorization-rules)
under Rule 11. As of room version 3, these conditions no longer exist as
represented by [this version's authorization rules](#authorization-rules).

While redactions are always accepted by the authorization rules for
events, they should not be sent to clients until both the redaction
event and the event the redaction affects have been received, and can
be validated. If both events are valid and have been seen by the server,
then the server applies the redaction if one of the following conditions
is met:

1. The power level of the redaction event's `sender` is greater than or
   equal to the *redact level*.
2. The domain of the redaction event's `sender` matches that of the
   original event's `sender`.

If the server would apply a redaction, the redaction event is also sent
to clients. Otherwise, the server simply waits for a valid partner event
to arrive where it can then re-check the above.
