# MSC2545: Image Packs (Emoticons & Stickers)

Custom emoticons and stickers have become commonplace in modern messaging apps.
They allow users to express themselves in ways that words, nor the
standard Unicode set cannot. And they can be functional, allowing bots to convey
meaning with custom symbols in messages or reactions.

If Matrix is to remain both a fun and useful messaging protocol, as well as a
flexible platform for bridging into other protocols, support for custom
emoticons and stickers are a must.

This proposal outlines how custom emoticons and stickers can both be sent into
rooms, as well as organised into "packs" and shared between users.

## Terminology
### Emoticons
Since there is a lot of confusion of how this relates to `m.emote`, why this isn't called "custom emoji"
etc,:

`m.emote` is for emotion - and it has been incorrectly named this way. `m.action` would have been more
appropriate, as you use it to describe *actions*, not *emotions*. E.g. "/me is walking to the gym", or
"/me is happy" and *not* "/me happy".

That, however, is *not* what this MSC is about. Instead, it is about emoticons, also known in short as
emotes.

Emoticons are just little images or text describing emotions or other things. Emoji are a subset of
emoticons, namely those found within unicode. Custom emoji here would actually refer to a custom emoji
font, that is your own rendering of 🦊, 🐱, etc., *not* new images. New images is what custom emoticons
are for.

Now, a client may choose to name these however they like. In the spec's history,
it has had naming disparity with clients, i.e. "groups" vs "communities". It is,
however, imperative to name things in the spec accurately after what they are.

### Stickers
Stickers already exist in Matrix. They are reusable images one can send, usually as a reaction to
something sent in the timeline. This MSC adds a way to distribute and define a source for a client to
send them.

## Proposal
### Emoticons in the formatted body
Emoticons have at least a shortcode and a mxc uri. A shortcode is a short identifier for an emoji. They 
are sent as `<img>` tags, which are currently in the spec. As such, many existing clients are able to render them.
To allow clients to distinguish emoticons from other inline images, a new
property, `data-mx-emoticon`, is introduced. A client can choose to ignore the size attributes of emoticons
when rendering, and instead pick the size based on other circumstances. This could e.g. be used to
display messages with only emoticons and emoji as larger than usual, which is commonly found in
messengers. Such an `<img>` tag of a shortcode `emote` and a mxc uri `mxc://example.org/emote`
could look as follows:

The shortcode must have a length of less than or equal to 100 bytes. This restriction must be enforced by 
servers when sending reactions, but servers should not reject events coming across federation due to having 
too many bytes in the shortcode field. Servers may still opt to locally redact events having too many bytes 
in the shortcode field.

The `:` character MUST NOT be included in the emote shortcode, so as not to end up with fragmentation with 
some clients removing `:` from the UI. Other than `:`, any other character is explicitly allowed so that 
we do not exclude languages which do not use the Latin alphabet.

```html
<img data-mx-emoticon src="mxc://example.org/emote" alt="emote" title="emote" height="32" />
```

