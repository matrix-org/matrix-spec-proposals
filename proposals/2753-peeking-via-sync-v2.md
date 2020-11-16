# MSC2753: Peeking via Sync (Take 2)

## Problem

[Room previews](https://matrix.org/docs/spec/client_server/r0.6.1#id116), more
commonly known as peeking, has a number of usecases, such as:

 * Look at a room before joining it, to preview it.
 * Look at a user's profile room (see
   [MSC1769](https://github.com/matrix-org/matrix-doc/issues/1769)).
 * Browse the metadata or membership of a space (see
   [MSC1772](https://github.com/matrix-org/matrix-doc/issues/1772)).
 * Monitor [moderation policy lists](https://matrix.org/docs/spec/client_server/r0.6.1#moderation-policy-lists).

Currently, peeking relies on the deprecated v1 `/initialSync` and `/events`
APIs.

This poses the following issues:

 * Servers and clients must implement two separate sets of event-syncing logic,
   doubling complexity.
 * Peeking a room involves setting a stream of long-lived /events requests
   going. Having multiple streams is racey, competes for resources with the
   /sync stream, and doesn't scale given each room requires a new /events
   stream.
 * v1 APIs are deprecated and not implemented on new servers.

This proposal suggests a new API in which events in peeked rooms would be
returned over `/sync`.

## Proposal

We add an CS API called `/peek/{roomIdOrAlias}`, very similar to `/join/{roomIdOrAlias}`.

Calling `/peek`:
 * Resolves the given room alias to a room ID, if needed.
 * Adds the room (if permissions allow) to a new section of the `/sync` response
   called `peek` - but only for the device which called `/peek`.
 * The `peek` section is identical to `join`, but shows the live activity of
   rooms for which that device is peeking.

The API returns 404 on an unrecognised room ID or alias, or 403 if the room
does not allow peeking.  Rooms allow peeking if they have `history_visibility`
of `world_readable`.  N.B. `join_rules` do not affect peekability - it's
possible to have an invite-only room which joe public can still peek into, if
`history_visibility` has been set to `world_readable`.

If the `history_visibility` of a room changes to not be `world_readable`, any
peeks on the room are cancelled.

Similar to `/join`, `/peek` lets you specify `server_name` querystring
parameters to specify which server(s) to try to peek into the room via (when
coupled with [MSC2444](https://github.com/matrix-org/matrix-doc/pull/2444)).

If a user subsequently `/join`s the room they're peeking, we atomically move
the room to the `join` block of the `/sync` response, allowing the client to
build on the state and history it has already received without re-sending it
down `/sync`.

To stop peeking, the user calls `/unpeek` on the room, similar to `/leave`.
This returns 200 on success, 404 on unrecognised ID, or 400 if the room was not
being peeked in the first place.  Having stopped peeking, the unpeeked room
will appear in the `leave` block of the next sync response to tell the client
that the user is no longer peeking.

The new `/peek` and `/unpeek` endpoints require authentication and can be
ratelimited. Their responses are analogous to their `/join` and `/leave`
counterparts (eg: `room_id` in the response and empty object when stopping).

Clients should check for any irrelevant peeked rooms on launch (left over from
previous instances of the app) and explicitly `/unpeek` them to conserve
resources.

## Encrypted rooms

(this para taken from MSC #2444):

It is considered a feature that you cannot peek into encrypted rooms, given
the act of peeking would leak the identity of the peeker to the joined users
in the room (as they'd need to encrypt for the peeker). This also feels
acceptable given there is little point in encrypting something intended to be
world-readable.

## Potential issues

It could be seen as controversial to add another new block to the `/sync`
response.  We could use the existing `join` block, but:

 * it's a misnomer (given the user hasn't joined the rooms)
 * `join` refers to rooms which the *user* is in, rather than that they are
   peeking into using a given *device*
 * we risk breaking clients who aren't aware of the new style of peeking.
 * there's already a precedent for per-device blocks in the sync response (for
   to-device messages)

It could be seen as controversial to make peeking a per-device rather than
per-user feature.  When thinking through use cases for peeking, however:

 1. Peeking a chatroom before joining it is the common case, and is definitely
    per-device - you would not expect peeked rooms to randomly pop up on other
    devices, or consume their bandwidth.
 2. [MSC1769](https://github.com/matrix-org/matrix-doc/pull/1769) (Profiles as
    rooms) is also per device: if a given client wants to look at the Member
    Info for a given user in a room, it shouldn't pollute the others with that
    data.
 3. [MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772) (Groups as
    rooms) uses room joins to indicate your own membership, and peeks to query
    the group membership of other users.  Similarly to profiles, it's not clear
    that this should be per-user rather than per-device (and worse case, it's a
    matter of effectively opting in rather than trying to filter out peeks you
    don't care about).

## Alternatives

[MSC1776](https://github.com/matrix-org/matrix-doc/pull/1776) defined an
alternative approach, where you could use filters to add peeked rooms into a
given `/sync` response as needed.  This however had some issues:

 * You can't specify what servers to peek remote rooms via.
 * You can't identify rooms via alias, only ID
 * It feels hacky to bodge peeked rooms into the `join` block of a given
   `/sync` response
 * Fiddling around with custom filters feels clunky relative to just calling a
   `/peek` endpoint similar to `/join`.

While experimenting with implementing MSC1776, I came up with this as an
alternative that empirically feels much simpler and tidier.

## Security considerations

Servers should ratelimit calls to the new endpoints to stop someone DoSing the
server.

Servers may stop maintaining a `/peek` if its device has not `/sync`ed
recently, and thus reclaim resources.  At the next `/sync` the server would
need to restore the `peek` and provide a gappy update.  This is most relevant
in the context of peeking into a remote room via
[MSC2444](https://github.com/matrix-org/matrix-doc/pull/2444) however.

## Unstable prefix


The following mapping will be used for identifiers in this MSC during
development:

Proposed final identifier       | Purpose | Development identifier
------------------------------- | ------- | ----
`/_matrix/client/r0/peek` | API endpoint | `/_matrix/client/unstable/org.matrix.msc2753/peek`
`/_matrix/client/r0/rooms/{roomId}/unpeek` | API endpoint | `/_matrix/client/unstable/org.matrix.msc2753/rooms/{roomId}/unpeek`
