# MSC2545: Image Packs (Emoticons & Stickers)

## Introduction

Custom emoticons and stickers have become commonplace in modern messaging apps.
They allow users to express themselves in ways that words - nor the
standard Unicode set - cannot. And they can be functional, allowing bots to convey
meaning with custom symbols in messages or reactions.

If Matrix is to remain both a fun and useful messaging protocol, as well as a
flexible platform for bridging into other protocols, support for custom
emoticons and stickers are a must.

This proposal outlines how custom emoticons and stickers can both be sent into
rooms, as well as organised into "packs" and shared between users.

## Proposal

### Terminology

#### Emoticons and emotes

There is confusion around how this relates to [`m.emote`
msgtype](https://spec.matrix.org/v1.14/client-server-api/#mroommessage-msgtypes)
as well as why this proposal isn't called "custom emoji", etc.

In short, `m.emote` is for emotion - and it has been incorrectly named this way.
`m.action` would have been more appropriate, as you use it to describe
*actions*, not *emotions*. E.g. "/me is walking to the gym", or "/me is happy"
and *not* "/me happy".

That, however, is not what this MSC is about. Instead, it is about emoticons,
also known in short as "emotes".

Emotes are images or text describing emotions or other things. Emoji are a
subset of emotes, namely those found within the Unicode spec. Custom emoji,
therefore, would actually refer to a custom emoji font; one's own rendering of
Unicode's 🦊, 🐱, etc. This differs from new images, which is what custom
emoticons are for.

A client may of course choose to name these however they like. In the spec's
history, it has had naming disparity with clients, i.e. "groups" vs
"communities". It is, however, imperative to name things in the spec accurately
after what they are.

#### Stickers

Stickers already exist in Matrix (see the [`m.sticker` event
type](https://spec.matrix.org/v1.14/client-server-api/#msticker)). They are
reusable images one can send; typically as a reaction to something sent in the
timeline. The value this MSC brings to stickers is creating a mechanism to
distribute them, such that a client can surface them to a user to choose and
send.

#### Shortcodes

A "shortcode" is a short, unique identifier for an emote or a sticker.

A shortcode is NOT intended to be a visual description of an image, often to
aide the visually impaired. That is more suitable to the `body` field, defined
as part of an "Image object" below and on
[`m.sticker`](https://spec.matrix.org/v1.14/client-server-api/#msticker) events.

### Image packs

Part of the joy of custom emotes (and stickers) is to be able to organise them
into packs and share these packs with others. This proposal defines a mechanism
for doing so.

#### `m.image_pack` state event

Image packs are defined by a new state event with type `m.image_pack`. The
`state_key` is simply a unique identifier for the pack itself. It is not
intended to be surfaced to users. This proposal does not associate any special
property with an empty string for an image pack's `state_key`.

`m.image_pack` state events contain the following keys within their `content`:

* `images`: **Required, Map[String, Object]**. A map from a shortcode ([grammar](#shortcode-grammar)) to an [Image Object](#image-object).
* `pack` **Optional, Object**. A [Pack Object](#pack-object).

```jsonc
{
  "type": "m.image_pack",
  "state_key": "Blobcats",
  "content": {
    "images": {
      "blob_amused": { /* ... Image Object ... */ },
      "blob_angel": { /* ... Image Object ... */ }
    },
    "pack": { /* ... Pack Object ... */ }
  },
  // ...
}
```

#### Pack object

A pack object consists of the following keys:

- `display_name`: **Optional, String**. A display name for the pack.
    If unset, and the pack event is within a room, defaults to the room's name.
    Otherwise, the pack does not have a name.
    This does not have to be unique from other packs in a room.
- `avatar_url`: **Optional, String**. The MXC uri of an avatar/icon to display
    for the pack. If unset, and the pack is within a room, defaults to the
    room's avatar.
    Otherwise, the pack does not have an avatar.
- `usage`: **Optional, Array[String]**. An array of the usages for this pack.
    Possible usages are `emoticon` and `sticker`. If the usage array is absent or
    empty, all possible usage types are assumed. Client SHOULD use this field to
    determine when to suggest images to use (i.e. in a sticker picker, emoji
    picker) from an image pack.
- `attribution`: **Optional, String**. The attribution for this pack.

An example of a pack object:

```json
{
  "display_name": "Awesome Pack",
  "avatar_url": "mxc://element.io/6130836e26b462a6fe63d4e080dd9d2037490f2b",
  "usage": ["emoticon"],
  "attribution": "From https://commons.wikimedia.org/wiki/Category:Blob_emoji and various Fediverse instances"
}
```

#### Image object

An image object consists of the following keys:

- `url`: **Required, String**. The MXC URL for this image.
- `body`: **Optional, String**. A textual representation or associated 
    description of the image.
- `info`: **Optional, ImageInfo**. The already specified
    [`ImageInfo`](https://spec.matrix.org/v1.14/client-server-api/#msticker_imageinfo) 
    object (from `m.sticker`).

An example of an image object:

```jsonc
{
  "url": "mxc://element.io/1c8cac2c949b11649140b446d969d1934c59facf",
  "body": "a lazy cat lays on the floor",
  "info": {
    // ... ImageInfo ...
  }
}
```

Taking all of this into account, a full image pack event may look like:

```json
{
  "images": {
    "myemote": {
      "url": "mxc://example.org/blah"
    },
    "mysticker": {
      "url": "mxc://example.org/sticker",
      "usage": ["sticker"]
    }
  },
  "pack": {
    "display_name": "Awesome Pack",
    "usage": ["emoticon"],
    "attribution": "drawn by @kayley:example.org"
  }
}
```

#### User and room image packs

A room itself can have an unlimited amount of image packs by specifying the
`m.image_pack` state event with different state keys. By default, the user
SHOULD be presented with these images only when interacting in the room that
the packs are defined in.

For a user to enable a room image pack to be presented in all rooms, the room ID
can be added to a `m.image_pack.rooms` account data event.

#### `m.image_pack.rooms` account data event

The `m.image_pack.rooms` account data event consists of the following:

- `rooms` **Required, Map[String, Map[String, Object]]**. A map of room ID to
    another map: from `state_key` to an empty object.

This data structure allows specifying a single room image pack given the pack's
room ID and `state_key`.

Clients should make the corresponding room image packs globally accessible in all
rooms.

While this MSC does not define any keys for the bottom-level object, defining it
as an object means greater flexibility in the case of future changes. For
instance, a future MSC could define only certain images to be sourced from a
pack, instead of the entire pack.

An example of a `m.image_pack.rooms` account data event:

```json
{
  "rooms": {
    "!someroom:example.org": {
      "": {},
      "de.sorunome.mx-puppet-bridge.discord": {}
    },
    "!someotherroom:example.org": {
      "": {}
    }
  }
}
```

An empty object under a room ID, for example:

```json
{
  "rooms": {
    "!someroom:example.org": {}
  }
}
```

translates to *all image packs that a room defines*, rather than *no image
packs*. This is intended as an optimisation to reduce event size versus
listing the (potentially many) packs a room may have.

"All image packs that a room defines" does not include second-order packs listed
in `m.image_pack.rooms` state events (defined below) in the room. This is to
prevent loops when sourcing image packs.

Clients should be aware that users may not be in the room referenced by this
event, and MAY wish to show appropriate UX around this.

#### `m.image_pack.rooms` state event

This state event can be added to a room in order to reference an existing image
pack from another room. This allows room administrators to make an image pack
available to their local community without copying (and continuously updating)
said packs.

This state event has a similar structure to the equivalent account data event,
and must have an empty state key:

```json
{
  "type": "m.image_pack.rooms",
  "state_key": "",
  "content": {
    "rooms": {
      "!someroom:example.org": {
        "": {},
        "de.sorunome.mx-puppet-bridge.discord": {}
      },
      "!someotherroom:example.org": {
        "": {}
      }
    }
  }
}
```

The definition of an empty object under a room ID from the `m.image_pack.rooms`
account data event holds for this state event as well.

Clients should be aware that users may not be in the room referenced by this
event, and MAY wish to show appropriate UX around this.

#### Space image packs

Clients SHOULD suggest image packs of a room's canonical space, if the user is
also in that space. This should be done recursively on canonical spaces. So, if
a room has a canonical space and that space again has a canonical space, the
clients should suggest image packs of both of those spaces.

Care should be taken to avoid cycles when iterating, and to limit the max chain
length of rooms to a sensible number.

#### Image pack source priority

If a client gives image suggestions (emotes, stickers) to the user in some
ordered fashion (e.g. an ordered list where you click an entry), the order of
the image packs SHOULD be predictable between rooms.

A suggestion for clients of image pack ordering is as follows:

1. User image pack (defined in the user's account data)
2. Image pack rooms (defined in the `m.image_pack.rooms` user account data
    object)
3. Room image packs (defined in the currently open room's state)
4. Referenced room image packs (defined in the `m.image_pack.rooms` room
    state event)
5. Space image packs (defined in the hierarchy of canonical spaces for the
    current room)

Note: this MSC does not define an ordering for images within packs. That is left
to a future MSC.

### Image properties

Emoticons SHOULD be at least 128x128 pixels. This is to ensure that custom emotes look good, even on higher DPI displays.

Stickers SHOULD be at least 512x512 pixels, for the same reason.

Images filetypes are not limited by this proposal. Instead they are
equivalent to the formats allowed in an
[`m.image`](https://spec.matrix.org/v1.11/client-server-api/#mimage) event. As
of writing, no limitations for `m.image` are currently defined (see [this spec
issue](https://github.com/matrix-org/matrix-spec/issues/453)).

Emotes and stickers may be animated, and clients may choose to pause animations
based on user preferences.

### Shortcode grammar

A shortcode's length MUST not exceed 100 bytes. This is to prevent a
sufficiently long shortcode from being impossible to insert into subsequent events
due to exceeding the event limit (e.g. emoji reactions). This restriction MUST be
enforced by servers when sending reactions, but servers MUST NOT reject events
coming across federation due to having too many bytes in the shortcode field.
This avoids a split-brain in the room. Servers MAY opt to locally redact events
having too many bytes in the shortcode field.

The `:` character MUST NOT be included in the emote shortcode. The `:` character
has become synonymous with emotes - oftentimes typing the `:` character in a
message field will allow one to filter and choose and emote to send.

To avoid client fragmentation, with some clients opting to trim `:` when
displaying emote shortcodes and others leaving it in, the `:` character is
barred from the shortcode grammar. This is in attempt to standardise `:` as the
delimiter character for shortcodes.

Similarly, the `/` character MUST NOT be included in the emote shortcode. This
character may be used by clients to deliminate between shortcode and image pack
when designing auto-completion UI in the message field (i.e. `:some_emote/my_pack_slug:`)

In addition, the space character is not allowed. This helps avoid common
usability paper-cuts (multiple spaces between words, spaces at the beginning/end
of a shortcode). Shortcodes containing multiple words are encouraged to use alternative
separators like hyphens (`-`) or underscores (`_`).

Specifically, the `U+0020` character (normal space) is disallowed. There are
multiple other byte sequences associated with spaces in Unicode, but as this is
only intended to eliminate a common foot gun, more esoteric space characters are
not considered.

Any other character is explicitly allowed. This allows shortcodes containing
non-Latin characters for communities of those languages, and ensures
forwards-compatibility with future Unicode updates.

### Sending

#### Custom emotes

Custom emotes are sent into rooms as `<img>` tags within the `formatted_body`
field of an
[`m.room.message`](https://spec.matrix.org/v1.14/client-server-api/#mroommessage)
event. Many existing clients already render `<img>` tags in message bodies when
they render HTML, and it's logical to reuse that functionality here.

To allow clients to distinguish custom emotes from other inline images, a new
attribute, `data-mx-emoticon`, is introduced to the `<img>` tag:

```html
<img data-mx-emoticon src="mxc://example.org/emote" alt="A cat holding a paper heart" title="cat_luvs_u" height="32" />
```

A client should treat an `<img>` tag as a custom emote if the custom
`data-mx-emoticon` attribute is present. If this attribute has a value, that
value is ignored. Some libraries may automatically add an empty value, i.e.
`data-mx-emoticon=""`.

##### `src` attribute

The `src` attribute is required and MUST be a [Matrix Content (MXC)
URI](https://spec.matrix.org/v1.14/client-server-api/#matrix-content-mxc-uris).
Other URI schemes, such as `https`, `mailto` etc. are not allowed. Clients MUST
NOT attempt to render images accessible through other URI schemes, as this may
lead to unintended network requests.

##### `alt` attribute

The `alt` attribute MUST be present. Its value SHOULD be the `body` of the emote, or if unavailable, its shortcode.

The `alt` attribute's meaning is inherited from the HTML specification:
<https://html.spec.whatwg.org/multipage/images.html#alt>. It is primarily used
for accessibility purposes in describing an image for visually impaired users.

##### `title` attribute

The `title` attribute MUST be present. Its value SHOULD be the shortcode of the
emote.

The `title` attribute's meaning is inherited from the HTML specification:
<https://html.spec.whatwg.org/multipage/dom.html#attr-title>. It is primarily
used for advisory information, such as tooltips. This could allow users viewing
a message to quickly find the shortcode of a given emote in order to send it in
their own messages.

##### `height` attribute

The `height` attribute MUST be present. This maintains backwards-compatibility
with clients that do not support custom emotes.

Clents SHOULD set `height` to "32px". This is a default intended to look good on
most devices, and is for the benefit of legacy clients that do not treat custom
emotes differently from other inline images.

Clients implementing this MSC are expected to override the height when rendering
emotes, based on their particular environment (the user's font size, etc.). Or
they may choose to display messages containing only emoticons in a larger font.

A `width` attribute is not required, in order to maintain the aspect ratio of
non-square emotes.

##### Client suggestions

A client could use the `:` delimiter to signify that the user wants to send an
emote. Typing `:` and then a character could initiate a search action through
available emotes.

If there are multiple emotes with the same shortcode available (from multiple
packs), the client could slugify the containing pack's display name and append
it to each emote's shortcode, using a `/` to separate shortcode and image pack.
For instance, the user could enter `:my_emo/my_pack_na:` to quickly surface an
image with shortcode `my_emote` in the pack `My Pack Name!`.

It's important to note that image pack names aren't globally unique either, so
even `:emote/my-pack:` could refer to multiple possible emotes. Thus, it is not
recommended to add a feature to clients to try and automatically translate
`:shortcode:` or `:shortcode/image-pack-name:` in the message field to a
specific emote.

A "search modal" or other UI that allows the user to tie-break is the approach
recommended by this proposal.

#### Stickers

When sending a sticker, the `body` field of the `m.sticker` event SHOULD be set
to the `body` defined for that image, or if absent, its shortcode.

The `info` object of the `m.sticker` event SHOULD be set to the `info` object of
the image, or if absent, an empty object.

## Security Considerations

### Encrypted image packs

This MSC considers that image packs, and the images contained within them, are
not encrypted. That means media included in image packs cannot be hidden from
the homeserver. That is a privacy and security concern.

In addition, a homeserver could deduce from traffic patterns that an encrypted
event contains a certain emote by correlating the time an event was sent with
other local, participating user's access requests to a particular piece of
media. This is not a new concern, as the same attack can be performed for links
sent in a chat with URL previews enabled in clients. In addition, caching of
images across clients can help with reducing the need to download the media
again.

Encrypting image packs is dependent on encrypted state events being implemented
in the protocol; potentially by
[MSC3414](https://github.com/matrix-org/matrix-spec-proposals/pull/3414) or
another MSC.

Once encrypted state events are implemented, images could be encrypted before
upload with a symmetric key included within the encrypted state event. Then,
said key would be sent within the `<img>` tag emotes are sent in, allowing
other clients to download and decrypt the media. [This matrix-spec
issue](https://github.com/matrix-org/matrix-doc/issues/2418) calls for
standardising this behaviour for any kind of inline image.

Encrypted emotes sent in *non-E2EE* rooms would leak these keys, but this may
be deemed acceptable as many emotes would not be leaked. Plus, it still
raises the barrier for homeserver operators to implement tooling to browse
messages in E2EE rooms.

Ultimately end-to-end encryption of image packs or emoticons is purposefully
not within the scope of this MSC. That being said, clients SHOULD warn users
that images in image packs sent in E2EE rooms are not encrypted and thus
visible to homeservers.

### Abusive images in packs

There is the potential for the administrator of an image pack, after getting
users and rooms to add the pack, to add abusive imagery to the pack that
users will then be exposed to. This is enabled by the `m.image_pack.rooms`
state and account data events, which allow referencing external image packs.

This can be mitigated after the fact depending on how the user's client has
sourced the offensive images:

1. The user has enabled a pack globally that's defined by a room
2. The user is suggested a pack by their client as the current room they're
    typing in references a pack (space, the new `m.image_pack.rooms` state
    event, etc.)

For 1., the user should remove the pack from their global configuration. For 2.,
the user should inform the room admin. If the room admin should disappear, then
this is fairly similar to an attacker spamming a room which has no moderation.

Given the benefits of the features, and the assumption that such an attack has
limited impact and rarely affects other messaging services, the features are
left in.

## Unstable prefix

| **Stable identifier** | **Unstable identifier** |
|---|---|
| `m.image_pack` state event type | `im.ponies.room_emotes` |
| `m.image_pack.rooms` account data event type | `im.ponies.emote_rooms` |

## Potential Issues

### Event size limits

Due to the [size limitation of
events](https://spec.matrix.org/v1.14/client-server-api/#size-limits) (65536
bytes), room image packs are limited to roughly 400 emotes per pack (see [this
calculation](https://github.com/matrix-org/matrix-spec-proposals/pull/2545/files#r1705977956)).

This has been deemed sufficient for the vast majority of use cases.

### Multiple usages per pack complicates pack management client UI

It's possible that allowing a pack to have multiple usages can complicate
implementing UI for managing packs. See [this
thread](https://github.com/matrix-org/matrix-spec-proposals/pull/2545#discussion_r1734825589).
This was considered acceptable, as the benefit of being able to use a single
pack in multiple contexts, as well as this MSC originally allowing multiple
usages-per-pack for much of its implementation lifespan, were considered to
outweigh the alternative.

## Alternatives

One can easily think of near infinite ways to implement emotes. The aspect of
sending an `<img>` tag and marking it as an emote with `data-mx-emoticon` seems
to be pretty universal though, so the question is mainly on different emote
sources. For that, a separate MSC,
[MSC1951](https://github.com/matrix-org/matrix-doc/pull/1951) already exists, so
it is reasonable to compare this one with that one:

### Comparison with MSC1951

[MSC1951](https://github.com/matrix-org/matrix-spec-proposals/pull/1951) defines a dedicated room as the only image pack source. This MSC, however, also allows you to bind image packs
to your own account, offering greater flexibility. In MSC1951 there can also only be a single image pack
in a room. This could be problematic in e.g. bridged rooms: You set some emotes or stickers from the matrix
side and a discord bridge would plop all the discord emotes and stickers in another pack in the same room.

The original sharing-focused idea of MSC1951 is still preserved: you could
easily have an image pack-only room via a new room type.

MSC1951 defines a way to recommend using a pack of a different room - this MSC does not have an equivalent
to that. Instead, this MSC allows multiple image packs for a room, typically one where you already
chat in anyways. Furthermore, it allows you to enable an image pack to be globally available for yourself
across all rooms you are in.

The core difference is how MSC1951 and this MSC define the image packs themselves: In MSC1951 you have to
set one state event *per image*. While this might seem like a nice idea on the surface, it doesn't
scale well. There are people who easily use and want hundreds or even thousands of image packs accessible.
A simple dict of shortcode to mxc URI seems more appropriate for this.

In general, MSC1951 feels like a heavier approach to image pack sources, while this MSC is more lightweight.

## Future ideas

A couple of interesting points have been raised in discussions of this MSC that
tangentially touch custom emotes. Each warrant an MSC for themselves.

- Include a backlink to image packs from custom emotes/stickers in events,
  allowing users to see an image pack an emote or sticker came from. See [this
  thread](https://github.com/matrix-org/matrix-spec-proposals/pull/2545/files#r2020176546)
  and
  [this thread](https://github.com/matrix-org/matrix-spec-proposals/pull/2545#discussion_r753881475)
  for discussion on the matter.
- Allow SVGs in the `<img>` tag. Currently clients try to thumbnail the mxc URL,
    and most media repositories can't thumbnail SVGs. Possible solution: Somehow embed the mimetype.
- For stickers: Recommend rendering sizes / resolutions
- Loading placeholders for emotes and stickers (i.e. via blurhashes
    [MSC2448](https://github.com/matrix-org/matrix-spec-proposals/pull/2448) or
    vector paths) 

## Dependencies

This MSC does not depend on any other MSCs.
