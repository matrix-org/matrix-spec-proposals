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
 * any members which are power events (aka control events): bans & kicks.
 * one joined member per server (if we want to be able to send messages while
   the room state is synchronising, otherwise we won't know where to send them
   to)
 * any membership events with membership `invite` (to mitigate risk of double invites)
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

The remote server may decide not to honour lazy_loading if a room is too small
(thus saving the additional roundtrip of calling `/state`), so the response to
`/send_join` or `/peek` must include a `lazy_load_members: true` field if the
state is partial and members need to be subsequently loaded by `/state`.

Clients which are not lazy loading members (by MSC1227) must block returning
the CS API `/join` or `/peek` until this `/state` has completed and been
processed.

Clients which are lazy loading members however may return the initial `/join`
or `/peek` before `/state` has completed.  However, we need a way to tell
clients once the server has finished synchronising its local state. We do this
by adding an `syncing: true` field to the room's `state` block in the `/sync`
response.  Once this field is missing or false, the client knows that the joining
server has fully synchronised the state for this room.  Operations which are
blocked on state being fully synchronised are:

 * Sending E2EE messages, otherwise some of the users will not have the keys
   to decrypt the message.
 * Calling /members to get an accurate detailed list of the users in the room.
   Instead clients showing a membership list should calculate it from the
   members they do have, and the room summary (e.g. "these 5 heroes + 124 others")

While the joining server is busy syncing the remaining room members via
`/state`, it will also need to sync new inbound events to the user (and old
ones if the user calls `/messages`).  If these events refer to members we're
not yet aware of (e.g. they're sent by a user our server hasn't lazyloaded
yet) we should separately retrieve their membership event so the server can
include it in the `/sync` response to the client.  To do this, we add fields
to `/state` to let our server request a specific `type` and `state_key` from
the target server.

Matrix requires each server to track the full state rather than a partial
state in its DB for every event persisted in the DAG, in order to correctly
calculate resolved state as of that event for authorising events and servicing
/state queries etc.  Loading the power events up front lets us authorise new
events (backfilled & new traffic) using partial state - when you receive an
event you do the lookup of the event to the list of event state keys you need
to auth; and if any of those are missing you need to fetch them from the
remote server by type & state_key via /state (and auth them too).

However, once our server has fully synced the state of the room at the point
of the join event, we must rollback the DAG and replay all the events we've
accepted into the room DAG in order to correctly capture the full state in the
room as of that event. This could theoretically result in some events now
being rejected/soft-failed, so it's important that "uncommitted" events in the
DAG (i.e. those which arrived since the join, but before state was fully
synced) do not have side-effects on the rest of the server (e.g. generate
push) until the room is fully synced.

XXX: what's an example of an event being failed/rejected during replay which
was previously accepted?  If we could auth it correctly before, shouldn't it
still auth correctly afterwards?

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

## Security considerations

We currently trust the server we join via to provide us with accurate room state.
This proposal doesn't make this any better or worse.

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
