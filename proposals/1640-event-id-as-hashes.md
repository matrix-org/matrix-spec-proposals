# Changing Event IDs to be Hashes

## Motivation

Having event IDs separate from the hashes leads to issues when a server receives
multiple events with the same event ID but different reference hashes. While
APIs could be changed to better support dealing with this situation, it is
easier and nicer to simply drop the idea of a separate event ID entirely, and
instead use the reference hash of an event as its ID.

## Identifier Format

Currently hashes in our event format include the hash name, allowing servers to
choose which hash functions to use. The idea here was to allow a gradual change
between hash functions without the need to globally coordinate shifting from one
hash function to another.

However now that room versions exist, changing hash functions can be achieved by
bumping the room version. Using this method would allow using a simple string as
the event ID rather than a full structure, significantly easing their usage.

One side effect of this would be that there would be no indication about which
hash function was actually used, and it would need to be inferred from the room
version. To aid debuggability it may be worth encoding the hash function into
the ID format.

**Conclusion:** Don't encode the hash function, since the hash will depend on
the version specific redaction algorithm anyway.

The proposal is therefore that the event IDs are a base 64 encoded `sha256` hash
prefixed with `$` (to aid distinguishing different types of identifiers). For
example, an event ID might be: `$CD66HAED5npg6074c6pDtLKalHjVfYb2q4Q3LZgrW6o`.

The hash is calculated in the same way as previous event reference hashes were,
which is:

1. Redact the event
2. Remove `signatures` field from the event
3. Serialize the event to canonical JSON
4. Compute the hash of the JSON bytes

Event IDs will no longer be included as part of the event, and so must be
calculated by servers receiving the event.


## Protocol Changes

The `auth_events` and `prev_events` fields on an event need to be changed from a
list of tuples to a list of strings, i.e. remove the old event ID and simply
have the list of hashes.

The auth rules also need to change:

-   The event no longer needs to be signed by the domain of the event ID (but
    still needs to be signed by the sender’s domain)

-   We currently allow redactions if the domain of the redaction event ID
    matches the domain of the event ID its redacting. This allows self redaction
    for servers, but would no longer be possible and there isn’t an obvious way
    round it. The only practical suggestion to this is to accept the redactions
    and only check if we should redact the target event once we received the
    target event.
