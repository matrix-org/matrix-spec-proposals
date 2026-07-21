# MSC4514: EDU size limit

This proposal clarifies/specifies that [EDUs](https://spec.matrix.org/v1.19/server-server-api/#edus)
are limited to 65536 bytes. See [this issue](https://github.com/matrix-org/matrix-spec/issues/807)
for more detail.


## Proposal

EDUs MUST NOT exceed 65536 bytes when formatted as [Canonical JSON](https://spec.matrix.org/v1.19/appendices/#canonical-json).
This matches the [size limit for events](https://spec.matrix.org/v1.19/client-server-api/#size-limits).

This implicitly means that [to-device messages](https://spec.matrix.org/v1.19/server-server-api/#send-to-device-messaging)
and other information bundled into an EDU cannot exceed 65536 bytes. Clients MAY encounter errors if
they attempt to send information larger than the implied EDU permits. For example, a large to-device
message.

Note that this limit also implicitly creates a maximum size for a [`/send`](https://spec.matrix.org/v1.19/server-server-api/#put_matrixfederationv1sendtxnid)
transaction. Servers SHOULD split transactions over multiple requests if they encounter
[413](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/413) errors on the endpoint.

Parallel to [MSC4513](https://github.com/matrix-org/matrix-spec-proposals/pull/4513), this proposal
permits 413 HTTP status codes to be returned on the following endpoints because they (sometimes)
generate EDUs in normal operation:

* [`PUT /_matrix/federation/v1/send/:txnId`](https://spec.matrix.org/v1.19/server-server-api/#put_matrixfederationv1sendtxnid)
* [`PUT /_matrix/client/v3/sendToDevice/:eventType/:txnId`](https://spec.matrix.org/v1.19/client-server-api/#put_matrixclientv3sendtodeviceeventtypetxnid)
* [`POST /_matrix/client/v3/rooms/:roomId/receipt/:receiptType/:eventId`](https://spec.matrix.org/v1.19/client-server-api/#post_matrixclientv3roomsroomidreceiptreceipttypeeventid)
* [`PUT /_matrix/client/v3/presence/:userId/status`](https://spec.matrix.org/v1.19/client-server-api/#put_matrixclientv3presenceuseridstatus)
* [`PUT /_matrix/client/v3/rooms/:roomId/typing/:userId`](https://spec.matrix.org/v1.19/client-server-api/#put_matrixclientv3roomsroomidtypinguserid)
* [`PUT /_matrix/client/v3/devices/:deviceId`](https://spec.matrix.org/v1.19/client-server-api/#put_matrixclientv3devicesdeviceid)
* [`POST /_matrix/client/v3/keys/device_signing/upload`](https://spec.matrix.org/v1.19/client-server-api/#post_matrixclientv3keysdevice_signingupload)
* [`POST /_matrix/client/v3/keys/signatures/upload`](https://spec.matrix.org/v1.19/client-server-api/#post_matrixclientv3keyssignaturesupload)

Servers SHOULD return a [standard Matrix error](https://spec.matrix.org/v1.19/client-server-api/#standard-error-response)
with the 413 status code, but are not required to. This is in alignment with MSC4513.


## Potential issues

Large EDUs were possible before, but were somewhat likely to encounter 413 or similar status codes in
the wild due to reverse proxy configurations. Those applications will need to be adjusted to fit their
data into a smaller form factor.

Noted by [synapse#19617](https://github.com/element-hq/synapse/pull/19617), it's still possible for
implementations to split up to-device messages such that they're larger than the individual EDU size
limit. This proposal doesn't carve out an exception for this because it's believed that a to-device
message *could* be rejected at client send time with the size of the EDU's boilerplate being known.
If it ends up being that some EDUs need to be larger than the target, the target SHOULD be adjusted
by this proposal.


## Alternatives

Alternatives largely amount to "don't do this", so aren't discussed here.


## Security considerations

This MSC is a security consideration.


## Unstable prefix

None possible - implementations need to be able to reject large EDUs without namespacing.


## Dependencies

This proposal would benefit from [MSC4513](https://github.com/matrix-org/matrix-spec-proposals/pull/4513),
but is deliberately not blocked by it. The relevant portions of MSC4513 have
been minimally incorporated into this proposal.
