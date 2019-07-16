# MSC2176: Update the redaction rules

The current [redaction
algorithm](https://matrix.org/docs/spec/client_server/r0.5.0#redactions) is now
somewhat dated. This MSC proposes a number of changes to the rules which will
improve the security and reliability of the Matrix protocol.

## Proposal

The following changes will require a new room version, since changes to the
redaction algorithm also change the way that [event
hashes](https://matrix.org/docs/spec/server_server/r0.1.2#calculating-the-reference-hash-for-an-event)
(and hence event IDs) are calculated.

The following *event* keys should be *removed* from the list of those to be
preserved by a redaction:

 * `membership`
 * `prev_state`

(Note this refers to the *event-level* `membership` property, rather than the
similarly-named sub-property under the `content` key.)

Rationale: neither of the above properties have defined meanings in the Matrix
protocol, so there is no reason for them to be special-cased in this way.

The following should be added to the list of subkeys of the content property
which should be preserved:

 * `m.room.redaction` should allow the `redacts` key (assuming
   [MSC2174](https://github.com/matrix-org/matrix-doc/pull/2174) is merged).
   Rationale: currently, redacting a redaction can lead to inconsistent results
   among homservers, depending on whether they receive the `m.room.redaction`
   result before or after it is redacted (and therefore may or may not redact
   the original event).

 * `m.room.create` should allow the `room_version` key. Currently, redacting an
   `m.room.create` event will make the room revert to a v1 room.

 * `m.room.power_levels` should allow the `notifications` key. Rationale:
   symmetry with the other `power_levels` settings. (Maybe? See
   https://github.com/matrix-org/matrix-doc/issues/1601#issuecomment-511237744.)


## Potential issues

What if there is spam in sub-properties of the `notifications` property of
power-levels? Should we not be able to redact it?
