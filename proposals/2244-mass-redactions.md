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
This proposal builds upon [MSC2174](https://github.com/matrix-org/matrix-doc/pull/2174)
and suggests making the `redacts` field in the content of `m.room.redaction`
events an array of event ID strings instead of a single event ID string.

It would be easiest to do this before MSC2174 is written into the spec, as then
only one migration would be needed: from an event-level redacts string to a
content-level redacts array.

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
of event ID strings.

### Server behavior (auth rules)
The redaction auth rules should change to iterate the array and check if the
sender has the privileges to redact each event.

There are at least two potential ways to handle targets that are not found or
rejected: soft failing until all targets are found or handling each target
separately.

#### Soft fail
[Soft fail](https://matrix.org/docs/spec/server_server/r0.1.3#soft-failure) the
event until all targets are found, then accept only if the sender has the
privileges to redact every listed event. This is how redactions currently work.

This has the downside of requiring servers to fetch all the target events (and
possibly forward them to clients) before being able to process and forward the
redaction event.

#### Handle each target separately
The target events of an `m.room.redaction` shall no longer be considered when
authorizing an `m.room.redaction` event. Any other existing rules remain
unchanged.

When a server accepts an `m.room.redaction` using the modified auth rules, it
evaluates individually whether each target can be redacted under the existing
auth rules. Servers MUST NOT include failing and unknown entries to clients.

> Servers do not know whether redaction targets are authorized at the time they
  receive the `m.room.redaction` unless they are in possession of the target
  event. Implementations retain entries in the original list which were not
  shared with clients to later evaluate the target's redaction status.

When the implementation receives a belated target from an earlier
`m.room.redaction`, it evaluates at that point whether the redaction is
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
