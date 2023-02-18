# MSC3969: Size limits

Matrix owes its name to its aim to interoperate with many protocols, some of which (Twitter,
RFC1459 IRC, ...) have stricter message length limits than Matrix, or lower media size limit
than typical Matrix homeservers.
Bridges can address this by "pastebining" the text to a stable URL, and posting this URL to
the other platform, but this can cause friction, especially when senders are unaware of
this behavior.

Additionally, room administrators may also prefer to limit the size of media and messages
to lower resource usage of the room on participating servers, or to provide a different
experience of Matrix.

This MSC aims to provide a way for bridges and room administrators to signal size limits,
to both media and messages should avoid using.
This allows clients to show a warning or block users from posting messages or media which
are larger than desired.


## Proposal

This MSC introduces a new `m.room.size_limits` state event types, which associates soft and
hard size limits to text and media size.


### Semantics of limits

Both soft and hard limits are integers and expressed in bytes.

Clients should prevent their users from exceeding the "hard" limit.
Receiving clients and servers may hide events which do.
If part of a message (eg. `formatted_body` or the body of a specific [MSC1767][MSC1767] block)
exceeds a hard limit, receiving clients and servers may hide only this part (and fallback to
either the `body` or a different [MSC1767][MSC1767] block).

A "soft" limit should only show a warning in user interfaces, but clients should not prevent
users from exceeding it. Receiving clients and servers should not hide such events because of this.

If, because of wildcards, a MIME type matches the masks of multiple soft (resp. hard) limits,
the most specific mask is used to compute the limit for that MIME type.
If multiple masks have uncomparable specificity, the lowest limit should be considered.

