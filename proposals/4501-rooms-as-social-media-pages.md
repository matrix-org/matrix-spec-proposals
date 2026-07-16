# MSC4501: Social Media on Matrix

*Note: this proposal is a spiritual successor to
[MSC3639: Matrix for the Social Media Use Case](https://github.com/Henri2h/matrix-doc/blob/henri2h-matrix-for-social-media/proposals/3639-matrix-for-the-social-media-use-case.md),
which has been abandoned. It keeps MSC3639's core idea, dedicated room types for social-media-style
profiles and groups, and builds on top of it: MSC3639 had no structures for representing actions like
reposting or cross-room replies, and left other social media conventions, like how liking should work,
unclear. See Comparison to MSC3639, below, for the full picture.*

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
- A minimal, generic mechanism for referencing another post across rooms, covering reposts and
  quote-posts, as well as cross-posting a reply into your own profile feed.
- Reusing the existing `m.reaction` mechanism for "liking" a post, rather than a new event type.
- Conventions for structuring an `m.room.message` post so a compliant social client can render it
  differently from how it renders in an ordinary room timeline, without looking malformed or confusing
  to a non-compliant client.
- Guidance for how a client builds a "feed" out of these rooms.
- A phased rollout plan for when clients should treat `m.room.message` as an interchangeable stand-in
  for a real post, so that the ecosystem doesn't have to flag-day cut over and break interoperability
  with clients that haven't adopted this MSC yet.

## Proposal

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

This relies on [profile fields beyond `displayname`/`avatar_url`](https://spec.matrix.org/latest/client-server-api/#profiles),
added to the Client-Server API in Matrix 1.16 (originally proposed as MSC4133), which is what makes
arbitrary per-key profile fields like this possible, see Dependencies.

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

A new event type, `m.social.post`, for a piece of social-media content submitted to a profile or group,
as distinct from a "message" sent in an ordinary Matrix room. Its content is **structurally identical to
`m.room.message`**: same `msgtype`, `body`, `formatted_body`, media fields, etc. It is not a new content
schema, only a different top-level event `type`.

Also known as:

- **Tweet** (X/Twitter)
- **Toot** (Mastodon)
- **Note** (Misskey, also used by Nostr)
- **Skeet** (Bluesky)

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
`m.social.relates_to` block, with a `rel_type` field naming the relationship, the same field name
Matrix's own `m.relates_to` uses for the same purpose. `m.social.relates_to` is its own, distinctly
named block, though, not the real `m.relates_to`: it carries none of that mechanism's server-side
aggregation, bundling, or thread-rollup behavior, only the identifier-naming convention. Its fields:

**Mandatory**

- `rel_type`: `m.social.repost` or `m.social.reply` (see Quote Posts, Reposts, and Cross-posted reply,
  below, for what each means).
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
  already an identical duplicate of the referenced post. Only meaningful for `rel_type: "m.social.repost"`;
  MUST NOT be set for `rel_type: "m.social.reply"`, whose outer `body` is always the replying user's own
  text, never a duplicate of what they're replying to. See Client Backwards Compatibility, below.
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

### Quote Posts

A repost with the reposting user's own added commentary in the *outer* post's `body`, with the quoted
post held entirely inside `m.social.relates_to`. Uses `rel_type: "m.social.repost"`.

Also known as:

- **Quote Tweet** (X/Twitter)
- **Quote post** (Bluesky)
- **Quote** (Threads, Misskey)

```json
{
  "type": "m.social.post",
  "content": {
    "msgtype": "m.text",
    "body": "This is exactly what I was talking about:",
    "m.social.relates_to": {
      "rel_type": "m.social.repost",
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

### Reposts

A repost with no added commentary. Also uses `rel_type: "m.social.repost"`, the same as a quote-post;
the only difference is what the outer `body` contains.

Also known as:

- **Retweet** (Twitter)
- **Boost** (Mastodon)
- **Reblog** (Tumblr)
- **Repost** (X, Instagram, Threads, Bluesky)
- **Share** (Facebook, LinkedIn)
- **Renote** (Misskey)
- **Repeat** (Pleroma)

Rather than an empty (or absent) outer `body`, the outer `body` MUST contain only a permalink: a
`matrix.to` URI
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
      "rel_type": "m.social.repost",
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
the event as a plain `m.room.message`) shows a normal, clickable link to the reposted post instead of a
blank bubble that looks like a send failure. Clients MAY additionally send a `formatted_body` with the
same link as an HTML anchor, for nicer rendering in clients that support formatted bodies but not this
proposal.

A plain repost and a quote-post are the same event shape. A compliant client detects a plain repost by
checking whether `content_inline` is `true`, or `body` (trimmed) parses as a permalink matching
`relates_to`'s `room_id`/`event_id`; otherwise it's a quote-post, even if the commentary happens to look
like a URI.

On a detected repost, clients SHOULD NOT render the literal `body` as commentary; instead show something
like "Alice reposted Bob's post" above the reposted content (from `relates_to.content`, or the outer
`content` when `content_inline` is `true`), naming both the reposting user (outer `sender`) and the
original author (`relates_to`'s `sender`/`displayname`).

No new event type is needed to distinguish a plain repost from a quote-post, avoiding near-identical
event types for what is fundamentally one relationship.

### Cross-posted reply

It's common on social media for a reply someone makes in a thread to also show up on their own profile,
so followers see it without needing to find the thread it was posted in. This is what `rel_type:
"m.social.reply"` is designed for.

A reply to a post already uses the ordinary `m.thread` relation within the room it's replying in (see
Posts, above); this is a separate, additional mechanism for surfacing that same reply in the replying
user's own profile feed, even though the people following them may never see the room the reply
actually lives in.

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
      "rel_type": "m.social.reply",
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

A client rendering a post with `m.social.relates_to` of `rel_type: "m.social.reply"` SHOULD show something
like "Alice replied to Bob's post" above the reply text, using `relates_to.content` for the referenced
post the same way a quote-post does, and naming both the replying user (outer `sender`) and the
original author (`relates_to`'s `sender`/`displayname`). This event is a copy posted purely for feed
visibility, not the real in-thread reply, so clients MUST NOT rely on it for thread aggregation,
reaction counts, or anything else that depends on the actual in-room relation; that still comes from
the genuine `m.thread`-related event in the room the reply was sent in.

### Client Backwards Compatibility

Because Phase 1 (and any client that never adopts this proposal at all, see Handling `m.room.message`
in social rooms, below) relies on plain `m.room.message` for posts, and because profile/group rooms are
joinable by any Matrix client whether or not it understands this proposal, a post needs to render
sensibly in a non-compliant client's ordinary room timeline, not just in a compliant social client's
feed. This section covers the parts of this proposal that exist purely to keep `m.room.message` events
looking correct there, as distinct from the rest of this proposal, which exists to make a *compliant*
client's rendering better.

**`m.social.body` and `m.social.formatted_body`** are two new, optional content fields, usable alongside
the ordinary `body`/`formatted_body` on any post:

- `m.social.body` MUST only be set when `body` is also present.
- `m.social.formatted_body` MUST only be set when `formatted_body` (and `format`) is also present.

A compliant social client SHOULD render `m.social.body`/`m.social.formatted_body` in place of
`body`/`formatted_body` when present. A non-compliant client, with no knowledge of this proposal, renders
`body`/`formatted_body` exactly as it would for any other message, unaffected by these fields' presence.

This exists because what a non-compliant client's ordinary room timeline needs to show, and what a
compliant social client needs to show, can genuinely differ. A repost with the reposting user's own
commentary (see Quote Posts, above) is the motivating case: a non-compliant client has no idea the event
is a repost at all, so `body` needs to spell that out in full, the commentary followed by a "reposted
so-and-so's post:" line and a quoted copy of the original, or the event looks like unexplained text
sitting next to a bare permalink or attachment with no context. A compliant social client already
renders that same attribution and original-post context itself, from `m.social.relates_to`, so repeating
it inside the rendered body would just duplicate it. `m.social.body` lets the compliant client show only
the reposting user's own added commentary, leaving the fuller, self-explanatory version in `body` for
everyone else:

```json
{
  "type": "m.room.message",
  "content": {
    "msgtype": "m.text",
    "body": "This is exactly what I was talking about:\n\n🔁 reposted Bob's post:\n> This is the original post being reposted",
    "m.social.body": "This is exactly what I was talking about:",
    "format": "org.matrix.custom.html",
    "formatted_body": "This is exactly what I was talking about:<p>🔁 reposted <a href=\"https://matrix.to/#/@bob:example.org\">Bob</a>'s <a href=\"https://matrix.to/#/!originalroom:example.org/$original:example.org\">post</a></p><blockquote>This is the original post being reposted</blockquote>",
    "m.social.formatted_body": "This is exactly what I was talking about:",
    "m.social.relates_to": {
      "rel_type": "m.social.repost",
      "event_id": "$original:example.org",
      "room_id": "!originalroom:example.org",
      "sender": "@bob:example.org",
      "displayname": "Bob",
      "content": {
        "msgtype": "m.text",
        "body": "This is the original post being reposted"
      }
    }
  }
}
```

`m.social.body` and `m.social.formatted_body` MUST NOT be set on `m.social.post` events. A native post
has no non-compliant room timeline to accommodate; `body`/`formatted_body` can be used directly, with no
need for a second, duplicate pair of fields.

**Reposting with inline content** is an alternative to the permalink form (see Reposts, above), for
implementations, such as a bridge mirroring reposts from another network, that already build one copy of
the reposted content as the event's own `content` and would rather a non-compliant client render that
content directly than a bare link. Set `content_inline: true` and omit `relates_to.content`:

```json
{
  "type": "m.social.post",
  "content": {
    "msgtype": "m.text",
    "body": "This is the original post being reposted",
    "m.social.relates_to": {
      "rel_type": "m.social.repost",
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
the `content` copy instead (Quote Posts, above).

`content_inline` duplicates the outer event's entire `content`, not just its text: any media fields
(`url`/`file`, `info`, etc.) on the outer event are just as much a copy of the original post as `body`
is, so a compliant client rendering the duplicated content SHOULD render the whole thing, attachment
included, not only extract text from it. And where `m.social.body`/`m.social.formatted_body` (see
Client Backwards Compatibility, above) are also present on the outer event, they, not the raw
`body`/`formatted_body`, are what a compliant client should treat as the duplicated content's actual
text, the same way it already prefers them over `body`/`formatted_body` for any other post. `body`
still carries whatever a non-compliant client's timeline needs, which for a repost is the fuller,
self-explanatory version, not the clean duplicate:

```json
{
  "type": "m.room.message",
  "content": {
    "msgtype": "m.image",
    "body": "🔁 reposted Bob's post:\n> Look at this cat!",
    "m.social.body": "Look at this cat!",
    "format": "org.matrix.custom.html",
    "formatted_body": "<p>🔁 reposted <a href=\"https://matrix.to/#/@bob:example.org\">Bob</a>'s <a href=\"https://matrix.to/#/!originalroom:example.org/$original:example.org\">post</a></p><blockquote>Look at this cat!</blockquote>",
    "m.social.formatted_body": "Look at this cat!",
    "url": "mxc://example.org/catpicture",
    "info": {
      "mimetype": "image/jpeg",
      "w": 800,
      "h": 600,
      "size": 123456
    },
    "m.social.relates_to": {
      "rel_type": "m.social.repost",
      "event_id": "$original:example.org",
      "room_id": "!originalroom:example.org",
      "sender": "@bob:example.org",
      "displayname": "Bob",
      "content_inline": true
    }
  }
}
```

Here, Bob's original post was a cat picture captioned "Look at this cat!". Alice reposted it via an
implementation that builds the outer event as a duplicate rather than sending `relates_to.content`, so
the outer event carries the same image (`url`/`info`) and, via `m.social.body`, the same clean caption.
`body`/`formatted_body` carry the fuller "reposted Bob's post:" version for a non-compliant client's
timeline; a compliant client renders the image with just "Look at this cat!" as its caption, using
`m.social.body` in place of `body`, the same as it would for any other post carrying that field.

### Liking

Posts can be reacted to with any `m.reaction` event, the same as messages in any other Matrix room
today. This proposal does not define a new event type for "liking" a post. Instead, clients SHOULD
treat an `m.reaction` whose `key` is "👍" as a like: showing it in a dedicated like count/button rather
than (or in addition to) the room's normal reaction display, incrementing a "like" affordance when the
current user has sent one, and so on.

Also known as:

- **Favorite**/**Favourite**: old Twitter (pre-2015), and still Mastodon/Pleroma and other
  ActivityPub/Fediverse software today
- **Heart**/**Hearting**: informal name for the same action on Instagram, Twitter, and Tumblr
- **Thumbs up**: Slack, GitHub, and Facebook's own Reactions bar

### Repost counts

When sending a post with `m.social.relates_to` of `rel_type: "m.social.repost"` (a quote-post or a
plain repost, in either form described under Reposts, above), clients SHOULD (but are not required to)
additionally send an `m.reaction` with `key: "🔁"` annotating the referenced event. This is RECOMMENDED,
not mandatory, but it lets any client compute a repost count for a post using the same
reaction-aggregation mechanism it already needs for likes, without waiting for every viewing client to
understand `m.social.relates_to` itself, mirroring how a 👍 `m.reaction` is treated as a like (see
Liking, above). This is only possible where the reposting user has permission to react in the referenced
event's room; where they don't, the reaction is simply not sent and the count isn't incremented from
that repost.

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
  `content_inline` repost, the outer event's own `content`) is a copy taken at reference time, an edit to
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
- **A quote-post whose entire commentary happens to be a permalink to the same event is
  indistinguishable from a plain repost.** Specific to `rel_type: "m.social.repost"`: because a plain
  repost is detected purely by `body` being nothing but a matching permalink (see Proposal, above), a
  user who deliberately quote-posts with no text other than a copy-pasted link to that same event will
  have their post rendered as a plain repost instead. This proposal considers that an acceptable, rare
  edge case (the rendered outcome, "a repost with no commentary", is arguably correct anyway, since a
  bare link duplicating `m.social.relates_to` carries no information a plain repost doesn't already
  convey). This does not affect `rel_type: "m.social.reply"`, whose outer `body` is never used to
  distinguish sub-cases.
- **Phase transition timing is deliberately unmeasured.** "Majority of active users"/"majority of
  posts" in the phased rollout are not tied to any concrete, verifiable metric, since Matrix does not
  currently have a reliable mechanism for measuring client adoption share across the network. This is
  intentionally left as a judgment call rather than invented for this proposal, but is flagged here as
  a real gap in how the phase transitions would actually be triggered in practice.

## Alternatives

- **Keep reviving MSC3639 as-is.** Rejected because MSC3639 is abandoned (no active author or
  momentum), and this proposal isn't just a straight continuation: it adds structures MSC3639 never
  had, such as reposts/quote-posts and cross-room replies, and replaces its bespoke
  `org.matrix.msc3639.social.comment` event type with standard thread relations (which did not yet
  exist when MSC3639 was written) and its `m.social.image-ref` field with `m.room.message`'s existing
  media `msgtype`s directly. See Comparison to MSC3639, below.
- **No new room types, treating "feed" as a purely client-side filter over ordinary rooms.** Rejected
  because, without a room-level type marker, there is no reliable way for a client to know a room is
  *meant* to be a social profile or group at all, e.g. to show a "Create Profile" versus "Create Room"
  distinction in the UI, or to avoid accidentally treating a private DM as postable. Room types are
  also an existing, established Matrix mechanism (the same one `m.space` already uses) for exactly this
  kind of container classification, so reusing it is the smaller addition to the protocol.
- **Reusing the real `m.relates_to` key itself**, rather than a distinctly-named `m.social.relates_to`
  block. Considered, but rejected: `m.relates_to`-based relations (bundled aggregations, the
  `/relations` endpoint, thread rollups) are resolved by walking the *same room's* event graph, so a
  foreign `room_id` alongside `rel_type` would be silently ignored by that machinery rather than doing
  anything useful, and reusing the same top-level key risks a client or server misreading a cross-room
  reference as an ordinary in-room relation. `m.social.relates_to` still borrows `rel_type` as its
  discriminator field's name, matching existing Matrix convention, but living under a distinct key means
  it carries none of `m.relates_to`'s aggregation/rollup semantics; implementations MUST NOT assume
  `m.social.relates_to.rel_type` behaves like `m.relates_to.rel_type` beyond naming an identifier. The
  embedded content is also still needed regardless (see Proposal, above, for why), and a relation
  doesn't carry that payload any more naturally than a plain content field would.
- **A bare pointer event carrying only `event_id`/`room_id`, with no content-embedding option at all.**
  Considered as the minimal possible mechanism, but rejected: a viewer who isn't joined to the referenced
  room, the common case for both reposts and cross-posted replies, since followers usually aren't
  members of every room a post could originate from, would have no way to render it without a fetch that
  can fail (missing permission, an unreachable server, a room since made inaccessible). Keeping `content`
  optional-but-recommended already covers the minimal-pointer case for implementations that don't need
  it, without forcing every implementation into that failure mode.
- **A separate `m.social.in_reply_to` block mirroring `m.social.repost_of`'s original shape**, instead
  of unifying both into `m.social.relates_to` with a `rel_type` field. Rejected: reposts and cross-posted
  replies need the exact same fields (`event_id`, `room_id`, `sender`, optional `content`/`displayname`)
  for the exact same reason, rendering a cross-room reference without requiring room membership; the
  only real difference is what the relationship *means*, which a `rel_type` field captures far more cheaply
  than a second, near-identical block would.
- **Separate event types for a plain repost versus a quote-post** (e.g. `m.social.repost` as an event
  type of its own and `m.social.quote_post`). Rejected in favor of a single mechanism (a `body` that is
  only a permalink to the reposted event, versus one that isn't) to minimize the number of new event
  types and avoid clients needing to special-case several near-identical shapes.
- **Empty or absent outer `body` for a plain repost**, rather than an embedded permalink. This was the
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
  always its own real text, neither can double as a duplicate of the referenced post the way a plain
  repost's can. Keeping `relates_to.content` as the general-case mechanism, with `content_inline` as an
  opt-in for repost implementations that already build the outer content as a duplicate anyway, covers
  all three cases without forcing every implementation to special-case quote-posts and replies.

## Comparison to MSC3639

MSC4501 keeps MSC3639's core idea, dedicated room types for social-media-style profiles and groups,
and builds on top of it rather than simplifying it. MSC3639 has no structures for representing actions
like reposting or cross-room replies at all, and leaves other social media conventions unclear:

- **Reposts, quote-posts, and cross-room replies.** MSC3639 has no mechanism for referencing a post in
  another room; a "comment" there is only ever a same-room thread reply to a same-room post. This
  proposal's `m.social.relates_to` mechanism (see Cross-room post references, above) is new.
- **Liking.** MSC3639 only says emoji reactions are standard Matrix reactions, without specifying which
  reaction represents a like, or any convention for counting reposts. This proposal makes both explicit
  (see Liking and Repost counts, above).

**Profile and group rooms are currently compatible between the two proposals.** Both use the same room
type identifiers, `m.social.profile` and `m.social.group` (see Unstable prefix, above), so a room typed
this way is recognized as a profile or group room by an implementation of either proposal, regardless
of which one created it.

**Posts are only partly compatible.** Both proposals use the same event type, `m.social.post`, for a
top-level piece of content, and a plain-text post (a bare `body`, no attachments) is readable under
either proposal's rules. Where they diverge is media: MSC3639 posts reference separately-sent image
events via an `m.social.image-ref` array, while this proposal embeds media directly using
`m.room.message`'s own media `msgtype`s (see Posts, above), so an implementation of one proposal will
not render media attached the other proposal's way.

**Comments and replies are not compatible.** MSC3639 gives a reply its own event type,
`m.social.comment`, related to its post via a thread. This proposal deliberately drops that distinct
type in favor of standard thread relations: a reply is just another `m.social.post`, related to the
post it replies to via an ordinary `m.thread` relation (see Posts, above). An MSC3639-only
implementation has no reason to expect a threaded `m.social.post` to be anything other than a new
top-level post, and an implementation of this proposal will not recognize an `m.social.comment`-typed
event as a reply at all.

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
  said, or who said it.** Because `m.social.relates_to.content`/`sender`/`displayname` (and `rel_type`
  itself) are a snapshot taken at reference time, a malicious or careless repost or reply could keep an
  offensive or retracted statement (or image, or other media) circulating in others' feeds after the
  original author has edited or redacted it, or attribute real or fabricated content to a user who never
  posted it at all. Nothing ties `content`, `sender`, or `displayname` to the actual content or author of
  the referenced `event_id`/`room_id`: a malicious user can point those fields at a real post while
  embedding any `content`/`sender`/`displayname` they want, fabricating something the original author
  never said, or attributing real content to the wrong person entirely; a malicious `rel_type` can likewise
  mislabel a repost as a reply or vice versa, though this only misleads a viewer about the *nature* of
  the relationship, not its authenticity. Clients SHOULD indicate when a live referenced event can no
  longer be found or has been redacted, distinct from a reference whose original is unchanged, and
  SHOULD verify the embedded `content`/`sender` against the live original's actual content/sender where
  it is accessible, flagging a mismatch as fabricated or altered (or misattributed) rather than silently
  trusting the embedded copy. This applies equally to a `content_inline: true` repost: the outer event's
  own `content` is exactly as self-asserted and unverified as a `relates_to.content` copy would have
  been, so it carries no additional trust just for living at the top level of the event.
- **Public, joinable profile/group rooms carry the same abuse surface as any public Matrix room
  today** (spam, unwanted joins, abusive content). This proposal introduces no new attack surface
  beyond what already exists for public `m.room.message`-based rooms, and defers entirely to existing
  moderation tooling (power levels, bans, policy-room-based moderation) rather than proposing anything
  new.
- **No new client-server or server-server API surface.** This proposal only defines conventions layered
  on existing mechanisms (room types, message-shaped events, and the Client-Server API's per-key
  profile fields), so it introduces no new endpoints and no attack surface beyond what those
  existing/dependency mechanisms already carry.

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
| `m.social.body`                   | `org.matrix.msc4501.social.body`                  |
| `m.social.formatted_body`         | `org.matrix.msc4501.social.formatted_body`        |

*(This mirrors how MSC3639 itself moved from `org.matrix.msc3639.*` unstable identifiers to
`m.social.*` on acceptance; the same rename will happen here if/when this proposal is accepted.)*

The `m.social.profile_room_id` profile field additionally depends on the implementing homeserver
supporting per-key profile fields, part of the Client-Server API since Matrix 1.16; clients should
check the server's supported spec versions (`/_matrix/client/versions`) before relying on
`m.social.profile_room_id` being writable/readable.

## Dependencies

This MSC builds on the following:

- [Per-key profile fields](https://spec.matrix.org/latest/client-server-api/#profiles), part of the
  Client-Server API since Matrix 1.16 (originally proposed as MSC4133): the profile discoverability
  mechanism (`m.social.profile_room_id`) depends on this.
- [MSC4221](https://github.com/matrix-org/matrix-spec-proposals/pull/4221) (Room Banners), not yet
  accepted into the spec at the time of writing: used for `m.room.banner` in Profile rooms and Group
  rooms, above. Without it, profile/group rooms still have a name, avatar, and topic, just no banner
  image, so this dependency is not load-bearing for the rest of this proposal.
