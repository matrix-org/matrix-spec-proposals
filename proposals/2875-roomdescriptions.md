Rooms currently have `m.room.name` for the room name, `m.room.topic` for a short description, and `m.room.avatar` for an avatar.
However, there is no currently-specced way to set a long description for a room, such as an FAQ or extensive rules.

# Proposal
A new state event (set with empty state key), `m.room.description`, is added. It has the field `description`, which is HTML-formatted (supporting the same types of HTML as `org.matrix.custom.html` implies).
It can contain images (as long as they are references to `mxc` URIs, headings, colored text, and links.
It can also include anchors and links to said anchors (such as `<a id="example"></a>` and `<a href="#example">jump to example</a>` for easy navigation or table of contents.

# Client implementation
Clients should either expose editing the description as raw HTML, or as Markdown, though translation to markdown may be lossy. This is left up to client developers.

# Server implementation
None necessary, though servers should consider setting the default power level to edit `m.room.description` to the same as `m.room.topic`.

# Unstable prefix
While this msc is in development, the event should be sent as `cat.blob.msc2875.description` instead of `m.room.description`.

# Alternatives
`m.room.pinned_events` can be used, though not all clients may have access to pinned events, causing issues in many rooms, as well as less consistent display, usage, and support.
