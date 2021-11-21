# MSC2545: Image Packs (Emoticons & Stickers)

Emoticons, or short emotes...we need them!

We also need proper stickers, too!

## Terminology
### Emoticons
Since there is a lot of confusion of how this relates to `m.emote`, why this isn't called "custom emoji"
etc.:

`m.emote` is for emotion - and it has been incorrectly named this way. `m.action` would have been more
appropriate, as you use it to describe *actions*, not *emotions*. E.g. "/me is walking to the gym", or
"/me is happy" and *not* "/me happy".

That, however, is *not* what this MSC is about. Instead, it is about emoticons, also known in short as
emotes.

Emoticons are just little images or text describing emotions or other things. Emoji are a subset of
emoticons, namely those found within unicode. Custom emoji here would actually refer to a custom emoji
font, that is your own rendering of 🦊, 🐱, etc., *not* new images. New images is what custom emoticons
are for.

Now, a client may choose to name these however they like. We already have a naming disparity between
spec and clients with groups vs communities. It is, however, imperative to name things in the spec
accurately after what they are.

### Stickers
Stickers already exist in Matrix. They are reusable images one can send, usually as a reaction to
something sent in the timeline. This MSC adds a way to distribute and define a source for a client to
send them.

## Proposal
### Emoticons in the formatted body
Emoticons have at least a shortcode and a mxc uri. They are sent as `<img>` tags, which are currently in
the spec. As such, many existing clients are already be able to render them.
To allow clients to distinguish emoticons from other inline images, a new
property, `data-mx-emoticon`, is introduced. A client can choose to ignore the size attributes of emoticons
when rendering, and instead pick the size based on other circumstances. This could e.g. be used to
display messages with only emoticons as larger than usual, which is commonly found in
messengers. Such an `<img>` tag of a shortcode `emote` and a mxc uri `mxc://example.org/emote`
could look as follows:

```html
<img data-mx-emoticon src="mxc://example.org/emote" alt=":emote:" title=":emote:" height="32" />
```

Both the `alt` and the `title` attributes are specified as they serve different purposes: `alt` is
displayed if e.g. the emote does not load. `title` is displayed e.g. on mouse hover over the emote.
Thus, specifying both the `alt` and `title` attributes is required.

The `height` is just a height that looks good on most devices with the normal, default font size.
No width is displayed as to not weirdly squish non-square emotes. In order to maintain backwards-compatibility
with clients not supporting emotes, specifying the `height` is required.

If the new `data-mx-emoticon` attribute has a value, it is ignored. Due to limitations of some libraries,
the attribute may even look like `data-mx-emoticon=""`.

The `src` attribute *must* be a mxc url. Other URIs, such as `https`, `mailto` etc. are not allowed.

### Sending stickers
To send stickers, the already spec'd `m.sticker` is used.

### Image types
Emoticons are recommended to have a size of about 128x128 pixels. Even though the fallback specifies
a height of 32, this is to ensure that the emotes still look good on higher DPI screens.

Stickers are recommended to have a size of up to 512x512 pixels.

Furthermore, these images should either have a mimetype of `image/png`, `image/gif` or `image/webp`.
They can be animated.

Due to the low resolution of emotes, `image/jpg` and `image/jpeg` have been purposefully excluded from this
list.

### Image pack event
The image pack event has a type of `m.image_pack`. It contains a key `images`, which is a map from a
shortcode to an image object. It may also contain a key `pack`, which is a pack object, described in
the following section.

#### Pack object
The pack object consists of the following keys:
 - `display_name`: (String, optional) A display name for the pack. Defaults to the room name, if the
   image pack event is in a room. This does not have to be unique from other packs in a room.
 - `avatar_url`: (String, optional) The mxc uri of an avatar/icon to display for the pack. Defaults
   to the room avatar, if the pack is in a room. Otherwise, the pack does not have an avatar.
 - `usage`: (String[], optional) An array of the usages for this pack. Possible usages are `"emoticon"`
   and `"sticker"`. Defaults to `["emoticon", "sticker"]` if absent or an empty array.
 - `attribution`: (String, optional) The attribution of this pack.

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
There are several places where a client is expected to look for these `m.image_pack` events, mainly
in their own account data and in room state.

