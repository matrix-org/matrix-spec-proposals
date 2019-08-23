# Mass redactions
Matrix, like any platform with public chat rooms, has spammers. Currently,
redacting spam essentially requires spamming redaction events in a 1:1 ratio,
which is not optimal<sup>[1]</sup>. Most clients do not even have any mass
redaction tools, likely in part due to the lack of a mass redaction API. A mass
redaction API on the other hand has not been implemented as it would require
sending lots of events at once. However, this problem could be solved by
allowing a single redaction event to redact many events instead of sending many
redaction events.

## Proposal
This proposal builds upon [MSC2174] and suggests making the `redacts` field
in the content of `m.room.redaction` events an array of event ID strings
instead of a single event ID string.

It would be easiest to do this before MSC2174 is written into the spec, as then
only one migration would be needed: from an event-level redacts string to a
content-level redacts array.

### Number of redactions
Room v4+ event IDs are 44 bytes long, which means the federation event size
limit would cap a single redaction event at a bit less than 1500 targets.
Redactions are not intrinsically heavy, so a separate limit should not be
necessary.

### Auth rules
The redaction auth rules should change to iterate the array and check if the
sender has the privileges to redact each event.

There are at least two potential ways to handle targets that are not found or
rejected: soft failing until all targets are found and handling each target
separately.

#### Soft fail
Soft fail the event until all targets are found, then accept only if the sender
has the privileges to redact every listed event. This is how redactions
currently work.

This has the downside of requiring servers to fetch all the target events (and
possibly forward them to clients) before being able to process and forward the
redaction event.

#### Handle each target separately
Handle each target separately: if some targets are not found, remember the
redaction and check auth rules when the target is received. This option brings
some complexities, but might be more optimal in situations such as a spam
attack.

When receiving a redaction event:
* Ignore illegal targets
* "Remember" targets that can't be found
* Send legal target event IDs to clients in the redaction event.

When receiving an event that is "remembered" to be possibly redacted by an
earlier redaction, check if the redaction was legal, and if it was, do not
send the event to clients.

## Tradeoffs

## Potential issues

## Security considerations


[1]: https://img.mau.lu/hEqqt.png
[MSC2174]: https://github.com/matrix-org/matrix-doc/pull/2174
