# MSC3189: Per-room/per-space profile data

People frequently have different identities in different communities. In the
context of Matrix, users may therefore want their display name or avatar to
appear differently in certain social contexts, such as within a room or a space.

While most clients technically already support per-room display names (by
getting profile data from a user's membership events in a room), this feature
suffers from a lack of documentation and server-side support. This proposal
attempts to improve on per-room/per-space profile data in the following ways:

1. Documenting the current de-facto mechanism for per-room profile data
2. Keeping global profile changes from overwriting per-room profile data (if desired)
3. Allowing clients to set profile data for an entire space in a single request rather than sending membership events in bulk

## Proposal

### Per-room profile data

First, the existing behavior: When showing a user's display name or avatar in a
room, clients should reference the `displayname` and `avatar_url` attributes of
the user's `m.room.member` state. Thus, to set a display name or avatar in a
specific room, clients should modify these attributes via the relevant state
APIs.

In order to prevent per-room profile data from being overwritten when the user
updates their global profile, an optional query parameter named `force` of type
`boolean` is added to the `PUT /_matrix/client/r0/profile/{userId}/avatar_url`
and `PUT /_matrix/client/r0/profile/{userId}/displayname` endpoints.

If `force` is `true`, the profile change is propogated to all of the user's
rooms by adding, updating, or removing the relevant attribute of the user's
`m.room.member` state (and only that attribute) as needed. Unlike the current
behavior, updating `displayname` *must not* cause the user's `avatar_url` to
change in any rooms, and vice versa.

If `force` is `false` (the default value), the profile change is only propogated
to rooms in which the relevant attribute (`displayname` or `avatar_url`) is
equal to that of the user's global profile before the update. This ensures that
by default, custom per-room profile data will not be overwritten.

### Per-space profile data

Per-space profile data is communicated in the same way as global and per-room
profile data, by updating the relevant `m.room.member` attributes in the
space-room and all of its children, recursively. To make this a simple operation
for clients, another optional query parameter named `space` of type `string` is
added to the `PUT /_matrix/client/r0/profile/{userId}/avatar_url` and `PUT
/_matrix/client/r0/profile/{userId}/displayname` endpoints.

If specified, `space` must be a valid ID of a room of which the user is a member
(regardless of whether it is of type `m.space`), and its effect is to limit the
scope of the profile change to the given space. This is achieved by first
updating the per-room profile data for the given space-room, and then recursing
into all `m.space.child` rooms of which the user is a member.

The `space` parameter obeys `?force=false` as well, by only overwriting an
`m.room.member` attribute if it matches the previous profile data of the root
space *or* the user's global profile. If this is not the case, meaning a room
with a different per-room profile has been found, the profile change stops there
and does not continue recursing into the room's space children. Additionally,
servers must take care to handle cycles in the space graph and not recurse
infinitely (e.g. by tracking which rooms it has visited).

## Potential issues

This proposal assumes that having "one true display name per room" is a
desirable feature, since it minimizes complexity for clients and is compatible
with how most implementations already determine profile data. However, since
rooms can belong to multiple spaces, possibly with conflicting profile data,
this causes a certain degree of arbitrariness in what profile data gets set for
such rooms (depending purely on the order in which the user sets their per-space
profiles, and whether `force` is set). If this matters, users can always drill
down to room-level profile settings, though, and clients may assist them e.g. by
displaying a list of applicable per-space profiles to switch between.

Arguably, per-space profile data should be a more first-class feature, with
server support for things like inheriting profile data from parent spaces on
join. This proposal leaves it up to clients to implement such "inheritance"
behavior as they see fit, by altering individual `m.room.member` states when
rooms are joined, added to spaces, etc. If desired, servers could be changed to
automate some of this behavior in the future, though arguably this should be
left to clients, since they have more context for e.g. which parent space the
user was viewing a room from when they joined it.

## Alternatives

An alternative would be to store per-room/per-space profile data as a part of
[extensible profiles](https://github.com/matrix-org/matrix-doc/pull/1769),
essentially keeping a public mapping of room IDs → profile data in a single
location. While altering `m.room.member` state gives us per-room and per-space
profile data for free, this alternative would require more action from clients
to implement. It would also leak data about users' profiles in private rooms,
which is a significant privacy concern, and it is unclear how conflicting
profiles would affect the "one source of truth" given by `m.room.member` state.
Furthermore, extensible profiles seem unlikely to land anytime soon, while
per-room/per-space profile data is arguably a more urgent feature, and should
not depend on it.

## Security considerations

None that I am aware of.

## Unstable prefix

During development of this feature the versions of the profile APIs augmented
with `force` and `space` will be available at unstable endpoints:

```text
PUT /_matrix/client/unstable/org.matrix.msc3189/profile/{userId}/avatar_url
PUT /_matrix/client/unstable/org.matrix.msc3189/profile/{userId}/displayname
```
