# MSC2545: Emotes

Emotes.....emotes!

# Proposal
Emotes have at least a shortcode and an mxc uri. They are sent as `<img>` tags currently already in
the spec, as such existing clients *should* be able to render them (support for this is sadly poor,
even within riot flavours). Such an `<img>` tag of a shortcode `:emote:` and an mxc uri `mxc://example.org/emote`
could look as follows:

```html
<img src="mxc://example.org/emote" alt=":emote:" title=":emote:" height="32" />
```

Both the `alt` and the `title` attributes are specified as they serve different purposes: `alt` is
displayed if e.g. the emote does not load. `title` is displayed e.g. on mouse hover over the emote.
The height is just a height that looks good on most devices with the normal, default font size.
No width is displayed as to not weirdly squish non-square emotes.

## Emote sources
In order to be able to send emotes the client needs to have a list of shortcodes and their corresponding
mxc uris. For this there are two different emote sources:

### User emotes
User emotes are per-user emotes that are defined in the users respective account data. The type for that
is `im.ponies.user_emotes` (`m.emotes`). The content is as following:

```json
{
  "short": {
    ":emote:": "mxc://example.org/blah",
    ":other-emote:": "mxc://example.org/other-blah"
  }
}
```

The emotes are defined inside of a dict called `short`, meant as the "short and easy" representation
of the emotes. Other, additional keys may exist to define more metadata for the emotes. No such
guide exists yet.

### Room emotes
Room emotes are per-room emotes that every user of a specific room can use inside of that room. They
are set with a state event of type `im.ponies.room_emotes` (`m.emotes`). The state key denotes a possible
pack, whereas the default one would be a blank state key. E.g. a discord bridge could set as state key
`de.sorunome.mx-puppet-bridge.discord` and have all the bridged emotes in said state event, keeping
bridged emotes from own, custom ones separate.

The content extends that of the user emotes: It uses the `short` key, which is a map of the shortcode
of the emote to its mxc uri. Additionally, an optional `pack` key can be set, which defines meta-information
on the pack. The following attributes are there:

 - `pack.displayname`: An easy displayname for the pack. Defaults to the room name, if it doesn't exist
 - `pack.avatar_url`: The mxc uri of an avatar/icon to display for the pack. Defaults to the room name,
   if it doesn't exist.
 - `pack.short`: A short identifier of the pack. Defaults to the normalized state key, and if the state
   key is blank it defaults to "room".
   
   Normalized means here, converting spaces to `-`, taking only alphanumerical characters, `-` and `_`,
   and casting it all to lowercase.

As such, a content of a room emote pack could look as following:

```json
{
  "short": {
    ":emote:": "mxc://example.org/blah",
    ":other-emote:": "mxc://example.org/other-blah"
  },
  "pack": {
    "displayname": "Emotes from Discord!",
    "avatar_url": "mxc://example.org/discord_guild",
    "short": "some_discord_guild"
  }
}
```

### Emote rooms
While room emotes are specific to a room and are only accessible within that room, emote rooms should
be accessible from everywhere. They do not differentiate themself from room emotes at all, instead you
set an event in your account data of type `im.ponies.emote_rooms` (`m.emotes.rooms`) which outlines
which room emote states should be globally accessible for that user. For that, a `room` key contains
a map of room id that contains a map of state key that contains an optional pack definition override.
As such, the contents of `im.ponies.emote_rooms` could look as follows:

```json
{
  "rooms": {
    "!someroom:example.org": {
      "": {},
      "de.sorunome.mx-puppet-bridge.discord": {
        "name": "Overriden name",
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
`!someotherroom:example.org`.

## Sending
In places where fancy tab-complete with the emote itself is not possible it is suggested that sending
the shortcode will convert to the img tag, e.g. sending `Hey there :wave:` will convert to `Hey there <img-for-wave>`.

If there are collisions due to the same emote shortcode being present as both room emote and user emote
a user could specify the emote source by writing e.g. `:room~wave:` or `:user~wave:`. Here the short
pack name is used for room emotes, and "user" for user emotes.

# Ideas
 - ???

# Current implementations
## Emote rendering (rendering of the `<img>` tag)
 - riot-web
 - revolution
 - nheko
 - fluffychat
## Emote sending, using the mentioned events here
 - revolution
 - fluffychat
