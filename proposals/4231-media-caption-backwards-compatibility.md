# MSC4231: Backwards compatibility for media captions

## Problem

MSC2530 introduced the ability to use the `body` field on file transfers as a caption.  This merged and was shipped
in Matrix 1.10, and we're now seeing more clients sending captions in the wild.

Unfortunately, any client which is not "caption-aware" (i.e. has yet to implement MSC2530 or Matrix 1.10) does not know
to display the `body` field as a caption - and so these messages effectively get silently dropped, fragmenting Matrix
as a communication medium.  Given captions typically contain as much important information as any other message, this
can result in bad communication failures, and a very negative perception of Matrix's reliability.

We should have specified a means of backwards compatibility to avoid breaking communication between newer and older
clients during the window in which we wait for clients to upgrade to Matrix 1.10.

## Proposal

Clients should send a separate `m.room.message` event after the captioned media, including the caption as the body.

The content block of this mesage also includes an `m.caption_fallback: true` field, so that caption-aware clients do not
display this event, instead displaying the media event's `body` field as a caption per MSC2530.

However, caption-unaware clients will display the event and so avoid discarding the contents of the caption.

## Potential issues

It's a bit ugly and redundant to duplicate the caption in the fallback event as well as the media event.  However, it's
way worse to drop messages.

The fact that caption fallback events will be visible to some clients and invisible to others might highlight unread
state/count problems.  However, given we need to handle invisible events already, it's not making the problem worse -
and in fact by making it more obvious, might help fix any remaining issues in implementations.

## Alternatives

Captions should be provided by extensible events.  However, until extensible events are fully rolled out, we're stuck
with fixing up the situation with MSC2530.

Alternatively, we could ignore the issue and go around upgrading as many clients as possible to speak MSC2530.  However,
this feels like incredibly bad practice, given we have a trivial way to provide backwards compatibility, and in
practice we shouldn't be forcing clients to upgrade in order to avoid losing messages when we could have avoided it in
the first place.

## Security considerations

The caption in the fallback may not match the caption in the media event, causing confusion between caption-aware and
caption-unaware clients.

Sending two events (media + caption) in quick succession will make event-sending rate limits kick in more rapidly. In
practice this feels unlikely to be a problem.

## Unstable prefix

`m.caption_fallback` would be `org.matrix.msc4231.caption_fallback` until this merges.

## Dependencies

None, given MSC2530 has already merged.
