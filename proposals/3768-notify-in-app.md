# MSC3768: Push rule action for in-app notifications

The [push rule] system is used in two different ways. Home servers
evaluate the rules on messages (which may be encrypted) and send *push*
notifications. Clients re-evaluate the rules locally on (decrypted)
messages and display *in-app* notifications -- most commonly in the form
of notification-count badges.

However, there is currently no way to stop sending push notifications
while still receiving in-app notifications. This is a critical feature
of "Do Not Disturb" modes where users want to stop being notified
*outside* their client but still see notifications *inside* their client
so that they can catch up on them after leaving "Do Not Disturb" mode.

The present proposal attempts to resolve this situation by introducing a
dedicated push rule action for in-app notifications without accompanying
push notifications.

## Proposal

A new push rule action `notify_in_app` is introduced.

-   `notify_in_app` -- This causes each matching event to generate a
    notification **without sending a push**. In particular, this means,
    like `notify`, the server MUST consider the event when computing
    `notification_count` and `highlight_count` in the `/sync` response.
    Unlike `notify`, the server MAY skip forwarding the notification to
    any of its pushers. Suppressing the push is OPTIONAL because clients
    need to locally reapply push rules upon receiving push notifications
    anyway due to E2EE. Clients MUST suppress push notifications that
    resulted from `notify_in_app` but SHOULD display in-app notifications
    just like for `notify`.

The existing `notify` action is changed to imply `notify_in_app`.

-   `notify` -- This causes each matching event to generate a
    notification. Implies `notify_in_app`.

No change to the existing default push rules is required. Servers can
treat `notify_in_app` exactly like `notify`, merely omitting the push,
while clients don't have to distinguish between the two actions at all.
This makes for a minimally invasive solution to the problem of
in-app-only notifications.

## Potential issues

None.

## Alternatives

[MSC3881] and [MSC3890] solve a similar problem but can only disable
notifications globally and not per-room.

Several attempts at fixing similar problems have been made in the past.
Most of these alternatives fell through because they separated unread
and notification counts. For the specific case of in-app-only
notifications, such a separation is not needed and only adds unnecessary
complexity.

For the sake of completeness, what follows is the result of an exercise
in archaeology:

### dont_push action

An experimental [Synapse PR] defined a `dont_push` action. While the
latter exhibits the same semantics as `notify_in_app`, its naming
disguises the fact that notifications are still being displayed in-app.
The PR was abandoned in favor of [MSC2625].

### MSC2625: Add `mark_unread` push rule action #2625 

[MSC2625] went a step further by introducing a `mark_unread` action
together with an explicit `unread_count` next to the existing
`notification_count` and `highlight_count` in the `/sync` response. As
explained above, this kind of separation is not actually needed for
in-app-only notifications. [MSC2625], too, got abandoned, this time in
favor of [MSC2654].

### MSC2654: Unread counts

Finally, [MSC2654] went yet further and introduced a separate system for
computing unread counters without push rules. Again, the complexity
resulting from this separation is not actually required to support
in-app-only notifications.

## Security considerations

None.

## Unstable prefix

While this MSC is not considered stable, `notify_in_app` should be
referred to as `org.matrix.msc3768.notify_in_app`.

## Dependencies

None.

  [push rule]: https://spec.matrix.org/v1.2/client-server-api/#push-rules
  [Synapse PR]: https://github.com/matrix-org/synapse/pull/6061
  [MSC2625]: https://github.com/matrix-org/matrix-spec-proposals/pull/2625
  [MSC2654]: https://github.com/matrix-org/matrix-spec-proposals/pull/2654
  [MSC3881]: https://github.com/matrix-org/matrix-spec-proposals/pull/3881
  [MSC3890]: https://github.com/matrix-org/matrix-spec-proposals/pull/3890