`alt` and `title` are required attributes for their roles in accessibility and
improved UX. Their meaning is inherited from the HTML specification
([alt](https://html.spec.whatwg.org/multipage/images.html#alt),
[title](https://html.spec.whatwg.org/multipage/dom.html#attr-title)).

The `height` SHOULD be set to "32px". This is a default that looks good on most
devices. In practice, receiving clients are expected to override the height when
rendering emotes based on their particular environment (the user's font size,
etc.). In order to maintain backwards-compatibility with clients that do not
support emotes, specifying the `height` is required. No width is specified as to
maintain the aspect ratio of non-square emotes. 

If the new `data-mx-emoticon` attribute has a value, that value is ignored. Due to limitations of some libraries
the attribute may even look like `data-mx-emoticon=""`.

The `src` attribute *must* be a mxc URI. Other URI schemes, such as `https`,
`mailto` etc. are not allowed. Clients MUST NOT attempt to render images
accessible through other URI schemes.

### Sending stickers
To send stickers, the already spec'd
[`m.sticker`](https://spec.matrix.org/v1.11/client-server-api/#msticker) is
used.

### Image types
Emoticons SHOULD be at least 128x128 pixels. Even though the fallback specifies
a height of 32, this is to ensure that emotes still look good on higher DPI screens.

Stickers SHOULD be at least 512x512 pixels, for the same reason.

Images filetypes are not limited by this proposal. Instead they are
equivalent to the formats allowed in an
[`m.image`](https://spec.matrix.org/v1.11/client-server-api/#mimage) event. As
of writing, no limitations for `m.image` are currently defined (see [this spec
issue](https://github.com/matrix-org/matrix-spec/issues/453)).

Emoticons and stickers may be animated.

### Image pack event
The image pack event has a type of `m.image_pack`. It contains a key `images`, which is a map from a
short code to an image object. It may also contain a key `pack`, which is a pack object, described in
the following section.

#### Pack object
The pack object consists of the following keys:
 - `display_name`: (String, optional) A display name for the pack. Defaults to the room name, if the
   image pack event is in the room. This does not have to be unique from other packs in a room.
 - `avatar_url`: (String, optional) The mxc uri of an avatar/icon to display for the pack. Defaults
   to the room avatar, if the pack is in the room. Otherwise, the pack does not have an avatar.
 - `usage`: (String[], optional) An array of the usages for this pack. Possible usages are `"emoticon"`
   and `"sticker"`. If the usage is absent or empty, a usage for all possible usage types is to be assumed.
 - `attribution`: (String, optional) The attribution of this pack.

Example:
```json
{
  "display_name": "Awesome Pack",
  "usage": ["emoticon"]
}
```

#### Image object
The image object consists of the following keys:
 - `url`: (String, required) The mxc URL for this image.
 - `body`: (String, optional) An optional text body for this image. Useful for the sticker body text or
   the emote alt text. Defaults to the shortcode.
 - `info`: (`ImageInfo`, optional) The already spec'd `ImageInfo` object used for the `info` block of
   `m.sticker` events.
 - `usage`: (String[], optional) An array of the usages for this image. The possible values match those
   of the `usage` key of a pack object. If present and non-empty, this overrides the usage defined at
   pack level for this particular image. This is useful to e.g. have one pack contain mixed emotes and
   stickers. Additionally, as there is only a single account data level image pack, this is required to
   have a mixture of emotes and stickers available in account data.

#### Example image pack event
Taking all of this into account, an example pack event may look like the following:
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
    "usage": ["emoticon"]
  }
}
```

### Image sources
There are several places where a client is expected to look for events with type `m.image_pack`, mainly
in their own account data and in room state.

#### User image packs
Each user can have their own personal image pack defined in their account data, under the
`m.image_pack` key. The user is expected to be presented with these images in all rooms.

#### Room image packs
A room can have an unlimited amount of image packs, by specifying the `m.image_pack` state event with
different state keys. By default, the user is expected to be presented with these images only in the room they
they are defined in. To enable them to be presented in all rooms, see the "Image pack rooms" section.
E.g. a discord bridge could set as state key
`de.sorunome.mx-puppet-bridge.discord` and have all the bridged emotes in said state event, keeping
bridged emotes from matrix emotes separate.

#### Space image packs
Clients should suggest image packs of a room's canonical space, if the user is also in that space.
 This should be done recursively on canonical spaces. So, if a room has a canonical space and
that space again has a canonical space, the clients should suggest image packs of both of those spaces.

#### Image pack rooms
While room image packs are specific to a room, they can be made accessible from anywhere by setting
the `m.image_pack.rooms` key in a user's account data. The value is an object, with a `room` key containing
a map of room ids to the state keys to an object. If a room id / state key combination is provided in this form,
clients should make the corresponding room image pack globally accessible in all rooms.

Note that while this MSC does not define any keys for the bottom-level object, defining it as an object means greater
flexibility in the case of future changes.

The contents of `m.image_pack.rooms` could look like the following:

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

Here three emote packs are globally accessible to the user: Two defined in `!someroom:example.org`
(one with blank state key and one with state key `de.sorunome.mx-puppet-bridge.discord`) and one in
`!someotherroom:example.org` (with a blank state key).

### Image pack source priority
If a client gives image suggestions (emotes, stickers) to the user in some ordered fashion (e.g. an
ordered list where you click an entry), the order of the images should be predictable between rooms.
A suggestion for clients of image pack ordering is as follows:
1. User image pack (defined in your own account data)
2. Image pack rooms (defined in the `m.image_pack.rooms` account data object)
3. Space image packs (defined in the hierarchy of canonical spaces for the current room)
4. Room image packs (defined in the currently open room's state)

### Sending
#### Emoticons
For emoticons a client could add delimiters (e.g. `:`) around the image shortcode, meaning
that if an image has a shortcode of `emote`, the user can enter `:emote:` to send it. If there are
multiple emoticons with the same shortcode in a room, the client could e.g. slugify the packs display
name and then have the user enter `:slug~emote:`. As slugs typically match `^[\w-]+$`, that should
ensure complete-ability.

The alt / title text for the `<img>` tag is expected to be the `body` of the emote. If absent, its
shortcode should be used instead.

#### Stickers
When sending a sticker, the `body` of the `m.sticker` event should be set to the `body` defined for that
image, or if absent, its shortcode.

The `info` object of the `m.sticker` event should be set to the `info` object of the image, or if absent,
an empty object.

## Security Considerations
When sending an `<img>` tag in an encrypted room, the client will make a request to fetch
said image, in this case an emote. As there is no way to encrypt content behind `<img>` tags yet,
this could potentially leak part of the conversation. This is **not** a new security consideration,
it already exists. This, however, isn't much different from posting someone a link in an e2ee chat and
the recipient opens the link. Additionally, images, and thus emotes, are often cached by the client,
not even necessarily leading to a http query.

This MSC considers that imag epacks are not encrypted and that is a privacy and security concern.

Encrypting image packs is dependent on encrypted state events being implemented in the protocol, potentially 
by MSC3414 or another MSC.

End to End Encryption isn't in the scope of this MSC. Clients should warn users that images in image packs 
sent in E2EE rooms are not encrypted and thus visible to homeservers.

Related issue: https://github.com/matrix-org/matrix-doc/issues/2418

## Unstable prefix
The `m.image_pack` in the account data is replaced with `im.ponies.user_emotes`. The `m.image_pack` in
the room state is replaced with `im.ponies.room_emotes`. The `m.image_pack.rooms` is replaced with
`im.ponies.emote_rooms`.

Some existing implementations using `im.ponies.user_emotes` and `im.ponies.room_emotes` currently use
a dict called `short` which is just a map of the shortcode to the mxc url.

Some other implementations currently also call the `images` key `emoticons`.

## Potential Issues

### Multiple usages per pack complicates pack management client UI

It's possible that allowing a pack to have multiple usages can complicate implementing UI for managing packs. 
This was considered acceptable, as the benefit of being able to use a single pack in multiple contexts, as 
well as this MSC originally allowing multiple usages-per-pack for much of its implementation lifespan, were 
considered to outweigh the alternative.

### Event size limits

Due to size limitations of events (65535 bytes), image packs are limted to around 400 emotes per pack. This 
has been deemed sufficient for the vast majority of use cases.

## Alternatives
One can easily think of near infinite ways to implement emotes. The aspect of sending an `<img>` tag
and marking it as an emote with `data-mx-emoticon` seems to be pretty universal though, so the question
is mainly on different emote sources. For that, a separate MSC, [MSC1951](https://github.com/matrix-org/matrix-doc/pull/1951)
already exists, so it is reasonable to compare this one with that one:

### Comparison with MSC1951
MSC1951 defines a dedicated room as the only image pack source. This MSC, however, also allows you to bind image packs
to your own account, offering greater flexibility. In MSC1951 there can also only be a single image pack
in a room. This could be problematic in e.g. bridged rooms: You set some emotes or stickers from the matrix
side and a discord bridge would plop all the discord emotes and stickers in another pack in the same room.

The original sharing-focused idea of MSC1951 is still preserved: Once room types are a thing, you could
still easily have an image pack-only room.

MSC1951 defines a way to recommend using a pack of a different room - this MSC does not have an equivalent
to that. Instead, this MSC allows multiple image packs for a room, typically one where you already
chat in anyways. Furthermore, it allows you to enable an image pack to be globally available for yourself
across all rooms you are in.

The core difference is how MSC1951 and this MSC define the image packs themselves: In MSC1951 you have to
set one state event *per image*. While this might seem like a nice idea on the surface, it doesn't
scale well. There are people who easily use and want hundreds or even thousands of image packs accessible.
A simple dict of shortcode to mxc URI seems more appropriate for this.

In general, MSC1951 feels like a heavier approach to image pack sources, while this MSC is more lightweight.

## Looking further
A couple of interesting points have been raised in discussions of this MSC that tangentially touch
custom emoticons. Each warrant an MSC for themselves however, as they touch more on how `<img>` is works.
 - Figuring out how `<img>` should work with encrypted media.
 - Allow SVGs in the `<img>` tag. Current problem: Clients typically try to thumbnail the mxc URL,
   and most media repositories can't thumbnail SVGs. Possible solution: Somehow embed the mimetype.
 - For stickers: Recommend rendering sizes / resolutions

## Dependencies

This MSC does not depend on any other MSCs.