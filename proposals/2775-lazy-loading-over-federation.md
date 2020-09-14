# Lazy loading room membership over federation

## Problem

Joining remote rooms for the first time from your homeserver can be very slow.
This is particularly painful for the first time user experience of a new
homeserver owner.

Causes include:
 * Room state can be big.  For instance, a /send_join response for Matrix HQ is
   currently 24MB of JSON covering 28,188 events, and could easily take tens of
   seconds to calculate and send (especially on lower-end hardware).
 * All these events have to be verified by the receiving server.
 * Your server may have to fetch ths signing keys for all the servers who have
   sent state into the room.

This also impacts peeking over federation
([MSC2444](https://github.com/matrix-org/matrix-doc/pull/2444)), which is even
more undesirable, given users expect peeking to have a very snappy UX, letting them
quickly check links to sample rooms etc.

For instance Gitter shows a usable peeked page for a room with 20K
members in under 2 seconds (https://gitter.im/webpack/webpack) including
launching the whole webapp.  Similarly Discord loads usable state for a server
with 90K users like https://chat.vuejs.org in around 2s.

## Proposal

The vast majority of state events in Matrix today are `m.room.member` events.
For instance, 99.4% (30661 out of 30856) of Matrix HQ's state is
`m.room.member`s (see Stats section below).

Therefore, in the response to `/send_join` (or a MSC2444 `/peek`), we propose
sending only the following `m.room.member` events (if the initiating server
includes `lazy_load_members: true` in their JSON request body):

 * the "hero" room members which are needed for clients to display
   a summary of the room (based on the
   [requirements of the CS API](https://github.com/matrix-org/matrix-doc/blob/1c7a6a9c7fa2b47877ce8790ea5e5c588df5fa90/api/client-server/sync.yaml#L148))
 * any members which are in the auth chain for the state events in the response
 * any members for user_ids which are referred to by the content of state events
   in the response (e.g. `m.room.power_levels`) <-- TBD.  These could be irrelevant,
   plus we don't know where to look for user_ids in arbitrary state events.

In addition, we extend the response to `/send_join` and `/peek` to include a
`summary` block, matching that of the CS `/sync` API, giving the local server
the necessary data to support MSC1227 CS API lazy loading.

The joining server can then sync in the remaining membership events by calling
`/state` as of the user's join event.  To avoid retrieving duplicate data, we
propose adding a parameter of `lazy_load_members_only: true` to the JSON
request body which would then only return the missing `m.room.member` events.

Clients which are not lazy loading members (by MSC1227) must block returning
the CS API `/join` or `/peek` until this `/state` has completed and been
processed.

Clients which are lazy loading members however may return the initial `/join`
or `/peek` before `/state` has completed.  However, we need a way to tell
clients once the server has finished synchronising its local state.  For
instance, clients must not let the user send E2EE messages until their server
has acquired the full set of room members for the room, otherwise some of the
users will not have the keys to decrypt the message.  We do this by adding an
`syncing: true` field to the room's `state` block in the `/sync` response.
Once this field is missing or false, the client knows it is safe to call
`/members` and get a full list of the room members in order to encrypt
successfully.  The field can also be used to advise the client to not
prematurely call `/members` to show an incomplete membership list in its UI
(but show a spinner or similar instead).

While the joining server is busy syncing the remaining room members via
`/state`, it will also need to sync new inbound events to the user (and old
ones if the user calls `/messages`).  If these events refer to members we're
not yet aware of (e.g. they're sent by a user our server hasn't lazyloaded
yet) we should separately retrieve their membership event so the server can
include it in the `/sync` response to the client.  To do this, we add fields
to `/state` to let our server request a specific `type` and `state_key` from
the target server.

## Alternatives

Rather than making this specific to membership events, we could lazy load all
state by default. However, it's challenging to know which events the server
(and clients) need up front in order to correctly handle the room - plus this
list may well change over time.  For instance, do we need to know the
`uk.half-shot.bridge` event in the Stats section up front?

Rather than reactively pulling in missing membership events as needed while
the room is syncing in the background, we could require the server we're
joining via to proactively push us member events it knows we don't know about
yet, and save a roundtrip. This feels more fiddly though; we can optimise this
edge case if it's actually needed.

## Related

MSC1228 (and future variants) also will help speed up joining rooms
significantly, as you no longer have to query for server keys given the room
ID becomes a server's public key.

## Stats

```
matrix=> select type, count(*) from matrix.state_events where room_id='!OGEhHVWSdvArJzumhm:matrix.org' group by type order by count(*) desc;
           type            | count
---------------------------+-------
 m.room.member             | 30661
 m.room.aliases            |   141
 m.room.server_acl         |    23
 m.room.join_rules         |     9
 m.room.guest_access       |     6
 m.room.power_levels       |     5
 m.room.history_visibility |     3
 m.room.name               |     1
 m.room.related_groups     |     1
 m.room.avatar             |     1
 m.room.topic              |     1
 m.room.create             |     1
 uk.half-shot.bridge       |     1
 m.room.canonical_alias    |     1
 m.room.bot.options        |     1
```
