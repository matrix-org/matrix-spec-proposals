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
is `im.ponies.user_emotes`. The content is as following:

```json
{
  "short": {
    ":emote:": "mxc://example.org/blah",
    ":other-emote:": "mxc://example.org/other-blah"
  }
}
```

The emotes are defined inside of a dict called `short`, meant as the "short and easy" representation
of the emotes. Other, additional, keys may exist to define more metadata for the emotes. No such
guide exists yet.

### Room emotes
Room emotes are per-room emotes that every user of a specific room can use inside of that room. They
are set with a state event of type `im.ponies-room_emotes` and a blank state key. The contents are
the same as for the user emotes.

## Ideas
 - Tag rooms as "these emotes can be used anywhere" inside of account data somehow
 - Some kind of packs - for room emotes the state key could be used as pack identifier, for user
   emotes something like `im.ponies.user_emotes.<pack_name>`.
