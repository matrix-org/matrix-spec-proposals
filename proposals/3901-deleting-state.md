# MSC3901: Deleting State

TODO: rename to "obsolete" (or "useless" or "marked for deletion")?

## Introduction

### Why delete state?

Matrix rooms have an ever-growing list of state, caused by real-world events
like someone joining a room or sharing their live location.

Even when this state is potentially of little interest (e.g a person left the
room a long time ago, or they stopped sharing their location), servers and
clients must continue processing and passing around the state: once a
`state_key` has been created it will always exist in a room.

TODO: refer to live location sharing MSC

This ever-increasing list of state causes load on servers and clients in terms
of CPU, memory, disk and bandwidth. Since some of this state is of little
interest to users, it would be good to reduce this load.

Further, some more recent spec proposals attempt to increase the number of state
events in use, and give permission by default for less-privileged users to
create state events. If these proposals are accepted, it will be easier for
malicious or spammy users to flood a room with undeletable state, potentially
mounting a denial of service attack against involved homeservers. So, some
solution to "clean" an affected room is desirable.

Note that throughout this document we are only concerned with state
events[^and-redactions], other events are not relevant to this problem.

[^and-redactions] (and of course, events that redact state events.)

TODO: refer to relevant MSCs: live location, and also the owned state ones.

### How this came about

Over several months in 2022 some interested people got together and discussed
how to address this situation. There was much discussion of how to structure
the room graph to allow "forgetting" old state, and not all ideas were fully
explored, but all added complexity, and most ended up with some idea of a new
root node, similar in character to a `m.room.create` event.

We already have a mechanism to start a new room based on an old one: room
upgrades. So, we agreed to explore ideas about how to make room upgrades more
seamless, in the hope that they will become good enough to allow "cleaning"
rooms of unimportant state.

TODO: link to room upgrades in spec.

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
by excluding the state that is sent to clients on initial sync. This should
reduce unnecessary bandwidth use, and reduce storage use within clients.

### Structure of this document

This MSC will probably eventually be split into several MSCs, but they are
gathered together for now to ensure we keep their shared purpose in mind:
reducing the burden of uninteresting state.

Additionally, this document contains a definition of "deleted" state, which
is referenced in several of the sub-proposals.

The sub-proposals are all believed to be independent[1], but they are listed in
an order that we think makes sense to use, since those listed earlier will
probably be simpler and help us think more clearly about the later ones.

[1] Although 3 (auto-accept invites) does not make a lot of sense without 2
    (create invites).

## Definition of deleted state

### Purpose of this definition

If we can define clearly what state we consider to be "deleted", we can make
decisions about what to do with it, including not sending it to clients on an
initial sync, and not copying it across when a room is upgraded.

### Motivation for the definition

Loosely, "deleted" state is state that is not useful for understanding the state
of the room at this point.  For example, knowing that someone shared their
location in the past is of historical interest, but is not useful for displaying
a live indication of who is sharing now. Similarly, knowing that someone left
the room is not useful for displaying a list of current room members.

Removing a piece of "deleted" state does not materially change the actual
condition of the room (again, speaking loosely).

### Formal definition

A **deleted** state event is a state event that has `deleted: true` at the top
level of its `content`.

For example, this event is a deleted state event:

```json
{
  "type": "m.beacon_info",
  "state_key": "@matthew:matrix.org_46583241",
  "content": {
    "description": "Matthew's other phone",
    "live": false,
    "deleted": true,
    "m.ts": 1436829458432,
    "timeout": 86400000,
    "m.asset": { "type": "m.self" }
  }
}
```

