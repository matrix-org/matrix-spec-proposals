# MSC4577: Soundboards for MatrixRTC calls

Users in a voice or video call sometimes want to play a short sound for
everyone: an air horn, a laugh track, a notification chime. This proposal adds
sound packs, stored the way
[MSC2545](https://github.com/matrix-org/matrix-spec-proposals/pull/2545) image
packs are, and a small message that tells the other participants of a call to
play one of them.

## Proposal

### Sound packs

#### `m.room.soundboard` state event

A sound pack is a state event of type `m.room.soundboard`. The `state_key` is a
unique identifier for the pack and is not shown to users. A room can have any
number of packs. Whoever may send state events of this type in the room may
edit its packs, by the usual power-level rules. An event with empty content
deletes the pack.

`content` has the following keys:

- `sounds`: **Required, Map[String, Object]**. A map from a shortcode to a
  [Sound object](#sound-object).
- `pack`: **Optional, Object**. A [Pack object](#pack-object).

```json
{
  "type": "m.room.soundboard",
  "state_key": "airhorns",
  "content": {
    "sounds": {
      "airhorn": {
        "url": "mxc://example.org/abcdef",
        "body": "An air horn",
        "info": {
          "mimetype": "audio/ogg",
          "size": 48213,
          "duration": 2400
        }
      }
    },
    "pack": {
      "display_name": "Air horns",
      "attribution": "Recorded by @kay:example.org"
    }
  }
}
```

Shortcodes follow the [shortcode grammar of
MSC2545](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/2545-emotes.md#shortcode-grammar):
at most 100 bytes, matching `[a-zA-Z0-9-_]+`. They do not have to be unique
across packs. Clients SHOULD enforce the grammar when creating or editing a
pack, and SHOULD still offer sounds whose shortcodes do not follow it.

#### Pack object

- `display_name`: **Optional, String**. A display name for the pack. If unset,
  it defaults to the room's name.
- `avatar_url`: **Optional, String**. The `mxc://` URI of an icon for the pack.
  If unset, it defaults to the room's avatar.
- `attribution`: **Optional, String**. The attribution for this pack.

These have the same meaning as in an MSC2545 pack object. MSC2545's `usage` is
not used, because a sound pack has only one use.

#### Sound object

- `url`: **Required, String**. The `mxc://` URI of an audio file. Entries
  without one, or with a URL that is not an `mxc://` URI, are ignored.
- `body`: **Optional, String**. A textual description of the sound, for
  display and accessibility. Clients fall back to the shortcode.
- `info`: **Optional, AudioInfo**. The existing
  [`AudioInfo`](https://spec.matrix.org/v1.18/client-server-api/#maudio)
  object from `m.audio`: `mimetype`, `size` (bytes) and `duration`
  (milliseconds). These are hints. Clients must not trust them for enforcing
  limits.

Unknown keys in any of these objects are preserved by clients that edit a
pack.

#### `m.soundboard.rooms` account data event

By default a room's packs are offered only in calls in that room. A user can
make a room's pack available in every call by adding it to the
`m.soundboard.rooms` account data event. It has the same shape and meaning as
MSC2545's `m.image_pack.rooms`:

- `rooms`: **Required, Map[String, Map[String, Object]]**. A map from room ID
  to a map from the pack's `state_key` to an empty object.

```json
{
  "rooms": {
    "!someroom:example.org": {
      "airhorns": {}
    }
  }
}
```

A user who wants sounds of their own can keep them in a pack in any room they
control, for example a private room with only themselves in it, and add that
pack here.

Clients should be aware that users may not be in a room referenced by this
event, and MAY show appropriate UX around this.

#### Space packs

Clients SHOULD offer the sound packs of a room's canonical space, if the user
is also in that space, recursively, as MSC2545 does for image packs. Care
should be taken to avoid cycles and to limit the length of the chain.

#### Pack order

Clients SHOULD offer packs in a call in this order, matching MSC2545:

1. Packs listed in `m.soundboard.rooms`.
2. Packs in the room of the call.
3. Packs in the room's canonical spaces.

### Playing a sound

A participant plays a sound by sending a play message to the other
participants of the call. The message is a JSON object:

```json
{
  "url": "mxc://example.org/abcdef",
  "shortcode": "airhorn"
}
```

- `url`: **Required, String**. The sound's `mxc://` URI.
- `shortcode`: **Optional, String**. The sound's shortcode, for display. At
  most 100 bytes.

Receivers ignore unknown keys. Messages over 1 KiB are ignored. The sender
plays the sound locally as well.

The message names the media rather than carrying audio. Every client
downloads the file (the media is shared and cacheable) and plays it locally.

The message carries no sender. A transport binding must deliver it only to the
participants of the call, and must attribute each message to the call member
who sent it, from that member's authenticated connection and not from the
message itself. A client resolves that member to a Matrix user in the same way
it does for the member's media, and uses that user for everything below:
per-user volume, per-user mute, and rate limiting. Because the identity is not
taken from the message, a participant cannot make a sound appear to come from
someone else. A message that the transport cannot attribute to a call member
is ignored.

This proposal defines one binding, for LiveKit. A future MatrixRTC transport
needs only to define how it delivers a small, reliable, attributed message to
the call's participants.

#### LiveKit binding

On a MatrixRTC call that uses the LiveKit transport
([MSC4195](https://github.com/matrix-org/matrix-spec-proposals/pull/4195)),
the play message is sent as a reliable LiveKit data message with the topic
`m.soundboard.play`, whose payload is the message encoded as UTF-8 JSON.
LiveKit does not deliver data messages back to their sender.

The sender is the participant the SFU reports for the data message. Its
identity comes from the sender's access token and is the same identity their
audio and video tracks carry. A data message with no participant (for example
one injected through the SFU's server API) is ignored.

Sending needs the `video.canPublishData` grant in the participant's LiveKit
access token. See [Potential issues](#potential-issues).

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
  prefetch the sounds of the packs offered in the call.
- **Data publishing permission:** on LiveKit, sending needs the
  `video.canPublishData` grant.
  [MSC4576](https://github.com/matrix-org/matrix-spec-proposals/pull/4576)
  proposes that the service issuing those tokens leave it off unless a
  MatrixRTC application needs it. This proposal is such an application, so
  where it is in use the service SHOULD grant `canPublishData` to participants
  who may publish media (`canPublish`). Without the grant the message cannot
  be sent and the soundboard does not work. Receiving needs no extra grant.

## Alternatives

### Publish the sound as an audio track

As screen-share audio is. It works for clients with no soundboard support,
but costs bandwidth and an encode for every play, goes through the voice
codec, and cannot be volume-adjusted by the listener apart from the sender's
voice without a second track per sender.

### Send the play message as a room event

A room event per play would work on every transport, and the sender would be
the event's sender. It was rejected because it fits a transient, call-scoped
cue badly:

- **Persistence:** every press becomes a permanent event in the room's
  history, replicated to every server in the room, including servers with no
  one in the call.
- **Audience:** a room event goes to every member of the room, not only to
  the call's participants. Members who are not in the call receive, and may
  be notified about, every sound.
- **Latency:** delivery goes through the sender's homeserver, federation, and
  each receiver's sync, rather than the call's own transport, which carries
  the call's media with the call's latency.
- **Rate limits:** homeserver send limits are tuned for chat. Ordinary
  soundboard use can hit them.
- **Moderation:** spam lands in the timeline and has to be redacted, rather
  than ending with the call.

To-device messages avoid the persistence and the audience, but need one
message per participant device and add the same homeserver latency.

### Store sounds in MSC2545 image packs with a new `usage`

A sound could be an entry in an `m.room.image_pack` pack whose `usage` is a
new value such as `soundboard`, with `AudioInfo` in place of `ImageInfo`.
MSC2545 says clients SHOULD use `usage` to decide where to offer a pack, so in
principle such a pack would appear in no emoji or sticker picker.

In practice, MSC2545 also says an absent or empty `usage` means all usages,
and most clients reach that case for a list of only unknown values. A pack
with `"usage": ["soundboard"]`, put in a room as both `m.room.image_pack` and
`im.ponies.room_emotes`, was tested in November 2026:

| Client | Result | Checked by |
| --- | --- | --- |
| Cinny | Offered as emotes and stickers, as broken images | Live and source |
| Sable | Offered as stickers and emotes, as broken images | Live and source |
| FluffyChat (matrix-dart-sdk) | Not offered | Live and source |
| Nheko (mtxclient) | Offered, with no image. Editing the pack drops the unknown usage on save | Live and source |
| Commet | Offered, with no image | Live and source |
| NeoChat | Not offered | Source |
| Element Web, Element X | No image pack support | Source |

Four of the six clients with image pack support would offer every sound as a
broken emote and sticker, and one would destroy the `usage` when the pack is
edited. Separate event types avoid this. A future MSC could change MSC2545 so
that a `usage` list with only unknown values means no known usage, after which
sound packs could move into image packs.

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
- **The message is encrypted only if the transport encrypts it.** On LiveKit,
  data messages are encrypted when the client creates its `Room` with the
  `encryption` option (the older `e2ee` option alone covers only media
  tracks). A client in an encrypted MatrixRTC call should set it, so the SFU
  operator cannot see which media was referenced. In a call that is not
  encrypted the message is plaintext. In an encrypted call a client must
  ignore a message that arrives unencrypted, since LiveKit passes such a
  packet through and it could have been injected with any sender attached.

  The media itself is an ordinary, unencrypted upload, so the homeserver can
  see it regardless. Sounds that are private should not be used. A future
  version could use encrypted attachments (`file`) for the media.

- **Attribution.** Trust in the sender rests on the transport's attribution
  of the message (see [Playing a sound](#playing-a-sound)), exactly as it
  does for the call's audio and video. Clients must not read a sender from
  the message.
- **Abusive sounds in packs.** As with MSC2545, the administrator of a pack
  that users have added to `m.soundboard.rooms` can later replace its sounds.
  Clients should show where a pack comes from, and users can remove the pack.
  Moderation tools that apply to state events apply to packs.

## Unstable prefix

Until this proposal is accepted, implementations use:

| Stable                | Unstable                      |
| --------------------- | ----------------------------- |
| `m.room.soundboard`   | `moe.crafty.room_soundboard`  |
| `m.soundboard.rooms`  | `moe.crafty.soundboard_rooms` |
| `m.soundboard.play`   | `moe.crafty.soundboard`       |

## Dependencies

- [MSC4576](https://github.com/matrix-org/matrix-spec-proposals/pull/4576)
  (no data publishing on the LiveKit transport unless needed), which the
  LiveKit binding needs servers to relax for calls that use it.

## Reference implementation

Zam (<https://github.com/az4521/Zam>) implements this proposal. The pack
handling is in `src/lib/matrix/soundboard.ts` and
`src/lib/utils/soundboard.ts`; sending, receiving and playback are in
`src/lib/matrix/livekitCall.ts`.
