# Changing Event IDs to be Hashes

## Motivation

Having event IDs separate from the hashes leads to issues when a server
receives multiple events with the same event ID but different hashes.
While APIs could be changed to better support dealing with this
situation, it is easier and nicer to simply drop the idea of a separate
event ID entirely.

## Identifier Format

Currently hashes in JSON include the hash name, allowing servers to
choose which hash functions to use. The idea here was to allow a gradual
change between hash functions without the need to globally coordinate
shifting from one hash function to another.

However now that room versions exist, changing hash functions can be
achieved by bumping the room version. Using this method would allow
using a simple string as the event ID rather than a full structure,
significantly easing their usage.

One side effect of this would be that there would be no indication about
which hash function was actually used, and it would need to be inferred
from the room version. To aid debuggability it may be worth encoding the
hash function into the ID format.

**Conclusion:** Don't encode the hash function, since the hash will depend on
the version specific redaction algorithm anyway.

## Protocol Changes

The `auth_events` and `prev_events` fields on an event need to be
changed from a list of tuples to a list of strings, i.e. remove the old
event ID and simply have the list of hashes.

The auth rules also need to change:

-   The event no longer needs to be signed by the domain of the event ID
    (but still needs to be signed by the sender’s domain)

-   We currently allow redactions if the domain of the redaction event ID
    matches the domain of the event ID its redacting. This allows self redaction
    for servers, but would no longer be possible and there isn’t an obvious way
    round it. The only practical suggestion to this is to accept the redactions
    and only check if we should redact the target event once we received the
    target event.
