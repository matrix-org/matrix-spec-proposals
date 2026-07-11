# MSCXXXX: Room Playlists

Matrix rooms already carry ad hoc audio and video, sent as ordinary `m.room.message` events using the
existing `m.audio`/`m.video`/`m.file` `msgtype`s. There is, however, no shared, ordered,
collectively-curated concept of "the room's playlist" distinct from scrolling the timeline looking for
media messages: no first-class way to say "here is the current queue for this room, in this order,
with this playback preference," the way `m.room.pinned_events` already gives a curated subset of the
timeline a first-class state representation.

This proposal defines a room-level state event, `m.room.playlist`, holding an ordered list of media
entries and an advisory playback-order preference, so any compliant client can render a shared queue,
a "now playing" view, or shuffle/sequential controls, without scanning the timeline for media messages
itself.

- A new state event, `m.room.playlist`, holding an ordered array of playlist entries.
- Each entry reuses the same `msgtype`/`url`/`file`/`info` schema `m.room.message` already defines for
  audio, video, and file attachments, so no new media-description schema is introduced.
- An advisory `playback` preference (sequential or random) that clients SHOULD respect by default but
  MAY override, since it's the playlist's creator's stated preference, not a hard requirement.
- The same entries/playback shape can optionally be published on a user's own global profile instead of
  (or as well as) any particular room, so a playlist can move with a user across rooms without anyone
  needing to join a room to see it.
- No new client-server or server-server API surface: entries reference existing MXC URIs (or encrypted
  file objects), exactly as messages already do, whether held in a room state event or a profile field.

## Proposal

### The `m.room.playlist` state event

A room's playlist lives at the `m.room.playlist` state event, with an empty `state_key`, the same
fixed-empty-state-key convention already used for "there is only ever one current instance of this"
room state (e.g. `m.room.topic`, `m.room.pinned_events`). Its fields:

**Mandatory**

- `entries`: an ordered array of entry objects (see Entries, below). An empty array means the playlist
  currently has no tracks queued.

**Optional**

- `playback`: `m.sequential` or `m.random`, the playlist's stated preference for how a client should
  advance through `entries`. See Playback preference, below. Absence means no preference is stated;
  clients fall back to their own default, typically sequential.

```json
{
  "type": "m.room.playlist",
  "state_key": "",
  "content": {
    "playback": "m.sequential",
    "entries": [
      {
        "entry_id": "a1b2c3",
        "msgtype": "m.audio",
        "body": "Never Gonna Give You Up.mp3",
        "url": "mxc://example.org/abc123",
        "info": {
          "mimetype": "audio/mpeg",
          "size": 4212332,
          "duration": 213000
        },
        "sender": "@alice:example.org",
        "added_ts": 1720000000000
      },
      {
        "entry_id": "d4e5f6",
        "msgtype": "m.video",
        "body": "conference-talk.mp4",
        "url": "mxc://example.org/def456",
        "info": {
          "mimetype": "video/mp4",
          "size": 104857600,
          "duration": 1800000,
          "w": 1920,
          "h": 1080
        },
        "sender": "@bob:example.org",
        "added_ts": 1720000500000
      }
    ]
  }
}
```

### Entries

Each object in `entries` describes one media file. Its fields:

**Mandatory**

- `entry_id`: an opaque string, unique within this playlist, chosen by whoever adds the entry (e.g. a
  UUID or short random string). The whole `entries` array is replaced as a unit every time the playlist
  is edited (see Potential issues, below), so a stable per-entry ID is what lets a client target a
  specific track for removal, reordering, "now playing" tracking, or reactions, without relying on
  matching its content.
- `msgtype`: one of `m.audio`, `m.video`, or `m.file`, with the same meaning as in `m.room.message`.
- `body`: same meaning as in `m.room.message`: a plain-text description, typically a filename or
  title, used as a fallback and for accessibility.
- `url` (or `file`, for an encrypted attachment): the MXC URI of the media, or its `EncryptedFile`
  object in an encrypted room, exactly as `m.room.message` already defines for these `msgtype`s.

