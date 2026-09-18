# MSC4546: Circles

Voice messages give Matrix a fast, conversational way to send short audio without leaving the app.
The same desire exists for video: users often want to send a brief camera clip within the app
and play it quickly, rather than opening another app, recording it, sending, then playing it in a
media viewer.

Circles implement this. A Circle is a 1:1 video with recording and playback UX modelled on voice messages
([MSC3245]). Clients that do not implement this proposal still parse
a normal [`m.video`](https://spec.matrix.org/v1.16/client-server-api/#mvideo) event and fallback to their
existing video rendering.

## Proposal

A Circle is an [`m.room.message`](https://spec.matrix.org/v1.16/client-server-api/#mroommessage)
event with `msgtype` `m.video` whose `content` includes:

```json
"m.circle": true
```

The flag is only a rendering and UX hint. All existing `m.video` fields continue to apply. Circles
inherit `m.video` behaviour, with circular timeline rendering and the same recording and playback UX
as voice messages.

The key MUST be omitted when the video is not a Circle.
Any other value, including `false`, MUST be treated as if the key were absent.

Clients MUST ignore `m.circle` on events that are not `m.video` messages.

The recommended video resolution is 512x512. The video aspect ratio MUST be 1:1.
Clients MAY send the video in other 1:1 resolutions.

## Potential issues

Senders can set `m.circle` on a video that is not 1:1.
Receivers SHOULD still treat the event as a Circle and MAY use crop-to-fit to mitigate this.

## Alternatives

A dedicated `msgtype` (for example `m.circle`) would make the intent obvious, but unknown `msgtype`
values are often rendered poorly or hidden entirely. Annotating `m.video` preserves a working
fallback, which is the same reason voice messages are sent as annotated `m.audio`.

Putting the flag on `info` (for example `info.circle`) would mix a UX hint with file metadata.
`info` already describes the bitstream (`w`, `h`, `duration`, `mimetype`); the circle marker belongs
with other content-level annotations such as [MSC3245]'s voice marker.

For naming, I believe "Circles" is the most natural way to call this feature.
"Video messages" is easy to confuse with a normal video message.
"Video Notes" is Telegram-specific and personally doesn't sound right to me.

## Security considerations

Circles are ordinary video attachments plus a display hint. Clients MUST apply and consider the same
safeguards they already use for `m.video`, voice messages, and any other media event.

## Unstable prefix

While this proposal is unstable, implementations MUST use `org.interferolog.circle` in place of
`m.circle`:

```json
"org.interferolog.circle": true
```

After the proposal is stable, the key is `m.circle`.

## Dependencies

None.

[MSC3245]: https://github.com/matrix-org/matrix-spec-proposals/pull/3245
