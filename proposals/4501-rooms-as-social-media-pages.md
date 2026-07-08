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
- A minimal, generic mechanism for referencing another post across rooms, covering reposts, boosts,
  retweets, and quote-posts, as well as cross-posting a reply into your own profile feed.
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

A profile room additionally carries a new state event, `m.social.profile_user_id`, identifying the single
Matrix user the room is a profile *of*:

```json
{
  "type": "m.social.profile_user_id",
  "state_key": "",
  "content": {
    "user_id": "@alice:example.org"
  }
}
```

The event always uses an empty `state_key`. Matrix's state resolution rules mean a room has exactly one
current event for a given `(type, state_key)` pair, so with a fixed, empty `state_key` a profile room
can hold exactly one `m.social.profile_user_id` at a time, whichever was sent last (subject to the room's
own power levels); it can never simultaneously claim to belong to two different users.

Because `m.social.profile_user_id` is not one of the state events a default `m.room.power_levels` gives
its own override for (unlike `m.room.name` or `m.room.avatar`, which default to requiring power level
50), it falls back to that power levels event's `state_default`, which itself defaults to 50 ("Moderator"
in most clients) when a room is created with no explicit overrides, not 100 ("Admin"). Left at that
default, any user promoted to Moderator, not just the room's Admin/owner, would be able to send a new
`m.social.profile_user_id` and reassign the profile away from its actual owner.

Clients creating a profile room SHOULD therefore explicitly set a power level requirement for
`m.social.profile_user_id` in the room's initial `m.room.power_levels` `events` override, at or above the
level of the intended owner (typically 100), separately from `state_default`:

```json
{
  "type": "m.room.power_levels",
  "state_key": "",
  "content": {
    "events": {
      "m.social.profile_user_id": 100
    }
  }
}
```

This is what lets a profile have moderators (e.g. at power level 50, able to redact posts or ban
abusive members) without those moderators being able to reassign or strip the profile's ownership out
from under its actual owner.

`m.social.profile_user_id` is the inverse of `m.social.profile_room_id` (see Profile/Group
discoverability, below): that field lives on a user's own account and points at a room, while
`m.social.profile_user_id` lives on the room and points back at a user. This matters because a profile
room's `m.room.create` `creator` is not always the person the profile is *of*: a room created by a
bridge or appservice on a user's behalf (e.g., a Matrix/ActivityPub federation bridge creating a local
profile room for a fediverse account) will have the bridge's own bot as `creator`, not the person the
profile represents. `m.social.profile_user_id` lets that room assert its true intended owner regardless
of who technically created it, which `creator` alone cannot do.

