# MSC4184: Dynamic Notification Suppression

*Not to be confused with Domain Name System.*

An unfortunately common method of spam is to mention users individually in events, causing disruption
for the users in that room. These events are often large as well.

The [current specification](https://spec.matrix.org/v1.11/client-server-api/#push-notifications) for
notifications relies on "push rules" to alter behaviour for received events. A solution to reduce the
impact of the spam may be to create a new push rule and condition which does not allow the event to cause
notification if there's more than X mentions. Determining a value for X can be difficult, and would
require experimentation through suffering spam waves and daily usage to get a decent balance on an
acceptable number. Further, spammers can somewhat trivially work around the number by sending more
events 1 step below the limit.

This proposal instead creates a provision in the specification for a server (or client) to decide
to suppress a notification on a per-event basis. Servers can then protect their users by adjusting
an X value described above, or implement other suppression mechanisms depending on the situation.
Clients can already choose to not notify the user on events, but their counts may differ from the
server if they do this. This proposal includes a way for the server to communicate to the client that
notifications (or more specifically, push rules) are ignoring the event.

## Proposal

Servers and clients become explicitly able to skip push rule execution on events which appear to contain
spam. The definition of "spam" is deliberately left as an implementation detail, though is not intended
to permit a server to arbitrarily suppress notifications.

Non-exhaustive examples of acceptable reasons to skip push rules are:

* Too many mentions in a message.
* Repeated messages in a room.
* Excessively high traffic.
* The notification would expose the user to illegal material.

When the server skips push rule execution on an event, it adds `m.push_rules_executed: false` to the
`unsigned` object when serving that event over [`/sync`](https://spec.matrix.org/v1.11/client-server-api/#get_matrixclientv3sync).
The value may be `true` and included on events served from other endpoints as well, though doesn't
serve significant utility to the client.

Clients SHOULD NOT execute push rules locally on events with `m.push_rules_executed: false` as this
may cause notification counts to desynchronize from the server, leading to 'stuck notifications' for
the user.

Clients SHOULD consider local suppression of notifications on spammy events, particularly in encrypted
rooms where the server is unable to provide a reliable notification count.

## Potential issues

Server owners may abuse this feature to cause users grief, or disrupt communications for a group using
their server. While technically made possible, users are typically able to relocate to a more kind
server, removing the incentive for this particular method of abuse.

A server or community moderator may wish to receive these notifications regardless of spam so they
can take action against the spammer. It is expected that implementation of this feature would be
paired with other spam suppression mechanisms, including soft-failure or automatically redacting
events to reduce outward impact. If the spammer is a local user, heavy rate limiting may also be
applied. Servers should additionally consider maintaining a list of users to never suppress notifications
for, and potentially the power level of the user receiving the notification. Another strategy may
be to let 1 notification per minute through to avoid overly spamming the user's device.

## Alternatives

Mentioned in the introduction for this proposal, a number of push rules and push rule conditions
could be introduced to cover the different types of spam a user might not want to be notified for.
These push rules and conditions may be trivial to work around, and potentially faster than the spec
process is able to consider them. Instead, this proposal suggests that the Matrix.org Foundation C.I.C.'s
Trust & Safety team create MSCs for push rules and conditions which prove themselves useful against
spam visible to the team. In particular, when the team uses this MSC's suppression mechanism, they
shall follow up with an MSC to describe the effective push rule/condition. Other T&S teams and server
owners are encouraged to do the same.

## Security considerations

See 'Potential Issues' - the considerations are the same.

## Unstable prefix

While this proposal is not considered stable, servers must use `org.matrix.msc4184.push_rules_executed`
instead of `m.push_rules_executed`.

## Dependencies

This proposal has no dependencies.