**Optional**

- `info`: media metadata (`mimetype`, `size`, `duration`, `w`/`h`, `thumbnail_url`/`thumbnail_file`,
  etc.), exactly as `m.room.message` already defines for these `msgtype`s.
- `formatted_body`/`format`: an optional rich-text rendering of `body`, same meaning as in
  `m.room.message`.
- `sender`: the Matrix ID of the user who added this entry. RECOMMENDED: because the `entries` array
  can be edited by anyone with sufficient power level (see Security considerations, below), the outer
  state event's own `sender` only reflects whoever last touched the playlist, not who queued any given
  track.
- `added_ts`: the timestamp (milliseconds since the Unix epoch) this entry was added. RECOMMENDED, for
  the same reason as `sender`.

Reusing `m.room.message`'s existing media schema verbatim means a client's existing media handling
(thumbnailing, download, encrypted-attachment decryption) already works for playlist entries with no
new parsing logic; only the surrounding "this is a queued track, not a timeline message" context is
new.

### Playback preference

`playback` is an advisory hint, not a protocol requirement: it lets whoever curates the playlist state
a preference for how `entries` should be advanced through, without forcing every client to honor it.

- `m.sequential`: play `entries` in array order.
- `m.random`: play `entries` in a random order, ideally without repeating a track before all others
  have played.

Clients SHOULD default to respecting the stated `playback` value when first opening a room's playlist,
since that reflects the curating user's intent, but MAY let their own user override it locally (e.g. a
"shuffle" toggle in the transport controls), the same way most media players let a listener override a
playlist's stated order. A local override is just a playback choice; it does not change the room's own
`playback` state unless the user also explicitly edits it.

### Profile playlists

A playlist can also be published on a user's own global profile instead of, or as well as, any
particular room, using [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133)
(Extensible Profiles): the same `entries`/`playback` shape, set as the profile field `m.playlist`:

```json
PUT /_matrix/client/v3/profile/{userId}/m.playlist

{
  "m.playlist": {
    "playback": "m.sequential",
    "entries": [
      {
        "entry_id": "a1b2c3",
        "msgtype": "m.audio",
        "body": "Never Gonna Give You Up.mp3",
        "url": "mxc://example.org/abc123",
        "info": {
          "mimetype": "audio/mpeg",
          "size": 4212332,
          "duration": 213000
        }
      }
    ]
  }
}
```

A profile playlist moves with the user across every room they're in, and is visible to anyone who can
view their profile at all, without that viewer needing to join, or even peek, any particular room. This
is its main advantage over `m.room.playlist`: it's tied to an identity, not a container, and doesn't
depend on a room's `history_visibility` allowing peeking, or on a viewer already knowing which room to
look in.

The tradeoff is that a profile playlist gives up two things a room's playlist gets for free: live
propagation and shared editing. MSC4133 fields don't trigger state events or any other broadcast
mechanism, so viewers only see whatever was last published whenever they happen to fetch the profile,
not a live update. And only the profile owner (or their own homeserver) can write their own profile
fields, so a profile playlist is inherently one person's curated list, not a collaboratively edited
queue the way a room's playlist can be. Since it can only ever be added to by its owner, a profile
playlist's entries have no need for their own `sender`; clients MAY omit it here even though it's
RECOMMENDED for `m.room.playlist` (see Entries, above).

Because MSC4133 bounds a user's *entire* profile to 64 KiB, shared with `displayname`, `avatar_url`,
and any other custom fields, clients SHOULD treat a profile playlist as a small, curated "favorites"
list rather than a large or fast-changing queue. A room's `m.room.playlist` remains the better fit for
that.

## Potential issues

- **Editing the playlist is read-modify-write over the whole `entries` array.** State events are
  replaced wholesale, so two clients adding a track around the same time can race: whichever
  `m.room.playlist` event lands second simply overwrites the first editor's addition, unless that
  client re-reads the latest state and merges its own change in first. This is the same limitation any
  single-state-blob list already has in Matrix, since there's no server-side list-append primitive.
  Clients SHOULD re-fetch current state immediately before editing to minimize, though not eliminate,
  this race.
