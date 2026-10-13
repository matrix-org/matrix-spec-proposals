# MSC3994: Display why an event caused a notification

Currently users may not understand why a particular event caused a notification. This can be confusing, lead to notification fatigue, and make creating a custom notification setup difficult.

Currently it is not possible to identify which push rule triggered an action (notification/highlight/ping) for an event without rerunning push processing for that event on the client.

By identifying which rule triggered an action clients can reduce user confusion and enable better management of push rules.

For example: a user receiving pings for a keyword they forgot they had configured can easily understand the pings, and remove the keyword rule.

## Proposal

Extend the `Notification` object returned by [`GET /notifications`](https://spec.matrix.org/latest/client-server-api/#listing-notifications) to include the `kind` and `rule_id` of the executed push rule. 
`kind` and `rule_id` (along with `room_id` and `profile_tag` already present) will enable the client to uniquely identify the matched rule locally if necessary.

| Name | Type | Description |
|--|--|--|
| `rule_kind` | [push rule kind](https://spec.matrix.org/latest/client-server-api/#push-rules) (`override` \| `content` \| `room` \| `sender` \| `underride`) | `kind` of the executed push rule |
| `rule_id` | string | `rule_id` of the executed push rule |


## Alternatives

Let clients determine the executed push rule. This would mean rerunning push processing client-side on notifications fetched from `/notifications`.
Clients likely already do client-side push processing in many cases. For example, Element Web runs client-side push rule processing for encrypted events, and on `/sync` response.

## Security considerations

N/A

## Unstable prefix
While this MSC is not included in the spec `rule_kind` and `rule_id` should use the unstable prefixes `org.matrix.msc3994.rule_kind` and `org.matrix.msc3994.rule_id` respectively
