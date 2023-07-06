# MSC4033: Providing thread and order for all events to allow consistent read receipt handling

We argue that we have made it unnecessarily hard for clients and servers to
decide whether a message is read or unread, and we can solve this problem by
clarifying the definitions, and including extra pieces of information with
every event that help to identify its thread(s) and ordering.

## Motivation

In order to decide whether a room is unread, a Matrix client must decide whether
it contains any unread messages.

Similarly, in order to decide whether a room has notifications, a Matrix client
or server must decide whether any of its potentially-notifying messages is
unread.

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

The meaning of *the same as* is clear: if a receipt points at an event, then
that event is read.

### Current definition of *after*

The current spec (see
[11.6 Receipts](https://spec.matrix.org/latest/client-server-api/#receipts)) is not clear
about what it calls "read up to" means.

Clients like Element Web make the assumption that *after* means "after in Sync
Order", where "Sync Order" means "the order in which I (the client) received the
events from the server via sync", so if a client received an event and another
event for which it has a receipt via sync, then the event that was later in the
sync or received in a later sync, is after the other one [^1].

[^1]: We think this is similar to Stream Ordering, which is mentioned once in
  the spec without definition in
  [7.6 Syncing](https://spec.matrix.org/unstable/client-server-api/#syncing),
  but we are not certain that it is identical, because we believe it may be
  possible for different clients to receive events in a different order from
  each other for the same account. For example, if one client is doing an
  incremental sync, and another is doing an initial sync, recently-arrived
  events that are "old" in Topological Order may be received in different orders
  on the two clients.

See also [Spec Issue #1167](https://github.com/matrix-org/matrix-spec/issues/1167),
which calls out this ambiguity about the meaning of "read up to".

### Current definition of *in the same thread*

See [11.6.22 Threaded read
receipts](https://spec.matrix.org/latest/client-server-api/#threaded-read-receipts),
but a summary in looser language is:

An event is in thread A if:

* its event ID is A and it has `m.thread` children (i.e. it is the thread root), or
* it has an `m.thread` relationship to the event with ID A (i.e. it is a message
  in the thread), or
* it has an ancestor event (found by traversing relationships) that fits either of the above.

The spec states that room events are in `main` if they are not in another thread, but
clients such as Element Web treat thread roots, and non-thread descendants of thread roots
(such as reactions to the thread root) as being in BOTH `main` and the thread branching
from the thread root. We strongly suspect that home servers also consider thread roots
to be in the main thread, since otherwise their status would change when a new thread
reply was added.

### Problems with the current definitions

The current definition of *after* is ambiguous, and difficult for clients to
calculate. It depends on only receiving events via sync, which is impractical
due to backpagination, and the desire to fetch thread messages via the
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

We propose to modify the definitions slightly, and include extra information in
the events provided by the server to make it easy to calculate whether an event
is read.

### Proposed definition of *after*

We propose that the definition of *after* should be:

* Event A is after event B if its *Stream Order* is larger.

We define *Stream Order* to be an immutable, unique number attached to an event
on creation that defines the order of events in regard to receipts.

We propose updating the spec around receipts
([11.6 Receipts](https://spec.matrix.org/latest/client-server-api/#receipts))
to be explicit about what "read up to" means, using the above definition.

#### Notes

Some home servers already have a concept of Stream Order, and we intend
that this definition is consistent with that as currently implemented. But, for
the purposes of this proposal the only important aspect of Stream Order is that
server and clients agree that receipts apply to events with a lower Stream
Order, and that the Stream Order of an event never changes.

If the name Stream Order proves confusing, this proposal can function equally
well using a different name: it simply needs to be unique, immutable, and
increase for "newer" messages.

We do not require that Stream Order be consistent across federation (in fact, we
believe that this would be impossible to achieve). The only requirement is that
all the clients for a user and the one server to which they connect agree. For
this reason, we propose that `order` be included in an event's `unsigned`
property.

### Notes on the meaning of Stream Order

Because it controls the meaning of read receipts, it is desirable that Stream
Order be as close as possible to Sync Order, the order in which clients receive
events via sync. However, since clients receive events in different orders
depending on the APIs they use, it is not a goal that Stream Order exactly match
the order in which clients receive events. Instead, it provides a canonical
order that means we can be clear about what the user has read, and thus should
generally increase for "newer" messages. Clients may decide to re-order events
into Stream Order, or they may decide to display unread messages higher up the
timeline if the orders do not match the order they choose for display.

Because Stream Order may be inconsistent across federation[^2], one user may
occasionally see a different unread status for another user from what that user
themselves see. We regard this as impossible to avoid, and expect that in most
cases it will be unnoticeable, since home servers with good connectivity will
normally have similar Stream Order. When servers have long network splits, there
will be a noticeable difference at first, but once messages start flowing
normally and users start reading them, the differences will disappear as new
events will have higher Stream order than the older ones on both servers.

[^2]: In theory, Stream Order could also be inconsistent across different users
  on the same home server, although we expect in practice this will not happen.

### Proposed definition of *in the same thread*

We propose that the definition of *in the same thread* should use this wording:

An event is in a non-main-thread if:

* it has a `thread_id` property in its cleartext content

Otherwise, it is in the `main` thread.

No events are in more than one thread.

Note: this means that thread roots are in the `main` thread, and not in the
thread branching from them. Non-thread children of thread roots (e.g.
reactions to a thread root) are also in the `main` thread. This is a change to
the current definition.

### Proposed change in consideration of redacted events

We propose that redacted events should never be considered unread.

This avoids the need to identify which thread a redacted event belongs to, which
will be difficult if its `thread_id` property has been stripped out.

Since we propose that receipts contain the `order` of their referred-to event,
this means we do not need to look within a redacted event for its Stream Order,
because the receipt provides it. This avoids needing to preserve the `order`
property when redacting events.

### Supporting changes to event structure

Example event (changes are highlighted in bold):

<pre>{
  "content": {
    "body": "This is an example text message",
    "format": "org.matrix.custom.html",
    "formatted_body": "&lt;b&gt;This is an example text message&lt;/b&gt;",
    "msgtype": "m.text"
    <b>"thread_id": "$fgsUZKDJdhlrceRyhj", // Optional</b>
  },
  "event_id": "$143273582443PhrSn:example.org",
  "origin_server_ts": 1432735824653,
  "room_id": "!jEsUZKDJdhlrceRyVU:example.org",
  "sender": "@example:example.org",
  "type": "m.room.message",
  "unsigned": {
    "age": 1234,
    <b>"order": 56764334543</b>
  }
}</pre>

Example encrypted event (changes are highlighted in bold):

<pre>{
    "type": "m.room.encrypted",
    "content": {
        <b>"thread_id": "$fgsUZKDJdhlrceRyhj", // Optional</b>
        "algorithm": "m.megolm.v1.aes-sha2",
        "sender_key": "<sender_curve25519_key>",
        "device_id": "<sender_device_id>",
        "session_id": "<outbound_group_session_id>",
        "ciphertext": "<encrypted_payload_base_64>"
    }
    // irrelevant fields not shown
}</pre>

Example receipt (changes are highlighted in bold):

<pre>{
  "content": {
    "$1435641916114394fHBLK:matrix.org": {
      <b>"order": 56764334544,</b>
      "m.read": {
        "@rikj:jki.re": {
          "ts": 1436451550453
        }
      },
      "m.read.private": {
        "@self:example.org": {
          "ts": 1661384801651
        }
      }
    }
  },
  "type": "m.receipt"
}</pre>

We propose:

* all events in a thread should contain a `thread_id` property in their content.
* all events should contain an `order` property.
* all receipts should contain an `order` property alongside `m.read`
  and/or `m.read.private` inside the information about an event, which is a
  cache of the `order` property within the referred-to event [^3].

[^3]: This might make the `ts` property within receipts redundant. We are not
  actually sure what purpose this property is intended to serve.

The creator of an event should include a `thread_id` property in the cleartext
content of any event that has an ancestor relationship that includes an
`m.thread` relationship. The value of `thread_id` is the event ID of the event
referenced by the `m.thread` relationship.

This makes it explicit how events are categorised, meaning clients and servers
can always agree on which thread an event is in, so the meaning of a threaded
receipt is clear.

It also makes it explicit which event is before or after another event in Stream
Order.

This prevents disagreements between clients and servers about the meaning of a
particular read receipt, and by including the Stream Order of the referred event
in the receipt, avoids the need to fetch that event in order to make a decision
about which events are read.

### Definition of read and unread events

We propose that the definition of whether an event is read should be:

> An event is read if the room contains an unthreaded receipt pointing at an
> event which is *after or the same as* the event, or a threaded receipt
> pointing at an event that is *in the same thread* as the event, and is *after
> or the same as* the event.
>
> Because the receipt itself contains the `order` of the pointed-to event,
> there is no need to examine the pointed-to event, so it is sufficient to
> compare the `order` of the event in question with the `order` in the
> receipt.
>
> Redacted events are always read.
>
> Otherwise, it is unread.

Obviously, this definition depends on the definitions above.

## Potential issues

This special-cases threads over other relationships, raising them a little
closer to the same status as rooms.

But, this was already the case with threaded receipts, and because of
`thread_id`'s special place in receipts, we believe it needs similar special
treatment in events to provide consistent behaviour.

The change to consider thread roots (and reactions to them) as outside of the
thread may be inconvenient for clients, because they will probably want to
display those events in any "thread view" they display. We consider this
inconvenience worthwhile because it is necessary to ensure the semantics of read
receipts make sense. We do not think that reactions or edits to a thread root
should mark that thread as unread - instead they mark the main thread as unread,
which the client can use to draw attention to the thread root.

## Alternatives

### Use MSC3501 instead of thread_id

If [MSC3051: A scalable relation format](https://github.com/matrix-org/matrix-spec-proposals/pull/3051)
is on the path to standardisation, it could be used to specify the thread
containing each event.

For the purposes of making receipts work, this is just as good as using
`thread_id`, and the author of this MSC supports MSC3051.

We would simply need to mandate that anyone creating an event within a thread
must include an `m.thread` relation to that thread, even if the event is
a child of an event with a similar relation. This would be directly equivalent
to adding `thread_id` to the content.

### This replaces other attempts to fix receipts

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

### Avoiding saying "Stream Order"

We could avoid the phrase Stream Order in this proposal, and instead simply talk
about a consistent order that the server and client agree on because it is
included with event info.

We could even note that we expect it to be Stream Order for homeservers that
have such a concept, but the important thing for us is that it is consistent and
explicit.

### The server calculates unread status

We could use the definitions within this proposal but avoid calculating what was
unread on the client. Instead we could ask the server to figure out which rooms
are unread.

The client will still need to know which events are unread in order to process
notifications that are encrypted when they pass through the server, so this
proposal would probably be unaltered even if we added the capability for servers
to surface which rooms are unread.

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
