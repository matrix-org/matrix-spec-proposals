# MSC4577: Soundboards for MatrixRTC calls

Users in a voice or video call sometimes want to play a short sound for
everyone: an air horn, a laugh track, a notification chime. This proposal adds
sound packs, stored the way MSC2545 image packs are, and a small message that
tells the other participants of a call to play one of them.

## Proposal

### Sound packs

A sound pack has the same shape as an MSC2545 image pack, with `sounds` in
place of `images`.

```json
{
    "pack": {
        "display_name": "Air horns"
    },
    "sounds": {
        "airhorn": {
            "url": "mxc://example.org/abcdef",
            "info": {
                "mimetype": "audio/ogg",
                "size": 48213,
                "duration": 2.4
            }
        }
    }
}
```

- `sounds` maps a short name to a sound. Names are 1 to 48 characters:
  letters, digits, spaces and `_ . + -`. They are shown to users and are not
  required to be unique across packs.
- `url` is the `mxc://` URI of an audio file. It is required. Entries without
  one, or with a URL that is not an `mxc://` URI, are ignored.
- `info.mimetype`, `info.size` (bytes) and `info.duration` (seconds) are
  optional hints. Clients must not trust them for enforcing limits.
- `pack.display_name` names the pack. Unknown keys are preserved by clients
  that edit a pack.

There are two places a pack can live:

- **User pack:** account data of type `m.soundboard`. One pack per user, for
  sounds they can use in any call.
- **Room pack:** a state event of type `m.room.soundboard`, with the pack name
  as the state key. Rooms and spaces can have any number of packs. Whoever may
  send state events of this type in the room may edit its packs, by the usual
  power-level rules. An event with empty content deletes the pack.

A client offers, in a call in a given room, the user's pack, the room's packs,
and the packs of the spaces the room is in (by `m.space.parent` and
`m.space.child`), in that order. Unlike MSC2545 there is no equivalent of
`m.image_pack.rooms`: packs from rooms the user is not in are not offered.
Clients may let users copy a sound into their own pack by reference, without
re-uploading the media.

### Playing a sound in a call

A participant plays a sound by sending a message to the other participants of
the call. On a MatrixRTC call that uses LiveKit (MSC4195), this is a reliable
LiveKit data message with the topic `m.soundboard.play` and a UTF-8 JSON
payload:

```json
{
    "v": 1,
    "url": "mxc://example.org/abcdef",
    "name": "airhorn"
}
```

- `v` is the message version, currently `1`. Receivers ignore other versions.
- `url` is the sound's `mxc://` URI.
- `name` is the sound's name, for display. Optional, at most 48 characters.

Payloads over 1 KiB are ignored. The sender plays the sound locally as well,
because senders do not receive their own data messages.

The message names the media rather than carrying audio. Every client downloads
the file (the media is shared and cacheable) and plays it locally.

### Identifying the sender

