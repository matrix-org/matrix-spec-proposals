# MSC3593: Safety Controls through a generic Administration API

## Abstract

This MSC tries to do two things;
- Define a foundation on how to expose a generic administration API to matrix clients
- Define 4 core APIs on that interface with regard to server oversight and moderation functionality.

## Background & Rationale

Historically, matrix administration tasks have been done through a non-specced API on synapse, which
today lives under the `_synapse/` prefix.

This API handles everything from background updates to registration tokens, documentation on this is
available on it's own
[documentation page](https://matrix-org.github.io/synapse/latest/usage/administration/admin_api/index.html).

However, this API is specific to Synapse, and unspecced. Other servers, such as Dendrite and
Conduit, would have to implement their own ways to expose admin interfaces.

Conduit already does so by exposing an internal room with bot commands.

Meanwhile, clients could like to integrate administration tasks into their own interfaces, making
server moderation easy and seamless. Today this cannot be executed, as it would mean a reliance on
unspecced interfaces or integrations such as Synapse's custom API, or Conduit's Bot commands.

## Proposal

This is what this proposal wishes to fix; a generic interface through which clients could hail data
and functionality from it's own server.

A non-goal of this proposal, and this interface, is to exhaustively replicate or spec the entirety
of Synapse's admin API. Instead, it wishes to give a foundation of properties to easily have future
MSCs integrate and work off of.

To give this base some tests, base functionality, and recognition, it'll (with it) bring 4 endpoints
that'll render core administration functionality that is common to all matrix servers today.

### Historic note

Currently in the matrix spec, a "module" called ["server
administration"](https://spec.matrix.org/v1.1/client-server-api/#server-administration) exists, this
module only exposes a `/whois` endpoint.

This proposal wishes to "adopt" this endpoint into the proposed foundation, and use the
`/_matrix/client/vX/admin/` prefix as its base.

### Capability API

This interface will not (as of yet) provide an in-band way to promote users to be able to do
administration tasks, this will stay out-of-band for now.

However, a client would wish to know which APIs it is *able* to access at any time, and for this, a
"capability" will be exposed.

This proposal will call the user for which this capability is exposed a "Capable User", this is to
have an as-ambiguous naming as possible for such an endpoint, as then homeserver implementations can
focus on sub-dividing this API according to its own philosophy of administration (i.e. let it by
itself define ideas such as "admin", "mod", or even "janitor", all according to its own rules.)

As such, the Capability API will look like so;

```
GET /_matrix/client/v1/admin/capabilities
Authentication: yes

Response:
200: Json array of Capability
```

A `Capability` is a matrix identifier (java-notated domain) which positively signals that a client
can access a particular endpoint.

A capability could look like so; `m.user.whois`.

A user which would have absolutely no capability to act in any administrative format would receive a
`200` with an empty array: `[]`.

The next section will define some APIs, and will list their corresponding Capability string.

### Safety Controls

This proposal will also add some endpoints pertaining to the most basic form of safety controls.

These endpoints would give some semblance of moderation on a server-scale basis. And with this
addition to the generic interface

#### Listing all active rooms

`GET /_matrix/client/v1/admin/rooms/active`
`Authentication: yes`
`Capability: m.rooms.list.active`

This API lists all rooms on a server which at least one local user has joined.

On `200`, this API returns;
```json5
{
    // Positive integer of total results
    "count": 1234,
    "rooms":[
        // Array of room IDs
    ]
}
```

XXX: Only room IDs are exposed here because we assume the client to fetch+cache a lot of room
information, so that it could more easily be re-arranged. Bots or automated functionality would
likely not have to know those details either, just information about active rooms.

FIXME: How to expose further room details? Capability to request preview for any room?

A few parameters exist;

`?sort`;
  - `id`, Lexicographic sort by room ID, "pseudo-random" (default)
  - `name`, Lexicographic sort by room Name
  - `users`, Descending sort by how many local users have joined this room

Filters;
  - `?user=`, Filter on which rooms the exact MXID is currently in
  - `?name_s=`, Substring search on room displayname
  - `?domain=`, Shorthand `:{}^` regex search on room ID (`example.com` becomes `:example\.com^`)

Pagination;
  - `?amount`, Positive integer, the amount of results to return, default 100
  - `?offset`, Positive integer, the offset of the returned results, default 0
  - `?rev`, bool, wether to reverse the sort, default `false`

#### Listing all users

`GET /_matrix/client/v1/admin/users/list`
`Authentication: yes`
`Capability: m.users.list`

Lists all users on the local server, this includes appservice and deactivated users.

On `200`, this API returns;
```json5
{
    // Positive integer of total results
    "count": 1234,
    "rooms":[
        // Array of user IDs
    ]
}
```

XXX: Same problem as rooms, we dont expose a lot of info here because we assume the client to
fetch+cache the rest.

FIXME: How to expose further user details? Capability to request profile for any user? How to expose
deactivated and appservice status? Expose corresponding appservice?

A few parameters exist;

`?sort`;
  - `id`, Lexicographic sort by user ID (default)
  - `displayname`, Lexicographic sort by user profile displayname
  - `avatar_url`, Lexicographic sort by user profile avatar MXC URL

Filter;
  - `?deactivated`, bool, if wether to include deactivated users, defaults to `false`,
  - `?appservice`, bool, if wether to include appservice users, defaults to `true`,

Pagination;
  - `?amount`, Positive integer, the amount of results to return, default 100
  - `?offset`, Positive integer, the offset of the returned results, default 0
  - `?rev`, bool, wether to reverse the sort, default `false`

#### Banning a room ID

`POST /_matrix/client/v1/admin/room/{room_id}/ban`
`Authentication: yes`
`Capability: m.room.ban`

"Bans" a room from a local server, prohibiting all local users from joining or interacting with it.

XXX: Should we also immidiately define an "unban" API in this proposal?

It accepts a request body with the following JSON;
```json5
{
    // Have all local users leave the room immediately, defaults to true
    "leave": true,
}
```

This API returns `204`.

After a room has been banned, a user will get `403` errors on any attempt to "read" or "write" to a
room, e.g. sending a message, a typing indicator, read indicator, or fetching an event.

If `leave: false`, a server can opt-in emulating/injecting a `leave`-like event in a sync stream if
they wish so to minimize client breakage, but minimizing client synchronization breakage is a
secondary concern to this API.

Note that this API does not ban a room *alias*, but a room *id*, this would still enable third-party
actors to upgrade or switch room IDs sequentially for their activities. A conservative approach such
as this has been taken to ensure at least the basic functionality for prohibiting rooms on a server
can be ensured via a generic interface.

#### Deactivating a user

`POST /_matrix/client/v1/admin/user/{room_id}/deactivate`
`Authentication: yes`
`Capability: m.user.deactivate`

XXX: This API is pretty severe, I'd like to also put a "put your password here" UIA-like interaction
on it, or some way that this cannot be abused once an admin token has been acquired.

Deactivates the user, accepts a JSON body with the following;

```json5
{
    // Wether to delete additional profile information of this user, bool, mandatory
    "erase": true,
}
```

This does the following; (Partially copied from the synapse API)
- Delete all devices and E2EE keys
- Delete all access tokens
- Delete all pushers
- Delete login information
- Force-leaves the user from all rooms
- Rejects all pending invites

And with `erase: true`;
- Remove the user's profile information;
  - Display Name
  - Avatar URL

Implementations may also have further actions taken when deactivating a user.

A user deactivation is considered **non-reversible**.

#### XXX: API Design

*Note: These are WIP concerns, please comment on these*

Synapse's admin API has a bit of an inconsistent theme, but one theme is that a GET-POST relation is
kept in some of them.

Blocking rooms (similar to banning rooms here), uses `GET` to retrieve a `{block: true}` body, and
`POST` to set the status. In `GET`, it can also get a user_id of whom has banned this room.

Maybe we should change the ban-room API to that?
`GET /room/{id}/ban`
```json5
{
    "banned": true,
    "user": "@it_was_me_all_along:example.com"
}
```
`POST /room/{id}/ban` with `banned: true`

This'd possibly also coalesce the `m.room.ban` capability into both reading and writing to these
endpoints.

### Implementation Requirements

While this proposal adds 4 endpoints it strongly requires every server to implement, this "strength"
may not apply to every endpoint.

Some use-cases may exist which do not make sense for some homeservers; a requirement to implement
"freezing" or "quarantining" users, disallowing them any "write" access to matrix, may be costly to
implement with non-critical benefits.

As such, the design of the Capability API deliberately blinds clients to probing if some APIs are
not implemented on a homeserver, this proposal wishes for any future MSCs to add a degree of
"requirement" (such as RFC2119's "MUST", "SHOULD", "COULD") for which these servers are required to
implement these interfaces.

For the sake of brevity, the 4 APIs listed in this proposal are on a "MUST-implement" basis, as they
are core to matrix's safety controls.

*Rationale: This places an admin API to be definition-first, standardizing it. This makes more sense
when looked upon in the context of the matrix ecosystem, if 90% of all homeserver implementations
are able to implement an administration API, and while the remaining 10% wouldn't, would they be
absolutely compelled to implement it, regardless of the complexity cost? This proposal wishes to
standardize common administration functionality, not compel. In the case of safety controls, the
"compelling" displayed in this proposal comes more from the value and need of safety controls
themselves, not from its implementation as a generic API.*

### Possible Future Proposals

This proposal wishes to spawn more proposals, a short list of possible immediate future expansions
on this API could be;
- Reset Passwords
- Freeze/Quarantine User
- List and Manipulate User devices
- List and Manipulate User access tokens
- List and Manipulate Media
- List and Manipulate Registration Tokens
- Peek local rooms
- Show Event Reports

Furthermore, future MSCs could define capabilities which alter the way conventional APIs such as
event fetching or context requests can have their "normal restrictions" be bypassed on admin
override.

## Security Considerations

All of these APIs work off of a user's normal access token, any compromise would enable the attacker
access to this API surface. (Note: This was already the case with synapse's Admin API)

## Unstable prefix

This MSC has an unstable prefix of `org.matrix.msc3593` for any `vX` or `m.` instance.