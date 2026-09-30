# MSC4553: Forwarded messages

Clients forward a message by copying it into a new event. Without metadata, recipients see the copy as if the
forwarding user wrote it, and bridges have nothing to translate into their network's notion of a forward.

[MSC2723] proposed an `m.forwarded` object for this but stalled. This MSC reuses that object and adds
`m.forwarded_content`, a separate copy of the original content. The top-level fields can then carry a text fallback
for clients and bridges that don't support this MSC, without affecting what supporting clients render.

## Proposal

This MSC only covers `m.room.message` events. Forwarding other event types, such as stickers, polls, reactions, or
state events, is out of scope.

### `m.forwarded`

A forwarded message MUST include an `m.forwarded` object describing the original message, with the following required
fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `event_id` | string | Event ID of the original event. |
| `room_id` | string | Room ID of the original event. |
| `sender` | string | User ID of the original event's sender. |
| `origin_server_ts` | integer | Origin server timestamp of the original event. |

An event is a forward if its content has an `m.forwarded` object with all of these fields.

If the event the user selected to forward is itself a forward, the sender MUST copy its `m.forwarded` unchanged, so
the new event points at the original message rather than at the intermediate forward. Otherwise, the selected event is
the original, and `m.forwarded` describes it.

### `m.forwarded_content`

A forwarded message MUST also include `m.forwarded_content`, the content of the original message. `m.forwarded_content`
is valid if it is an object with a string `msgtype` and a string `body`.

If the selected event is a forward with a valid `m.forwarded_content`, the sender MUST copy it unchanged. Otherwise,
the sender builds it from the selected event's content, decrypted if the event was encrypted:

1. If the event has been edited, the sender MUST apply the latest edit available to it, as it would for display.
2. The sender MUST remove `m.forwarded`, `m.forwarded_content`, and their unstable equivalents, and strip any legacy
   reply fallback from `body` and `formatted_body`.

The sender MUST NOT modify `m.forwarded_content` in any other way.

### Top-level content

The top-level content is a copy of `m.forwarded_content` without `m.relates_to`, `m.mentions`, `m.new_content`,
`m.forwarded`, and `m.forwarded_content`, with the fallback below applied and the new `m.forwarded` and
`m.forwarded_content` added.

The sender MUST set its own top-level `m.mentions`, which stops legacy push rules from matching the fallback text. It
MUST NOT mention the original sender just because the event attributes them. The sender MAY add its own
`m.relates_to`, for example to send the forward as a reply or in a thread.

Media fields, including `file`, are copied as they are, even into an unencrypted room. This exposes the media's
decryption key to that room, which is intended: the forwarding user is sharing that media, and clients do not need to
upload it again.

### Rendering

A supporting client renders a forward with attribution from `m.forwarded`. If `m.forwarded_content` is valid, the
client MUST render it as the message content and MUST NOT render the top-level `body` or `formatted_body`. Otherwise,
as with [MSC2723] forwards, the client renders the top-level content.

If `m.forwarded_content` is an `m.emote`, it MUST be rendered as an emote by `m.forwarded.sender`, not by the
forwarding user.

Relationships and mentions inside `m.forwarded_content` MUST NOT be treated as relationships or mentions in the
destination room.

Forwards cannot be edited. Clients MUST NOT offer to edit a forward, and MUST ignore any edit whose target is a
forward.

### Fallback