(This example is from
[MSC3489](https://github.com/matrix-org/matrix-spec-proposals/pull/3489), and
in that specific case it would need to be considered whether `deleted` makes the
`live` property redundant.)

If a state event has `deleted: false` or no `deleted` property at all, it is not
deleted.

TODO: should it be `m.deleted`?

No event should ever have a `deleted` property with any other value (other than
`true` or `false`.

To mark some state as deleted, a client sends a state event with `deleted: true`
in its content. To "undelete" some state later, the client sends another state
event with no `deleted` property (or with `deleted: false`).

### Concerns

This would effectively prevent anyone from using a `deleted` property for some
other purpose in their event content definition, and would clash with anyone who
has already defined their events in this way.

### Redacted state events are deleted

We propose to update the definition of event redaction[^spec-redactions] to
specify that all redacted events contain `deleted: true` in their content.

[^spec-redactions] https://spec.matrix.org/v1.4/rooms/v10/#redactions

### Leave events are deleted

We propose to update the definition of membership events so that events saying
a member has left contain `deleted: true` in theit content.

TODO: link to membership events in the spec

### Encrypted deleted state events

Currently, state events are not encrypted, but
[MSC3414](https://github.com/matrix-org/matrix-spec-proposals/pull/3414)
proposes allowing them to be encrypted.

If MSC3414 goes ahead, a deleted encrypted state event should contain
`deleted: true` in its unencrypted content, as a sibling of e.g. `algorithm`
and `ciphertext`.

When the ciphertext is decrypted, the `content` in the plaintext JSON
should also contain `deleted: true`.

### Alternative definitions

#### content: null

We considered defining a deleted state event as an event with a state_key and
null content.

However, some existing deleted state events such as leaving events (membership
events indicating that someone left the room) contain useful content, and there
is no reason to assume that future ones won't also want to do something similar.

#### deleted as a sibling of content

We could say that the `deleted` property is not inside `content`, but alongside
it.

This has the advantage that it cannot clash with any existing event definitions
that include a `deleted` key, and it might make it easier for servers to find
and index deleted state.

However, it would require us to provide a special mechanism (e.g. a new
endpoint) to allow clients to mark events as deleted, making the implementation
burden of this proposal much greater for both clients and servers.

#### Avoiding a new room version by adding special cases

Some state is already, loosely speaking, "deleted" in the sense that new members
don't really care about it. For example, leaving events.

It might be possible to define deleted state as including these special cases,
and this might allow us to avoid needing a new room version.

However, we believe that we need to change the rules around redacted events,
meaning that we can't avoid a new room version. Since we need a new room version
anyway, we have gone for a simpler definition of deleted state with no special
cases.

## Sub-proposal 1: Hide deleted state from clients on initial sync
### Proposal

Based on our definition of "deleted" state, when sending room state to clients
for an initial sync, do not include deleted state.

TODO: specific spec wording change

### Potential issues

If clients actually need deleted state to render properly, this would imply
that events have been marked as deleted when they should not have been. (Note:
we are discussing room state here, not state events. Deleted state events
should be returned as normal when the events timeline is requested. This allows
users to explore historical events.)

The only time when a deleted state event is needed to update room state is when
a client has already received non-deleted state for this `event_key`. Since
this proposal only affects initial sync, clients have not received any state,
so this does not apply.

### Alternatives

We could simply not do this, and hope that the measures we will take to reduce
the load of state on the server will also be enough to help clients.

However, this seems a relatively easy proposal, and we hope that implementing
it will help us understand what we really mean by "deleted" state, and flush
out problems we have not yet considered.

### Security considerations
### Unstable prefix
### Dependencies

As soon as we can agree on a definition of deleted state, we believe this
proposal can be implemented.

## Sub-proposal 2: Invite users to an upgraded room

Currently, when an invite-only room is upgraded, all the users must be
re-invited to the new room.

We propose to invite all users as part of the room upgrade process.

### Proposal

TODO: specific spec wording change
TODO: consider a bulk-invite event, either as part of this MSC or a separate one

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

This involves copying all non-deleted, non-user-scoped room state by creating
state events in the upgraded room.

### Proposal
### Potential issues

TODO: this could cause too much state to be copied, or bad or abusive state to
be copied.

### Alternatives
### Security considerations
### Unstable prefix
### Dependencies

## Sub-proposal 5: Upgraded rooms have the same room ID
### Proposal
### Potential issues
### Alternatives
### Security considerations
### Unstable prefix
### Dependencies