The number of lines includes empty lines, except the empty trailing line if any.
(eg. `"foo\n\nbar" counts as three lines; "foobar\n" as one).


### Format of `m.room.size_limits`

`m.room.size_limits` events may have two keys, `"soft"` and `"hard"`, each with a dictionary
as value. These dictionaries may have the following keys:

- `msgtypes` (object with positive integer values): This is a mapping from `msgtype` of `m.room.message`
  events to the size limit of their `body` and `formatted_body`, including the `body` of
  blocks defined by [MSC1767][MSC1767] for clients which implement it
- `attachment_mimetypes` (object with positive integer values): This is a mapping from file mimetypes
  to size limits. `*` may be used as a wildcard.
- `lines` (positive integer): A limit on the number of lines in text message.

Values not matching these types and undefined keys should be ignored.

`m.room.size_limits` events with a non-empty state key should be ignored.


### Examples


#### RFC1459 IRC

RFC1459 IRC messages are limited to 512 bytes, including message metadata overhead, whose
length is per-user.
IRC bridges may therefore consider the maximum possible size of the overhead, and subtract
it from the total limit, and advertise this in `m.room.size_limits`.

Sending long messages (over 3-5 lines) is usually considered poor style, but pastebining long ones
occasionally is tolerated.

For example, for an IRC server whose maximum overhead size is 100 bytes for PRIVMSG:

```json5
{
    "content": {
        "soft": {
            "lines": 4
        },
        "hard": {
            "msgtypes": {
                "m.emote": 403,
                "m.notice": 413,
                "m.text": 412
            }
        }
    },
    "sender": "@appservice:example.com",
    "state_key": "",
    "type": "m.room.size_limits"
}
```


#### multiline IRC

On IRC networks supporting the [`multiline`](https://ircv3.net/specs/extensions/multiline)
capability, this is relaxed, and limits can be counted without the message overhead.
For example, for servers advertising `max-bytes=40000,max-lines=10`, and IRC bridge could
set this to the room:

```json5
{
    "content": {
        // To be nice to IRC clients on that network not implementing `multiline`:
        "soft": {
            "lines": 4,
            "msgtypes": {
                "m.emote": 403,
                "m.notice": 413,
                "m.text": 412
            }
        },
        // The IRC server's hard limits:
        "hard": {
            "lines": 10,
            "msgtypes": {
                "m.emote": 403,
                "m.notice": 40000,
                "m.text": 40000
            }
        }
    },
    "sender": "@appservice:example.com",
    "state_key": "",
    "type": "m.room.size_limits"
}
```


#### Limiting resource use

Room administrators can choose to limit resource usage for their own reasons. For example:

```json5
{
    "content": {
        "soft": {
            "lines": 5,
            "mimetypes": {
                "text/*": 10000,  // 10kB
                "video/*": 5000000,  // 5MB
                "*/*": 1000000,  // 1MB for everything else
            }
        },
        "hard": {
            "lines": 100,
            "mimetypes": {
                "text/*": 100000,  // 100kB
                "*/*": 1000000,  // 10MB
            }
        }
    },
    "sender": "@room-admin:example.com",
    "state_key": "",
    "type": "m.room.size_limits"
}
```

## Potential issues

Clients not implementing this MSC will allow their users to send events hidden from other users.
This is already a problem when sending event types not supported by other clients, but in order
to minimize further impact, the following precautions should be taken until this MSC is widely
implemented:

- room administrators are discouraged from configuring hard limits
- developers are discouraged from hiding events matching either soft or hard limits

Clients may disagree on line number counts from HTML messages.

Bridges converting to different format to platforms with a hard limit may want to set conservative
soft and hard limits, in order to limit the risk of users exceeding the limit after conversion.
When this happens, they may choose to redact the offending event (to keep the room consistent with
the bridged platform) and/or inform the user their event was dropped.

Attachment limits are set by room administrators, and specific to that room.
A homeserver's content repository operates independently of any room, so it may have different
limits. Clients should not assume following size limits of a room implies their homeserver's
content repository will allow their uploads.

New/updated `m.room.size_limits` state events may race with new events.
Receiving clients/servers should allow a short grace period if possible before hiding
or dropping events.

When backfilling history backward, clients should consider they may receive a
`m.room.size_limits` event that predates events they already received.


## Alternatives

- Allowing multiple soft limits of increasing value, each with its own message/reason
  (eg. 256 -> "this won't be bridged to Twitter", 400 -> "this is unlikely to be bridged
  to IRC", 450 -> "this is very unlikely to be bridged to IRC", ...).
  This could get unwieldy especially in terms of internationalization, and may not bring
  many benefits
- Allowing only two soft limits, with meaning "this is frowned upon" and "this is likely
  to be dropped". It is probably better for user experience overall for "this is likely
  to be dropped" to be the hard limit itself.
- Dropping soft limits entirely. 
- Making clients bundle a list of known limits for each bridge and rely on [MSC2346][MSC2346]
  to allow them to discover bridges in a room.
  This puts a significant maintenance burden on clients, requires users to constantly update
  them to match new bridges (or new bridge configurations), may lead to different Matrix clients
  showing different sets of events, does not allow room administrators to set arbitrary limits.
- Counting grapheme clusters instead of bytes for text messages. They are more user-friendly,
  but clients and bridged platforms implementing differing versions of Unicode would count them
  differently.
- Counting characters instead of bytes for text messages. Clients can easily agree on them,
  but they do not provide much improvement over bytes
- Adding audio/video length limits and image/video maximum resolution. This requires at least
  partially downloading and processing the attachment, so this brings little benefit.


## Security considerations

Clients should not expect or rely on servers blocking or hiding events exceeding either soft
or hard limits, even when events are not end-to-end encrypted.

Different clients may see different things (but it is already an issue with `body`/`formatted_body`
or with [MSC1767][MSC1767]), allowing abusers to send messages targeted to certain (classes of) users
via public rooms.
It is therefore recommended for receiving clients and servers not to hide these events from
users with some sort of moderation powers (eg. power-level over 50, or high enough to issue
kicks or redactions).


## Unstable prefix

During development, `org.matrix.msc3969.room.size_limits` is to be used
instead of `m.room.size_limits`.


## Dependencies

This MSC builds on [MSC1767][MSC1767], though clients not implementing MSC1767 can simply ignore
parts related to mimetypes, as they have nothing to enforce anyway.


[MSC1767]: https://github.com/matrix-org/matrix-spec-proposals/pull/1767
[MSC2346]: https://github.com/matrix-org/matrix-spec-proposals/pull/2346
