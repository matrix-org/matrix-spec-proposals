# MSC3368: Message Content Tags

Inspired by [MSC3286](https://github.com/matrix-org/matrix-doc/pull/3286), this proposal aims to solve the same
and similar problems in a more generic way, taking into consideration more possible reasons for hiding
events by default, like:

- medical (e.g., photosensitive epilepsy warning)
- NSFW
- graphic / potentially disturbing

To summarise, this proposal intends to provide hints for clients as to the contents of an event primarily to allow
them to automatically hide certain types of content which the user may not wish to see.

## Proposal

To facilitate this, the proposal adds an optional `tags` object to the `content` object of `m.room.message` events.
This object can contain any combination of any/all of the following keys:

  - `m.spoiler` (content which provides information the user may wish to acquire themselves)
  - `m.nsfw` (not safe for work / 18+ content)
  - `m.medical` (content which may negatively affect people with certain health issues e.g., photosensitive epilepsy)
  - `m.graphic` (content which can be seen as disturbing)
  - `m.hidden` (content which is recommended to be hidden by default; should only be used when a more specific tag for the type of
 content does not exist to allow clients/users to more easily decide which content to show/see)

The presence of a key indicates that the content is tagged as such.

Each key must map to a string value describing why the content has this tag. The value can be an empty string if
no reason is provided. This is to allow users to decide if they wish to see an individual message.

Despite the fact that all currently-defined tag types could warrant hiding by default, clients should not assume
that the presence of the `tags` object indicates that the message should be hidden by default. This is to allow
for expanding the use of the `tags` object in the future for other purposes like searching, for example.

## Potential issues

- Users of outdated clients will continue to see content which should be hidden by default. Unfortunately, I could not think of
any clean way to avoid this.
- Multi-tagged messages may be difficult to show UI-wise, but this is the only way to ensure tagging is accurate. Only allowing
single tags could lead to situations like the following: Alice is comfortable with seeing disturbing content and configures her
client to automatically show it. However, she suffers from photosensitive epilepsy and does not wish to see content which
includes flashing lights. A video is sent in a room which is both graphic and includes flashing lights. Bob, who sent the video,
tagged it as graphic because he could only choose a single tag. Hence, Alice watches the video.

## Alternatives

- [MSC3286](https://github.com/matrix-org/matrix-doc/pull/3286)
- Embedding images in `m.text` messages (see Alternatives section of MSC3286)

## Security considerations

None known

## Unstable prefix

The `tags` object should be replaced with `space.0x1a8510f2.msc3368.tags` and all its subkeys should be prefixed with `space.0x1a8510f2.msc3368.` instead of `m.`.
