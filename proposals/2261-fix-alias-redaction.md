# MSC2261: Allow `m.room.aliases` events to be redacted by room admins

Currently, the content of `m.room.aliases` events are protected from redaction
by the [redaction algorithm](https://matrix.org/docs/spec/client_server/r0.5.0#redactions).

This opens it as an abuse vector where users can add spam or offensive aliases
to the room state, which room adminstrators cannot remove.

## Proposal

`content.aliases` should no longer be preserved when an `m.room.aliases` event
is redacted.

This will require a new room version, since changes to the redaction algorithm
also change the way that event hashes (and hence event IDs) are calculated.

TODO: should the room directory be updated to match the new room state, where
possible? It kinda makes sense when the redaction is used to undo an accidental
addition, but in general it might not be a great plan, particularly if we are
switching to a world in which `m.room.aliases` is very much advisory. Also,
bear in mind that redacting the removal of an alias would mean re-adding the
alias.

## Potential issues

* This could increase the number of cases in which `m.room.aliases` events
  differ from reality (see https://github.com/matrix-org/matrix-doc/issues/2262).

* Redacting an `m.room.aliases` event adding an abusive alias will remove not
  only the abusive alias from the room state, but also all other aliases that
  are in the same state_key (i.e. other aliases from the same server).

  This could be mitigated by replacing `m.room.aliases` events with granular
  `m.room.alias` events (https://github.com/matrix-org/matrix-doc/issues/2259).

## See also

 * [MSC2176](https://github.com/matrix-org/matrix-doc/pull/2176), which
proposes other changes to the redaction rules.
 * [MSC2260](https://github.com/matrix-org/matrix-doc/pull/2260), which
suggests changes to the auth rules for `m.room.aliases` events.