#### User image packs
Each user can have their own personal image pack defined in their account data, under the
`m.image_pack` key. The value matches the shape of the `m.image_pack` room state event.
The user is expected to be presented with these images in all rooms.

#### Room image packs
A room can have an unlimited amount of image packs, by specifying the `m.image_pack` state event with
different state keys. By default, the user is expected to be presented with these images only in the room
they are defined in. To enable them to be presented in all rooms, see the "Image pack rooms" section.
An empty state key is the default pack for a room.
E.g. a discord bridge could set as state key
`de.sorunome.mx-puppet-bridge.discord` and have all the bridged emotes in said state event, keeping
bridged emotes from matrix emotes separate.

#### Space image packs
Clients should suggest image packs of a room's canonical space if the user is in that space.
This should be done recursively on canonical spaces. So, if a room has a canonical space and
that space again has a canonical space, clients should suggest image packs of both spaces.

#### Image pack rooms
While room image packs are specific to a room, they can be made accessible from anywhere by setting
the `m.image_pack.rooms` key in a user's account data. The value is an object, with a `room` key containing
a map of room ids to state keys to an object. If a room id / state key combination is provided in this form,
clients should make the corresponding room image pack globally accessible in all rooms.

Note that while this MSC does not define any for the bottom-level object, defining it as an object means greater
flexibility in case of future changes.

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

### Image pack source priority and de-duplication
If a client gives image suggestions (emotes, stickers) to the user in some ordered fashion (e.g. an
ordered list where you click on an entry), the order of the images should be predictable between rooms.
A suggestion for clients of image pack ordering is as follows:
1. the User image pack (defined in your own account data)
2. Image pack rooms (defined in the `m.image_pack.rooms` account data object)
3. Space image packs (defined in the hierarchy of canonical spaces for the current room)
4. Room image packs (defined in the currently open room's state)

Furthermore, clients are expected to de-duplicate images based on their mxc url. Common cases where this
is necessary is:

1. when viewing a room that has a pack defined in the `m.image_pack.rooms` account data object, and
2. a bot which syncs emotes over multiple rooms.

### Sending
#### Emoticons
For emoticons a client could add deliminators (e.g. `:`) around the image shortcode, meaning
that if an image has a shortcode of `emote`, the user can enter `:emote:` to send it. If there are
multiple emoticons with the same shortcode in a room, the client could e.g. slugify the packs display
name and then have the user enter `:slug~emote:`. As slugs typically match `^[\w-]+$`, that should
ensure complete-ability.

The alt / title text for the `<img>` tag is expected to be the `body` of the emote. If absent, its
shortcode should be used instead, optionally with tacked on deliminators.

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

Related issue: https://github.com/matrix-org/matrix-doc/issues/2418

## Unstable prefix
The `m.image_pack` in the account data is replaced with `im.ponies.user_emotes`. The `m.image_pack` in
the room state is replaced with `im.ponies.room_emotes`. The `m.image_pack.rooms` is replaced with
`im.ponies.emote_rooms`.

Some existing implementations using `im.ponies.user_emotes` and `im.ponies.room_emotes` currently use
a dict called `short` which is just a map of the shortcode to the mxc url.

Some other implementations currently also call the `images` key `emoticons`.

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
A couple of interesting points have been raised in discussion of this MSC that tangentially touch
custom emoticons. Each warrant an MSC for themselves however, as they touch more on how `<img>` works.
 - Figuring out how `<img>` should work with encrypted media.
 - Allow SVGs in the `<img>` tag. Current problem: Clients typically try to thumbnail the mxc URL,
   and most media repositories can't thumbnail SVGs. Possible solution: Somehow embed the mimetype.
 - For stickers: Recommend rendering sizes / resolutions