- **Event size limits bound how long a playlist can get.** All of `entries` lives inside one event's
  `content`, subject to the same per-event size cap (currently 65 KiB) as any other event. This
  proposal does not define a pagination or overflow mechanism. Clients SHOULD warn a user attempting to
  add a track that would push the playlist over a reasonable size; a playlist of a few hundred tracks,
  with a minimal entry shape, is still well within typical limits in practice.
- **No built-in de-duplication.** Nothing stops the same `url` being added as two different entries
  with two different `entry_id`s. This proposal considers that acceptable; deduplication, if wanted, is
  a client-side UI concern, the same way `m.room.message` doesn't deduplicate identical messages either.
- **A profile playlist has no live-update signal.** Unlike `m.room.playlist`, which propagates instantly
  to every joined (or peeking, if world-readable) client via `/sync`, MSC4133 profile fields have no
  broadcast mechanism at all (see Profile playlists, above): a viewer only sees what a fresh fetch
  returns. Clients SHOULD treat a profile playlist as something fetched on demand (e.g. when opening a
  user's profile), not something to hold open waiting for updates.
- **A room playlist and a profile playlist can drift out of sync.** Nothing ties `m.room.playlist` to
  `m.playlist`; they are two independent pieces of state that happen to describe "the same" playlist
  from a user's point of view, e.g. a user who keeps a playlist on their [MSC4501](https://github.com/matrix-org/matrix-spec-proposals/pull/4501)
  profile room and also wants it on their global profile. If a track is added to one but not the other,
  they simply diverge; this proposal defines no mechanism to link or reconcile them. Keeping both in
  sync, for a user who wants both, is entirely the responsibility of whatever client manages their
  playlist: it SHOULD write both locations on every edit if it supports publishing to both, and a user
  relying on a client that doesn't do this should expect them to disagree.

## Alternatives

- **Reuse `m.room.pinned_events`** to reference existing `m.room.message` events already carrying
  media, instead of a dedicated `m.room.playlist` state event with its own embedded entries.
  Considered, but rejected: `m.room.pinned_events` only stores an array of event IDs, so every track
  would first have to exist as an ordinary timeline message, with nowhere to attach per-entry metadata
  like `sender`/`added_ts` beyond what the original message already carries, and nowhere to store a
  room-wide `playback` preference at all. A dedicated state event with embedded entries also lets a
  playlist include media that was never independently posted to the room, e.g. curated from elsewhere
  and added directly to the queue.
- **A dedicated event type per playlist entry** (e.g. `m.playlist.item`), aggregated client-side from
  the timeline, instead of one state event holding the whole list. This would avoid the single-event
  size cap and read-modify-write race described in Potential issues, above, at the cost of needing a
  separate mechanism (redaction, or a companion "remove" event) to take a track out of the queue, and
  an explicit ordering field, since arrival order in the timeline isn't necessarily queue order once
  removals happen. This proposal favors the simpler single-state-event model for an initial version,
  given how small a typical playlist's `content` still is relative to the event size cap, but a future
  proposal could revisit this if very large or high-churn playlists turn out to be common in practice.
- **Making `playback` a strict requirement rather than an advisory preference.** Rejected because
  playback order is fundamentally a personal listening preference; forcing every listener into the same
  order regardless of their own player's shuffle setting would be a worse experience than most existing
  media players and playlist tools already provide, where a playlist's stated order is a default, not a
  mandate.
- **A closed enum of only `m.sequential`/`m.random`, instead of an open identifier space.** This
  proposal keeps `playback` as any Matrix identifier, namespaced the same way `msgtype`/`rel_type`
  values already are, rather than a hardcoded two-value enum, so future proposals can add further values
  (e.g. some "smart shuffle" convention) without needing to revise this one.
- **Only defining the room-scoped `m.room.playlist`, with no profile-level option.** Rejected: a
  playlist that only lives in one room can't move with a user across rooms, and viewing it requires
  either joining that room or it happening to be world-readable and peekable. A profile-attached option
  (see Profile playlists, above) lets a playlist function as part of a user's portable identity, at the
  cost of live updates and shared editing, both of which remain available via the room-scoped mechanism
  for anyone who wants them instead.
- **Relying on room peeking (`history_visibility: world_readable`) instead of a profile field**, for a
  playlist a user wants visible without requiring room membership. Considered, but rejected as a
  complete substitute: peeking depends on a room's own `history_visibility` setting, which a public,
  joinable room does not necessarily have, and still requires a viewer to already know which room to
  peek into. A profile field is discoverable directly from the user's account and works regardless of
  any particular room's visibility settings.

## Security considerations

- **`m.room.playlist` defaults to Moderator-level, not Admin-level, protection.** A room's
  `m.room.power_levels` only overrides specific well-known state event types, so a custom type like
  `m.room.playlist` falls back to `state_default` (50, "Moderator" in most clients) unless a room
  explicitly overrides it. A room that wants to restrict who can edit its playlist SHOULD set an
  explicit `events` override for `m.room.playlist` in `m.room.power_levels` at room-creation time.
- **Entries are self-asserted, unverified metadata about their own referenced media.** Nothing ties an
  entry's `body`/`info`/`msgtype` to the actual bytes at its `url`/`file`; a user with sufficient power
  level to edit the playlist could add an entry whose `body`/`info` describe innocuous media while
  `url` points at something else entirely, the same way an ordinary `m.room.message`'s `body` doesn't
  have to accurately describe its own attachment today either. Clients SHOULD apply the same
  content-type/size checks to playlist entries they would already apply to an ordinary media message,
  rather than trusting a claimed `mimetype` blindly.
- **No new client-server or server-server API surface.** This proposal only defines a new state event
  `type`, a new MSC4133 profile field, and a content schema built entirely from fields `m.room.message`
  already defines; it introduces no new endpoints, and no attack surface beyond what the existing
  content repository, state event, and (for the profile variant) MSC4133 profile field mechanisms
  already carry.
- **A profile playlist is public to anyone who can view that user's profile at all**, the same
  visibility model as every other MSC4133 field (see MSC4133's own Security considerations). A user
  publishing a playlist to their profile is exposing it, and the media it references, more broadly than
  one scoped to a single room's membership; clients SHOULD make this distinction clear in their UI when
  a user chooses between publishing a playlist to their profile versus a specific room.

## Unstable prefix

Until this proposal is accepted into the spec, implementations should use the following identifiers,
all under the `org.matrix.mscXXXX.` namespace:

| Stable (once accepted)   | Unstable (for now)                    |
| ------------------------- | -------------------------------------- |
| `m.room.playlist`         | `org.matrix.mscXXXX.room.playlist`     |
| `m.playlist`              | `org.matrix.mscXXXX.playlist`          |
| `m.sequential`            | `org.matrix.mscXXXX.sequential`        |
| `m.random`                | `org.matrix.mscXXXX.random`            |

The `m.playlist` profile field additionally depends on whatever unstable identifier the implementing
homeserver uses for MSC4133 support itself (e.g. some deployments currently advertise
`uk.tcpip.msc4133`/`uk.tcpip.msc4133.stable` in `/_matrix/client/versions`), and, per MSC4133's own
unstable-prefix convention for fields in the `m.*` namespace, would need to be set as
`uk.tcpip.msc4133.org.matrix.mscXXXX.playlist` until both proposals are stable. Clients should check for
MSC4133 support before relying on a profile playlist being writable or readable at all.

## Dependencies

The core `m.room.playlist` state event has no dependencies. It builds entirely on existing,
already-stable Matrix mechanisms: state events, `m.room.message`'s `m.audio`/`m.video`/`m.file` content
schema, and the content repository's encrypted attachment format.

The optional profile playlist (see Profile playlists, above) depends on
[MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133) (Extensible Profiles), which
has not been accepted into the spec at the time of writing. This dependency is not load-bearing for the
rest of this proposal: without MSC4133, `m.room.playlist` still works exactly as described; a user
simply has no way to publish a playlist independent of any specific room.
