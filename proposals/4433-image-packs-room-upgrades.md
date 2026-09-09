# MSC4433: Image Packs and Room Upgrades

*This proposal was split out of
[MSC2545] in
order to simplify that proposal; as this was the only homeserver implementation
requirement in the proposal.*

[MSC2545] introduces the concept of `m.room.image_pack` state events, holding a
set of related images (e.g. for use in sticker packs, custom emote packs, etc.).
It also defines a `m.image_pack.rooms` account data event which can be used to
refer to packs within a room for use "globally" (e.g. sending stickers in one
room sourced from a pack in another room).

This proposal provides the following quality of life features:

* Transferring `m.room.image_pack` state events from the old room to the new
  room upon a room upgrade.
* Updating a user's `m.image_pack.rooms` account data entry when a room is
  upgraded, ensuring the references don't become stale.

## Proposal

Upon upgrading a room, homeservers SHOULD transfer `m.room.image_pack` state events
to the new room.

Homeservers SHOULD also update user's account data so that any
`m.image_pack.rooms` account data events are re-pointed from the old room ID to
the newly upgraded room ID; otherwise a user's global packs will quietly grow
stale.

One possible implementation strategy is laid out below.

Upon a user joining a room;

1. Determine whether the room is the result of a room upgrade from a previous room.
2. If so, retrieve the previous room's room ID.
3. Check whether the user has an `m.image_pack.rooms` entry in their account data.
4. If so, check whether the previous room ID is one of the entries in that data
  structure.
5. If it's present, check whether `m.room.image_pack` state events with the
  referenced `state_key`s exist in the new room.
6. If so, replace that room ID with the upgraded room IDs. Implementations should
  handle the case of only *some* `m.room.image_pack` state keys being migrated to
  the upgraded room.

## Potential issues

The suggested implementation strategy leaves the edge case of:

1. The upgraded room is created.
2. A user joins the upgraded room.
3. Image packs are then transferred over.

Leaving the user's list of `m.image_pack.rooms` stale.

Thus, when performing a room upgrade, homeserver implementations should take
care to *first* transfer `m.room.image_pack` state events to a new room, *then*
invite users to the new room.

## Alternatives

Clients could take on the responsibility of updating their own account data
instead. However, the homeserver is able to provide this functionality easily,
which would save it needing to be implemented across all client implementations.

It also allows for a consistent UX, even when using 'simple' external tooling
which that joins users to rooms with a single `/join` call.

## Security considerations

As account data is entirely client-controlled, homeservers should take
reasonable precautions when parsing its contents.

## Unstable prefix

While MSC2545 is unstable, implementations should make use of [its unstable
prefix
definitions](https://github.com/Sorunome/matrix-doc/blob/soru/emotes/proposals/2545-emotes.md#unstable-prefix).

## Dependencies

This MSC builds on [MSC2545] (which at
the time of writing has not yet been accepted into the spec).

[MSC2545]: https://github.com/matrix-org/matrix-spec-proposals/pull/2545
