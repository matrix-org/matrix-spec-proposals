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

The following *event* keys are to be *removed* from the list of those to be
preserved by a redaction:

 * `membership`
 * `prev_state`

(Note this refers to the *event-level* `membership` property, rather than the
similarly-named sub-property under the `content` key.)

Rationale: neither of the above properties have defined meanings any more in the Matrix
protocol, so there is no reason for them to be special-cased in this way.

The following are to be added to the list of subkeys of the content property
which are preserved:

 * `m.room.create` preserves *all* content. Rationale: the values in a
   `create` event are deliberately intended to last the lifetime of the room,
   and if values are redacted, there is no way to add correct settings
   afterwards. It therefore seems non-sensical to allow redaction of a `create`
   event.

 * `m.room.redaction` should allow the `redacts` key (assuming
   [MSC2174](https://github.com/matrix-org/matrix-doc/pull/2174) is merged).
   Rationale: currently, redacting a redaction can lead to inconsistent results
   among homservers, depending on whether they receive the `m.room.redaction`
   result before or after it is redacted (and therefore may or may not redact
   the original event).

 * `m.room.power_levels` should allow (in addition to the keys already listed
   in the spec):

   * the `invite` key. Rationale: this is required to authenticate
     `m.room.member` events with the `invite` membership. Currently, redacting
     a `power_levels` event will mean that such events cannot be authenticated,
     potentially leading to a split-brain room.

## Other properties considered for preservation

Currently it is *not* proposed to add these to the list of properties which are
proposed for a redaction:

 * The `notifications` key of `m.room.power_levels`. Unlike the other
   properties in `power_levels`, `notifications` does not play a part in
   authorising the events in the room graph. Once the `power_levels` are
   replaced, historical values of the `notifications` property are
   irrelevant. There is therefore no need for it to be protected from
   redactions.

 * The `algorithm` key of `m.room.encryption`. Again, historical values of
   `m.room.encryption` have no effect, and servers do not use the value of the
   property to authenticate events.

   The effect of redacting an `m.room.encryption` event is much the same as that
   of sending a new `m.room.encryption` event with no `algorithm` key. It's
   unlikely to be what was intended, but adding rules to the redaction
   algorithm will not help this.

### Background to things not included in the proposal

The approach taken here has been to minimise the list of properties preserved
by redaction; in general, the list is limited to those which are required by
servers to authenticate events in the room. One reason for this is to simplify
the implementation of servers and clients, but a more important philosophical
reason is as follows.

Changing the redaction algorithm requires changes to both servers and clients,
so changes are difficult and will happen rarely. Adding additional keys now
sets an awkward precedent.

It is likely that in the future more properties will be defined which might be
convenient to preserve under redaction. One of the two scenarios would then
happen:

 * We would be forced to issue yet more updates to the redaction algorithm,
   with a new room versions and mandatory updates to all servers and clients, or:

 * We would end up with an awkward asymmetry between properties which were
   preserved under this MSC, and those which were introduced later so were not
   preserved.

In short, I consider it important for the elegance of the Matrix protocol that
we do not add unnecessary properties to the list of those to be preserved by
redaction.
