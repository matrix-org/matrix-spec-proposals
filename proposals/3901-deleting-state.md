# MSC3901: Deleting State

TODO:

- [x] Create document
- [x] Intro and motivation
- [x] History
- [x] Room upgrades will help
- [x] Definition of obsolete state
- [x] Rename to "obsolete"
- [x] Brief summary of each sub-proposal
- [x] Consider changing "definition of obsolete state" into a sub-proposal
    - No, I think it is part of sub-proposal 1
- [x] Go through the meeting notes and transfer ideas into sub-proposals
- [ ] Complete TODOs scattered through the doc
- [x] Add Travis' thought about bans [1]
- [ ] Complete detailed definition of sub-proposals, with help from people who
      know about each area
- [ ] Request review
- [ ] Ask whether we can speed up faster remote joins by omitting obsolete state



## Introduction

### Why delete state?

Matrix rooms have an ever-growing list of state, caused by real-world events
like someone joining a room or sharing their live location.

Even when this state is potentially of little interest (e.g a person left the
room a long time ago, or they stopped sharing their
[MSC3489](https://github.com/matrix-org/matrix-spec-proposals/pull/3489)
location), servers and clients must continue processing and passing around the
state: once a `state_key` has been created it will always exist in a room.

This ever-increasing list of state causes load on servers and clients in terms
of CPU, memory, disk and bandwidth. Since some of this state is of little
interest to users, it would be good to reduce this load.

Further, some more recent spec proposals attempt to increase the number of state
events in use (e.g.
[MSC3401](https://github.com/matrix-org/matrix-spec-proposals/pull/3401),
[MSC3489](https://github.com/matrix-org/matrix-spec-proposals/pull/3489)), and
give permission by default for less-privileged users to create state events
(e.g. [MSC3757](https://github.com/matrix-org/matrix-spec-proposals/pull/3757),
[MSC3779](https://github.com/matrix-org/matrix-spec-proposals/pull/3779)). If
these proposals are accepted, it will be easier for malicious or spammy users to
flood a room with undeletable state, potentially mounting a denial of service
attack against involved homeservers. So, some solution to "clean" an affected
room is desirable.

Note that throughout this document we are only concerned with state
events[^and-redactions]: other events are not relevant to this problem.

[^and-redactions] (and of course, events that redact state events.)

### How this came about

Over several months in 2022 some interested people got together and discussed
how to address this situation. There was much discussion of how to structure
the room graph to allow "forgetting" old state, and not all ideas were fully
explored, but all added complexity, and most ended up with some idea of a new
root node, similar in character to a `m.room.create` event.

We already have a mechanism to start a new room based on an old one: [room
upgrades](https://spec.matrix.org/v1.5/client-server-api/#room-upgrades). So, we
agreed to explore ideas about how to make room upgrades more seamless, in the
hope that they will become good enough to allow "cleaning" rooms of unimportant
state.

### Improving room upgrades will help

We propose improving room upgrades in various ways, and offering an "Optimise
Room" function in clients that allows room administators to "upgrade" a room
(manually) to a new one with the same version.

With enough improvements to upgrades, we believe this will materially improve
the current situation, since there will be a viable plan for rooms that become
difficult to use due to heavy activity or abuse.

We accept that an automatic process that was fully seamless would be better,
but we were unable to design one, and we hope that:

a) improvements to room upgrades may eventually lead to a process that is so
   smooth it can be automatic, or at least very easy, and

b) improvements to room upgrades will bring benefits to Matrix even if they
don't turn out to be the right way to solve the deleting state problem.

### Also, reduce state sent to clients

In addition to improving room upgrades, we think we can improve the situation
by shrinking the state that is sent to clients on initial sync. This should
reduce unnecessary bandwidth use, and reduce storage use within clients.

### Structure of this document

This MSC will probably eventually be split into several MSCs, but they are
gathered together for now to ensure we keep their shared purpose in mind:
reducing the burden of uninteresting state.

Additionally, this document contains a definition of "obsolete" state, which
is referenced in several of the sub-proposals.

The sub-proposals are all believed to be independent[1], but they are listed in
an order that we think makes sense to use, since those listed earlier will
probably be simpler and help us think more clearly about the later ones.

[1] Although 3 (auto-accept invites) does not make a lot of sense without 2
    (create invites).

## Definition of obsolete state

### Purpose of this definition

If we can define clearly what state we consider to be "obsolete", we can make
decisions about what to do with it, including not sending it to clients on an
initial sync, and not copying it across when a room is upgraded.

### Motivation for the definition

Loosely, "obsolete" state is state that is not useful for understanding the
state of the room at this point.  For example, knowing that someone shared their
location in the past is of historical interest, but is not useful for displaying
a live indication of who is sharing now. Similarly, knowing that someone left
the room is not useful for displaying a list of current room members.

Removing a piece of "obsolete" state does not materially change the actual
condition of the room (again, speaking loosely).

### Formal definition

An **obsolete** state event is a state event that has `m.obsolete: true` at the
top level of its `content`.

For example, this event is an obsolete state event:

```json
{
  "type": "m.beacon_info",
  "state_key": "@matthew:matrix.org_46583241",
  "content": {
    "description": "Matthew's other phone",
    "live": false,
    "m.obsolete": true,
    "m.ts": 1436829458432,
    "timeout": 86400000,
    "m.asset": { "type": "m.self" }
  }
}
```

(This example is from
[MSC3489](https://github.com/matrix-org/matrix-spec-proposals/pull/3489), and
in that specific case it would need to be considered whether `m.obsolete` makes
the `live` property redundant.)

If a state event has `m.obsolete: false` or no `m.obsolete` property at all, it
is not obsolete.

No event should ever have an `m.obsolete` property with any other value (other
than `true` or `false`.

To mark some state as obsolete, a client sends a state event with
`m.obsolete: true` in its content. To "unobsolete" some state later, the client
sends another state event with no `m.obsolete` property (or with
`m.obsolete: false`).

### Redacted state events are obsolete

We propose to update the definition of event redaction[^spec-redactions] to
specify that all redacted state events contain `m.obsolete: true` in their
content.

[^spec-redactions] https://spec.matrix.org/v1.4/rooms/v10/#redactions

### Leave events are obsolete

We propose to update the definition of [membership
events](https://spec.matrix.org/v1.5/client-server-api/#mroommember) so that
every event with `membership: "leave"` must also have `m.obsolete: true` in its
content.

Note: `membership: "ban"` events are not considered obsolete since this
information is needed in future to prevent bad actors from re-entering a room.

### Encrypted obsolete state events

Currently, state events are not encrypted, but
[MSC3414](https://github.com/matrix-org/matrix-spec-proposals/pull/3414)
proposes allowing them to be encrypted.

If MSC3414 goes ahead, an obsolete encrypted state event should contain
`m.obsolete: true` in its unencrypted content, as a sibling of e.g. `algorithm`
and `ciphertext`.

When the ciphertext is decrypted, the `content` in the plaintext JSON
should also contain `m.obsolete: true`.

### Alternative definitions

#### content: null

We considered defining an obsolete state event as an event with a state_key and
null content.

However, some existing obsolete state events such as leaving events (membership
events indicating that someone left the room) contain useful content, and there
is no reason to assume that future ones won't also want to do something similar.

#### m.obsolete as a sibling of content

We could say that the `m.obsolete` property is not inside `content`, but
alongside it.

This might make it easier for servers to find and index obsolete state.

However, it would require us to provide a special mechanism (e.g. a new
endpoint) to allow clients to mark events as obsolete, making the implementation
burden of this proposal much greater for both clients and servers.

#### Avoiding a new room version by adding special cases

Some state is already, loosely speaking, "obsolete" in the sense that new
members don't really care about it. For example, leaving events.

It might be possible to define obsolete state as including these special cases,
and this might allow us to avoid needing a new room version.

However, we believe that we need to change the rules around redacted events,
meaning that we can't avoid a new room version. Since we need a new room version
anyway, we have gone for a simpler definition of obsolete state with no special
cases.

## Sub-proposal 1: Hide obsolete state from clients on initial sync
### Proposal

Based on our definition of "obsolete" state, when sending room state to clients
for an initial sync, do not include obsolete state.

### Proposed spec wording change

In [`GET /_matrix/client/v3/sync`](https://spec.matrix.org/latest/client-server-api/#get_matrixclientv3sync),
under "Responses", "Joined Room", in the Description of "state", should be
updated to read:

> Updates to the state in the form of state events. Only includes events that
> occurred before the events provided in `timeline`.

> If since is not provided, or full_state is true, this includes one event for
> each non-obsolete state key that was updated before the start of the events

> Updates to the state, between the time indicated by the since parameter, and
> the start of the timeline (or all state up to the start of the timeline, if
> since is not given, or full_state is true).

> N.B. state updates for m.room.member events will be incomplete if
> lazy_load_members is enabled in the /sync filter, and only return the member
> events required to display the senders of the timeline events in this
> response.

For reference, the current wording is:

> Updates to the state, between the time indicated by the since parameter, and
> the start of the timeline (or all state up to the start of the timeline, if
> since is not given, or full_state is true).

> N.B. state updates for m.room.member events will be incomplete if
> lazy_load_members is enabled in the /sync filter, and only return the member
> events required to display the senders of the timeline events in this
> response.


### New room version

Since this depends on the definition of obsolete state, which requires changes
to redaction logic, this proposal requires a new room version.

### Potential issues

If clients actually need obsolete state to render properly, this would imply
that events have been marked as obsolete when they should not have been. (Note:
we are discussing room state here, not state events. Obsolete state events
should be returned as normal when the events timeline is requested. This allows
users to explore historical events.)

The only time when an obsolete state event is needed to update room state is
when a client has already received non-obsolete state for this `event_key`.
Since this proposal only affects initial sync, clients have not received any
state, so this does not apply.

### Alternatives

We could simply not do this, and hope that the measures we will take to reduce
the load of state on the server will also be enough to help clients.

However, this seems a relatively easy proposal, and we hope that implementing
it will help us understand what we really mean by "obsolete" state, and flush
out problems we have not yet considered.

### Security considerations
### Unstable prefix
### Dependencies

As soon as we can agree on a definition of obsolete state, we believe this
proposal can be implemented.

We will want to adapt existing and proposed behaviour to mark obsolete events as
such. (Examples: [leave
events](https://spec.matrix.org/v1.5/client-server-api/#mroommember), stopping
[live location
sharing](https://github.com/matrix-org/matrix-spec-proposals/pull/3489), ending
a [video call](https://github.com/matrix-org/matrix-spec-proposals/pull/3401).)
However, this does not need to be done at the same time as implementing the
behaviour of not sending obsolete state to clients: we can create the behaviour
first and gradually adapt events to fit with it later.

## Sub-proposal 2: Invite users to an upgraded room

Currently, when an invite-only room is upgraded, all the users must be
re-invited to the new room.

We propose to invite all users as part of the room upgrade process.

### Proposal

TODO: specific spec wording change

### Potential issues
### Alternatives
### Security considerations
### Unstable prefix
### Dependencies

## Sub-proposal 3: Auto-accept invitations to upgraded rooms

Currently, when a room is upgraded, users do not join them until their client
follows the room link in the tombstone event. Some clients require users to
perform this step manually, and others do it automatically.

This makes room upgrades clunky, and prevents users from receiving events for
upgraded rooms until their client triggers the upgrade. This can cause users
to miss important messages.

We propose to specify how servers can evaluate suggested room upgrades, and
if they consider them valid, automatically join users from the old room to the
upgraded one.

### Proposal
### Potential issues
### Alternatives
### Security considerations

TODO: obviously, doing something on behalf of the user is a potential abuse
vector.

### Unstable prefix
### Dependencies

## Sub-proposal 4: Copy more state to upgraded rooms

Currently, when a room is upgraded, the new room is only somewhat similar to
the old one.

We propose to expand the definition of a room upgrade to copy all useful
information from the old to the new room.

This involves copying all non-obsolete, non-user-scoped room state by creating
state events in the upgraded room.

### Proposal
### Potential issues

Homeservers cannot impersonate users from other homeservers, so no one
homeserver can copy the required state.

TODO: this could cause too much state to be copied, or bad or abusive state to
be copied.

### Alternatives
### Security considerations
### Unstable prefix
### Dependencies

## Sub-proposal 5: Upgraded rooms have the same room ID
### Proposal

After a room is upgraded, links to the room still point at the old ID.

For example:

- room aliases point at the old room ID
- bot integrations (including moderation bots) refer to the old room ID
- space hierarchies depend on room ID to represent parent/child space
  relationships
- push rules refer to room IDs
- sync filters are based on room IDs
- 3PID invitations include room ID

We propose to make upgraded rooms keep the same room ID as the old version, by
introducing a server-only sub-ID that represents the version of the room.

Clients and external systems continue to use the existing room ID, and servers
use room ID + room version to identify the real actual room.

When a client talks to a server using just room ID, the server automatically
picks the most recent version of that room.

TODO: much more specific here.

### Potential issues

If servers disagree on which version is most recent, and which version exists,
split brain situations could occur.

### Alternatives
### Security considerations
### Unstable prefix
### Dependencies

## Future work

This section lists partially-formed ideas of further proposals that could
complement or enhance this proposal

### Pruning bans of deactivated users

Some rooms have large numbers of bans, which normally need to be carried over
on a room upgrade. However, it is common for accounts that have been banned in
one room to end up deactivated on the homeserver.

If an account has been deactivated, the ban is no longer useful, so we could
exclude it from the room state.

Risks include:

* Malicious homeservers being able to reverse bans. We could mitigate this by
  restricting the behaviour to the homeserver that is doing the upgrade, and in
  the longer term federating deactivations and trusting some other homeservers.
* Accounts may be reactivated, so this could only be implemented on homeservers
  that implement policies preventing this from happening in ways which would
  disrupt rooms.

### Bulk invite events

When a room is upgraded and we invite all users to the new room, we expect to
invite a lot of users. It would almost certainly improve performance to collect
these invitations into larger events.

Events have a limited size, so we would need to allow sending multiple bulk
events, not just one.
