# MSCVVVV: Formatted display names

A user's display name in Matrix is a plain string. Many users want more than that, most commonly
custom emoji in their name. This is especially common on the fediverse, where Mastodon, Pleroma,
Akkoma, Misskey and others let an actor's `name` contain `:shortcode:` tokens that are rendered as
custom emoji images. Bridges that carry those accounts into Matrix currently have no way to show
those images: the best they can do is leave the raw `:shortcode:` text in the display name.

Matrix already has a well understood way to express rich text: the `org.matrix.custom.html` format
used by `m.room.message`, including inline custom emoji via `<img data-mx-emoticon>` from
[MSC2545](https://github.com/matrix-org/matrix-spec-proposals/pull/2545). This proposal reuses a
strictly inline subset of that format for an optional formatted display name, carried alongside the
existing plain `displayname` in both the global profile and `m.room.member` events.

## Proposal

### The `m.formatted_displayname` field

A new optional field, `m.formatted_displayname`, is defined. Its value is an object:

| Field | Type | Required | Description |
|---|---|---|---|
| `format` | string | Yes | The format of `formatted_body`. Only `org.matrix.custom.html` is defined by this proposal. |
| `formatted_body` | string | Yes | The formatted display name, using the restricted HTML subset described below. |

Example:

```json
{
  "displayname": "Cat :blobcat: Person",
  "m.formatted_displayname": {
    "format": "org.matrix.custom.html",
    "formatted_body": "<b>Cat</b> <img data-mx-emoticon src=\"mxc://example.org/abc123\" alt=\":blobcat:\" title=\":blobcat:\"> <span data-mx-color=\"#ff8800\">Person</span>"
  }
}
```

The plain `displayname` remains required whenever `m.formatted_displayname` is present, and remains
the source of truth for everything other than visual rendering (see below).

### Where the field appears

**Global profile.** `m.formatted_displayname` is a profile field as defined by
[MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133), set and read with the
normal `/_matrix/client/v3/profile/{userId}/{keyName}` endpoints.

**Room membership.** MSC4133 states that custom profile fields MUST NOT be replicated into
`m.room.member` events "unless a future proposal creates exceptions for specific fields". This
proposal creates that exception for `m.formatted_displayname`: it is propagated into `m.room.member`
content under exactly the same rules as `displayname`. Specifically:

* When the user changes `m.formatted_displayname` in their global profile, the server sends updated
  `m.room.member` events in the same way it does for a `displayname` change.
* When the server copies profile information into a new `m.room.member` event (for example on join),
  it copies `m.formatted_displayname` alongside `displayname` and `avatar_url`.
* If [MSC4466](https://github.com/matrix-org/matrix-spec-proposals/pull/4466) is accepted, its
  `propagate_to` parameter applies to `m.formatted_displayname` exactly as it does to `displayname`.

**Per-room names.** As with `displayname` today, a client can set a per-room formatted display name
by sending an `m.room.member` event with a different `m.formatted_displayname` (and a matching
`displayname`). Clients can offer this however they like, for example through a rich text composer
for the name, or a command that accepts the HTML directly.

### Consistency with the plain display name

Clients MUST compute the *text content* of `formatted_body` as follows:

1. Parse the HTML.
2. Replace every permitted `<img>` element with the value of its `alt` attribute.
3. Concatenate the remaining text nodes, ignoring all tags.

Clients MUST ignore `m.formatted_displayname`, and render the plain `displayname` instead, if this
text content is not exactly equal to `displayname`.

This rule means:

* Disambiguation, mentions, push rules, notifications and every other existing use of `displayname`
  keep working unchanged, and a formatted name can never *read* as anything other than the user's
  plain name. A user named "Alice" cannot render as "Admin".
* Clients that don't support this proposal are handled automatically. If a user changes their
  `displayname` from such a client, the old formatted name stops matching and is ignored, with no
  cleanup needed by the server.
* Using the shortcode as the `alt` text of a custom emoji maps directly onto the fediverse model:
  an ActivityPub actor's `name` can be used as `displayname` unchanged, and the formatted version is
  that name, HTML-escaped, with each `:shortcode:` replaced by an `<img>` whose `alt` is the
  shortcode.

Clients SHOULD use the emoji's shortcode, including surrounding colons, as the `alt` of an inline
image, so that the plain display name stays readable on clients that don't render images.

### Permitted HTML

Only inline formatting is permitted. Clients MUST NOT render any tag or attribute not listed below.
Disallowed tags SHOULD be stripped while keeping their text content, which may cause the consistency
check above to fail; this is intended.

| Tag | Permitted attributes |
|---|---|
| `b`, `strong` | none |
| `i`, `em` | none |
| `u` | none |
| `s`, `del` | none |
| `span` | `data-mx-color`, `data-mx-bg-color` |
| `img` | `src` (MUST be an `mxc://` URI), `alt`, `title`, `data-mx-emoticon` (MUST be present) |

Notably excluded, compared to the HTML permitted in messages:

* **All block-level elements** (`p`, `div`, `h1` to `h6`, `blockquote`, `ul`, `ol`, `li`, `pre`,
  `hr`, `br`, `table` and friends, `details`, `summary`). A display name is a single line of text.
* **`a`.** Links in names are a phishing risk, and clicking a name already has a meaning in most
  clients (opening the user's profile).
* **`data-mx-spoiler`.** Hidden text in a name helps impersonation.
* **`data-mx-maths`** and **`code`.** Not meaningful in a name.
* **`sup` and `sub`.** These can make rendered text look substantially different from its plain
  text content.
* **`img` without `data-mx-emoticon`.** Only custom emoji are allowed, not arbitrary images.

Clients MUST render inline images at the height of the surrounding text, ignoring any `width` or
`height` attributes, and SHOULD respect the user's preference for animated images (for example, not
autoplaying them unless the user has opted in).

**Fonts are intentionally out of scope.** The existing message HTML rules have no notion of font
family (the deprecated `font` tag only ever carried colours), so supporting font choice in names
would mean inventing a new attribute and deciding which fonts are allowed. This proposal leaves that
to a future MSC.

### Limits

* `formatted_body` MUST NOT exceed 1024 bytes when encoded as UTF-8.
* `formatted_body` MUST NOT contain more than 10 `<img>` elements.
* Tags MUST NOT be nested more than 10 levels deep.

Servers SHOULD reject attempts to set a value exceeding these limits with `400 M_INVALID_PARAM`.
Clients MUST ignore (fall back to the plain name for) values exceeding them. Note that the value is
copied into every `m.room.member` event for the user, so it contributes to room state size.

### Where formatted names are rendered

Clients SHOULD render the formatted name wherever they show a user's display name in the context of
a room they share, including the timeline, member list, and profile view.

Mention pills SHOULD render the formatted name of the mentioned user. The `body` and
`formatted_body` of the message itself continue to use the plain display name as text, as today.

Clients SHOULD NOT render formatted names, and SHOULD show the plain name instead, in:

* user directory search results;
* invites, until the user has accepted them;
* membership change notices (for example "X was banned"), so that a removed user's imagery isn't
  shown as part of their removal;
* contexts involving a user who has left, been kicked, or been banned from the room in question.

Clients SHOULD offer an option to disable formatted display names entirely.

## Potential issues

**Abuse through imagery.** Custom emoji in names put user-chosen images in many places across a
client, which is a moderation concern also raised by
[MSC4426](https://github.com/matrix-org/matrix-spec-proposals/pull/4426). The rendering guidance
above limits where images appear for users who aren't (or are no longer) in a shared room, and
banning a user removes their formatted name from the room's current state along with their
membership. The option to disable formatted names entirely gives users a final fallback.

**Room state size.** Every member event grows by up to the size of the formatted name. The 1024 byte
limit keeps this bounded.

**Stale formatted names.** A user who changes their name from a client without support for this
proposal leaves a stale `m.formatted_displayname` behind. The consistency rule makes this harmless,
but the stale value still takes up space until a supporting client clears or replaces it.

**Linked media.** If [MSC3911](https://github.com/matrix-org/matrix-spec-proposals/pull/3911) or
[MSC4396](https://github.com/matrix-org/matrix-spec-proposals/pull/4396) is accepted, media in a
formatted name will need the same linking treatment those proposals give to `avatar_url` in
`m.room.member` events. Until then, authenticated media means any logged-in user can fetch the
emoji images, as with avatars.

**Per-message profiles.** [MSC4144](https://github.com/matrix-org/matrix-spec-proposals/pull/4144)
defines a per-message `displayname`. A per-message formatted display name would be a natural
extension, but is left to that proposal or a future one.

## Alternatives

### Plain display name plus a shortcode map

The fediverse model: keep `displayname` as plain text containing `:shortcode:` tokens, and add a
map from shortcode to image:

```json
{
  "displayname": "Cat :blobcat: Person",
  "m.displayname_emoji": {
    ":blobcat:": "mxc://example.org/abc123"
  }
}
```

This needs no HTML parsing and is simpler to render safely. It was rejected because it only covers
custom emoji: it gives up bold, italics, colour and any other formatting, and any later extension
for those would need a second, separate mechanism. It also gives a client no way to tell an
intentional `:shortcode:` from the same text appearing literally in a name. The HTML approach covers
the emoji use case just as well (the consistency rule keeps the plain name identical to what the
fediverse model would produce) while reusing a format clients already have sanitisers for.

### Extensible events `m.text` array

[MSC4440](https://github.com/matrix-org/matrix-spec-proposals/pull/4440) uses an
[MSC1767](https://github.com/matrix-org/matrix-spec-proposals/pull/1767)-style `m.text` array for
its formatted biography field. The same shape could be used here. This proposal uses the
`format`/`formatted_body` pair instead because the plain representation already lives in
`displayname`, and duplicating it in the array would create two plain names that could disagree.

### No propagation to member events

The formatted name could live only in the global profile, fetched by clients on demand. This would
avoid growing room state, but would mean many extra profile requests to render a timeline or member
list, would make per-room formatted names impossible, and would make the formatted name behave
differently from the plain name it accompanies.

## Security considerations

* Clients MUST apply the permitted tag and attribute list strictly, as for message HTML, to avoid
  HTML injection and cross-site scripting.
* The consistency rule prevents a formatted name from showing different text from the plain name.
  However, custom emoji can still contain images of text; clients' existing defences against
  look-alike display names (disambiguation by user ID) continue to apply because they operate on
  the plain name.
* Colours can be used to make text unreadable or blend into the background. Clients MAY adjust or
  ignore colours to keep names legible, for example in high contrast themes.

## Unstable prefix

Until this proposal is accepted, implementations should use `org.matrix.mscVVVV.formatted_displayname`
in place of `m.formatted_displayname`, in both profiles and `m.room.member` events.

## Dependencies

This proposal depends on [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133)
(merged) for the profile field, and builds on custom emoticons from
[MSC2545](https://github.com/matrix-org/matrix-spec-proposals/pull/2545) (merged).
