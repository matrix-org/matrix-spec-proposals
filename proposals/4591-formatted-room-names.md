# MSC4591: Formatted room names

Room names in Matrix are plain text. Many communities want more than that, most commonly custom emoji
in a room's name, and rooms named after people (for example a bridged fediverse user's profile room,
see [MSC4501](https://github.com/matrix-org/matrix-spec-proposals/pull/4501)) end up showing raw
`:shortcode:` text where the person's name has custom emoji.

[MSC4589](https://github.com/matrix-org/matrix-spec-proposals/pull/4589) adds an optional formatted
display name alongside `displayname`. This proposal is its sibling for rooms: an optional formatted
room name alongside the plain `name` in `m.room.name`, using the same restricted HTML and the same
rules.

The spec already took this approach for room topics:
[MSC3765](https://github.com/matrix-org/matrix-spec-proposals/pull/3765) (in the spec since v1.15)
added the rich topic as an `m.topic` field inside `m.room.topic`, next to the plain `topic`, rather
than as a separate event.

## Proposal

### The `m.formatted_name` field

A new optional field, `m.formatted_name`, is added to the content of `m.room.name`. It has the same
schema as MSC4589's `m.formatted_displayname`:

| Field | Type | Required | Description |
|---|---|---|---|
| `format` | string | Yes | The format of `formatted_body`. Only `org.matrix.custom.html` is defined by this proposal. |
| `formatted_body` | string | Yes | The formatted room name, using the restricted HTML subset from MSC4589. |

Example:

```json
{
  "type": "m.room.name",
  "state_key": "",
  "content": {
    "name": "Blob Cats",
    "m.formatted_name": {
      "format": "org.matrix.custom.html",
      "formatted_body": "<b>Blob Cats</b> <img data-mx-emoticon src=\"mxc://example.org/abc123\" alt=\"\" title=\":blobcat:\">"
    }
  }
}
```

The plain `name` remains required whenever `m.formatted_name` is present, and remains the source of
truth for everything other than visual rendering: search, notifications, sorting, accessibility, and
clients that don't support this proposal. If `name` is absent, null or empty (meaning the room has no
name), `m.formatted_name` is ignored.

### Rules shared with MSC4589

The following rules from MSC4589 apply unchanged, with `name` in place of `displayname`:

* **Consistency with the plain name.** Clients MUST compute the text content of `formatted_body`
  (each permitted `<img>` replaced by its `alt`, all tags ignored), normalize whitespace in both it
  and `name` (runs collapsed to a single space, ends trimmed), and ignore `m.formatted_name` unless
  the two are equal.
* **Custom emoji in the plain name.** Each image's `alt` may be its `:shortcode:` (so the emoji
  appears as its shortcode in the plain name) or empty (so the emoji is left out of the plain name),
  as the room's moderators choose. Clients SHOULD set `title` to the shortcode either way.
* **Permitted HTML.** Only `b`/`strong`, `i`/`em`, `u`, `s`/`del`, and `img` with `data-mx-emoticon`
  and an `mxc://` source. No color, no fonts, no links, no block elements. Inline images are rendered
  at the height of the surrounding text.
* **Limits.** `formatted_body` is at most 1024 bytes and contains at most 10 images, with tags nested
  at most 10 levels deep.

### Setting and clearing

`m.formatted_name` is set by sending an `m.room.name` event containing it, so it requires the same
power level as renaming the room. A room can be created with a formatted name by passing a full
`m.room.name` event in `initial_state` to `/createRoom`.

A client that doesn't support this proposal renames a room by sending `m.room.name` with only `name`,
which clears `m.formatted_name` at the same time. Formatted room names therefore can't go stale when
renamed from such a client.

### Where formatted names are rendered

Clients SHOULD render the formatted name wherever they show a room's name from its `m.room.name`
event, such as the room list, room header, and room settings.

Clients SHOULD show the plain name instead for pending invites, until the user accepts them, so that
invite spam can't put arbitrary imagery in front of users. (Invites carry `m.room.name` in their
stripped state, so the formatted name is available once the user chooses to look at it.)

