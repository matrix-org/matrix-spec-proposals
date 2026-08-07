# MSC3872: Order of rooms and subspaces in Spaces

Spaces are incredibly disorganized, unlike other platforms, such as [Revolt](https://revolt.chat),
[Discord](https://discord.com) and [Slack](https://slack.com).

To solve this issue, this MSC proposes a custom, manual order for rooms and subspaces in Spaces.

## Proposal

This MSC proposes Spaces to have a specific, custom order of rooms and subspaces that clients are sent upon joining,
and that can be updated at any time with the right permissions, which can then be reflected on other clients.

This should greatly complement Spaces, and would make organisation and navigation simpler, especially since clients
could implement features such as drag-and-drop reordering.

### Why are the methods of algorithmic sorting insufficient?

Often, it is helpful to have a specific layout manually edited by administrators of the Space. You can then have
important rooms and subspaces at the top (like ones for rules, announcements, etc), discussion at the bottom (general,
off-topic) and more layouts. Other platforms have this feature, and missing features are often what stops people from
switching to other platforms, including Matrix.

### How it works

Rooms and subspaces are stored in an array with a certain order. This order is, unlike algorithmic sorting, an order
manually set by client interaction (like drag-and-drop reordering), and does not sort by an algorithm like alphabetical
sorting.

This helps the Space administrators organize the Space as they see fit, and can always be overridden client-side.

## Potential Issues

This could require a certain amount of code changes in Matrix implementations.

## Alternatives

Manually adding tags one at a time to rooms/subspaces or numbers/letters to the start of their names could work
instead, though this is more tedious and will likely prevent simple client interaction like drag-and-drop reordering,
which apps like Discord and Slack have.

<!-- This entire file's contents and all commits (including bc589d8fad66f954363bc72188cb71564c1922f2) are Signed-off-by:
Alex LeBlanc <alexsour@protonmail.com> -->