Like `m.social.profile_room_id`, `m.social.profile_user_id` is self-asserted; see Security considerations
for how a client can corroborate it.

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
its creator. `m.social.profile_room_id` (set on the candidate user's own account) and
`m.social.profile_user_id` (set on the room itself, see Profile rooms, above) are the authoritative
signals a client should use to decide "this is user X's current profile," ideally checked together
(see Security considerations). A profile-typed room's `type` and `m.room.create` `creator` are only a
weaker, best-effort fallback signal (useful for legacy clients, or while neither of these fields has
propagated yet), not a substitute for either.

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
event. This proposal does not define a separate "comment" event type, unlike MSC3639. A reply MAY
additionally be cross-posted into the replying user's own profile feed; see Cross-posting a reply to
your profile, below.

### Cross-room post references

A post can reference another post in a different room, whether it's reposting it or cross-posting a
reply into the replying user's own profile so followers see it. Its content then includes an
`m.social.relates_to` block, with a `kind` field naming the relationship. Its fields:

**Mandatory**

- `kind`: `m.social.repost` or `m.social.reply` (see Reposting/Boosting/Retweeting/Quote-posting and
  Cross-posting a reply to your profile, below, for what each means).
- `event_id`: the referenced post's event ID.
- `room_id`: the room the referenced post was sent in.
- `sender`: Matrix ID of the referenced post's author.

**Optional**

- `content` (RECOMMENDED): a full copy of the referenced post's entire `content` at reference time.
  Without it, a client has to either fetch the live referenced event to render this post, which can
  fail if the viewer lacks permission to see it or isn't joined to `room_id` at all, or fall back to a
  bare placeholder linking to the event. MUST NOT be present alongside `content_inline: true` (see
  below), since that would duplicate the same content twice.
- `content_inline` (boolean): set in place of `content`, when the outer event's own `content` is
  already an identical duplicate of the referenced post. Only meaningful for `kind: "m.social.repost"`;
  MUST NOT be set for `kind: "m.social.reply"`, whose outer `body` is always the replying user's own
  text, never a duplicate of what they're replying to. See Boosting with inline content, below.
- `displayname`: snapshot of the referenced post's author's display name at reference time, for nicer
  default rendering. Clients MUST fall back to the bare `sender` Matrix ID when it is absent, the same
  as Matrix already does anywhere else a display name is unset.

`sender` is mandatory, and `content`/`displayname` are RECOMMENDED, precisely so this kind of post
doesn't require viewers to fetch the referenced event to render or attribute it: the person viewing it
in their feed may not share a room with the referenced post's author at all, e.g., reposting a post
from a public group into your own profile, or replying to a post in a room the replier's own followers
have never joined. Clients SHOULD still attempt to resolve the live referenced event (via `event_id` +
`room_id`) where accessible, to support "view original", live reaction counts, or detecting that it has
since been edited or redacted, falling back to the embedded copy when it isn't reachable, or to a bare
placeholder linking to the event when no embedded copy was sent either.

**Reposting / Boosting / Retweeting / Quote-posting** uses `kind: "m.social.repost"`. The outer `body`
then determines which of the two:

**Quote-posting** is a repost with the reposting user's own added commentary in the *outer* post's
`body`, with the quoted post held entirely inside `m.social.relates_to`:

```json
{
  "type": "m.social.post",
  "content": {
    "msgtype": "m.text",
    "body": "This is exactly what I was talking about:",
    "m.social.relates_to": {
      "kind": "m.social.repost",
      "event_id": "$original:example.org",
      "room_id": "!originalroom:example.org",
      "sender": "@bob:example.org",
      "displayname": "Bob",
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
pointing at the same event referenced by `m.social.relates_to`:

```json
{
  "type": "m.social.post",
  "content": {
    "msgtype": "m.text",
    "body": "https://matrix.to/#/!originalroom:example.org/$original:example.org",
    "m.social.relates_to": {
      "kind": "m.social.repost",
      "event_id": "$original:example.org",
      "room_id": "!originalroom:example.org",
      "sender": "@bob:example.org",
      "content": {
        "msgtype": "m.text",
        "body": "This is the original post being reposted"
      }
    }
  }
}
```

A permalink, rather than an empty string, means a client with no support for this proposal (rendering
the event as a plain `m.room.message`) shows a normal, clickable link to the boosted post instead of a
blank bubble that looks like a send failure. Clients MAY additionally send a `formatted_body` with the
same link as an HTML anchor, for nicer rendering in clients that support formatted bodies but not this
proposal.

**Boosting with inline content** is an alternative to the permalink form, for implementations, such as
a bridge mirroring reposts from another network, that already build one copy of the reposted content
as the event's own `content` and would rather a non-compliant client render that content directly than
a bare link. Set `content_inline: true` and omit `relates_to.content`:

```json
{
  "type": "m.social.post",
  "content": {
    "msgtype": "m.text",
    "body": "This is the original post being reposted",
    "m.social.relates_to": {
      "kind": "m.social.repost",
      "event_id": "$original:example.org",
      "room_id": "!originalroom:example.org",
      "sender": "@bob:example.org",
      "content_inline": true
    }
  }
}
```

This MUST NOT carry reposting-user commentary: once `content_inline` is set, there is no way to tell
duplicated original content apart from genuine commentary, so a repost with its own added text MUST use
the `content` copy instead (Quote-posting, above).

A boost and a quote-post are the same event shape. A compliant client detects a boost by checking
whether `content_inline` is `true`, or `body` (trimmed) parses as a permalink matching `relates_to`'s
`room_id`/`event_id`; otherwise it's a quote-post, even if the commentary happens to look like a URI.

On a detected boost, clients SHOULD NOT render the literal `body` as commentary; instead show something
like "Alice reposted Bob's post" above the reposted content (from `relates_to.content`, or the outer
`content` when `content_inline` is `true`), naming both the reposting user (outer `sender`) and the
original author (`relates_to`'s `sender`/`displayname`).

No new event type is needed to distinguish a boost from a quote-post, avoiding near-identical event
types for what is fundamentally one relationship.

**Repost/boost counts.** When sending a post with `m.social.relates_to` of `kind: "m.social.repost"`,
in any of the forms above (quote-post, boost, or boost with inline content), clients SHOULD (but are
not required to) additionally send an `m.reaction` with `key: "🔁"` annotating the referenced event.
This is RECOMMENDED, not mandatory, but it lets any client compute a repost/boost count for a post
using the same reaction-aggregation mechanism it already needs for likes, without waiting for every
viewing client to understand `m.social.relates_to` itself, the same rationale as treating a 👍
`m.reaction` as a like (see Liking, below). This is only possible where the reposting user has
permission to react in the referenced event's room; where they don't, the reaction is simply not sent
and the count isn't incremented from that repost.

**Cross-posting a reply to your profile** uses `kind: "m.social.reply"`. A reply to a post already uses
the ordinary `m.thread` relation within the room it's replying in (see Posts, above); this is a
separate, additional mechanism for surfacing that same reply in the replying user's own profile feed,
the same way replying to someone on other social platforms shows up on your own timeline, even though
the people following you may never see the room the reply actually lives in.

To do this, the replying client (or, e.g., a federation bridge mirroring replies from another network)
additionally posts an ordinary `m.social.post` into the replier's own profile room, with an
`m.social.relates_to` block pointing at the post being replied to. Unlike a repost, the outer `body` is
always the reply's own real text, never a permalink or duplicate placeholder, since a reply inherently
has its own content:

```json
{
  "type": "m.social.post",
  "content": {
    "msgtype": "m.text",
    "body": "Completely agree with this!",
    "m.social.relates_to": {
      "kind": "m.social.reply",
      "event_id": "$original:example.org",
      "room_id": "!originalroom:example.org",
      "sender": "@bob:example.org",
      "displayname": "Bob",
      "content": {
        "msgtype": "m.text",
        "body": "This is the post being replied to"
      }
    }
  }
}
```

A client rendering a post with `m.social.relates_to` of `kind: "m.social.reply"` SHOULD show something
like "Alice replied to Bob's post" above the reply text, using `relates_to.content` for the referenced
post the same way a quote-post does, and naming both the replying user (outer `sender`) and the
original author (`relates_to`'s `sender`/`displayname`). This event is a copy posted purely for feed
visibility, not the real in-thread reply, so clients MUST NOT rely on it for thread aggregation,
reaction counts, or anything else that depends on the actual in-room relation; that still comes from
the genuine `m.thread`-related event in the room the reply was sent in.

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

- **Cross-room reference content duplication.** Because `m.social.relates_to.content` (or, for a
  `content_inline` boost, the outer event's own `content`) is a copy taken at reference time, an edit to
  the referenced post does not propagate to reposts or cross-posted replies that already copied the old
  content, the same limitation any "forwarded message" feature already has. Clients can mitigate this by
  re-fetching the live referenced event where accessible (see Security considerations for the more
  serious version of this concern). `content_inline` avoids storing the duplicate twice within the
  repost event itself, but does not change this staleness limitation either way.
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
  indistinguishable from a boost.** Specific to `kind: "m.social.repost"`: because a boost is detected
  purely by `body` being nothing but a matching permalink (see Proposal, above), a user who deliberately
  quote-posts with no text other than a copy-pasted link to that same event will have their post
  rendered as a plain boost instead. This proposal considers that an acceptable, rare edge case (the
  rendered outcome, "a repost with no commentary", is arguably correct anyway, since a bare link
  duplicating `m.social.relates_to` carries no information a boost doesn't already convey). This does
  not affect `kind: "m.social.reply"`, whose outer `body` is never used to distinguish sub-cases.
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
- **Reusing the real `m.relates_to`/`rel_type` mechanism** (e.g. `rel_type: "m.social.repost"`)
  referencing the original event, instead of a separate `m.social.relates_to` content block. Considered,
  but rejected: `m.relates_to`-based relations (bundled aggregations, the `/relations` endpoint, thread
  rollups) are resolved by walking the *same room's* event graph, so a foreign `room_id` under `rel_type`
  would be silently ignored by that machinery rather than doing anything useful, and reusing the same
  key risks a client or server misreading a cross-room reference as an ordinary in-room relation. A
  distinctly-named `m.social.relates_to` avoids colliding with that machinery while still borrowing its
  "kind discriminator" idea. The embedded content is also still needed regardless (see Proposal, above,
  for why), and a relation doesn't carry that payload any more naturally than a plain content field
  would.
- **A bare pointer event carrying only `event_id`/`room_id`, with no content-embedding option at all.**
  Considered as the minimal possible mechanism, but rejected: a viewer who isn't joined to the referenced
  room, the common case for both reposts and cross-posted replies, since followers usually aren't
  members of every room a post could originate from, would have no way to render it without a fetch that
  can fail (missing permission, an unreachable server, a room since made inaccessible). Keeping `content`
  optional-but-recommended already covers the minimal-pointer case for implementations that don't need
  it, without forcing every implementation into that failure mode.
- **A separate `m.social.in_reply_to` block mirroring `m.social.repost_of`'s original shape**, instead
  of unifying both into `m.social.relates_to` with a `kind` field. Rejected: reposts and cross-posted
  replies need the exact same fields (`event_id`, `room_id`, `sender`, optional `content`/`displayname`)
  for the exact same reason, rendering a cross-room reference without requiring room membership; the
  only real difference is what the relationship *means*, which a `kind` field captures far more cheaply
  than a second, near-identical block would.
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
- **Relying solely on a profile room's `m.room.create` `creator` to identify its owner**, rather than
  adding `m.social.profile_user_id`. Rejected because `creator` is not always the person a profile room
  is of: a room created by a bridge or appservice on a user's behalf will have the bridge's own bot as
  `creator`. A dedicated state event lets the room assert its true intended owner independent of who
  technically created it. See Profile rooms, above.
- **Always requiring the outer `content` to double as the duplicate, dropping `relates_to.content`
  entirely**, rather than making `content_inline` an opt-in alongside it. Rejected because a
  quote-post's outer `body` is the reposting user's own commentary, and a reply's outer `body` is
  always its own real text, neither can double as a duplicate of the referenced post the way a boost's
  can. Keeping `relates_to.content` as the general-case mechanism, with `content_inline` as an opt-in
  for boost implementations that already build the outer content as a duplicate anyway, covers all
  three cases without forcing every implementation to special-case quote-posts and replies.

## Security considerations

- **`m.social.profile_room_id` and `m.social.profile_user_id` are both self-asserted, unauthenticated
  claims.** Nothing stops a user from pointing their `m.social.profile_room_id` at a room they don't
  own or aren't even a member of, and nothing stops whoever holds sufficient power level in a room from
  setting its `m.social.profile_user_id` to any user ID, including one who has never heard of the room.
  Clients SHOULD treat either field alone as a hint rather than proof of ownership. The strongest
  corroboration this proposal offers is checking that the two agree in both directions: the room's
  `m.social.profile_user_id` names a user whose own `m.social.profile_room_id` points back at that same
  room. Requiring agreement in both directions is harder to fake than either field alone, since it
  needs control of both the claimed user's account and sufficient power level in the room, though it is
  still not cryptographic proof. Clients MAY additionally fall back to checking the room's
  `m.room.create` sender as a weaker signal still, though this proposal does not mandate any specific
  verification. This matches the existing trust model for `avatar_url`/`displayname`, which are equally
  self-asserted today.
- **`m.social.profile_user_id` defaults to Moderator-level, not Admin-level, protection.** A room's
  `m.room.power_levels` only overrides specific well-known state events; anything else, including a
  custom event type like `m.social.profile_user_id`, falls back to `state_default`, which itself defaults
  to 50 ("Moderator") rather than 100 ("Admin") when a room is created with no explicit overrides. A
  profile room created without an explicit power level override for `m.social.profile_user_id` (see
  Profile rooms, above) can therefore have its ownership reassigned by any Moderator, not only the
  room's Admin/owner. Clients creating profile rooms SHOULD set this override at room-creation time.
- **Reposts and cross-posted replies can misrepresent, or entirely fabricate, what the referenced post
  said, or who said it.** Because `m.social.relates_to.content`/`sender`/`displayname` (and `kind`
  itself) are a snapshot taken at reference time, a malicious or careless repost or reply could keep an
  offensive or retracted statement (or image, or other media) circulating in others' feeds after the
  original author has edited or redacted it, or attribute real or fabricated content to a user who never
  posted it at all. Nothing ties `content`, `sender`, or `displayname` to the actual content or author of
  the referenced `event_id`/`room_id`: a malicious user can point those fields at a real post while
  embedding any `content`/`sender`/`displayname` they want, fabricating something the original author
  never said, or attributing real content to the wrong person entirely; a malicious `kind` can likewise
  mislabel a repost as a reply or vice versa, though this only misleads a viewer about the *nature* of
  the relationship, not its authenticity. Clients SHOULD indicate when a live referenced event can no
  longer be found or has been redacted, distinct from a reference whose original is unchanged, and
  SHOULD verify the embedded `content`/`sender` against the live original's actual content/sender where
  it is accessible, flagging a mismatch as fabricated or altered (or misattributed) rather than silently
  trusting the embedded copy. This applies equally to a `content_inline: true` boost: the outer event's
  own `content` is exactly as self-asserted and unverified as a `relates_to.content` copy would have
  been, so it carries no additional trust just for living at the top level of the event.
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
| `m.social.relates_to`             | `org.matrix.msc4501.social.relates_to`            |
| `m.social.repost`                 | `org.matrix.msc4501.social.repost`                |
| `m.social.reply`                  | `org.matrix.msc4501.social.reply`                 |
| `m.social.profile_room_id`        | `org.matrix.msc4501.social.profile_room_id`       |
| `m.social.profile_user_id`        | `org.matrix.msc4501.social.profile_user_id`       |

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
