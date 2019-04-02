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

The proposal is therefore that the event IDs are a sha256 hash, encoded using
[unpadded
Base64](https://matrix.org/docs/spec/appendices.html#unpadded-base64), and
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


## Changes to Event Formats

As well as changing the format of event IDs, we also change the format of the
`auth_events` and `prev_events` keys in events to simply be lists of event IDs
(rather than being lists of tuples).

A full event would therefore look something like (note that this is just an
illustrative example, and that the hashes are not correct):

```json
{
  "auth_events": [
    "$5hdALbO+xIhzcLTxCkspx5uqry9wO8322h/OI9ApnHE",
    "$Ga0DBIICBsWIZbN292ATv8fTHIGGimwjb++w+zcHLRo",
    "$zc4ip/DpPI9FZVLM1wN9RLqN19vuVBURmIqAohZ1HXg",
  ],
  "content": {
    "body": "Here is the message content",
    "msgtype": "m.message"
  },
  "depth": 6,
  "hashes": {
    "sha256": "M6/LmcMMJKc1AZnNHsuzmf0PfwladVGK2Xbz+sUTN9k"
  },
  "origin": "localhost:8800",
  "origin_server_ts": 1548094046693,
  "prev_events": [
    "$MoOzCuB/sacqHAvgBNOLICiGLZqGT4zB16MSFOuiO0s",
  ],
  "room_id": "!eBrhCHJWOgqrOizwwW:localhost:8800",
  "sender": "@anon-20190121_180719-33:localhost:8800",
  "signatures": {
    "localhost:8800": {
      "ed25519:a_iIHH": "N7hwZjvHyH6r811ebZ4wwLzofKhJuIAtrQzaD3NZbf4WQNijXl5Z2BNB047aWIQCS1JyFOQKPVom4et0q9UOAA"
    }
  },
  "type": "m.room.message"
}
```

## Changes to existing APIs

All APIs that accept event IDs must accept event IDs in the new format.

For S2S API, whenever a server needs to parse an event from a request or
response they must either already know the room version *or* be told the room
version in the request/response. There are separate MSCs to update APIs where
necessary.

For C2S API, the only change clients will see is that the event IDs have changed
format. Clients should already be treating event IDs as opaque strings, so no
changes should be required. Servers must add the `event_id` when sending the
event to clients, however.

Note that the `auth_events` and `prev_events` fields aren't sent to clients, and
so the changes proposed above won't affect clients.


## Protocol Changes

The `auth_events` and `prev_events` fields on an event need to be changed from a
list of tuples to a list of strings, i.e. remove the old event ID and simply
have the list of hashes.

The auth rules also need to change:

-   The event no longer needs to be signed by the domain of the event ID (but
    still needs to be signed by the sender’s domain)

-   We currently allow redactions if the domain of the redaction event ID
    matches the domain of the event ID it is redacting; which allows self
    redaction. This check is removed and redaction events are always accepted.
    Instead, the redaction event only takes effect and is sent down to clients
    if/when the original event is received, and the domain of the events'
    senders match. (While this is clearly suboptimal, it is the only practical
    suggestion)


## Room Version

There will be a new room version v3 that is the same as v2 except uses the new
event format proposed above. v3 will be marked as 'stable' as defined in [MSC1804](https://github.com/matrix-org/matrix-doc/blob/travis/msc/room-version-client-advertising/proposals/1804-advertising-capable-room-versions.md)

