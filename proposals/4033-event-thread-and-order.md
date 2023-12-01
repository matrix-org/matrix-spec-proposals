# MSC4033: Explicit ordering of events for receipts

The [spec](https://spec.matrix.org/unstable/client-server-api/#receipts) states
that receipts are "read-up-to" without explaining what order the events are in,
so it is difficult to decide whether an event is before or after a receipt.

We propose adding an explicit order number to all events, so that it is clear
which events are read.

This proposal covers receipts, and not fully-read markers. Fully-read markers
have the same issue in terms of ordering, and should probably be fixed in a
similar way, but they are not addressed here.

## Motivation

To decide whether a room is unread, a Matrix client must decide whether it
contains any unread messages.

Similarly, to decide whether a room has notifications, we must decide whether
any of its potentially-notifying messages is unread.

Both of these tasks require us to decide whether a message is read or unread.

To make this decision we have receipts. We use the following rule:

> An event is read if the room contains an unthreaded receipt pointing at an
> event which is *after* the event, or a threaded receipt pointing at an event
> that is in the same thread as the event, and is *after* or the same as the
> event.
>
> Otherwise, it is unread.

(In both cases we only consider receipts sent by the current user, obviously. We
consider either private or public read receipts.)

To perform this calculation we need a clear definition of *after*.

### Current definition of *after*

The current spec (see
[11.6 Receipts](https://spec.matrix.org/latest/client-server-api/#receipts)) is not clear
about what it calls "read up to" means.

Clients like Element Web make the assumption that *after* means "after in Sync
Order", where "Sync Order" means "the order in which I (the client) received the
events from the server via sync", so if a client received an event and another
event for which it has a receipt via sync, then the event that was later in the
sync or received in a later sync, is after the other one.

See
[room-dag-concepts](https://github.com/matrix-org/synapse/blob/develop/docs/development/room-dag-concepts.md#depth-and-stream-ordering)
for some Synapse-specific information on Stream Order. In Synapse, Sync Order is
expected to be identical to its concept of Stream Order.

See also [Spec Issue #1167](https://github.com/matrix-org/matrix-spec/issues/1167),
which calls out this ambiguity about the meaning of "read up to".

### Problems with the current definition

The current definition of *after* is ambiguous, and difficult for clients to
calculate. It depends on only receiving events via sync, which is impossible
since we sometimes want messages that did not arrive via sync, so we use
different APIs such as `messages` or `relations`.

The current definition also makes it needlessly complex for clients to determine
whether an event is read because the receipt itself does not hold enough
information: the referenced event must be fetched and correctly ordered.

Note: these problems actually apply to all receipts, not just those of the
current user. The symptoms are much more visible and impactful when the current
user's receipts are misinterpreted than for other users, but this proposal
covers both cases.

## Proposal

We propose to add an explicit order number to events and receipts, so we can
easily compare whether an event is before or after a receipt.

This order should be a number that is attached to an event by the server before
it sends it to any client, and it should never change. It should,
loosely-speaking, increase for "newer" messages within the same room.

The order of an event may be negative, and if so it is understood that this
event is always read. The order included with a receipt should never be
negative.

The ordering must be consistent between a user's homeserver and all of that
user's connected clients. There are no guarantees it is consistent across
different users or rooms. It will be inconsistent across federation as there is
no mechanism to sync order between homeservers. For this reason, we propose that
`order` be included in an event's `unsigned` property.

This proposal attaches no particular meaning to the rate at which the ordering
increments. (Although we can imagine that some future proposal might want to
expand this idea to include some meaning.)

### Examples

Example event (changes are highlighted in bold):

<pre>{
  "type": "m.room.message",
  "content": {
    "body": "This is an example text message",
    "format": "org.matrix.custom.html",
    "formatted_body": "&lt;b&gt;This is an example text message&lt;/b&gt;",
    "msgtype": "m.text"
  },
  "event_id": "$143273582443PhrSn:example.org",
  "origin_server_ts": 1432735824653,
  "room_id": "!jEsUZKDJdhlrceRyVU:example.org",
  "sender": "@example:example.org",
  "unsigned": {
    "age": 1234,
    <b>"order": 56764334543</b>
  }
}</pre>

Example encrypted event (changes are highlighted in bold):

<pre>{
  "type": "m.room.encrypted",
  "content": {
    "algorithm": "m.megolm.v1.aes-sha2",
    "sender_key": "<sender_curve25519_key>",
    "device_id": "<sender_device_id>",
    "session_id": "<outbound_group_session_id>",
    "ciphertext": "<encrypted_payload_base_64>"
  }
  "event_id": "$143273582443PhrSn:example.org",
  "origin_server_ts": 1432735824653,
  "room_id": "!jEsUZKDJdhlrceRyVU:example.org",
  "sender": "@example:example.org",
  "unsigned": {
    "age": 1234,
    <b>"order": 56764334543</b>
  }
}</pre>

Example receipt (changes are highlighted in bold):

<pre>{
  "content": {
    "$1435641916114394fHBLK:matrix.org": {
      "m.read": {
        "@erikj:jki.re": {
          "ts": 1436451550453,
          <b>"order": 56764334544,</b>
        }
      },
    }
  },
  "type": "m.receipt"
}</pre>

We propose:

* all events should contain an `order` property inside `unsigned`.
* all receipts should contain an `order` property alongside `ts` inside the
  information about an event, which is a cache of the `order` property within
  the referred-to event.

The `order` property in receipts should be inserted by servers when they are
creating the aggregated receipt event.

If the server is not able to provide the order of a receipt (e.g. because it
does not have the relevant event) it should not send the receipt. If a server
later receives an event, allowing it to provide an order for this receipt, it
should send the receipt at that time. Rationale: without the order, a receipt is
not useful to the client since it is not able to use it to determine which
events are read. If a receipt points at an unknown event, the safest assumption
is that other events in the room are unread i.e. there is no receipt.

If a receipt is received for an event with negative order, the server should set
the order in the receipt to zero. All events with negative order are understood
to be read.

Note that the `order` property for a particular event will probably be the same
for every user, so will be repeated multiple times in an aggregated receipt
event. This structure was chosen to reduce the chance of breaking existing
clients by introducing `order` at a higher level.

### Proposed definition of *after*

We propose that the definition of *after* should be:

* Event A is after event B if its order is larger.

We propose updating the spec around receipts
([11.6 Receipts](https://spec.matrix.org/latest/client-server-api/#receipts))
to be explicit about what "read up to" means, using the above definition.

### Definition of read and unread events

We propose that the definition of whether an event is read should include the
original definition plus the above definition of *after*, and also include this
clarification:

> (Because the receipt itself contains the `order` of the pointed-to event,
> there is no need to examine the pointed-to event: it is sufficient to compare
> the `order` of the event in question with the `order` in the receipt.)

Further, it should be stated that events with negative order are always read,
even if no receipt exists.

### Order does not have to be unique

If this proposal required the `order` property to be unique within a room, it
might inadvertently put constraints on the implementation of servers since some
linearised process would need to be involved.

So, we do not require that `order` should be unique within a room. Instead, if
two events have the same `order`, they are both marked as read by a receipt with
that order.

Events with identical order introduce some imprecision into the process of
marking events as read, so they should be minimised where possible, but some
overlap is tolerable where the server implementation requires it.

So, a server might choose to use the epoch millisecond at which it received a
message as its order. However, if a server receives a large batch of messages in
the same millisecond, this might cause undesirable behaviour, so a refinement
might be the millisecond as the integer part and a fractional part that
increases as the batch is processed, preserving the order in which the server
receives the messages in the batch.

If a server were processing multiple batches in parallel, it could implement
this in each process separately, and accept that some events would receive
identical orders, but this would be rare in practice and have little effect on
end users' experience of unread markers.

### Redacted events

Existing servers already include an `unsigned` section with redacted events,
despite `unsigned` not being mentioned in the [redaction
rules](https://spec.matrix.org/unstable/rooms/v10/#redactions).

Therefore we propose that redacted events should include `order` in exactly the
same way as all room events.

## Discussion

### What order to display events in the UI?

It is desirable that the order property should match the order of events
displayed in the client as closely as possible, so that receipts behave
consistently with the displayed timeline. However, clients may have different
ideas about where to display late-arriving messages, so it is impossible to
define an order that works for all clients. Instead we agree that a consistent
answer is the best we can do, and rely on clients to provide the best UX they
can for late-arriving messages.

### Stream order or Topological Order?

The two orders that we might choose to populate the `order` property are "stream
order" where late-arriving messages tend to receive higher numbers, or
"Topological Order" where late-arriving message tend to receive lower numbers.

We believe that it is better to consider late-arriving messages as unread,
meaning the client has the information that these newly arrived messages have
not been read and can choose how to display it (or not). This is what leads us
to suggest Stream Order as the correct choice.

However, if servers choose Topological Order, this proposal still works - we
just have what the authors consider undesirable behaviour regarding
late-arriving events (they are seen as read even though they are not).

### Inconsistency across federation

Because order may be inconsistent across federation[^1], one user may
occasionally see a different unread status for another user from what that user
themselves see. We regard this as impossible to avoid, and expect that in most
cases it will be unnoticeable, since home servers with good connectivity will
normally see events in similar orders. When servers have long network splits,
there will be a noticeable difference at first, but once messages start flowing
normally and users start reading them, the differences will disappear as new
events will have higher Stream order than the older ones on both servers.

[^1]: In fact, order could also be inconsistent across different users on the
  same home server, although we expect in practice this will not happen.

The focus of this proposal is that a single user sees consistent behaviour
around their own read receipts, and we consider that much more important that
the edge case of inconsistent behaviour across federation after a network split.

## Implementation Notes

Some home servers such as Synapse already have a concept of Stream Order. We
expect that the order defined here could be implemented using Stream Order.

## Potential issues

This explicitly allows receipts to be inconsistent across federation. In
practice this is already the case in the wild, and is impossible to solve using
Stream Order. The problems with using Topological Order (and Sync Order) have
already been outlined.

## Alternatives

### Solves the same problem MSC3981 Relations Recursion tried to solve

This proposal would not replace
[MSC3981: /relations recursion](https://github.com/matrix-org/matrix-spec-proposals/pull/3981)
but would make it less important, because we would no longer depend on the
server providing messages in Sync Order, so we could happily fetch messages
recursively and still be able to slot them into the right thread and ordering.

Note that the expectation (from some client devs e.g. me @andybalaam) was that
MSC3981 would solve many problems for clients because the events in a thread
would be returned in Sync Order, but this is not true: the proposal will return
events in Topological Order, which is useless for determining which events are
read.

### The server could report which rooms are unread

We could use the definitions within this proposal but avoid calculating what was
unread on the client. Instead we could ask the server to figure out which rooms
are unread.

The client will still need to know which events are unread in order to process
notifications that are encrypted when they pass through the server, so this
proposal would probably be unaltered even if we added the capability for servers
to surface which rooms are unread.

### Location of order property in receipts

Initially, we included `order` as a sibling of `m.read` inside the content of a
receipt:

<pre>{
  "content": {
    "$1435641916114394fHBLK:matrix.org": {
      <b>"order": 56764334544,</b>
      "m.read": { "@rikj:jki.re": { "ts": 1436451550453, "thread_id": "$x" } },
      "m.read.private": { "@self:example.org": { "ts": 1661384801651 } }
    }
  },
  "type": "m.receipt"
}</pre>

We moved it inside the content, as a sibling to `ts`, because multiple existing
clients (mautrix-go, mautrix-python and matrix-rust-sdk) would have failed to
parse the above JSON if they encountered it without first being updated.

### Drop receipts with missing order information

In the case where a server has a receipt to send to the client, but does not
have the event to which it refers, and therefore cannot find its order, we
proposed above that the server should hold the receipt until it has the relevant
event, and send it then.

Alternatively, we could simply never send the receipt under these circumstances.
We believe that this is reasonable because it is not expected to happen for the
user's own events, which are the most critical to provide accurate read
receipts, and implementing the "hold and send later" strategy may cause extra
work for the server for little practical gain.

## Security considerations

None highlighted so far.

## Unstable prefix

TODO

## Dependencies

None at this time.

## Acknowledgements

Formed from a discussion with @ara4n, with early review from @clokep. Built on
ideas from @t3chguy, @justjanne, @germain-gg and @weeman1337.

## Changelog

* 2023-07-04 Initial draft by @andybalaam after conversation with @ara4n.
* 2023-07-05 Remove thread roots from their thread after conversation with @clokep.
* 2023-07-05 Make redactions never unread after conversation with @t3chguy
* 2023-07-05 Give a definition of Stream Order
* 2023-07-05 Be explicit about Stream Order not going over federation
* 2023-07-05 Mention disagreeing about what another user has read
* 2023-07-05 Move thread_id into content after talking to @deepbluev7
* 2023-07-06 Reduced to just order. Thread IDs will be a separate MSC
* 2023-07-06 Moved order deeper within receipts to reduce existing client impact
* 2023-07-13 Include order with redacted events after comments from @clokep
