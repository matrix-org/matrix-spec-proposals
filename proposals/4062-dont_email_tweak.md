# MSC4062: Add a push rule tweak to disable email notification

A user may set up a pusher to receive emails with unread notifications (see the spec
[here](https://spec.matrix.org/v1.8/client-server-api/#post_matrixclientv3pushersset) with `kind` = "email"). Note that
in the current Synapse implementation this pusher sends emails on a delay of ~10 minutes to give people time to see the
notification and mark it as read. It looks like some other server implementations don't support email pushers though
(see details in [this comment](https://github.com/matrix-org/matrix-spec-proposals/pull/4028#discussion_r1364373223)).

In order to support mentions-and-keywords-only notifications in encrypted rooms on clients which get push notifications,
we introduced in [MSC4028](https://github.com/matrix-org/matrix-spec-proposals/pull/4028) a new predefined **override**
push rule (`.m.rule.encrypted_event`). When this rule is enabled, the server pushes all encrypted events except for
muted rooms. The resulting notifications are not relevant for the email notifications. They concern encrypted events
which may contain an actual notification or not. The server implementations which support email notifications should
ignore in the email the events pushed because of this new push rule. Otherwise the users will receive an immense amount
more email notifications. This will cause people to treat those emails as spam.

The present proposal attempts to resolve this situation by introducing a new push rule tweak to disable the email
notification for a push rule when it triggers a notification for an event.

## Proposal

A new tweak `dont_email` is introduced in the push rules
[`actions`](https://spec.matrix.org/latest/client-server-api/#actions) definition.

- **`dont_email`** -- A boolean representing whether or not this event should be notified by email too. If a
`dont_email` tweak is given with no value, its value is defined to be true. If no dont_email tweak is given at all then
the value of `dont_email` is defined to be false.

The servers which implement email notifications have to check this tweak before adding a new notification in the
email. No change is expected in the client implementation.

## Potential issues

None.

## Alternatives

Another option was to define a new action `push_but_dont_notify`. We prefer the new tweak option because no change is
required in the client implementations. They can ignore it.

About the naming of this new tweak, `http_only` has been suggested too (if we don't want a negative). We prefer
`dont_email` in case a new kind of pusher is introduced later.

## Security considerations

None.

## Unstable prefix

While this MSC is not considered stable, `dont_email` should be referred to as `org.matrix.msc4062.dont_email`.

## Dependencies

None.
