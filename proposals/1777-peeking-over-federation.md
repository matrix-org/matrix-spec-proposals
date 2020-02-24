# Proposal for implementing peeking over federation (server pseudousers)

## Problem

Currently you can't peek over federation, as it was never designed or
implemented due to time constraints when peeking was originally added to Matrix
in 2016.

As well as stopping users from previewing rooms before joining, the fact that
servers can't participate in remote rooms without joining them first is
inconvenient in many other ways:

 * You can't reliably participate in E2E encryption in rooms you're invited to
   unless the server is actually participating in the room
   (https://github.com/vector-im/riot-web/issues/2713)
 * Rooms wink out of existence when all participants leave (but if servers were
   able to participate even when their users have left, this would go away)
   (https://github.com/matrix-org/matrix-doc/issues/534)
 * You can't use rooms as generic pubsub mechanisms for synchronising data like
   profiles, groups, device-lists etc if you can't peek into them remotely.
 * Search engines can't work if they can't peek remote rooms.

## Solution

If a client asks to peek into a room which its server is not currently joined
to, the server should attempt to join the room using a pseudouser account which
represents the server itself.

This allows the server to participate in the room and peek the data being
requested without disclosing the identity of the peeking user, and without
bloating the membership table of the room by joining on behalf of every local
peeking user.

This proposal suggests `@:server` is standardised as the special form of the
server pseudo-user (changing the rules for user IDs to allow zero-length
localparts).

Clients must not show this pseudouser in their membership lists, and the
pseudouser membership event must not be used when calculating room names.
However, clients may choose to show the existence of the member in advanced
details about a given room.

`m.room.join_rules` is extended with a new type: `peekable`, which describes
public-joinable rooms which may also be joined by `@:server` pseudousers.
Otherwise, server pseudousers must not be allowed to join the room, unless a
user from that server has already joined or been invited.

This replaces the `world_readable` setting on `m.room.history_visibility`.

XXX: Presumably this requires a room version upgrade.

This also solves the 'rooms wink out of existence' bug
(https://github.com/matrix-org/matrix-doc/issues/534)
if servers which have aliases pointing to a room also join their pseudouser to
the room in order to keep the room 'alive' (and thus the alias working) even
if everyone leaves.

Pseudousers could potentially also act on behalf of ASes within a room without
the AS having to unpleasantly join/part a bot to interact with it
(https://github.com/matrix-org/matrix-doc/issues/544)

## Security considerations

This has potential to allow users to unilaterally invite servers into their rooms,
which could be a DoS vector.  If a user creates a peekable room, and invites a
remote user in, it's now possible for that server to join via their pseudouser
in order to (say) participate in E2E... even if the user themselves hasn't
acted on the invitation.  Care must be taken in being lured into peekable rooms.

## Tradeoffs

We could instead create a new m.room.server_membership event type.  But whilst
slightly semantically clearer, it complicates the implementation even more,
whereas here we can leverage most of the existing behaviour of m.room.membership
events.

## Dependencies

This unblocks MSC1769 (profiles as rooms) and MSC1772 (groups as rooms)
and is required for MSC1776 (peeking via /sync) to be of any use.

## History

This would close https://github.com/matrix-org/matrix-doc/issues/913
