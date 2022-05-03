# MSC2540: Stricter event validation: JSON compliance

## Background

There has been [prior discussions](https://github.com/matrix-org/matrix-doc/issues/1646)
about validating events more strictly. This MSC proposes fixing a small piece of
this: JSON compliance.

The [Canonical JSON](https://matrix.org/docs/spec/appendices#canonical-json)
specification requires that numbers that are serialized in JSON are integers in
the inclusive range of `[-(2^53) + 1, (2^53) - 1]`, which matches the requirements of
[section 6 of RFC 7159](https://tools.ietf.org/html/rfc7159). Note that it is
not explicit, but all floats are invalid.

It is worth mentioning that there are common extensions to JSON which produce 
invalid JSON according to the Matrix specification; some programming languages
even support these by default. One common additional feature is handling
"special" float values: `Infinity`, `-Infinity`, and `NaN`.


## Proposal

In a future room version, homeserver implementations are to strictly enforce
the JSON compliance of the Canonical JSON specification for events.
Non-compliant events should be treated like any other malformed event, 
for example by rejecting the request with an HTTP 400 error with `M_BAD_JSON`,
or by discarding the event.

The rationale for doing this in a future room version is to avoid a split brain
room -- where some federated servers believe an event is valid and others reject
it as invalid. Rooms will be able to opt into this behavior as part of a room
version upgrade.

Homeserver implementations are not to strictly enforce this JSON compliance in
[room versions 1, 2, 3, 4, and 5](https://matrix.org/docs/spec/#complete-list-of-room-versions).
The rationale is essentially the same as why a future room version is necessary:
this ensures that all federated servers treat the same events as valid.


## Potential issues

Homeserver implementations might include JSON parsers which are stricter than
others. It may not be worthwhile or reasonable to loosen those restrictions for
stable room versions. 


## Alternatives

It could be argued that this MSC is unnecessary since it does not add any new
requirements for handling of JSON data. Unfortunately starting to enforce these 
requirements in current rooms could cause federation to break as homeservers
will disagree on whether events are valid.


## Security considerations

N/A


## Unstable prefix

A room version of `org.matrix.strict_canonicaljson` until a future room version
is available. This room version will use
[room version 5](https://matrix.org/docs/spec/rooms/v5) as base and include the
above modifications.
