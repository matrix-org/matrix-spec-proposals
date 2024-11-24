# MSC4231: Backwards compatibility for media captions

## Problem

[MSC2530](https://github.com/matrix-org/matrix-spec-proposals/pull/2530) introduced the ability to use the `body` field
on file transfers as a caption.  This merged and was shipped in Matrix 1.10, and we're now seeing more clients sending
captions in the wild.

Unfortunately, any client which is not "caption-aware" (i.e. has yet to implement
[MSC2530](https://github.com/matrix-org/matrix-spec-proposals/pull/2530) or Matrix 1.10) does not know to display the
`body` field as a caption - and so these messages effectively get silently dropped, fragmenting Matrix as a
communication medium.  Given captions typically contain as much important information as any other message, this can
result in bad communication failures, and a very negative perception of Matrix's reliability.

We should have specified a means of backwards compatibility to avoid breaking communication between newer and older
clients during the window in which we wait for clients to upgrade to Matrix 1.10.

## Proposal

Clients should send a separate `m.room.message` event after the captioned media, including the caption as the body,
and replying to the media event.  This is referred to as a caption fallback event.

The content block of the caption fallback event includes an `m.caption_fallback: true` field, so that caption-aware
clients do not display this event, instead displaying the media event's `body` field as a caption per
[MSC2530](https://github.com/matrix-org/matrix-spec-proposals/pull/2530).

However, caption-unaware clients will display the event as a reply to the media and so avoid discarding the contents of
the caption, while associating it visually with the original media via the reply.

If a user on a caption-aware client edits their caption, their client should update both the media event and the caption
fallback with the edit.

If a user on a caption-aware client redacts their media, their client should redact its caption fallback too.

If a user on a caption-unaware client edits or redacts a caption fallback sent on a caption-aware client, then the
fallback will drift out of sync with the caption on the media event - see Outstanding Issues below.

The event contains an `m.relates_to` field of type `m.caption_fallback` in order to associate the fallback to the media
event, and so make it easy to locate when a caption-aware client applies edits or redactions.  This also stops clients
trying to start threads from the caption fallback, as the server will reject the invalid thread.  The end result looks
like this:

```json
  "type": "m.room.message",
  "content": {
    "body": "Caption text",
    "msgtype": "m.text",
    "m.relates_to": {
        "event_id": "$(some image event)",
        "rel_type": "m.caption_fallback",
		"m.in_reply_to": {
	        "event_id": "$OYKwuL..."
	    },
    }
  },
```

If non-caption-aware users reply to a caption fallback, then caption-aware clients should display the media event
as the event being replied to.

## Outstanding issues

If a user on a caption-unaware client edits a caption fallback sent on a caption-aware client, then this change
will not be visible to caption-aware clients, causing inconsistent history between caption-aware and unaware clients.

If a user on a caption-unaware client redacts a caption fallback sent on a caption-aware client, then the caption in
the media event won't be redacted, potentially leaking the redacted content.

Clients or bridges that are caption-aware but not MSC4231-aware capable will display or transport the text content
twice, displaying double content to the user.

## Potential issues

It's a bit ugly and redundant to duplicate the caption in the fallback event as well as the media event.  However, it's
way worse to drop messages.

The fact that caption fallback events will be visible to some clients and invisible to others might highlight unread
state/count problems.  However, given we need to handle invisible events already, it's not making the problem worse -
and in fact by making it more obvious, might help fix any remaining issues in implementations.

## Alternatives

Captions should be provided by extensible events.  However, until extensible events are fully rolled out, we're stuck
with fixing up the situation with [MSC2530](https://github.com/matrix-org/matrix-spec-proposals/pull/2530), and this is
a problem which is playing out right now on the public network.

Alternatively, we could ignore the issue and go around upgrading as many clients as possible to speak
[MSC2530](https://github.com/matrix-org/matrix-spec-proposals/pull/2530).  However, this feels like incredibly bad
practice, given we have a trivial way to provide backwards compatibility, and in practice we shouldn't be forcing
clients to upgrade in order to avoid losing messages when we could have avoided it in the first place.

This has ended up combining both [MSC2530](https://github.com/matrix-org/matrix-spec-proposals/pull/2530) and
[MSC2529](https://github.com/matrix-org/matrix-spec-proposals/pull/2529). There's a world where the fallback event could
be the primary source of truth for the caption, and meanwhile the field on the media event be the 'fallback' for the
convenience of bridges.

Alternatively, we could change to sending captions entirely as relations, as in
[MSC2529](https://github.com/matrix-org/matrix-spec-proposals/pull/2529), and require bridges to wait for the caption
event (if flagged on the media event) before they send on the media event.  This would avoid needing a dedicated
caption fallback event - as the caption would have its own event anyway.  It would also avoid the risk of edits
and redactions getting out of sync between the media event and the caption fallback.  **This feels like it might
be a preferable approach, given the outstanding issues above**.  It does however travel in the opposite direction to
extensible events (where the caption would be a mixin on the media event).

## Security considerations

The caption in the fallback may not match the caption in the media event, causing confusion between caption-aware and
caption-unaware clients.  From a trust & safety perspective, the caption in the fallback might contain abusive content
not visible to human moderators because their caption-aware clients hide the fallback (and vice versa, for
caption-unaware clients).

Sending two events (media + caption) in quick succession will make event-sending rate limits kick in more rapidly. In
practice this feels unlikely to be a problem.

## Unstable prefix

`m.caption_fallback` would be `org.matrix.msc4231.caption_fallback` until this merges.

## Dependencies

None, given [MSC2530](https://github.com/matrix-org/matrix-spec-proposals/pull/2530) has already merged.
