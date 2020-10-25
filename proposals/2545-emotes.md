# MSC2545: Emoticons

Emoticons, or short emotes...we need them!

## Terminology
Since there is a lot of confusion of how this relates to `m.emote`, why this isn't called custom emoji
etc, there it is:

`m.emote` is for emotion - and it has been incorrectly named this way. `m.action` would have been more
appropriate, as you use it to describe *actions*, not *emotions*. E.g. "/me is walking to the gym", or
"/me is happy" and *not* "/me happy".

That, however, is *not* what this MSC is about. Instead it is about emoticons, also known in short as
emotes.

Emoticons are just little images or text describing emotions or other things. Emoji are a subset of
emoticons, namely those found within unicode. Custom emoji here would actually refer to a custom emoji
font, that is your own rendering of 🦊, 🐱, etc., *not* new images. New images is what custom emoticons
are for.

Now, a client may choose to name these however they like, we already have a naming disparity between
spec and clients with groups vs communities. It is, however, imperative to name things in the spec
accurately after what they are.

## Proposal
Emoticons have at least a shortcode and an mxc uri. They are sent as `<img>` tags currently already in
the spec, as such existing clients should already be able to render them, though not all clients currently
handle `img` tags. To allow clients to distinguish emoticons from other inline images, a new
property, `data-mx-emoticon`, is introduced. A client can chose to ignore the size attributes of emoticons
when rendering, and instead pick the size based on other circumstances. This could e.g. be used to
display emoticons in messages with only emoticons and emoji larger than usual, which is commonly found in
messengers. Such an `<img>` tag of a shortcode `:emote:` and an mxc uri `mxc://example.org/emote`
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

If the new `data-mx-emoticon` attribute has a value it is ignored. Due to limitations of some libraries
the attribute may even look like `data-mx-emoticon=""`.

The `src` attribute *must* be an mxc url. Other URIs, such as `https`, `mailto` etc. are not allowed.

### Emoticon image types
Emoticons are recommended to have a size of about 128x128 pixels. Even though the fallback specifies
a height of 32, this is to ensure that the emotes still look good on higher DPI screens.

Furthermore, emotes should either have a mimetype of `image/png`, `image/gif` or `image/webp`. Emotes
can be animated.

Due to the low resolution of emotes, `image/jpg`/`image/jpeg` has been purposefully excluded from this
list.

### Emoticon sources
So that emoticons are compatible between different clients, they should follow the emoticon sources
described here.

#### User emoticons
User emotes are per-user emotes that are defined in the user's respective account data. The type for that
is `m.emoticons`, the content of which is as following:

```json
{
  "emoticons": {
    ":emote": {
      "url": "mxc://example.org/blah"
    },
    ":other-emote:": {
      "url": "mxc://example.org/other-blah"
    }
  }
}
```

The emotes are defined inside of a dict called `emoticons`. The key is the shortcode of the emoticon.
The value is an object with `url` as a required field, containing the mxc uri as a string. This is so
that it is easier for clients or future MSCs to define custom metadata to emotes directly.

#### Room emoticons
Room emotes are per-room emotes that every user of a specific room can only use inside of that room. They
are set with a state event of type `m.emoticons`. Multiple packs can be specified by different state
keys, the identifier being an opague string. An empty state key is the default pack for a room.
E.g. a discord bridge could set as state key
`de.sorunome.mx-puppet-bridge.discord` and have all the bridged emotes in said state event, keeping
bridged emotes from matrix emotes separate.

The content extends that of the user emotes: It uses the `emoticons` key, which is a map of the shortcode
of the emote to an object containing its mxc url, just as with user emoticons. Additionally, an optional `pack` key can be set,
which defines meta-information on the pack. The following keys for `pack` are valid:

 - `display_name`: (String, optional) An easy display name for the pack. Defaults to the room name,
   if it doesn't exist. This does not have to be unique within all packs of a room.
 - `avatar_url`: (String, optional) The mxc uri of an avatar/icon to display for the pack. Defaults
   to the room avatar, if it doesn't exist. If the room also does not have one, then this pack does
   not have an avatar.
 - `short`: (String, `^[a-z0-9-_]+$`, optional) A short human-readable identifier of the pack. Defaults
   to the normalized state key, and if the state key is blank it defaults to "room". This is used to
   easily specify which pack to pick an emoticon from, should there be clashes.

   Normalized means here, converting spaces to `-`, taking only alphanumerical characters, `-` and `_`,
   and casting it all to lowercase. In regex, this would be `^[a-z0-9-_]+$`.

As such, a `m.emoticons` state event could look like the following:

