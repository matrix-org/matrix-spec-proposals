# Proposal for implementing peeking over federation (peek API)

## Problem

Currently you can't peek over federation, as it was never designed or
implemented due to time constraints when peeking was originally added to Matrix
in 2016.

As well as stopping users from previewing rooms before joining, the fact that
servers can't participate in remote rooms without joining them first is
inconvenient in other ways:

 * You can't use rooms as generic pubsub mechanisms for synchronising data like
   profiles, groups, reputation lists, device-lists etc if you can't peek into
   them remotely.
 * Matrix-speaking search engines can't work if they can't peek remote rooms.

A related problem (not solved by this MSC) is that servers can't participate
in E2E encryption when peeking into a room, given the other users in the
room do not know to encrypt for the peeking device.

Another related problem (not solved by this MSC) is that invited users can't
reliably participate in E2E encryption before joining a room, given the invited
server doesn't currently have a way to know about new users/devices in the room
without peeking, and so doesn't tell them if the invited user's devices changes.
(https://github.com/vector-im/element-web/issues/2713#issuecomment-691480736
outlines a fix to this, not covered by this MSC).

## Solution

We let servers participate in peekable rooms (i.e. those with `world_readable`
`m.room.history_visibility`) without having actually joined them.

We do this by subscribing to a room on one or more servers via a new `/peek`
S2S API, which lets users on a given server declare their interest in viewing
events in that room.  Having started peeking into the room, the server(s)
being peeked will relay *all* events it sees in that room to the peeking
server (including ones from other servers) via `/send` as if it were joined.
Backfill and event-retrieval APIs should be changed to be queryable from
servers not in the room if the room is peekable.

This continues until the peeking server calls DELETE on the peek it initiated.

To start peeking, firstly the peeking server must pick server(s) to peek via.
This is typically the same server you would use to try to join the room via
(i.e. one taken from the alias, or the via param on a matrix.to URL). The
server could also call S2S /state on m.room.members to find other servers
participating in the room and try to peek them from too.

The peeking server starts to peek by PUTting to `/peek` on the peeked server.
The peeked server is determined from the `server_names` parameter of the CS API
`/peek` command (from [MSC2753](https://github.com/matrix-org/matrix-doc/pull/2753)),
or failing that the domain of the room_alias or room_id being peeked.
The request takes an empty object as a body as a placeholder for future (where
we might put filters). The peeking server selects an ID for the peeking
subscription for the purposes of idempotency. The ID must be 8 or less bytes
of ASCII and should be unique for a given `{ origin_server, room_id, target_server }`
tuple. The request takes `?ver=` querystring parameters with the same behaviour
as `/make_join` to advertise the room versions the peeking server supports.

We don't just use the `room_id` for idempotency because we may want to add
filtering in future to the /peek invocation, and this lets us distinguish
between different peeks which are filtering on different things for the
same room between the same pair of servers.  Until filtering is added to the API,
implementors can just go use `room_id` as a `peek_id` for convenience.

PUT returns 200 OK with the current state of the room being peeked on success,
using roughly the same response shape as the /state SS API.

The response also includes a field called `renewal_interval` which specifies
how often the peeked server requires the peeking server to re-PUT the /peek in
order for it to stay active.  If the peeked server is unavailable, it should
retry via other servers from the room's members until it can reestablish.
We require `/peek`s to be regularly renewed even if the server has been accepting
peeked events, as the fact a server happens to accept peeked events doesn't
mean that it was necessarily deliberately peeking.

Finally, the response also includes a `latest_event` field which provides
the most recent event (as ordered by stream id) at the point of the `/peek`.
This is the event whose id you would pass to `/state` to get the same
response as this `/peek`, and identifies the precise point in time that the
given state refers to.  We return a full event rather than an eventid to
avoid an unnecessary roundtrip.

If the peek is renewed without having lapsed, `PUT /peek` simply returns `{}`
on success.

PUT returns 403 if the user does not have permission to peek into the room,
and 404 if the room ID or peek ID is not known to the peeked server.
If the server implementation doesn't wish to honour the peek request due to
server load, it may respond with 429.  If the room version of the room being
peeked isn't supported by the peeking server, it responds with 400 and
`M_INCOMPATIBLE_ROOM_VERSION`.

DELETE return 200 OK with an empty `{}` on success, and 404 if the room ID or peek ID is
not known to the peeked server.

```
PUT /_matrix/federation/v1/peek/{roomId}/{peekId}?ver=5&ver=6
{}

200 OK
{
    "auth_chain": [
      {
        "type": "m.room.minimal_pdu",
        "room_id": "!somewhere:example.org",
        "content": {
          "see_room_version_spec": "The event format changes depending on the room version."
        }
      }
    ],
    "state": [
      {
        "type": "m.room.minimal_pdu",
        "room_id": "!somewhere:example.org",
        "content": {
          "see_room_version_spec": "The event format changes depending on the room version."
        }
      }
    ],
    "renewal_interval": 3600000,
    "latest_event": {
        "type": "m.room.minimal_pdu",
        "room_id": "!somewhere:example.org",
        "content": {
          "see_room_version_spec": "The event format changes depending on the room version."
        }
      }
    }
}
```

```
DELETE /_matrix/federation/v1/peek/{roomId}/{peekId}
{}

200 OK
{}
```

The state block returned by /peek should be validated just as the one returned
by the /send_join API.

When the user joins the peeked room, the server should just emit the right
membership event rather than calling /make_join or /send_join, to avoid the
unnecessary burden of a full room join, given the server is already participating
in the room.

It is considered a feature that you cannot peek into encrypted rooms, given
the act of peeking would leak the identity of the peeker to the joined users
in the room (as they'd need to encrypt for the peeker).  This also feels
acceptable given there is little point in encrypting something intended to be
world-readable.

## Security considerations

The peeked server becomes a centralisation point which could conspire against
the peeking server to withhold events.  This is not that dissimilar to trying
to join a room via a malicious server, however, and can be mitigated somewhat
if the peeking server tries to query missing events from other servers.
The peeking server could also peek to multiple servers for resilience against
this sort of attack.

The peeked server will be able to track the metadata surrounding which servers
are peeking into which of its rooms, and when.  This could be particularly
sensitive for single-person servers peeking at profile rooms.

## Design considerations

This doesn't solve the problem that rooms wink out of existence when all
participants leave (https://github.com/matrix-org/matrix-doc/issues/534),
unlike other approaches to peeking (e.g. MSC1777)

Do we allow filtering the peek? (e.g. if you only care about particular
events, or particular servers - e.g. if load-balancing peeking via multiple
servers). Similarly, is it concerning that this significantly overlaps with
the /sync CS API?

How do we handle backpressure or rate limiting on the event stream (if at
all?)

## Dependencies

This unblocks MSC1769 (profiles as rooms) and MSC1772 (groups as rooms)
and is required for MSC2753 (peeking via /sync) to be of any use.

## History

This would close https://github.com/matrix-org/matrix-doc/issues/913

An earlier rejected solution is MSC1777, which proposed joining a pseudouser
(`@:server`) to a room in order to peek into it.  However, being forced to write
to a room DAG (by joining such a user) in order to perform a read-only operation
(peeking) was deemed inefficient and rejected.
