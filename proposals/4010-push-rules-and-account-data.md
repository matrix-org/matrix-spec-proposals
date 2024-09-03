# MSC4010: Push rules and account data

Push rules have a [bespoke API](https://spec.matrix.org/v1.6/client-server-api/#push-rules-api)
which clients use to retrieve, add, modify, and remove push rules. Any modifications
made using this API are sent to all clients via a `m.push_rules` event in the
`account_data` section in the
[the next `/sync` response](https://spec.matrix.org/v1.6/client-server-api/#push-rules-events).

The client-server API does not have any special behavior around using the
[account data APIs](https://spec.matrix.org/v1.6/client-server-api/#client-behaviour-17)
with the `m.push_rules` type leading to different behavior on different homeservers:

* Synapse will accept the data and shadow the real push rules in `/sync`, but
  *won't use the data when evaluating push rules*.
* Dendrite will return an HTTP 403 if you attempt to set `m.push_rules` via
  `/account_data`.
* Conduit has no protections for special account data. It will accept `m.push_rules` via
  `/account_data` *and* use those when evaluating push rules.

The [fully read marker](https://spec.matrix.org/v1.6/client-server-api/#fully-read-markers)
operates in a similar way and
[servers must reject updating `m.fully_read` via `/account_data`](https://spec.matrix.org/v1.6/client-server-api/#server-behaviour-10).

Note that when attempting to set `m.fully_read` via `/account_data` the following
behavior is observed:

* Synapse will reject it with a 405 error (only for room account data).
* Dendrite will reject it with an HTTP 403 error.

## Proposal

To make push rules data consistent with fully read markers, the following
clarifications are offered:

* The `m.push_rules` account data type becomes protected and cannot be set using
  the `/account_data` API, similarly to `m.fully_read`.
* "Rejected" means to use the 405 error response as
  [documented](https://spec.matrix.org/v1.6/client-server-api/#put_matrixclientv3useruseridaccount_datatype):

  > This `type` of account data is controlled by the server; it cannot be modified
  > by clients. Errcode: `M_BAD_JSON`.
* `m.push_rules` and `m.fully_read` should be rejected for both global and room
  account data.
* Reading `m.push_rules` and `m.fully_read` should be allowed (although note that
  currently `m.push_rules` only makes sense for global account data and `m.fully_read`
  only makes sense for room account data). The format should match what is currently
  [returned via `/sync`](https://spec.matrix.org/v1.6/client-server-api/#push-rules-events).

The above rules shall also apply when deleting account data if [MSC3391](https://github.com/matrix-org/matrix-spec-proposals/pull/3391)
is merged before this MSC.

## Potential issues

It is possible that a client is currently storing data in the `m.push_rules`
(or global `m.fully_read`) account data. After this change it could no longer
be updated, deleted, or retrieved. It seems unlikely that the data stored here
is done purposefully (and is likely the result of undefined behavior that this
MSC is attempting to fix).

## Alternatives

An alternative would be to remove the current push rules API and have clients
store all push rules in bulk. This would be subject to race conditions between
clients.

A slight variation of the above would be to *additionally* define the `/account_data/m.push_rules`
endpoint as bulk modifying the push rules data. This could be seen as an alternative
to [MSC3934](https://github.com/matrix-org/matrix-spec-proposals/pull/3934).

## Security considerations

None foreseen.

## Unstable prefix

This is mostly clarifications and does not add any event types or new endpoints.

## Dependencies

N/A
