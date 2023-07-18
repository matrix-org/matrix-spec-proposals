# MSC4037: Thread root is not in the thread

The current spec implies that a thread root is considered within the thread, but
we argue that this does not make sense, and a thread root is not "in" the thread
branching from it.

This is important for creating and interpreting read receipts.

## Motivation

The current spec, in
[11.6.2.2 Threaded read receipts](https://spec.matrix.org/v1.7/client-server-api/#threaded-read-receipts)
says:

> An event is considered to be "in a thread" if it meets any of the following
> criteria:
>
> * It has a `rel_type` of `m.thread`.
> * It has child events with a `rel_type` of `m.thread` (in which case it’d be
>   the thread root).
> * Following the event relationships, it has a parent event which qualifies for
>   one of the above. Implementations should not recurse infinitely, though: a
>   maximum of 3 hops is recommended to cover indirect relationships.
>
> Events not in a thread but still in the room are considered to be part of the
> "main timeline", or a special thread with an ID of `main`.

This explicitly includes thread roots in the thread which branches off them, and
implicitly _excludes_ those messages from being in the `main` thread.

This is problematic because:

* It seems natural for messages that are displayed in the main timeline (as
  thread roots are in most clients) to be considered read/unread when the user
  reads them in the main timeline.

* It normally does not make sense for a threaded read receipt to point at the
  thread root, since the user has not really read anything in that thread if
  they have only read the thread root.

In practice, Synapse ignores any request to mark the thread root as read within
the thread, and accepts requests to mark it as read in the main timeline.

In consequence, Element Web exhibited bugs relating to unread rooms while its
underlying library used spec-compliant behaviour, many of which were fixed by
[adopting the behaviour recommended by this proposal](https://github.com/matrix-org/matrix-js-sdk/pull/3600).

It really does not make sense to treat thread roots as outside the main
timeline: any message can become a thread root at any time, when a user creates
a new threaded message pointing at it, so suddenly switching which receipts are
allowed to apply to it would not be sensible.

Similarly, it does not make sense for reactions to the thread root (or other
related events such as edits) to be outside the main timeline.

## Proposal

We propose that thread roots are in the main timeline, making the definition:

> An event is considered to be "in a thread" if:
>
> * It has a `rel_type` of `m.thread`, or it has an ancestor event with this
>   `rel_type`.
>
> Implementations should limit recursion to find ancestors: a maximum of 3 hops
> is recommended.
>
> Events not in a thread but still in the room are considered to be part of the
> "main timeline": a special thread with an ID of `main`.
>
> Note: thread roots (events that are referred to in a `m.thread` relationship)
> are in the main timeline.

## Potential issues

None known.

## Alternatives

We could treat thread roots as being in *both* their thread and the `main`
timeline, but it does not offer much benefit because a thread where only the
root message has been read is almost identical to one where the no messages have
been read. A thread cannot exist without at least one additional message.

## Security considerations

Unlikely to have any security impact.

## Unstable prefix

None needed.

## Dependencies

No dependencies.
