# MSC4376: Remove /v1/send_join and /v1/send_leave

[/_matrix/federation/v1/send_join/{roomId}/{eventId}] has been superseded by a `v2` endpoint and
deprecated with [MSC1802] in [r0.1.4] of the federation API in 2020. Given the time elapsed and the
fact that the continued presence of the deprecated endpoint occasionally causes confusion[^1], it
should be removed from the spec.

This proposal additionally affects the [/_matrix/federation/v1/send_leave/{roomId}/{eventId}]
endpoint as it is similarly superseded by a v2 variant.

## Proposal

The following endpoints are removed (they're already deprecated):

* [/_matrix/federation/v1/send_join/{roomId}/{eventId}]
* [/_matrix/federation/v1/send_leave/{roomId}/{eventId}]

## Potential issues

Compatibility issues appear unlikely as the ecosystem seems to have adapted rather well.

### Synapse

Synapse has started supporting the `v2` endpoint for incoming requests in [v1.8.0] (January 2020).
In the same version, Synapse has also started preferring the `v2` endpoint for outgoing requests,
falling back to `v1` only when `v2` is unavailable.

- https://github.com/matrix-org/synapse/commit/54ae52ba960df2bcc1daa76b6ef83b125ab9aac9#diff-b8a7e2066859e82776a9d0803499bfdc19707b3279e8fd43457f69f18c5cfecfL524-R548
  (incoming)
- https://github.com/matrix-org/synapse/commit/54ae52ba960df2bcc1daa76b6ef83b125ab9aac9#diff-3cf3f534d150a0319b7bdd81c884daff978bba8f8c603d7f023d5dd5d73e1ab1R600-R632
  (outgoing)

This behaviour is still present in the currently latest release [v1.141.0] (October 2025).

- https://github.com/element-hq/synapse/blob/v1.141.0/synapse/federation/transport/server/federation.py#L422
  (incoming)
- https://github.com/element-hq/synapse/blob/v1.141.0/synapse/federation/federation_client.py#L1356
  (outgoing)

Nearby, Synapse prefers `v2` for `/send_leave` as well.

### Dendrite

Dendrite has stopped supporting the `v1` endpoint for incoming requests in December 2019 and to this
day only offers `v2`.

- https://github.com/matrix-org/dendrite/commit/af9568ba4468eb106ec305df496fbe1319fd74eb

For outgoing requests Dendrite relies on gomatrixserverlib which since June 2020 is preferring `v2`,
falling back to `v1` only when `v2` is not available.

- https://github.com/matrix-org/gomatrixserverlib/commit/5539854e4abc4ce179e991fbffaccde06b695dbc

gomatrixserverlib's preference of `/v2/send_leave` is https://github.com/matrix-org/gomatrixserverlib/pull/208

### Conduit & friends

Conduit has first started to support the `v2` endpoint for incoming requests in April 2021.

- https://gitlab.com/famedly/conduit/-/commit/eedac4fd9610feee34963d0bb227b354f97cd210?expanded=1
  (see `server_server.rs`, line 1755)

Support for the `v1` endpoint was added shortly afterwards in July 2021.

- https://gitlab.com/famedly/conduit/-/commit/48494c946496c36b2d1f85da1e8877ac95e2d664?expanded=1

As of writing, this behaviour is still present in Conduit and derivates such as tuwunel today.

- https://github.com/matrix-construct/tuwunel/blob/d24986edf198cc8b37a47ed94b50a72a566c5cca/src/api/server/send_join.rs#L265

When Conduit first gained support for joining federated rooms in August 2020, it used `v2`
exclusively without falling back.

- https://gitlab.com/famedly/conduit/-/commit/eedac4fd9610feee34963d0bb227b354f97cd210 (see
  `membership.rs`, line 95)

Again, this behaviour is still present in Conduit and derivates such as tuwunel today.

- https://github.com/matrix-construct/tuwunel/blob/d24986edf198cc8b37a47ed94b50a72a566c5cca/src/service/membership/join.rs#L710

These implementations prefer `/v2/send_leave` in nearby code as well.

## Alternatives

None.

## Security considerations

None.

## Unstable prefix

None.

## Dependencies

None.

[^1]: See e.g. https://github.com/matrix-org/matrix-spec/issues/1514 and
    https://github.com/matrix-org/matrix-spec/issues/1515.

  [/_matrix/federation/v1/send_join/{roomId}/{eventId}]: https://spec.matrix.org/v1.16/server-server-api/#put_matrixfederationv1send_joinroomideventid
  [/_matrix/federation/v1/send_leave/{roomId}/{eventId}]: https://spec.matrix.org/v1.16/server-server-api/#put_matrixfederationv1send_leaveroomideventid
  [MSC1802]: https://github.com/matrix-org/matrix-spec-proposals/blob/old_master/proposals/1802-standardised-federation-response-format.md
  [r0.1.4]: https://spec.matrix.org/legacy/server_server/r0.1.4.html
  [v1.8.0]: https://github.com/matrix-org/synapse/releases/tag/v1.8.0
  [v1.141.0]: https://github.com/element-hq/synapse/releases/tag/v1.141.0
