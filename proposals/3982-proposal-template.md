# MSC3982: Limit maximum number of events sent to an AS

A core feature of the Application Service API is the ability for the homeserver to push events to another
service over a standard HTTP API. The spec currently sets no limit on how many events can be pushed in
one request to an application service, so the size of the request payload can vary wildly. Most HTTP listeners
and load balancers set "sensible defaults" on the maximum incoming body size (Nginx [uses a 1MB default](https://nginx.org/en/docs/http/ngx_http_core_module.html#client_max_body_size))
and while we shouldn't arbitrarily limit the spec based on that, it's clear we need to give developers
and administrators some idea of how large a request payload can be.

This proposal aims to spec a limit on the number of events that a single transaction can contain,
and since we already know [the maximum size of an event](https://spec.matrix.org/v1.6/client-server-api/#size-limits)
it would be possible to specify the maximum expected size of a body.

## Proposal

The [`PUT /_matrix/app/v1/transactions/{txnId}` endpoint](https://spec.matrix.org/v1.6/application-service-api/#put_matrixappv1transactionstxnid)
MUST only allow up to `100` events in the `events` array in it's body.

This spec follows the precedent set by the [Server-Server /transaction api](https://spec.matrix.org/v1.6/server-server-api/#put_matrixfederationv1sendtxnid)
of setting size limits on transaction payloads.

If the homeserver needs to send more than `100` events in a transaction, it should
send them in a subsequent transaction.

If an application service receives more than this maximum, it MAY choose to handle
those events but would also be within rights to reject the payload (with a 413) for being non-compliant.


### Maximum theoretical payload size

Assuming the worst case, the payload should be no larger than:

```
(65536 * 100) + 113 = 6553613 bytes
```

where 113 accounts for the JSON structure around the `events` array.

Hence, the spec can now hint that the transaction endpoint should be able to
handle at least `~6.5MB` payloads.


## Potential issues

The biggest loss here is that this effectively caps the number of events a single payload can contain,
and so there is potential for a cap to limit how quickly events are sent to an AS. However, a 50 event
limit is fairly high and a sensible [HTTP Keep-Alive](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Keep-Alive)
value will keep a HTTP connection open allowing for quicker streaming of events to the appservice.


## Alternatives

Potentially the homeserver and application service could negotiate a maximum event size instead of specifying
one in the spec, however this isn't desirable because:

 - This requires a two way communication between the Homeserver and AS, which presently isn't required.
 - This potentially costs more time in negotiation than any efficiency losses from the hardcoded limit.
 - Practically speaking, Synapse [has had a limit of 100](https://github.com/matrix-org/synapse/blob/develop/synapse/appservice/scheduler.py#L85-L86)
   for a few years and this hasn't caused many throughput issues. 


## Security considerations

None.

## Unstable prefix

This proposal makes no changes to the payload format. Existing applications should be
unaffected by the change.

## Dependencies

None.
