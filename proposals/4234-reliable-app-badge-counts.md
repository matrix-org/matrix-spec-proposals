# MSC4234: Update app badge counts when rooms are read

## Problem

[MSC4076](https://github.com/matrix-org/matrix-spec-proposals/pull/4076) addresses the problem that E2EE means that
only clients can calculate their app badges accurately, and gives clients a way of stopping the server from overriding
their app badges.

However, in order to actually get up-to-date app badge counts, you also need a way to nudge clients to recalculate their
app badge count whenever the user has cleared the unread state on a given room by reading it (i.e. to decrement the app
badge count). Otherwise, the app badge will be stale and only get updated at some arbitrary point when the app receives
an unrelated push notif, or happens to syncs in the background, or happens to be foregrounded.

## Solution

We add a new optional field to read receipts called `cleared_notifs` which defaults to `false` if absent.  This SHOULD
be set to `true` by clients implementing this MSC to indicate that a given receipt means the user has read all push
notifications for this room's main timeline.  The server should then send a 'null' push notification to all other
clients to encourage them to sync and recalculate their app badge counts, ensuring that the app badge count decreases
when the user catches up on a given room.  The 'null' notification is the same used historically to update the app badge
count as calculated by the server.

This is needed to replace the prior behaviour where the server would be responsible for calculating and pushing new app
badge updates to clients - instead, the client has to tell the server when to nudge clients with a blank push to get
them to calculate their own badge count, otherwise they will show a stale count.

## Potential issues

1. Rather than sending a null push to clients to get them to update their app badge counts, should we instead send the
`cleared_notifs` read receipt details through - to tell them which room cleared its notifs, and at which event, rather
than requiring them to /sync and guess?  This seems likelier to succeed within resource constraints, but exposes more
metadata to the push provider on what events have been read by the user.  This in turn could be mitigated by
[MSC3013](https://github.com/matrix-org/matrix-spec-proposals/pull/3013).

2. Just because one client thinks a room's notifs have been cleared doesn't mean a different client will agree, so if
another client has more noisy per-device rules, it may end up with a stuck app badge count.  A workaround could be for
e2ee_badge_aware clients to set `cleared_notifs: true` on every RR they send if they spot that the user has per-device
rules.  Alternatively, they could set `cleared_notifs: true` whatever when the user reads the most recent message in
the room as a guaranteed point where all clients will agree that there are no unread notifs.
Given per-device rules aren't common currently in the wild, I suggest we punt this to a later MSC.

The other potential issues in [MSC4076](https://github.com/matrix-org/matrix-spec-proposals/pull/4076) also apply.

## Alternatives

Alternatively, we could push all devices every time the user sends a read receipt anywhere, just in case they need to
recalculate their app badge count.  This would have an avoidable and large impact on battery life.

* `cleared_notifs` should be prefixed as `org.matrix.msc4234.cleared_notifs` when sending read receipts which clear
   all the notifs in the room.

## Security considerations

This assumes a user can trust their other apps to accurately say when they're sending a read receipt which will clear
the badge count for a given room.  This doesn't seem unreasonable.

## Dependencies

This only makes sense in combination with [MSC4076](https://github.com/matrix-org/matrix-spec-proposals/pull/4076),
which it was split out of.
