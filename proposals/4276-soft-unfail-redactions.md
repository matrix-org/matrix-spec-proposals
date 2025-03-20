# MSC4276: Soft unfailure for self redactions

When a user is removed from a room, the server may issue several redactions to their messages to clean
up rooms. Users may also use similar functionality, if supported by their server, to remove their own
messages after being removed.

These self redactions can end up being [soft failed](https://spec.matrix.org/v1.13/server-server-api/#soft-failure)
due to the authorization rules preventing the redaction event from being validated, despite being part of the
DAG at a legal point.

This proposal suggests that servers be less strict about soft failing self-redactions in particular.

## Proposal

When evaluating for soft failure, servers SHOULD permit `m.room.redaction` events which target events
by the same `sender` to go through normally, avoiding soft failure. Servers MAY impose limits on how
many events can bypass soft failure. Limits similar to the following may be of interest to developers:

* Only the first 300 redactions from the same `sender` bypass soft failure.
* Only the first redaction targeting a given event bypasses soft failure. "Duplicate" redactions are
  subject to soft failure.
* Only the redactions received within 1 hour of the most recent membership event change can bypass
  soft failure.

Applying some or all of the conditions may help servers avoid event spam abuse from making it to
local users over `/sync`.

## Potential issues

This may allow banned users to spam rooms with redaction events - the limits proposed above are potential
ways to mitigate the issue.

## Alternatives

Another approach could be to modify auth rules to exempt same-sender `m.room.redaction` events from the requirement
to pass authorization at the current resolved state. This approach may not work well with [how redactions work](https://spec.matrix.org/v1.13/rooms/v11/#handling-redactions).

## Security considerations

See Potential Issues.

## Unstable prefix

Not applicable.

## Dependencies

This proposal has no direct dependencies.
