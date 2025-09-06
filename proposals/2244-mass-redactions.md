# Mass redactions
Matrix, like any platform with public chat rooms, has spammers. Currently,
redacting spam essentially requires spamming redaction events in a 1:1 ratio,
which is not optimal<sup>[1](images/2244-redaction-spam.png)</sup>. Most
clients do not even have any mass redaction tools, likely in part due to the
lack of a mass redaction API. A mass redaction API on the other hand has not
been implemented as it would require sending lots of events at once. However,
this problem could be solved by allowing a single redaction event to redact
many events instead of sending many redaction events.

## Proposal
**Updated by [MSC4343](https://github.com/matrix-org/matrix-spec-proposals/pull/4343)**:
Instead of modifying `redacts` on `m.room.redaction`, this proposal now copies
`m.room.redaction` to `m.room.redactions` with the same `redacts` change. As such,
it is no longer built upon [MSC2174](https://github.com/matrix-org/matrix-doc/pull/2174).

This proposal suggests copying the schema of `m.room.redaction` to a new event
type, `m.room.redactions`, with `redacts` being an array of event ID strings
instead of a single event ID string.

It would be easiest to do this before MSC2174 is written into the spec, as then
only one migration would be needed instead of needing to introduce a new event
type: from an event-level redacts string to a content-level redacts array.

### Backwards compatibility
In order to not break old clients
completely, servers should still add a `redacts` string containing one of the
redacted event IDs to the top level of `m.room.redaction` events in *newer*
room versions when serving such events over the Client-Server API.

Like MSC2174, for improved compatibility with *newer* clients, servers should
add a `redacts` array to the `content` of `m.room.redaction` events in *older*
room versions when serving such events over the Client-Server API.

### Number of redactions
Room v4+ event IDs are 44 bytes long, which means the federation event size
limit would cap a single redaction event at a bit less than 1500 targets.
Redactions are not intrinsically heavy, so a separate limit should not be
necessary.

Due to the possible large number of redaction targets per redaction event,
servers should omit the list of redaction targets from the `unsigned` ->
`redacted_because` field of redacted events. If clients want to get the list
of targets of a redaction event in `redacted_because`, they should read the
`event_id` field of the `redacted_because` event and use the
`/rooms/{roomId}/event/{eventId}` endpoint to fetch the content.

### Client behavior
Clients shall apply existing `m.room.redaction` target behavior over an array
of event ID strings in `m.room.redactions`.

### Server behavior (auth rules)
The target events of an `m.room.redactions` event shall no longer be considered when
authorizing an `m.room.redactions` event. Any other existing rules remain
unchanged.

After a server accepts an `m.room.redactions` using the modified auth rules, it
evaluates individually whether each target can be redacted under the existing
room v5 auth rules. Servers MUST NOT include failing and unknown entries to
clients.

> Servers do not know whether redaction targets are authorized at the time they
  receive the `m.room.redactions` unless they are in possession of the target
  event. Implementations retain entries in the original list which were not
  shared with clients to later evaluate the target's redaction status.

When the implementation receives a belated target from an earlier
`m.room.redactions`, it evaluates at that point whether the redaction is
authorized.

> Servers should not send belated target events to clients if their redaction
  was found to be in effect, as clients were not made aware of the redaction.
  That fact is also used to simply ignore unauthorized targets and send the
  events to clients normally.

## Tradeoffs

## Potential issues

## Security considerations
Server implementations should ensure that large redaction events do not become
a DoS vector, e.g. by processing redactions in the background.