The payload deliberately carries no sender. The sender is the participant the
transport attributes the message to: with LiveKit, the participant the SFU
reports for the data message, whose identity comes from the sender's
authenticated connection and is the same `@user:server:DEVICE` identity their
audio and video tracks carry. A client resolves it to a Matrix user in the same
way it does for a participant's tracks, and uses that user for everything
below: per-user volume, per-user mute, and rate limiting. Because the identity
is not taken from the payload, a participant cannot make a sound appear to come
from someone else. A message with no attributed sender (for example one
injected through the SFU's server API) is ignored.

### Receiving

On a valid message a client fetches the media with its usual authenticated
media request and plays it, mixed into the call's audio output. To keep the
feature from being used to harass or crash other clients, receivers should:

- accept only `mxc://` URIs, and fetch them from their own homeserver like
  any other media, never from a URL in the message;
- refuse files over a size limit (suggested: 1 MiB) and clips over a duration
  limit after decoding (suggested: 15 seconds);
- limit how fast one sender can trigger sounds (suggested: at most one per
  400 ms, and at most 3 playing at once per sender);
- drop sounds from senders the user has muted in the call, and while the user
  is deafened or has the call's output muted;
- treat undecodable media as an error to ignore, not to report to the sender.

Senders should apply the same size and duration limits when a user adds a
sound.

### Volume

How loud a sound is, is entirely the listener's choice. This proposal sends no
volume. A client is expected to let a user set, for each other participant, a
soundboard volume that is separate from that participant's voice volume, and to
apply the call's output volume as well. This is the main reason the sound is
played locally from a reference instead of being sent as audio: a published
audio track would reach each listener mixed in with, and at the volume of, the
sender's voice.

## Potential issues

- **Support:** only clients that implement this play the sound. Others in the
  call hear nothing and see nothing. There is no fallback.
- **Cost:** each participant downloads each distinct sound once. Large calls
  with many distinct sounds put load on the media repository of the sender's
  homeserver, and on remote homeservers' federation, since the media is
  fetched by every participant's own server. The size limit bounds this.
- **Latency:** the first play of a sound costs a download before it can be
  heard, so it arrives later than the sender's own playback. Clients may
  prefetch the sounds a participant is likely to use.
- **Data publishing permission:** sending needs the `video.canPublishData`
  grant in the participant's LiveKit access token. MSC4576 proposes that the
  service issuing those tokens leave it off unless a MatrixRTC application
  needs it. This proposal is such an application, so where it is in use the
  service SHOULD grant `canPublishData` to participants who may publish media
  (`canPublish`). Without the grant the message cannot be sent and the
  soundboard does not work. Receiving needs no extra grant.
- **Not tied to LiveKit in principle:** the payload does not depend on LiveKit,
  but this proposal only specifies the transport for LiveKit-based
  MatrixRTC calls. Other transports would need their own binding.

## Alternatives

- **Publish the sound as an audio track** (as screen-share audio is). It works
  for clients with no soundboard support, but costs bandwidth and an encode
  for every play, goes through the voice codec, and cannot be volume-adjusted
  apart from the sender's voice by the listener without a second track per
  sender.
- **Send the sound as a Matrix event** (room event or to-device message).
  Matrix events are too slow and too persistent for a transient, interactive
  cue, would clutter the timeline if sent to the room, and to-device messages
  would need one per participant and device.
- **Store sounds as MSC2545 image packs** with a new `usage` value. Clients
  that ignore `usage` would render the audio as broken images, and the
  info fields differ. Separate event types avoid both.
- **Single global pack type shared with images**: rejected for the same
  reasons.

## Security considerations

- **Sender-controlled fetches.** The sender chooses which media every
  participant's client fetches and decodes. Receivers must only fetch
  `mxc://` references through their own homeserver, enforce size and duration
  limits, and never act on `info` as trusted. The media is decoded by the
  platform's audio decoder, which should be treated as an attack surface for
  malformed files.
- **Loudness and spam.** A malicious participant can play loud or repeated
  sounds. Rate limits, per-participant mute, and the listener-side volume cap
  limit the effect. A client may also apply a limiter to the mixed output.
- **The message is encrypted only if the LiveKit room is.** LiveKit encrypts
  data messages when the client creates its `Room` with the `encryption`
  option (the older `e2ee` option alone covers only media tracks). A client
  in an encrypted MatrixRTC call should set it, so the SFU operator cannot
  see which media was referenced. In a call that is not encrypted the message
  is plaintext. In an encrypted call a client must ignore a message that
  arrives unencrypted, since LiveKit passes such a packet through and it
  could have been injected with any sender attached.

  The media itself is an ordinary, unencrypted upload, so the homeserver can
  see it regardless. Sounds that are private should not be used. A future
  version could use encrypted attachments (`file`) for the media.

- **Attribution.** Trust in the sender rests on the SFU's attribution of the
  data message (see "Identifying the sender"), exactly as it does for the
  call's audio and video tracks. Clients must not read a sender from the
  payload.
- **Content.** Packs in a room or space are content the room's members chose
  to share. Clients should show where a pack comes from, and moderation tools
  that apply to state events apply to packs.

## Unstable prefix

Until this proposal is accepted, implementations use:

| Stable              | Unstable                     |
| ------------------- | ---------------------------- |
| `m.soundboard`      | `moe.crafty.soundboard`      |
| `m.room.soundboard` | `moe.crafty.room_soundboard` |
| `m.soundboard.play` | `moe.crafty.soundboard`      |

The unstable names are what Zam 1.40.0 and later write and read. No data
moves between them automatically when the stable names are adopted.

## Dependencies

- MSC2545 (image packs), for the shape of a pack and the idea of per-room and
  per-user packs.
- MSC4195 (MatrixRTC using LiveKit backend), for the call transport.
- MSC3401 / MSC4143 (MatrixRTC), for what a call is.
- MSC4576 (no data publishing on the LiveKit transport unless needed), which
  this proposal needs servers to relax for calls that use it.

## Reference implementation

Zam implements this at version 1.40.0 and later
(<https://github.com/az4521/Zam>). The pack handling is in
`src/lib/matrix/soundboard.ts` and `src/lib/utils/soundboard.ts`; sending,
receiving and playback are in `src/lib/matrix/livekitCall.ts`.
