# MSC0000: Image pack rooms

[MSC2545](https://github.com/matrix-org/matrix-spec-proposals/pull/2545) introduced image packs for storing stickers and
custom emojis in room state. While packs can be enabled globally via `m.image_pack.rooms` account data, there is
currently no way to create standalone image packs that are not tied to a normal joined room or space.
However, users may wish to create and share image packs independently of such existing chat rooms or communities,
similar to how other chat networks like Telegram or Signal handle sticker packs.

Accordingly, this proposal introduces a new room type dedicated to image pack usage, that allows clients to decouple
image pack handling from traditional room and space UI.


## Proposal

A new room type, `m.image_pack`, is introduced. Similar to
[spaces](https://spec.matrix.org/v1.18/client-server-api/#spaces)
(rooms configured as `m.space`), message sending should be disabled by default, as the main purpose of such rooms is to
hold `m.image_pack` state events. Furthermore, new image pack rooms are recommended to be configured as public rooms,
e.g. to allow users to share rooms by URL via
[traditional means of linking rooms](https://spec.matrix.org/v1.18/appendices/#uris).
Clients are still allowed to configure arbitrary join rules as desired.

Upon successful creation of an `m.image_pack` room, clients should add the new room ID to the user's `m.image_pack.rooms`
account data, since the user likely expects being able to use the new pack they created globally right away. Users may
however still decide to not enable these packs globally, e.g. when they only want to maintain a sticker pack for other
users without using it themselves. Accordingly, the presence of dedicated image pack rooms should not affect the logic
of which image packs to enable globally, i.e. `m.image_pack.rooms` account data remains the single source of truth in
this regard, and clients are allowed to expose suitable settings to users accordingly.

Managing image packs in dedicated image pack rooms works as before on a technical level, i.e., as defined by
[MSC2545](https://github.com/matrix-org/matrix-spec-proposals/pull/2545). Clients should however present such rooms
in a different way to the user, e.g. in some dedicated image pack settings screen, rather than in the room list
dedicated to chat rooms. Since a room may hold multiple image packs, clients may want to refer to image pack rooms as
"image pack collections" or similar. If clients wish to treat an image pack room equivalent to a single image pack, they should
refrain from setting any `m.image_pack` state events for non-empty state keys. The state event with an empty state key
can then be treated as the canonical image pack for the room.


## Potential issues

#### User expectations for sharing image packs may not match the Matrix room model

Since importing an image pack involves joining a room, this action will naturally expose the user's room membership to
other members of this room. Users may not expect this implication, as it is not common on other networks.

Maybe a future MSC could introduce the concept of "broadcast rooms" of some kind, in which the server hides the
membership of other users in a room, which would then also be a natural fit for image pack rooms.
Another approach would be some kind of federated room peeking mechanism, such that users can read image pack rooms
without actually joining. For the time being, clients are encouraged to educate users about the implications of
joining the image pack room.


## Alternatives

One could try to invent a completely new primitive that does not build on rooms, e.g. in order to allow sharing packs
without leaking room membership. New primitives add complexity both for clients and servers and can probably not be
justified for image packs.


## Security considerations

The mismatch between user expectations and the fact that importing image packs involves room membership, as outlined in
potential issues, may be considered a security consideration, if users are not properly educated.

Apart from that, none.


## Unstable prefix

`com.beeper.image_pack` can be used as room type instead of `m.image_pack`.


## Dependencies

This MSC builds on [MSC2545](https://github.com/matrix-org/matrix-spec-proposals/pull/2545), which has recently been
accepted and merged.

This MSC can furthermore naturally be combined with
[MSC4459](https://github.com/matrix-org/matrix-spec-proposals/pull/4459) to link image pack rooms from sent stickers and
emotes, but both can be useful independently, so it is not a dependency.
