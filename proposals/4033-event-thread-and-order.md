# MSC4033: Providing thread and order for all events to allow consistent read receipt handling

We argue that we have made it unnecessarily hard for clients and servers to
decide whether a message is read or unread, and we can solve this problem by
clarifying the definitions, and including extra pieces of information with
every event that help to identify its thread(s) and ordering.

## Motivation

In order to decide whether a room is unread, a Matrix client must decide whether
it contains any unread messages.

In order to decide whether a room has notifications, a Matrix client or server
must decide whether any of its potentially-notifying messages is unread.

Both of these tasks require us to decide whether a message is read or unread.

To make this decision we have receipts. There are two types of receipt: threaded
and unthreaded.

To decide whether an event is read, we use the following rule:

> An event is read if the room contains an unthreaded receipt pointing at an
> event which is *after or the same as* the event, or a threaded receipt
> pointing at an event that is *in the same thread* as the event, and is *after
> or the same as* the event.
>
> Otherwise, it is unread.

(In both cases we only consider receipts sent by the current user, obviously. We
consider either private or public read receipts.)

We do not propose to change the above definition.

To perform this calculation we need definitions of *after or the same as* and *in the same
thread*.

The meaning *the same as* is clear: if a receipt points at an event, then that
event is read.

### Current definition of *after*

The current spec (see
[11.6](https://spec.matrix.org/latest/client-server-api/#receipts) is not clear
about what it calls "read up to" means.

Clients like Element Web make the assumption that *after* means "after in Sync
Order", where "Sync Order" means "the order in which I (the client) received the
events from the server via sync", so if a client received an event and another
event for which it has a receipt via sync, then the event that was later in the
sync or received in a later sync, is after the other one. We think this is
similar to Stream Ordering, which is mentioned once in the spec without
defintion [7.6
Syncing](https://spec.matrix.org/unstable/client-server-api/#syncing), but we
are not certain that it is identical, because we believe it may be possible for
different clients to receive events in a different order from each other for the
same account.

See also [Spec Issue #1167](https://github.com/matrix-org/matrix-spec/issues/1167).

### Current definition of *in the same thread*

See [11.6.22 Threaded read
receipts](https://spec.matrix.org/latest/client-server-api/#threaded-read-receipts),
but a summary in looser language is:

An event is in thread A if:

* its event ID is A and it has `m.thread` children (i.e. it is the thread root), or
* it has an `m.thread` relationship to the event with ID A (i.e. it is a message
  in the thread), or
* it has an ancestor event (found by traversing relationships) that fits either of the above.

An event is in the main thread if:

* it is not in another thread, or
* its ancestor events do not include an `m.thread` relationship

Note that thread root events, and their non-threaded children (e.g. reactions to
thread root events) are in BOTH the main thread and another thread.

### Problems with the current definitions

The current definition of *after* is ambiguous, and difficult for clients to
calculate. It depends on only receiving events via sync, which is impractical
due to backpaginating, and the desire to fetch thread messages via the
`relations` API.

Further, we believe that the current working definition of "Sync Order" does not
make sense, because different clients may receive events in different orders,
meaning that a receipt from one client would be interpreted differently by
another client.

The current definition of *in the same thread* is difficult for clients to
calculate because it requires fetching all parents of an event to identify which
thread it belongs to. In the meantime, clients must deal with events and
receipts that are "homeless".

The current definitions also make it needlessly complex for clients to determine
whether an event is read because they must fetch the event that is referred to by
a receipt before they can make the decision, and hold the receipt "in limbo"
before it is available.

## Proposal

We propose to tighten up the definitions, and include extra information in the
events provided by the server to make it easy to calculate whether an event is
read.

### Proposed definition of *after*

We propose that the definiton of *after* should be:

* Event A is after event B if its Stream Order is larger.
* Where A and B have the same Stream Order, A is after B if A's event ID is
  lexicographically after B's event ID.

### Proposed definition of *in the same thread*

We propose that the definition of *in the same thread* should use this wording:

An event is in the `main` thread if:

* it has no `m.thread_id` property

An event is in a non-main thread if:

* it has an `m.thread_id` property (i.e. it is in the thread whose ID matches
  the value of this property), or
* it contains an `m.is_thread_root` property with value `true`, then it is in
  the thread whose ID is its event ID (i.e. it is a thread root).

Note: thread roots are in TWO threads: the one whose thread ID equals their
event ID, AND the `main` thread.

Note: other events with relationships to the thread root (e.g. reactions to the
thread root) are NOT considered part of the thread. This is a change to the
current definition. We propose that threads should not be considered unread if a
new reaction to the thread root is received.

### Supporting changes to event structure

We propose:

* all events in a thread should contain an `m.thread_id` property.
* all events should contain an `m.stream_order` property.
* all thread root events should contain an `m.is_thread_root` property with
  value `true`.
* all receipts should contain an `m.stream_order` property alongside `m.read`
  and/or `m.read.private` inside the information about an event, which is a
  cache of the `m.stream_order` property within the referred-to event.

This makes it explicit how the server has categorised events, meaning clients
and servers can always agree on what is a thread root, a threaded message, or a
main thread message.

It also makes it explicit which event is before or after another event in Stream
Order.

This prevents disagreements between clients and servers about the meaning of a
particular read receipt, and by including the Stream Order of the referred event
in the receipt, avoids the need to fetch that event in order to make a decision
about which events are read.

## Potential issues

This special-cases threads over other relationships.

But, this was already the case with threaded receipts, and we believe it is
necessary to provide consistent behaviour.

The change to consider reactions to thread roots as outside of the thread may be
inconvenient for clients, because they will probably want to display those
reactions in any "thread view" they display. We consider this inconvenience
worthwhile because it is necessary to ensure the semantics of read receipts make
sense. We do not think that reactions to a thread root should mark that thread
as unread (but we possibly could be persuaded?).

## Alternatives

This proposal would replace
[MSC4023: Thread ID for 2nd order-relation](https://github.com/matrix-org/matrix-spec-proposals/pull/4023)
and the idea that
[MSC3051: A scalable relation format](https://github.com/matrix-org/matrix-spec-proposals/pull/3051)
would help fix receipts.

This propsal would not replace
[MSC3981: /relations recursion](https://github.com/matrix-org/matrix-spec-proposals/pull/3981)
but would make it less important, because we would no longer depend on the
server providing messages in Sync Order, so we could happily fetch messages
recursively and still be able to slot them into the right thread and ordering.

Note that the expectation (from some client devs e.g. me @andybalaam) was that
MSC3981 would solve many problems for clients because the events in a thread
would be returned in Sync Order, but this is not true: the proposal will return
events in Topological Order, which is useless for determining which events are
read.

## Security considerations

None highlighted so far.

## Unstable prefix

TODO

## Dependencies

None at this time.
