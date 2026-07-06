# MSC4501: Rooms as Social Media Pages

*Note: this proposal is a spiritual successor to
[MSC3639: Matrix for the Social Media Use Case](https://github.com/Henri2h/matrix-doc/blob/henri2h-matrix-for-social-media/proposals/3639-matrix-for-the-social-media-use-case.md),
which has been abandoned. It keeps MSC3639's core idea, dedicated room types for social-media-style
profiles and groups, but narrows and simplifies the rest: it drops the bespoke comment event type in
favor of Matrix's own thread relations, reuses `m.room.message`'s content schema directly for posts
instead of defining a new one, and adds a profile-discoverability mechanism and a phased migration
plan that MSC3639 did not cover.*

Matrix has no standardized convention for building a social-media-style application (one organized
around personal profiles, group pages, a following/discovery model, and an aggregated "feed") on top
of rooms and events.

This proposal defines a small, focused set of conventions intended to be the common ground any Matrix
client can build a social media experience on top of:

- Two new room types for the two kinds of "pages" a social network needs (personal profiles, and
  groups/pages with no single owner).
- A profile field that lets any client discover which room is a given user's profile, plus a way to
  discover new profiles/groups in general via the existing public room directory.
- Room membership doubling as "following", with no new event needed to represent it.
- A post event type that is structurally identical to `m.room.message`, so existing message-handling
  code can be reused with no new parsing logic.
- A minimal, single mechanism for reposts, boosts, retweets, and quote-posts.
- Reusing the existing `m.reaction` mechanism for "liking" a post, rather than a new event type.
- Guidance for how a client builds a "feed" out of these rooms.
- A phased rollout plan for when clients should treat `m.room.message` as an interchangeable stand-in
  for a real post, so that the ecosystem doesn't have to flag-day cut over and break interoperability
  with clients that haven't adopted this MSC yet.

## Proposal

### Terminology

This proposal uses "post" to mean a piece of social-media content submitted to a profile or group (the
equivalent of a tweet/X post, a Bluesky post, or a Facebook status update), as distinct from a "message"
sent in an ordinary Matrix room (a chat message). Structurally, under this proposal, a post is simply a
message-shaped event sent into a room of a particular type: the distinction is about the room and
event *type*, not the content shape.

### Profile rooms

A new room type, `m.social.profile`, set via the existing `type` field of the room's `m.room.create`
event content (the same generic room-type mechanism `m.space` already uses):

```json
{
  "creator": "@alice:example.org",
  "room_version": "11",
  "type": "m.social.profile"
}
```

A profile room represents a single person's social media profile: a place other users join (follow)
to see that person's posts and interact with them (reply, react, repost). This is the Matrix analogue
of a personal profile/timeline on X, Bluesky, or a Fediverse instance.

A profile room's display name, avatar, topic, and banner image are set with the ordinary
`m.room.name`, `m.room.avatar`, `m.room.topic`, and `m.room.banner` (see
[MSC4221](https://github.com/matrix-org/matrix-spec-proposals/pull/4221); see Dependencies) state
events, same as any other room. There is no new state event for "profile bio" or similar; the room's
existing metadata *is* the profile's metadata.

This proposal does not mandate how a client enforces "single ownership" of a profile room (e.g., via
power levels restricting who can post); that is left to the creating client's own conventions, the
same way it already is for any other room today.

### Profile/Group discoverability

A new user profile key, `m.social.profile_room_id`, whose value is the room ID of the user's profile
room:

```json
PUT /_matrix/client/v3/profile/{userId}/m.social.profile_room_id

{ "m.social.profile_room_id": "!theirprofileroom:example.org" }
```

This relies on [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133) (Extensible
Profiles), which is what makes arbitrary per-key profile fields like this possible, see Dependencies.

Setting this field ties a user's Matrix account directly to their profile room, the same way
`avatar_url` and `displayname` are already discoverable from any account, without needing a directory
service, a room alias convention, or a shared space to find it. It also gives a user a clean way to:

- Change which room represents their profile (e.g. starting over), by simply updating the pointer, and
- Explicitly disassociate a room from their profile (without leaving the room, redacting anything, or
  otherwise disrupting it) by clearing the field.

A room being of type `m.social.profile` does **not** by itself mean it is "the" official profile of
its creator. `m.social.profile_room_id` is the authoritative signal a client should use to decide
"this is user X's current profile." A profile-typed room's own type and creator are only a secondary,
best-effort fallback signal (useful for legacy clients, or while this field hasn't propagated yet), not
a substitute for it.

`m.social.profile_room_id` only helps discover *a specific person's* profile once you already know who
you're looking for. To discover new profiles and groups more generally, this proposal relies on the
public room directory: profile and group rooms can be published to a server's room directory (via the
existing `PUT /_matrix/client/v3/directory/list/room/{roomId}` visibility mechanism, same as any other
publishable room), and the directory search endpoint (`POST /_matrix/client/v3/publicRooms`)
already supports filtering results by room type via its `filter.room_types` field (added by
[MSC3827](https://github.com/matrix-org/matrix-spec-proposals/pull/3827), which has already been
merged into the stable spec). A social media client can therefore let a user browse or search for new
profiles/groups to follow simply by querying the directory with
`filter.room_types: ["m.social.profile"]` or `["m.social.group"]`, without needing any new
server-side mechanism of its own.

### Following

Matrix's own room membership is used to represent "following": joining a profile or group room *is*
following it, with no separate follow/subscription event needed. A room's member count is therefore
also its follower count: clients can read it directly off the room (e.g. via `m.room.member` state, or
a server-provided summary/heroes count) without any new counter or state event.

For a profile room specifically, clients SHOULD subtract the profile's own owner (its creator) from the
displayed follower count, so the owner isn't counted as following themself just by virtue of being a
member of their own profile room. Group rooms have no single owner, so no such subtraction applies:
every member of a group room, including whoever created it, counts toward its member/follower count.

### Group rooms

A new room type, `m.social.group`, using the same mechanism as profile rooms:

```json
{
  "creator": "@alice:example.org",
  "room_version": "11",
  "type": "m.social.group"
}
```

A group room represents a shared social media space where multiple people post and interact with each
other's posts, with no single owner implied: the Matrix analogue of an X Community or a public
Facebook Page. As with profile rooms, `m.room.name`/`m.room.avatar`/`m.room.topic`/`m.room.banner`
carry the group's displayed metadata, and posting/moderation permissions are governed by ordinary power
levels.

### Posts

A new event type, `m.social.post`. Its content is **structurally identical to `m.room.message`**:
same `msgtype`, `body`, `formatted_body`, media fields, etc. It is not a new content schema, only a
different top-level event `type`:

```json
{
  "type": "m.social.post",
  "content": {
    "msgtype": "m.text",
    "body": "Hello, Social Matrix!"
  }
}
```

Reusing `m.room.message`'s schema verbatim means a compliant client's existing message
composing/rendering code (every `msgtype`, media attachment, formatted body, etc.) already works for
posts with zero new parsing logic; only the event `type` used to distinguish "this is a post" from
"this is an ordinary message" is new. Replies to a post use the existing `m.thread` relation
(`m.relates_to` with `rel_type: "m.thread"`) exactly as they would for a threaded reply to any other
event. This proposal does not define a separate "comment" event type, unlike MSC3639.

### Reposting / Boosting / Retweeting / Quote Posting

To mark a post as a repost of another post, its content includes an `m.social.repost_of` block, with
the outer `body` holding either the reposting user's own commentary (a quote-post) or a permalink to
the reposted event (a boost); see below for which.

`m.social.repost_of` contains the `event_id` and `room_id` of the original post, and a copy of its
entire `content` at the time of reposting, not just `body`: `formatted_body`, `format`, media fields
(`url`, `file`, `info`, etc.), and any other key present on the original event's `content` are all
copied in as-is, so a repost of, say, an image or a rich-formatted post renders identically to how the
original was authored, not just as a plain-text stand-in.

The content is embedded (rather than requiring viewers to fetch the original event) because the person
viewing a repost in their feed may not share a room with the original poster at all, e.g., reposting a
post from a public group into your own profile, seen by followers who aren't members of that group.
Embedding the content guarantees the repost is renderable, including any media it contains, without the
viewer's client needing to join or peek the original room. Clients SHOULD still attempt to resolve the
live original event (via `event_id` + `room_id`) where accessible, to support "view original", live
reaction counts, or detecting that the original has since been edited or redacted, falling back to the
embedded content when the original isn't reachable.

**Quote-posting** is a repost with the reposting user's own added commentary in the *outer* post's
`body`, with the quoted post held entirely inside `m.social.repost_of`:

```json
{
  "type": "m.social.post",
  "content": {
    "msgtype": "m.text",
    "body": "This is exactly what I was talking about:",
    "m.social.repost_of": {
      "event_id": "$original:example.org",
      "room_id": "!originalroom:example.org",
      "content": {
        "msgtype": "m.text",
        "body": "This is the original post being reposted",
        "format": "org.matrix.custom.html",
        "formatted_body": "This is the <b>original</b> post being reposted"
      }
    }
  }
}
```

**Boosting/Retweeting** is the same structure with no added commentary. Rather than an empty (or
absent) outer `body`, the outer `body` MUST contain only a permalink: a `matrix.to` URI
([MSC1704](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/1704-matrix.to-permalinks.md))
or a `matrix:` URI
([MSC2312](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/2312-matrix-uri.md)),
pointing at the same event referenced by `m.social.repost_of`:

```json
{
  "type": "m.social.post",
  "content": {
    "msgtype": "m.text",
    "body": "https://matrix.to/#/!originalroom:example.org/$original:example.org",
    "m.social.repost_of": {
      "event_id": "$original:example.org",
      "room_id": "!originalroom:example.org",
      "content": {
        "msgtype": "m.text",
        "body": "This is the original post being reposted"
      }
    }
  }
}
```

A permalink is used instead of an empty string so that a client with no support for this proposal at
all (one simply rendering the event as a plain `m.room.message`, since `body` is always a valid
message body) shows a normal, clickable link to the boosted post rather than a blank message bubble
that looks like a sending failure or a malformed event. Clients MAY additionally send a
`formatted_body` containing the same link as an HTML anchor, for nicer rendering in clients that
support formatted bodies but not this proposal.

A boost and a quote-post are therefore still the same event shape; what distinguishes them is whether
the outer `body` is *only* a permalink to the reposted event, or contains anything else. A compliant
client detects a boost by checking, for any post with an `m.social.repost_of` block, whether `body`
(trimmed of surrounding whitespace) parses as a `matrix.to`/`matrix:` permalink whose room and event
match `m.social.repost_of`'s `room_id`/`event_id` (a body that doesn't parse, or points elsewhere,
means the sender meant it as actual commentary (a quote-post) even if that commentary happens to
look like a URI). On a detected boost, the client SHOULD NOT render the literal `body` as commentary;
instead it SHOULD render something like "Alice reposted Bob's post" above the embedded repost content,
naming both the user who reposted and the original post's author. No new
event type is needed to distinguish a boost from a quote-post; this deliberately avoids a combinatorial
explosion of near-identical event types for what is fundamentally one relationship (this post reshares
that post, with or without commentary).

### Liking

Posts can be reacted to with any `m.reaction` event, the same as messages in any other Matrix room
today. This proposal does not define a new event type for "liking" a post. Instead, clients SHOULD
treat an `m.reaction` whose `key` is "👍" as a like: showing it in a dedicated like count/button rather
than (or in addition to) the room's normal reaction display, incrementing a "like" affordance when the
current user has sent one, and so on.

A dedicated `m.social.like` event type was considered and rejected: it would add a new event type that
carries no information a plain `m.reaction` doesn't already carry, since "reacting with 👍" and "liking"
are the same user intent for the purposes of this proposal. The one real tradeoff is that a client
cannot distinguish "this user actually meant to *like* the post" from "this user just happened to react
with a thumbs-up emoji". This proposal considers that an acceptable ambiguity, given the alternative is
an entire new event type whose only job is to disambiguate an edge case most users will never notice.
Using the standard `m.reaction`/`m.annotation` relation also means a like sent by a compliant client is
still a completely ordinary, renderable reaction to any non-compliant Matrix client, and a 👍 reaction
sent by a non-compliant client is automatically recognized as a like by compliant ones, keeping the
whole feature interoperable for free, the same rationale as
[reusing `m.room.message` for posts](#handling-mroommessage-in-social-rooms).

### Feeds

Constructing a "feed" is a client-side behavior, not a new room or event type. A client builds a
user's feed by walking every room the user has joined that is of type `m.social.profile` or
`m.social.group`, and merging their `m.social.post` events (see Phased rollout, below, for
`m.room.message`) into a single timeline sorted by timestamp.

Clients MAY additionally let a user opt in to including other, non-social-typed rooms in their feed,
for cases where a room has organically become a source of "posts" a user wants to follow without
formally reclassifying it. This is a client-local preference, not a protocol-level concept; this
proposal does not define a state or account data event for it, leaving it to individual client
implementations (which may already have their own account-data-backed settings sync).

### Handling `m.room.message` in social rooms

`m.social.post` will not be supported by every Matrix client immediately, and profile/group rooms are
ordinary rooms that any Matrix client, compliant with this MSC or not, can already join and post
`m.room.message` events into. To preserve interoperability with non-compliant clients during rollout,
this proposal defines three phases for how a compliant client should treat `m.room.message` events
found in `m.social.profile`/`m.social.group` rooms:

- **Phase 1 (initial rollout).** Compliant clients render `m.room.message` and `m.social.post`
  identically in the feed. When composing a post, clients default to sending `m.room.message`, with an
  option to send `m.social.post` instead. This maximizes compatibility: any existing Matrix client,
  compliant or not, can already fully participate in a profile/group room's content as ordinary
  messages, while the new type is introduced.
- **Phase 2 (majority adoption).** Once a majority of active Matrix users report using at least one
  MSC4501-compliant client, compliant clients should switch their default posting behavior to send
  `m.social.post`, with an option to fall back to `m.room.message`. Rendering in the feed is unchanged
  from Phase 1; both event types are still shown identically. (This proposal does not define how
  "majority of active users" is measured; that is left to the ecosystem and spec core team to judge,
  the same way other adoption-gated transitions in Matrix already are.)
- **Phase 3 (post-migration).** Once a majority of posts sent by compliant clients use `m.social.post`,
  clients are free to stop treating `m.room.message` as a post at all. A profile or group room could
  then use `m.room.message` for something other than posts, e.g. an internal chat thread alongside its
  public posts, without that content leaking into anyone's feed.

This phased approach is intended to avoid a hard cutover that would break interoperability for any user
still on a non-compliant or Phase-1 client, at the cost of a longer transition period before
`m.room.message` and `m.social.post` can be treated as meaningfully different things.

## Potential issues

- **Repost content duplication.** Because `m.social.repost_of.content` is a copy taken at repost time,
  an edit to the original post does not propagate to reposts that already copied the old content, the
  same limitation any "forwarded message" feature already has. Clients can mitigate this by re-fetching
  the live original where accessible (see Security considerations for the more serious version of this
  concern).
- **Feed construction doesn't distinguish "my posts" from "posts I follow" beyond room
  type/membership.** This proposal only specifies which *rooms* feed into a feed, not how a client
  should organize multiple joined profile/group rooms into, say, a "Home" feed versus an individual
  profile's own timeline. That is left to client implementations (similar to how room lists and space
  membership are already client-organized today).
- **No encryption guidance.** This proposal takes no position on whether profile/group rooms should be
  encrypted, public, or otherwise configured; that is left entirely to the room creator, same as any
  room today. Given that the whole point of a profile/group room is usually to be broadly readable,
  most deployments are expected to be unencrypted and public/knock-restricted in practice, but this MSC
  does not mandate it.
- **Depends on an MSC that hasn't landed.** Profile discoverability depends entirely on MSC4133. If
  MSC4133 stalls or changes shape significantly, this proposal's discoverability mechanism has no
  fallback (a profile-typed room a client happens to be a member of and was created by the target user
  remains usable as a weaker, best-effort substitute; see Profile/Group discoverability, above).
- **A quote-post whose entire commentary happens to be a permalink to the same event is
  indistinguishable from a boost.** Because a boost is detected purely by `body` being nothing but a
  matching permalink (see Proposal, above), a user who deliberately quote-posts with no text other than
  a copy-pasted link to that same event will have their post rendered as a plain boost instead. This
  proposal considers that an acceptable, rare edge case (the rendered outcome, "a repost with no
  commentary", is arguably correct anyway, since a bare link duplicating `m.social.repost_of` carries no
  information a boost doesn't already convey).
- **Phase transition timing is deliberately unmeasured.** "Majority of active users"/"majority of
  posts" in the phased rollout are not tied to any concrete, verifiable metric, since Matrix does not
  currently have a reliable mechanism for measuring client adoption share across the network. This is
  intentionally left as a judgment call rather than invented for this proposal, but is flagged here as
  a real gap in how the phase transitions would actually be triggered in practice.

## Alternatives

- **Keep reviving MSC3639 as-is.** Rejected because MSC3639 is abandoned (no active author or
  momentum), and this proposal intentionally narrows its scope in ways that aren't just a straight
  continuation: dropping the bespoke `org.matrix.msc3639.social.comment` event type in favor of
  standard thread relations (which did not yet exist when MSC3639 was written), and dropping
  post-specific fields like `m.social.image-ref` in favor of reusing `m.room.message`'s existing media
  `msgtype`s directly.
- **No new room types, treating "feed" as a purely client-side filter over ordinary rooms.** Rejected
  because, without a room-level type marker, there is no reliable way for a client to know a room is
  *meant* to be a social profile or group at all, e.g. to show a "Create Profile" versus "Create Room"
  distinction in the UI, or to avoid accidentally treating a private DM as postable. Room types are
  also an existing, established Matrix mechanism (the same one `m.space` already uses) for exactly this
  kind of container classification, so reusing it is the smaller addition to the protocol.
- **Model reposts as an `m.relates_to` relation** (e.g. `rel_type: "m.social.repost"`) referencing the
  original event, instead of an `m.social.repost_of` content block. Considered, but rejected: the
  embedded original content is still needed regardless (see Proposal, above, for why), and a relation
  doesn't carry that payload any more naturally than a plain content field would, so the relation form
  adds an extra concept without removing anything.
- **Separate event types for boosts versus quote-reposts** (e.g. `m.social.boost` and
  `m.social.quote_post`). Rejected in favor of a single mechanism (a `body` that is only a permalink
  to the reposted event, versus one that isn't) to minimize the number of new event types and avoid
  clients needing to special-case several near-identical shapes.
- **Empty or absent outer `body` for boosts**, rather than an embedded permalink. This was the
  original design, but was rejected: a blank `body` renders as an empty, confusing message bubble in
  any client without support for this proposal, indistinguishable from a send failure or a malformed
  event. A permalink-only `body` degrades gracefully instead, rendering as an ordinary clickable link
  in a fully non-compliant client (see Proposal, above).
- **A dedicated `m.social.like` event type.** Considered, but rejected for lack of value over reusing
  `m.reaction`: a like and a 👍 reaction are the same user intent for this proposal's purposes, and a
  new event type would only exist to disambiguate an edge case (someone reacting 👍 without "meaning"
  to like it) that most users will never notice or care about. See Liking, above.

## Security considerations

- **`m.social.profile_room_id` is a self-asserted, unauthenticated claim.** Nothing stops a user from
  pointing it at a room they don't own or aren't even a member of. Clients SHOULD treat the field as a
  hint rather than proof of ownership, and MAY additionally check that the referenced room's own
  `m.room.create` sender matches the profile's owner as a weak corroborating signal, though this
  proposal does not mandate any specific verification. This matches the existing trust model for
  `avatar_url`/`displayname`, which are equally self-asserted today.
- **Reposts can misrepresent, or entirely fabricate, what the original said.** Because
  `m.social.repost_of.content` is a snapshot taken at repost time, a malicious or careless repost could
  keep an offensive or retracted statement (or image, or other media) circulating in others' feeds
  after the original author has edited or redacted it. Nothing ties `content` to the actual content of
  the referenced `event_id`/`room_id` at all: a malicious user can point those fields at a real post
  while embedding any `content` they want, fabricating something the original author never said or
  posted. Clients SHOULD indicate when a live original event can no longer be found or has been
  redacted, distinct from a repost whose original is unchanged, and SHOULD verify the embedded
  `content` against the live original's actual content where the original is accessible, flagging a
  mismatch as a fabricated or altered quote rather than silently trusting the embedded copy.
- **Public, joinable profile/group rooms carry the same abuse surface as any public Matrix room
  today** (spam, unwanted joins, abusive content). This proposal introduces no new attack surface
  beyond what already exists for public `m.room.message`-based rooms, and defers entirely to existing
  moderation tooling (power levels, bans, policy-room-based moderation) rather than proposing anything
  new.
- **No new client-server or server-server API surface.** This proposal only defines conventions layered
  on existing mechanisms (room types, message-shaped events, and MSC4133's per-key profile fields), so
  it introduces no new endpoints and no attack surface beyond what those existing/dependency mechanisms
  already carry.

## Unstable prefix

Until this proposal is accepted into the spec, implementations should use the following identifiers,
all under the `org.matrix.msc4501.social.` namespace:

| Stable (once accepted)          | Unstable (for now)                              |
| -------------------------------- | ------------------------------------------------ |
| `m.social.profile`                | `org.matrix.msc4501.social.profile`               |
| `m.social.group`                  | `org.matrix.msc4501.social.group`                 |
| `m.social.post`                   | `org.matrix.msc4501.social.post`                  |
| `m.social.repost_of`              | `org.matrix.msc4501.social.repost_of`             |
| `m.social.profile_room_id`        | `org.matrix.msc4501.social.profile_room_id`       |

*(This mirrors how MSC3639 itself moved from `org.matrix.msc3639.*` unstable identifiers to
`m.social.*` on acceptance; the same rename will happen here if/when this proposal is accepted.)*

The `m.social.profile_room_id` profile field additionally depends on whatever unstable identifier the
implementing homeserver uses for MSC4133 support itself (e.g. some Synapse deployments currently
advertise `uk.tcpip.msc4133`/`uk.tcpip.msc4133.stable` in `/_matrix/client/versions`); clients should
check for MSC4133 support (by whatever identifier the server advertises) before relying on
`m.social.profile_room_id` being writable/readable.

## Dependencies

This MSC builds on the following, neither of which has been accepted into the spec at the time of
writing:

- [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133) (Extensible Profiles): the
  profile discoverability mechanism (`m.social.profile_room_id`) has no fallback if MSC4133 does not
  land in close to its current form.
- [MSC4221](https://github.com/matrix-org/matrix-spec-proposals/pull/4221) (Room Banners): used for
  `m.room.banner` in Profile rooms and Group rooms, above. Without it, profile/group rooms still have a
  name, avatar, and topic, just no banner image, so this dependency is not load-bearing for the rest of
  this proposal.
