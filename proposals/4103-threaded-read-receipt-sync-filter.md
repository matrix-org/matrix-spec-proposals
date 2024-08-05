# MSC4103: Make threaded read receipts opt-in in /sync

## Problem

When we added threaded RRs in [MSC3771](https://github.com/matrix-org/matrix-spec-proposals/pull/3771) we broke
existing (i.e. non-thread-aware) clients from reliably being able to calculate whether a room is unread, given threaded
read receipts are interpreted as unthreaded ones.

For instance, let's assume Alice is logged in on two clients: a desktop client which is thread aware, and a mobile
client which is not.

 * Alice has a bunch of unread messages on her main timeline and a bunch of unread threads.
 * The threads are newer than the main timeline msgs.
 * She reads the most recently active thread on desktop, which sends a threaded RR.
 * Mobile interprets this as a normal RR, and so marks the room as read (despite she hasn't read main timeline msgs)
 * Desktop however correctly shows the room as still unread.

The key thing is that **just because Alice happened to read a thread on a thread-aware client doesn't mean semantically
that she's also read the main timeline**.

Non-thread-aware clients simply do not care what messages users may have read on threads; they just care where the user
has read up to in the main timeline (which for them, is a linearized view of the whole room, and for threaded clients
is the main timeline).

Another way of thinking of it which may or may not be helpful:

 * If Alice reads a thread on desktop, then her mobile doesn't care.
 * If Alice reads a main timeline msg on desktop, then her mobile will want to show the flattened timeline as read up to
   that msg.
 * If Alice reads a given msg on mobile, then she sends an unthreaded RR, which can mark all threads prior to that point
   as read (for threaded clients). Non-thread-aware clients will be synced to the same RR point, as you'd expect.

## Proposal

Non-thread-aware clients should only act on unthreaded RRs.

Prior to this MSC, there is no way for non-thread-aware clients to determine which RRs are unthreaded, other than seeing
if the `thread_id` field is missing on the RR or present and equal to `main`.

As a result, to get sensible room read state semantics for non-thread-aware clients, they would all need to become aware of
the new `thread_id` field, breaking existing clients, even if they don't care about threads.  This feels contradictory and
suboptimal.

We could solve this by making threaded RRs a different event type (e.g. `m.read_thread`), so non-thread-aware clients
would automatically ignore them.  However, this would require threaded clients to send double the read receipts whenever
the user reads the main thread - both an `m.read` and an `m.read_thread`, which feels inefficient.  (It would however
mean that [MSC4102](https://github.com/matrix-org/matrix-spec-proposals/pull/4102) would not be necessary, as the RR types
would be clearly distinct).

Instead, we propose that they continue to follow MSC3771 (i.e. putting a `thread_id` on the `m.read` RR).  However, we
give threaded clients the ability to explicitly opt-in to threaded read receipts in the form of a new sync filter
param. If clients explicitly include `threaded_read_receipts: true` on their sync filter, then the server will send
them `m.read` events as received by the server.  If this filter is missing or false, then the server must only send the
client `m.read` events whose `thread_id` is missing or `main`.

This means that non-thread-aware clients are not spammed or confused with irrelevant threaded read receipts, and can
calculate read state purely based on main timeline activity.

## Alternatives

We could split the event types into `m.read` and `m.read_thread` but instead have the server synthesise `m.read` events
out of `m.read_thread` events with `thread_id: 'main'` when the `threaded_read_receipts` sync filter is false or
absent. This would end up with the same end result, and would be cleaner in terms of type safety (and avoid the need
for MSC4102), but would mean having to completely change the event type in every thread-aware client rather than just
fixing it in servers, and back it out of the spec.  So for pragmatism, this MSC proposes leaving MSC3771 as is, and
instead let thread-aware clients opt-in via sync filters to avoid breaking existing clients.  This can be done
incrementally by thread-aware clients when they find themselves talking to a server which implements this MSC, thus
avoiding breaking existing thread-aware clients.

## Security considerations

If we ever encrypt RRs, then the server won't be able to filter them out.  But that's not planned currently, and we
can always expose threadedness as metadata to aid this if it were to happen.

## Unstable prefix

`threaded_read_receipts` should be namespaced as `org.matrix.msc4103.threaded_read_receipts` while unstable.