```json
{
  "emoticons": {
    ":emote:": {
      "url": "mxc://example.org/blah"
    },
    ":other-emote:": {
      "url": "mxc://example.org/other-blah"
    }
  },
  "pack": {
    "display_name": "Emotes from Discord!",
    "avatar_url": "mxc://example.org/discord_guild",
    "short": "some_discord_guild"
  }
}
```

#### Emoticon rooms
While room emotes are specific to a room and are only accessible within that room, emote rooms should
be accessible from everywhere. They do not differentiate themselves from room emotes at all, instead you
set an event in your account data of type `m.emoticons.rooms` which outlines
which room emote states are globally accessible for that user. For that, a `room` key contains
a map of room ids that map to state keys that map to an optional pack definition override.
The the contents of `m.emoticons.rooms` could look like the following:

```json
{
  "rooms": {
    "!someroom:example.org": {
      "": {},
      "de.sorunome.mx-puppet-bridge.discord": {
        "display_name": "Overriden name",
        "short": "new_short_name"
      }
    },
    "!someotherroom:example.org": {
      "": {}
    }
  }
}
```

Here three emote packs are globally accessible to the user: Two defined in `!someroom:example.org`
(one with blank state key and one with state key `de.sorunome.mx-puppet-bridge.discord`) and one in
`!someotherroom:example.org`. The one in `!someroom:example.org` with state key `de.sorunome.mx-puppet-bridge.discord`
has an override for `display_name` and `short` of that pack, so that for this user the pack displays
differently for themselves.

### Emoticon source priority and deduplicating
When giving emoticon suggestions, clients are expected to deduplicate emotes by their mxc url. This
not only ensures that, when viewing a room that you also have in `m.emoticons.rooms`, it won't be
displayed twice, but also if you have e.g. a bot which syncs emotes over multiple rooms, those will
also be deduplicated.

Lastly, in order to have consistent and expected ordering of emotes when suggesting, they should be
suggested in the following order:
1. User emoticons (emotes set to your own account)
2. Emoticon rooms (rooms whos emotes you enabled to be accessible everywhere)
3. Room emoticons (emotes defined in the currently open room)

### Sending
Clients should consider converting shortcodes like `:wave:` to a relevant `<img>` tag for the emoticon.

Clients should also consider supporting ways for the user to find the emoticon they are attempting to send,
such as having a syntax like `:room~wave:` to find `wave` emoticon in the current room. Alternatives might also
be `user` or pack `short` attributes to search within.

## Security Considerations
When sending an `<img>` tag in an encrypted room, the client will make a request to fetch
said image, in this case an emote. As there is no way to encrypt content behind `<img>` tags yet,
this could potentially leak part of the conversation. This is **not** a new security consideration,
it already exists. This, however, isn't much different from posting someone a link in an e2ee chat and
the recipient opens the link. Additionally, images, and thus emotes, are often cached by the client,
not even necessarily leading to an http query.

## Unstable prefix
The `m.emoticons` in the account data is replaced with `im.ponies.user_emotes`. The `m.emoticons` in
the room state is replaced with `im.ponies.room_emotes`. The `m.emoticons.rooms` is replaced with
`im.ponies.room_emotes`.

Some existing implementations using `im.ponies.user_emotes` and `im.ponies.room_emotes` currently use
a dict called `short` which is just a map of the shortcode to the mxc url.

## Alternatives
One can easily think of near infinite ways to implement emotes. The aspect of sending an `<img>` tag
and marking it as an emote with `data-mx-emoticon` seems to be pretty universal though, so the question
is mainly on different emote sources. For that, a separate MSC, [MSC1951](https://github.com/matrix-org/matrix-doc/pull/1951)
already exists, so it is reasonable to compare this one with that one:

### Comparison with MSC1951
MSC1951 defines a dedicated room as the only emote source. This MSC, however, also allows you to bind emotes
to your own account, offering greater flexibility. In MSC1951 there can also only be a single emote
pack in a room. This could be problematic in e.g. bridged rooms: You set some emotes from the matrix
side and a discord bridge would plop all the discord emotes in another pack in the same room.

MSC1951 defines a way to recommend using a pack of a different room - this MSC does not have an equivalent
to that. Instead, this MSC allows multiple emote packs for a room, and allows you to enable an emote
pack to be globally available for yourself across all rooms you are in.

The core difference is how MSC1951 and this MSC define the emotes themselves: In MSC1951 you have to
set one state event *per emote*. While this might seem like a nice idea on the surface, it doesn't
scale well. There are people who easily use and want hundreds or even thousands of emotes accessible.
A simple dict of shortcode to mxc URI seems more appropriate for this.


In general, MSC1951 feels like a heavier approach to emote sources, while this MSC is more lightweight.
