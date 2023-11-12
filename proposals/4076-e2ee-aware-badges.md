# MSC4076: Let E2EE clients calculate app badge counts themselves

## Problem

Some push notification implementations (e.g. APNS) let the server update the notification badge count shown on an app
directly from the server, without the client running any code[^1].  In the early days of Matrix before we landed E2EE
this was a desirable thing to do, because: 1) the server knew how many pushes it had sent to the client 2) the client
displayed all pushes 3) the client typically didn't run code on receiving push, but just relied on the OS to display
the push.

However, since E2EE landed, this breaks down for E2EE rooms because only the client can reliably know whether a given
message should trigger a push notification or not - given only the client can see the event type and event contents
of E2EE messages, and so decide whether to notify based on the event type being visible - or based on mention keywords
within the message contents.

The workaround since we launched E2EE has been to assume that all events in E2EE rooms are visible, and so if an E2EE
room is configured to notify for all messages, unrenderable events will still trigger a push notification and increment
the `unread_notifications` count for that room and consider that room as unread when calculating the app badge count
passed to the push gateway.  As a result, invisible events like VoIP signalling will trigger an app badge count.

Meanwhile, clients now display notifications on both Android & iOS by running local code on receiving a push, rather
than displaying it verbatim from the server.  This means the push rules can be executed locally and notifications should
only be displayed if the event actually is visible and matched the push rules.  Moreover, the clients can calculate and
track their own accurate `unread_notification` count for E2EE rooms (while still using the `unread_notification` count
in the /sync response for non-E2EE rooms if they want), and from that calculate an accurate app badge count
clientside.

The problem is that the server still tries to override the app badge count whenever it sends a push to the client though,
which at best will be wrong (either understeering due to missing E2EE mentions, or oversteering due to alerting about
rooms with invisible events) - and at worst will race and fight[^2] with the app badge count maintained locally by the
app, if any.

Therefore we need a way for sophisticated E2EE clients to tell the server to stop overriding their app badge count.

Also, the server currently tracks which events the user has read, and will send a 'null' push to the client to update
the app badge count once a given pushed event has been read.  But given the server doesn't reliably know what events
cause pushes in E2EE rooms, we will need a new mechanism to reduce the badge count as the user reads rooms (or parts
them, or reconfigures their push settings).
 
Finally, a separate but related problem is that historically the description of the `unread` count passed to push
gateways in the Push API is currently wrong[^3]: it says it's "The number of unread messages a user has across all of
the rooms they are a member of." but in practice it's "The number of rooms the user has with unread push
notifications" (although synapse has a config option to change that, confusingly). So we should fix that too.

## Solution

When a pusher is registered for a given device via `POST /_matrix/client/v3/pushers/set`, we add a new boolean field
to the request called `e2ee_badge_aware` which defaults to `false` if absent.

If `e2ee_badge_aware` is set to true, then the pusher will not specify `unread` or `missed_calls` in the
`POST /_matrix/push/v1/notify` request to the target push gateway, and so not override the client's app badge.

We also add a new optional field to read receipts called `cleared_notifs` which defaults to `false` if absent.  This is
set to `true` by e2ee-badge-aware clients to indicate that a given receipt means the user has read all push
notifications for this room's main timeline.  The server should then send a 'null' push notification to all other
clients to encourage them to sync and recalculate their app badge counts, ensuring that the app badge count decreases
when the user catches up on a given room.

Finally, we fix the spec to describe the behaviour of the `unread` count field in `POST /_matrix/push/v1/notify`
correctly.  We also remove the `missed_calls` field at all, as nothing has ever implemented it, as far as I know - I
think it was originally included for questionable futureproofness and never hooked up ("ooh, if we are tracking unread
message notifs, let's also track unread call notifs")[^4].

## Potential issues

1. It's not clear that the push extension will be able to reliably calculate badge counts, as they run with very
constrained resources, and the client will need to have spidered all unread messages in all E2EE rooms to get a correct
number.  So if the client has been offline for a while and comes back, we have a problem if the push service has given
up pushing the client, and potential notifs get dropped.  Perhaps we can detect when this happens (e.g. seqnums on push
notifs?) and warn the user to launch the app to catch up on any notifs they may have missed?

2. Rather than sending a null push to clients to get them to update their app badge counts, should we instead send the
`cleared_notifs` read receipt details through - to tell them which room cleared its notifs, and at which event, rather
than requiring them to /sync and guess?  This seems likelier to succeed within resource constraints, but exposes more
metadata to the push provider on what events have been read by the user.  This in turn could be mitigated by
[MSC3013](https://github.com/matrix-org/matrix-spec-proposals/pull/3013).

3. Just because one client thinks a room's notifs have been cleared doesn't mean a different client will agree, so if
another client has more noisy per-device rules, it may end up with a stuck app badge count.  A workaround could be for
e2ee_badge_aware clients to set `cleared_notifs: true` on every RR they send if they spot that the user has per-device
rules.  Alternatively, they could set `cleared_notifs: true` whatever when the user reads the most recent message in
the room as a guaranteed point where all clients will agree that there are no unread notifs.
Given per-device rules aren't common currently in the wild, I suggest we punt this to a later MSC.

4. Ideally we should also omit `unread_notifications` and `unread_thread_notifications` in /sync responses entirely for
E2EE rooms for that device, given they will be subtly wrong and encourage the client not to correctly calculate them
themselves.  However, this is hygiene rather than functionality and can be a different MSC for an `e2ee_badge_aware`
room_filter or similar.

## Alternatives

We could track app badge count on the server, but let it be set by your clients instead - e.g. by a dedicated API like
`POST /_matrix/client/v3/pushers/set_badge { badge: 123 }`, which would in turn push it to all clients so they are in
sync.  This would avoid each client individually trying to figure out when to reduce the badge count in its Push
Extension - instead the client sending the read receipts would do it for them.  But on the other hand, it would not
work with per-device push rules.  (Then again, nor does the proposed solution).

Alternatively, we could push all devices every time the user sends a read receipt anywhere, just in case they need to
recalculate their app badge count.  This would have an avoidable and large impact on battery life.

In terms of configuring pushers as e2ee_badge_aware: we could also do this via a per-device underride push rule with
a custom `action` of `e2ee_badge_aware`.  However, this isn't really a push action: it shouldn't be changeable by other
push rules, for instance.  Instead it's config data at the point the pusher is created, hence putting it there.

## Security considerations

This assumes a user can trust their other apps to accurately say when they're sending a read receipt which will clear
the badge count for a given room.  This doesn't seem unreasonable.

## Unstable prefix

Until this MSC is merged:
 * `e2ee_badge_aware` should be prefixed as `org.matrix.msc4076.e2ee_badge_aware` when setting pushers
 * `cleared_notifs` should be prefixed as `org.matrix.msc4076.cleared_notifs` when sending read receipts which clear
   all the notifs in the room.

## Dependencies

None.

## Footnotes

[^1]: https://developer.apple.com/documentation/usernotifications/setting_up_a_remote_notification_server/generating_a_remote_notification#2943362
[^2]: https://github.com/vector-im/element-x-ios/issues/2066
[^3]: https://github.com/matrix-org/matrix-spec/issues/644
[^4]: https://github.com/matrix-org/synapse/blame/bdc21e72820e148941bbecb36200d51ca340748d/synapse/push/httppusher.py