# MSC2773: Room kinds

This is an alternative to [MSC1840](https://github.com/matrix-org/matrix-doc/pull/1840) with inspiration
taken from canonical DMs ([MSC2199](https://github.com/matrix-org/matrix-doc/pull/2199)).

Currently rooms are implicitly for conversation purposes, however there are several use cases where
non-conversational data might be present. Typically this could be avoided by using "protocol"
(non-conversational) rooms only on dedicated accounts, however this isn't always possible. MSC1840
solves the problem by specifying a state event which indicates a type of room with an opportunity to
filter them out.

This MSC uses a similar approach, though puts the burden on the homeserver to figure out.

## Proposal

In the `summary` of `/sync`, a field named `m.kind` is introduced. Like other fields in the summary,
the `m.kind` can be omitted if unchanged since the last sync.

The `m.kind` value grammar follows [MSC2758](https://github.com/matrix-org/matrix-doc/pull/2758)'s
proposal. When `m.kind` is not supplied or is an invalid value (not a string, doesn't match grammar, etc)
the default value is implied, as described below.

Specified types are currently:

* `m.conversational` - General conversational room. This is the default value.
* `m.protocol` - A "protocol" room where the information contained within is not intended to be consumed
  by humans. Further identification of the room is left to the individual functionality of the room. For
  example, a profile room might be identified by the presence of a `m.profile` state event.

It is the intention of this MSC to allow protocol rooms to mix different functionality into them where
possible. For example, a protocol room could mix moderation policies, profiles, and groups into a single
room where the context could be left ambiguous (ie: moderation policies could be related to the user
represented by the profile, or could just be a dumping ground - implementation behaviour is not a concern
for this MSC).

This MSC redefines MSC2199's `m.dm` as `m.conversational.dm`, implicitly following the rules of a
conversational room while maintaining MSC2199's described behaviour for the `m.kind`.

Conversational-focused clients SHOULD hide any kinds of rooms they do not recognize or cannot support.
Typically this means that clients would show `m.conversational` (including DMs) rooms only, leaving all the
protocol and custom kinds out of view of the user.

Clients should note that although a room might not be useful to a user, they might still be useful to
the client's own operation. For example, if groups as rooms were accepted then the client would be expected
to identify an `m.protocol` room as a group and use it accordingly.

Rooms have their `m.kind` baked into the room state in one of two ways:

1. As `m.kind` in the `m.room.create` event's `content`.
2. As an `m.room.kind` state event in the room, with `content` of `{"m.kind": "m.protocol"}` and empty string
   for a state key.

When `m.kind` is supplied on the create event, the `m.room.kind` state event serves no purpose. This ensures
the room will *always* be a particular kind and unchanging. Using the `m.room.kind` state event approach allows
the room to drift between kinds over time, as needed. Clients should be aware of the potential for a room to
change kinds and monitor the `m.kind` field in `/sync`.

*Why not just use the state events instead of `m.kind`, like in MSC1840?* For a few somewhat niche reasons:

1. **IoT device support**. IoT devices typically run on limited hardware where a full client-server API
   formatted event might push it over the edge, thus it is important to provide the information to them
   as minimally as possible over `/sync`. IoT devices typically achieve this with a strict filter, which
   would almost certainly exclude the expensive state events. Similarly, IoT devices typically want to
   limit their resource usage for things like web requests - if they're already expected to log to a
   particular room or `/sync`, they don't need the additional overhead of making a `GET /state` call.

2. **State events are heavy for clients**. Each state event a client has to keep track of is lost memory,
   storage, and CPU time to store a simple flag. Instead of expecting clients to haul around the heavyweight
   state events (like `m.room.create` and `m.room.kind`), we can let them get on by just storing the
   purpose for the room and moving on. A client could theoretically rip out the information it cares
   about instead of persisting the whole event, though in practice this is not how clients operate.

3. **Clients sometimes forget or miss state events**. During normal operation, a client might hit a point
   where a state event ends up in a gap over `/sync`, or might simply have storage reliability issues
   and lose the entire section of timeline. Instead of having the client try and always keep track of
   the state event, the server can just inform the client of changes via the `m.kind` described above.
   This is a slightly more efficient way of tracking the room, and allows servers to theoretically save
   some cycles by excluding the state event from the `/sync` stream as well. Further, like IoT, some
   clients apply sync filters which might (un)intentionally exclude the relevant state events.

As alluded to, the server can theoretically exclude to send the `m.room.kind` from the sync stream without
breaking the client as clients should be relying on the `summary`, not the state event rules, to identify
the room's purpose. Currently this MSC does not propose making the `m.room.kind` state event truly
optional for `/sync`, however it is acceptable implementation-wise to do so if the implementation
chooses.

For a bit more detail on point 3: a potential extension for a future MSC might be to also move the room's
name, topic, etc into the `summary` so the client doesn't have to track these giant events. Another
approach would be to make the events smaller, however quite a bit of that information is required for
the client to render appropriately.

This MSC does not propose any filtering semantics for `m.kind`, such as allowing clients to filter
rooms for `/sync` by their `m.kind`. This is left as a potential extension for a later MSC.

Servers SHOULD include the `m.room.create` and `m.room.kind` state events in the `invite_room_state`
over federation on an invite. Clients SHOULD check the `m.kind` for invites and render (or not
render) them appropriately. For example, a client might receive an invite to a group-as-room
identified by the `m.kind` - though it won't render the room in the room list, it should render
an invite to that *group* (not *room*) for the user to accept.

## Potential issues

Servers are now expected to keep track of a room's purpose using some rules, and report on changes
to the client. A naive implementation might never track changes and instead always include `m.kind`
under `summary`, calculating it each time. A more complete implementation would be watching for
`m.room.kind` state events and ensuring the `m.kind` is updated for all its clients.

## Alternatives

As mentioned, MSC1840 solves a similar problem. This MSC might work well in conjunction with it rather
than against it, though this MSC does define some potential downfalls of MSC1840. The downfalls are
niche and limited in practicality, though may be extremely important for the potential use cases of
a system like this outside of groups-as-rooms, profiles-as-rooms, etc.

## Security considerations

When transitioning from invite to joined in any room, the client should be wary of the `m.kind`
changing. For example, if a client receives an invite to a conversational room and the user accepts,
the client might be told by the server that it's actually a protocol room after joining. In this case
the client might wish to hide the problem by immediately leaving the room and telling the user that
their invite is no longer valid or malicious. Note that because `m.kind` can change over time, it is
entirely possible for a room to change purposes between an invite and join due to the state events
described above.

Moderators could also potentially alter the purpose of a room such that the room gets maliciously
removed from a user's room list. This is perceived as a human/social problem and not a technical
issue: do not promote people to power if they will abuse it.

Similarly, a user could invite someone to a conversational room, convert it to a protocol room after
they join, then start mentioning/pinging the user, spamming them. To deal with this, this proposal
recommends that servers silently do not execute notification rules of any kind on non-conversational
rooms. The same applies to clients. Future MSCs might change this as new room kinds are introduced.

On the same line, a client might be participating in a room that it is not showing to the user and
thus might be spammed with events the user is not seeing, but is causing their bandwidth/battery to
be consumed: this should be dealt with like any other hidden event being flooded. Servers could
intentionally create gaps in the timelines or outright block the events from reaching clients.
Similarly, clients might warn the user and recommend leaving the room.

Further in the abuse space of problems, a user could switch a room between conversational and
non-conversational frequently, causing the user's room list to "pop". Servers should apply extremely
strict rate limits to avoid this problem (there's no practical reason to change the room type
several times a minute), and as always the user could just leave the room.

## Unstable prefix

Implementations should use `org.matrix.msc2773.` instead of `m.` while this MSC has not entered a
released version of the specification.

## Sample use case: Things as Rooms

Irrespective of any particular thing as room proposal, it is feasible that a room could be a desirable
structure for representing a thing, such as profiles, groups, or moderation policies. Under this proposal
this could be done in three possible ways:

### Possibility 1: A room per thing

In this scenario, a profile, group, and moderation policy list would all be their own rooms, likely
with their own `m.kind` definitions. This has the advantage of compartmentalizing the data into
smaller, more distinct, structures though also has a disadvantage of using more server resources
and room IDs for small structures.

### Possibility 2: Hybrid rooms (preferred by this MSC)

Instead of separate rooms for a group and moderation policy, it is possible to use a common `m.kind`
of `m.protocol` and instead identify/interpret the information based solely upon each feature's
definition.

Continuing the example, the protocol room might have an `m.group` state event as well as several
`m.policy.rule` state events in it - this could be described as a group with its own moderation
policies, where a bot could apply those policies only in rooms part of that group.

### Possibility 3: Hybrid rooms with conversation support

This effectively makes this MSC useless as it's the same as Possibility 2, but with the room
labelled as a conversational room in addition to its other identified purposes. This could be
a general chat for a group, as an example.

## Sample use case: Controlling a drone at a WebRTC conference

*[Reference](https://matrix.org/blog/2015/05/18/matrix-wins-best-of-show-at-webrtc-world)*.

Instead of sending message events in a room where you're having a call with a drone, a user could
instead use a non-chat application and use a theoretical "login with Matrix" button to use their
existing account. This non-chat application would set up a room for their drone and allow them
to control it, all without their chat-focused apps screaming about WASD movements and ongoing calls.

This use case could be expanded to a wide variety of applications, such as data loggers, third
party integrations (anything that wants "login with Matrix", if we were to support such a button),
video games, etc.
