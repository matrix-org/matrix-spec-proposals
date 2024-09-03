# MSC3676: Transitioning away from reply fallbacks.

## Problem

As per [MSC2781](https://github.com/matrix-org/matrix-doc/pull/2781)
(Remove reply fallbacks), the current reply fallback implementation is very
problematic:
 * Its quotes leak history which may not be visible to the user
 * The quoted sections may trigger unexpected notifications
 * `<mx-reply/>` tags are hard and dangerous to manipulate, and have caused
   multiple vulnerabilities in clients
 * They don't localise.

[MSC2781](https://github.com/matrix-org/matrix-doc/pull/2781) proposes
removing them entirely.  However, this triggers a relatively large cascade of
additional dependent work:
 * Some users rely on their mxid existing in fallbacks to notified when
   someone replies to their messages.  So we'd need to create and implement
   new push rules to recreate this feature ([MSC3664](https://github.com/matrix-org/matrix-doc/pull/3664)).
 * The push rules are even more complicated than expected for this, because
   they also would need to stop replies which are used as fallback for
   threads (as per [MSC3440](https://github.com/matrix-org/matrix-doc/pull/3440))
   from firing notifications.
 * In the absence of fallbacks, in order to render replies simple clients will
   now have to parse `m.in_reply_to` objects and fish around for the missing
   events (or ask the server to bundle the replies, which is not yet a
   thing).

Meanwhile, [MSC3440](https://github.com/matrix-org/matrix-doc/pull/3440)
(Threads) uses replies as a fallback representation for threads (which is
very desirable to support clients while the threads transition is happening,
or to support simpler clients which support replies but not threads).
However, currently `m.in_reply_to` is only allowed on `m.room.message` events
of msgtype `m.text`, which means it cannot currently be used as a fallback
for arbitrary threaded events.

## Proposal

As a transitional step towards removing reply fallbacks entirely, instead: we
make reply fallbacks best effort.  Specifically:

 * `m.in_reply_to` is relaxed to apply to any event type
 * In practice only `m.room.message` events with msgtype `m.text` or similar
   (`m.emote`, `m.notice`) would be able to express reply fallbacks (using the
   `m.body`, `format` and `formatted_body` fields).
 * Thread events using replies as a fallback representation for threads should
   not include a textual reply fallback at all (and so avoid threaded messages
   triggering notifications).  The same would apply for any other usage which uses
   replies as a fallback.

This means that we can still use reply fallbacks for notification purposes
until that is properly fixed by [MSC2781](https://github.com/matrix-org/matrix-doc/pull/2781)
and [MSC3664](https://github.com/matrix-org/matrix-doc/pull/3664) - decoupling this
additional work from landing threads in
[MSC3440](https://github.com/matrix-org/matrix-doc/pull/3440).
Replying to a message with an attachment won't trigger a notification, but
this is no worse than the behaviour today.

## Alternatives

We could remove fallbacks entirely and do all the subsequent work needed to
support that ([MSC2781](https://github.com/matrix-org/matrix-doc/pull/2781),
[MSC3664](https://github.com/matrix-org/matrix-doc/pull/3664) and whatever
MSC handles thread+fallback notification interaction).  However,
we believe that adding threads to Matrix is (much) higher priority and
value for Matrix than cleaning up edge cases around reply fallbacks, and
given the two can be decoupled, they should be.  The importance of threads is
based on the fact that we're seeing Matrix repeatedly fail to be selected as
a collaboration technology thanks to other alternatives supporting
Slack-style threads.

We could not use `m.in_reply_to` as a fallback for clients which don't
understand `m.thread`, but this would result in an unnecessarily
terrible fallback for older/transitional/WIP/simple clients.

## Security 

By temporarily keeping reply fallbacks around on a best effort basis, we're
still vulnerable to their security risks.  Client implementors should read
the [security issues highlighted in MSC2781](https://github.com/deepbluev7/matrix-doc/blob/drop-the-fallbacks/proposals/2781-down-with-the-fallbacks.md#appendix-b-issues-with-the-current-fallbacks)
if implementing reply fallbacks. 

## Unstable prefix

None needed.

## Dependencies

None. (MSC3440 will depend on this, however)