When a room has no `m.room.name` and clients compute its name from its members, clients MAY use
those members' formatted display names (MSC4589).

Push notifications and other plain text contexts continue to use `name`.

### Room directory, space hierarchy and room summaries

[`/publicRooms`](https://spec.matrix.org/latest/client-server-api/#get_matrixclientv3publicrooms),
the [space hierarchy](https://spec.matrix.org/latest/client-server-api/#get_matrixclientv1roomsroomidhierarchy)
and the [room summary API](https://spec.matrix.org/latest/client-server-api/#get_matrixclientv1room_summaryroomidoralias)
return a room's plain `name`. Servers MAY additionally include `m.formatted_name`, copied from the
room's `m.room.name` event, in each room's entry in these responses, so that clients can display it.

Searching the room directory (the `filter.generic_search_term` of `POST /publicRooms`) continues to
match only the plain `name`. This is intentional: users search by typing text, and the plain name
holds that text.

### Room name overrides

[MSC4431](https://github.com/matrix-org/matrix-spec-proposals/pull/4431) (personal room name
overrides) and [MSC4432](https://github.com/matrix-org/matrix-spec-proposals/pull/4432) (server-wide
room name overrides) reuse the content schema of `m.room.name`. If they are accepted, an override MAY
include `m.formatted_name`, with the same rules, and clients apply it alongside the override's `name`.

## Potential issues

**Directory search is plain text only.** Users can't search for a room by its formatting or by its
emoji, unless the emoji's shortcode is part of the plain name. This is a deliberate limitation; a
future proposal could extend server-side search if there is demand.

**Directory and hierarchy responses may lack the formatted name.** Servers aren't required to include
`m.formatted_name` in these responses, so clients may only be able to show the plain name there.

**Abuse through imagery.** Custom emoji in room names appear in room lists, headers and (if servers
include them) the room directory. The invite rule above covers unsolicited rooms. Room moderators
control the name of rooms they run, and clients MAY offer users an option to disable formatted room
names.

## Alternatives

### A separate `m.room.formatted_name` state event

A new state event alongside `m.room.name` would keep `m.room.name` untouched, but:

* it would need adding to the spec's list of stripped state events before invites, knocks and
  previews could carry it, while `m.room.name` is already there;
* renaming a room from a client that doesn't support this proposal would leave a stale formatted
  name behind (hidden by the consistency rule, but still present);
* its power level would need configuring separately, rather than matching the room name's.

Putting the field inside `m.room.name` avoids all three, and matches the precedent set by rich room
topics.

### An `m.text` array, as for topics

MSC3765 represents rich topics as an MSC1767-style `m.text` array. This proposal uses the
`format`/`formatted_body` pair instead, to match MSC4589's formatted display names, since the two are
rendered by the same code with the same rules, and because the plain representation already lives in
`name`.

### Deriving formatted names from room owners

MSC4501 originally let clients show a profile room's owner's formatted display name in place of the
room name, when the two matched. That only works for room types with a single clear owner, and needs
a lookup of the owner's profile. A formatted room name works for every room, and lets a profile room
simply carry its own formatted name.

## Security considerations

* Clients MUST apply the permitted tag and attribute list strictly, as for message HTML, to avoid
  HTML injection and cross-site scripting.
* The consistency rule prevents a formatted room name from showing different text from the plain
  name. Custom emoji can still contain images of text, as with formatted display names.
* With an empty `alt`, the plain name gives no indication that the formatted name contains images.
  This adds no new way to spoof text, since an image of text is equally possible with a shortcode
  `alt`.

## Unstable prefix

Until this proposal is accepted, implementations should use `org.matrix.msc4591.formatted_name` in
place of `m.formatted_name`, in `m.room.name` content and in directory, hierarchy and room summary
responses.

## Dependencies

This proposal builds on [MSC4589](https://github.com/matrix-org/matrix-spec-proposals/pull/4589)
(formatted display names) for its permitted HTML, limits and consistency rule. If MSC4589 changes
those rules, this proposal is expected to follow.
