# MSC2625: Add `mark_unread` push rule action

[Push rule actions](https://matrix.org/docs/spec/client_server/r0.6.1#actions)
affect how a homeserver delivers notifications for events matching a given push
rule. Homeservers also return the number of unread notifications in the `/sync`
response.

This approach conflates "unread messages" (aka the "badge count") and "messages
that I want to be notified about". Users often want to see the count of unread
messages increasing in a room view, without receiving a push notification for
each such message.

This proposal suggests adding a new push rule action, and extending the `/sync`
response, to differentiate between these two cases.

## Proposal

** New push rule action **

To the current list of [Push rule
actions](https://matrix.org/docs/spec/client_server/r0.6.1#actions), we add
`mark_unread`, defined as:

 * `mark_unread`: This causes each matching event to contribute to the homeserver's count of
   unread messages in the room.

For compatibility with existing implementations, the `notify` action implies
`mark_unread`. Its definition is therefore updated to:

 * `notify`: This causes each matching event to generate a notification, *as
   well as* contributing to the homeserver's count of unread messages in the
   room.

 For clarity then: an actions list of `["notify", "mark_unread"]` is the same
 as an actions list of just `["notify"]`.

 (Aside: it may be helpful to note that the `dont_notify` action is a no-op and
 equivalent to an empty actions list. See also
 https://github.com/matrix-org/matrix-doc/issues/2624.)

** Extended response to `/sync` **

In the response to
[/sync](https://matrix.org/docs/spec/client_server/r0.6.1#get-matrix-client-r0-sync),
within the `Unread Notification Counts` structure, we add a mandatory new field
`unread_count`, which gives the number of unread messages which matched a
`mark_unread` or `notify` push rule.

We expect the following inviariant to hold:

    highlight_count <= notification_count <= unread_count

** Next steps **

We expect a future MSC to change the specification of the default push rules so
that `mark_unread` is used in place of `notify` in certain places. That change
is not included in this MSC.

## Potential issues

1. It seems counterintuitive that "push rules" are used to determine unread
   counts, and that this behaviour appears in the "push" section of the spec,
   when no "push" is involved at all. However, that is not a new problem, and
   the push rules engine actually fits the purpose quite well here.

   Arguably the problem is in the naming of "push rules", where "event action
   rules" or similar might be more appropriate.

## Alternatives

The push rules system is complicated: the multiple "kinds" of push rule, the
defaults, the fact that clients can change the behaviour of named push
rules. This complexity makes it hard to reason about, and makes it difficult
for Matrix clients to (reliably) represent the user's current state in a
comprehensible way. There is an argument that, rather than adding yet more
complexity, we should either replace it or use a different mechanism for the
new behaviour.

However, the change proposed here seems incremental, and:
 * a wholesale redesign would take a lot of time which would be better spent
   elsewhere.
 * using an alternative mechanism would add complexity overall rather than
   reduce it.

## Security considerations

None currently foreseen.

## Unstable prefix

While this feature is in development, the following names will be in use:

| Proposed final name | Name while in development |
| --- | --- |
| `mark_unread` | `org.matrix.msc2625.mark_unread` |
| `unread_count` | `org.matrix.msc2625.unread_count` |

## References

This document was based on an initial design at https://docs.google.com/document/d/1Fnh8sT_8hmWAZ_Yh9NaB8HI5occNfR4KyQ_NVdnXJzo.
