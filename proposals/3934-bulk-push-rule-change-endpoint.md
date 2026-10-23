# MSC3934: Bulk push rules change endpoint

Currently if a client wants to internally link several push rules to a single toggle they must coordinate
calls to the server to enable/disable or change the actions of those rules. This can cause the client
to be subject to multiple failure modes where some push rules get updated correctly, but others do not,
leading to indeterminate state on the client side.

This proposal introduces two new endpoints for bulk operations on `/actions` and `/enabled` for push
rules.

## Proposal

To support bulk calls to [`/actions`](https://spec.matrix.org/v1.4/client-server-api/#put_matrixclientv3pushrulesscopekindruleidactions),
a new endpoint is introduced:

```
PUT /_matrix/client/v1/pushrules_bulk/:scope/:kind/actions
{
  ".rule_id_here": {
    "actions": ["notify"]
  },
  ".other_rule_id_here": {
    "actions": ["notify", { "set_tweak": "highlight" }]
  }
}
```

The endpoint requires authentication and can be rate limited.

The body is simply a dictionary of rule ID to existing body of `/actions`. If any of the push rules
do not exist, none are changed and the server returns a 400 error to the client. If everything was
updated successfully, a 200 OK response with empty JSON object is returned.

Similar to `/actions`, bulk calls to [`/enabled`](https://spec.matrix.org/v1.4/client-server-api/#put_matrixclientv3pushrulesscopekindruleidenabled)
are supported via a similar new endpoint:

```
PUT /_matrix/client/v1/pushrules_bulk/:scope/:kind/enabled
{
  ".rule_id_here": {
    "enabled" true
  },
  ".other_rule_id_here": {
    "enabled": false
  }
}
```

The endpoint requires authentication and can be rate limited.

Like the bulk endpoint for `/actions`, the body is a dictionary of rule ID to existing body of
`/enabled`. If any of the push rules do not exist, none are changed and the server returns a 400
error to the client. If everything was updated successfully, a 200 OK response with empty JSON
object is returned.

## Potential issues

This would allow clients to update potentially thousands of rules at once. Servers are still welcome
to block a client's request due to request size.

Otherwise, this MSC appears to fix a gap in updating multiple push rules at the same time.

## Alternatives

A more sophisticated rework of push rules could cover a better set of endpoints.

## Security considerations

No new considerations apply.

## Unstable prefix

While this MSC is not considered stable, implementations should use `/_matrix/client/unstable/org.matrix.msc3934/pushrules_bulk/*`
instead.
