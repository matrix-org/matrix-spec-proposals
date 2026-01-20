# MSC4292: Handling incompatible room versions in clients

[Room versions](https://spec.matrix.org/v1.14/rooms/) are the mechanism where breaking
behaviours to rooms are managed. These changes usually only impact server implementations,
but there are exceptionally rare cases where clients may face breaking changes.

In the case of a strongly-typed client, they may experience significant incompatibility
with room versions which change core event type schemas, such as `m.room.redaction` in
[MSC2244 (accepted)](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/2244-mass-redactions.md).

This proposal introduces a mechanism for clients to express their compatible room versions
to the server, so they are less likely to encounter issues when a user joins that room. The
user experience of showing "incompatible rooms" is left as a client implementation detail.

## Proposal

A new query parameter and response section are added to [`/sync`](https://spec.matrix.org/v1.14/client-server-api/#get_matrixclientv3sync). Clients can add any number of `supported_room_version`
query parameters to indicate what room versions it supports to the server. This is preferred over
a filter to avoid clients needing to re-initial sync to change that filter, especially as new room
versions are introduced in future.

The server takes the unique set of `supported_room_version` parameters and determines which room
versions are compatible with that set. The compatible set may be larger than the supported set if
there are room versions which don't contain breaking changes for clients. These room versions will
be identified in the spec, and currently include the following:

* [Room Version 2](https://spec.matrix.org/v1.14/rooms/v2/) - No client changes.
* [Room Version 5](https://spec.matrix.org/v1.14/rooms/v5/) - No client changes.
* [Room Version 6](https://spec.matrix.org/v1.14/rooms/v6/) - While the redaction algorithm did change,
  it is not backwards incompatible for clients. The effects of redactions may be greater than intended,
  however can be relatively easily fixed after a client bugfix.
* [Room Version 7](https://spec.matrix.org/v1.14/rooms/v7/) - Knocking was added, but not in a way
  which requires clients to implement it right away.
* [Room Version 8](https://spec.matrix.org/v1.14/rooms/v8/) - Restricted join rules were added, but
  like in v7, not in a way which requires implementation.
* [Room Version 9](https://spec.matrix.org/v1.14/rooms/v9/) - Adds to the redaction algorithm, making
  the effect similar to v6.
* [Room Version 10](https://spec.matrix.org/v1.14/rooms/v10/) - Adds another join rule, similar to
  v7 and v8.
* [Room Version 11](https://spec.matrix.org/v1.14/rooms/v11/) - Reduces the set of redacted fields on
  events. Like v6 and v9, the effect of a redaction applied client-side may over- (or under-) redact
  an event, but clients can resolve this after a bugfix release if desired.

**Note**: This proposal expects that the room versions listed above will be amended to describe their
backwards compatibility functions. For example, that a client over/under-redacting an event does not
meaningfully change the intended effect client-side, as clients don't perform content hash checks. A
client which wishes to be perfectly accurate though may re-request redacted events from the server to
get the server-redacted copy and replace the locally cached event.

This implies that a client can make the following call to support all current (as of writing) room
versions:

```
/sync
  ?supported_room_version=1
  &supported_room_version=3
  &supported_room_version=4
```

As an example, if the client excluded v1 in its supported set, then v2 would also be considered
incompatible for that client.

**Note**: Room versions do not need to be linear, however a function of specified room versions is
that they all explicitly build upon each other. If this were to change, it'd likely be incompatible
with clients and require a new `supported_room_version`.

While complex, this "compatible set is larger than supported set" functionality is to ensure that when
the specification (and server) produces a backwards-compatible version, clients are not restricting
user access to those rooms. This mirrors the general rollout already used on all 11 room versions
today.

If a client does not specify any `supported_room_version` parameters, it is assumed to support 1, 3,
and 4 (as shown above). This is due to when this MSC was written, and the age of the "incompatible"
room versions.

Just before providing a response to the client, the server moves rooms with incompatible versions to
the new `incompatible_rooms` section. The object type is the same as `rooms`. Filters, limited syncs,
etc are all calculated prior to this move - the server calculates sync as normal, but just before it
`return 200 OK;`'s, it moves the rooms as needed.

There is no expectation that a server remember what supported versions a client calls `/sync` with.
If the client suddenly adds a new version, the server doesn't add any additional context to the affected
rooms when they get placed in `rooms`. This can also mean that a client will get two different responses
for otherwise identical requests: the same `filter`, `since`, etc parameters but different
`supported_room_version` set can mean that rooms "jump" between `rooms` and `incompatible_rooms`.

Clients SHOULD persist `incompatible_rooms` where possible to make it easier to render them when support
is added, *or* SHOULD ask the server for the set of joined rooms and their state with a highly filtered
`/sync` call upon first startup after adding a new `supported_room_version` to rebuild local state/cache.

If a client supplies a supported room version which is unknown to the server, the server ignores that
room version in its compatibility calculation.

## Potential issues

Clients may lose context on rooms they don't "know" how to participate in until they add support for
that room version. As described in the proposal, clients can (and should) use techniques for acquiring
the required information to make that room usable to the user.

Clients which have a concept of an "incompatible room" (ie: a room the client doesn't support, but is
still shown to the user as clickable) will need to add UI/UX to support that case. This may be a simple
case of showing a "please update your client to see this room" error for some clients.

Sliding sync, in any of its variants, will also need to consider a mechanism similar to this MSC.

This MSC does not affect any other endpoints. The assumption made is that clients which call other
endpoints after `/sync` are expecting potentially breaking events, especially if they implement this
MSC prior to making those calls. Clients which don't `/sync` are typically well aware of the room(s)
they're supposed to be participating in, acting as a natural compatibility check.

## Alternatives

The functionality itself doesn't really have alternatives, but there are multiple ways to represent
the proposed solution:

* **Use a filter** - Instead of adding more query parameters to `/sync`, clients could be asked to
  populate a field in a `Filter` object. This has complexity in that changing the filter means discaring
  previously-useful data, delaying startup of most clients.

* **Require the full set to be specified** - Instead of having the server calculate compatibility,
  clients could be required to specify *every* room version they support. This would lead to rooms
  being marked "incompatible" while room versions roll out. Further, most room versions only impact
  servers and not clients, leading to significant noise for users about missing/incompatible rooms.

* **Server-side tracking of client support** - The server could be required to track which room versions
  a client previously specified to `/sync`, and attempt to "re-introduce" rooms which may have been
  previously incompatible. This could be tricky to get right, especially when there's a lot of time
  between a room first showing up on a user's sync and when their client supports it. Clients may
  require different information to set up a room in their local cache, and having to reintroduce the
  room could lead to a slightly weird set of information returned. Instead, this proposal suggests
  that clients go out and retrieve the information they need, if any, upon supporting a new room
  version.

## Security considerations

No significant security considerations are made.

However, servers SHOULD be careful to avoid complex compatibility checking. Clients which specify
"weird" room versions could cause extra CPU time while the server figures out what that means.

## Unstable prefix

While this proposal is not considered stable, implementations should use `org.matrix.msc4292.supported_room_version`
and `org.matrix.msc4292.incompatible_rooms`. If a client does *not* specify any supported room
versions, servers should instead behave as though this MSC is not in effect for that request.

## Dependencies

This MSC does not have any direct dependencies, but may be required upon by other MSCs (especially
ones which cause breaking changes to clients in room versions).