The sender MUST add a fallback when the message type's `body` holds message text, or supports
[media captions](https://spec.matrix.org/v1.19/client-server-api/#media-captions). Message types whose `body` is
something else, such as the description of an `m.location`, and message types the sender does not recognise, keep
`body`, `format`, and `formatted_body` exactly as in `m.forwarded_content`.

In this section, "the source" means `m.forwarded_content`.

For message types that support media captions, the sender MUST set top-level `filename` to the source's `filename`,
or to its `body` if `filename` is absent. The fallback then becomes the media's caption. The source has an original
caption only if its `filename` is present and differs from its `body`.

Clients that don't support this MSC would show a forwarded emote as an emote by the forwarding user, so the sender
MUST set the top-level `msgtype` of a forwarded `m.emote` to `m.text` and put the original sender's display name, or
their user ID if the forwarding client does not know it, in front of the quoted text. In `body` it is plain text; in
`formatted_body` it is `<a href="{sender permalink}">{display name}</a>`, which clients may display as a mention.
`m.forwarded_content` keeps `m.emote`.

#### Plain text

The top-level `body` MUST be:

```text
Forwarded from {sender} - view original message: {permalink}
{original text or caption}
```

The newline and the second line are only included if the source has non-empty text or an original caption.

`{sender}` is `m.forwarded.sender`. `{permalink}` is a
[matrix.to event permalink](https://spec.matrix.org/v1.19/appendices/#matrixto-navigation) built from
`m.forwarded.room_id` and `m.forwarded.event_id`, each percent-encoded. It SHOULD include `via` parameters so the
room can be found by users who are not in it. The wording is fixed English; supporting clients MAY localise
attribution in their own UI.

#### HTML

The sender MUST set `format` to `org.matrix.custom.html` and `formatted_body` to:

```html
<strong>Forwarded from <a href="{sender permalink}">{sender}</a> - <a href="{event permalink}">view original message</a></strong><blockquote>{original HTML}</blockquote>
```

The `<blockquote>` is only included under the same condition as the second line of `body`.

`{sender permalink}` is a matrix.to link to `m.forwarded.sender`, and `{event permalink}` is the link used in `body`.
The sender MUST HTML-escape the sender ID, display name, and link attributes. `{original HTML}` is the source's
`formatted_body` if its `format` is `org.matrix.custom.html`; otherwise it is the source's text or caption,
HTML-escaped, with line breaks converted to `<br>`.

### Examples

A forwarded text message:

```json
{
  "msgtype": "m.text",
  "body": "Forwarded from @alice:example.org - view original message: https://matrix.to/#/!source%3Aexample.org/%24original%3Aexample.org?via=example.org\nMeeting starts at noon.",
  "format": "org.matrix.custom.html",
  "formatted_body": "<strong>Forwarded from <a href=\"https://matrix.to/#/%40alice%3Aexample.org\">@alice:example.org</a> - <a href=\"https://matrix.to/#/!source%3Aexample.org/%24original%3Aexample.org?via=example.org\">view original message</a></strong><blockquote><p>Meeting starts at noon.</p></blockquote>",
  "m.mentions": {},
  "m.forwarded": {
    "event_id": "$original:example.org",
    "room_id": "!source:example.org",
    "sender": "@alice:example.org",
    "origin_server_ts": 1722451200000
  },
  "m.forwarded_content": {
    "msgtype": "m.text",
    "body": "Meeting starts at noon.",
    "format": "org.matrix.custom.html",
    "formatted_body": "<p>Meeting starts at noon.</p>"
  }
}
```

A forwarded emote, originally `/me waves` from Alice:

```json
{
  "msgtype": "m.text",
  "body": "Forwarded from @alice:example.org - view original message: https://matrix.to/#/!source%3Aexample.org/%24emote%3Aexample.org?via=example.org\nAlice waves",
  "format": "org.matrix.custom.html",
  "formatted_body": "<strong>Forwarded from <a href=\"https://matrix.to/#/%40alice%3Aexample.org\">@alice:example.org</a> - <a href=\"https://matrix.to/#/!source%3Aexample.org/%24emote%3Aexample.org?via=example.org\">view original message</a></strong><blockquote><a href=\"https://matrix.to/#/%40alice%3Aexample.org\">Alice</a> waves</blockquote>",
  "m.mentions": {},
  "m.forwarded": {
    "event_id": "$emote:example.org",
    "room_id": "!source:example.org",
    "sender": "@alice:example.org",
    "origin_server_ts": 1722451200000
  },
  "m.forwarded_content": {
    "msgtype": "m.emote",
    "body": "waves"
  }
}
```

A forwarded file without a caption. The source `body` was a filename, so it moves to `filename` and is not quoted:

```json
{
  "msgtype": "m.file",
  "filename": "agenda.pdf",
  "body": "Forwarded from @alice:example.org - view original message: https://matrix.to/#/!source%3Aexample.org/%24file%3Aexample.org?via=example.org",
  "format": "org.matrix.custom.html",
  "formatted_body": "<strong>Forwarded from <a href=\"https://matrix.to/#/%40alice%3Aexample.org\">@alice:example.org</a> - <a href=\"https://matrix.to/#/!source%3Aexample.org/%24file%3Aexample.org?via=example.org\">view original message</a></strong>",
  "url": "mxc://example.org/agenda",
  "m.mentions": {},
  "m.forwarded": {
    "event_id": "$file:example.org",
    "room_id": "!source:example.org",
    "sender": "@alice:example.org",
    "origin_server_ts": 1722451200000
  },
  "m.forwarded_content": {
    "msgtype": "m.file",
    "body": "agenda.pdf",
    "url": "mxc://example.org/agenda"
  }
}
```

## Potential issues

Message types without a fallback, such as `m.location`, appear as ordinary messages to clients that don't support
this MSC.

The event carries the content twice, so senders SHOULD check that it fits within the event size limit before sending.

## Security considerations

Everything in `m.forwarded` is a claim by the forwarding user, and `m.forwarded_content` need not match the source
event. Forwarding a forward repeats the previous forwarder's claims unchecked. Clients MAY verify a forward against the
source event if they can access it, but MUST NOT present an unverified forward as verified. Clients MUST sanitise HTML
in both the fallback and `m.forwarded_content` as usual.

The fallback and `m.forwarded_content` can also differ, so clients and bridges that don't support this MSC may see
different content from supporting clients.

## Alternatives

Clients could strip a prefix from `body` and a wrapper from `formatted_body`, as rich reply clients did. That means
parsing two independently editable fields, and a malformed fallback can cause real content to be removed.

Storing only the original `body` and `formatted_body` would save space but lose media and custom fields.

Forwarding a forward could nest the previous forward inside `m.forwarded_content`. The event would grow with every
hop, and clients would have to unwrap it to find the original message.

## Unstable prefix

Until this MSC is accepted, implementations use `org.matrix.msc4553.forwarded` and
`org.matrix.msc4553.forwarded_content` in place of `m.forwarded` and `m.forwarded_content`. Clients SHOULD also treat
`com.famedly.app.forwarded` from [MSC2723] implementations as `m.forwarded` when reading, but MUST NOT send it. Such
events have no `m.forwarded_content`, so they are rendered from the top-level content.

[MSC2723]: https://github.com/matrix-org/matrix-spec-proposals/pull/2723
