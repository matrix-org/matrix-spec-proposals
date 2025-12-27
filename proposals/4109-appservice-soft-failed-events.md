# MSC4109: Appservices & soft-failed events

Application services currently take two major shapes: bridges/protocol converters, and tooling to
monitor activity. Each of these has a different use case and optimizing for either could potentially
harm the other. Currently, appservices don't receive [soft failed](https://spec.matrix.org/v1.9/server-server-api/#soft-failure)
events, which can make some monitoring tooling harder.

The appservice API is also intended to be relatively quick as a direct line to the server's internal
events stream. Adding extensive filtering options to that stream could slow down traffic, which leads
to a laggy bridge or extended response times from monitoring.

This proposal aims to expose soft failed events to appservices without creating traffic congestion.
With these events, monitoring tooling can more easily react to content which needs to be cleaned up
after a user is banned (for example). For bridges, they are able to make decisions about whether to
forward the event or react to its processing (maybe it sent an event and the echo indicates it was
soft-failed - the bridge could delete the message on the remote service).

## Proposal

Typically, extensions to the appservice API would be done with a registration flag to enable inclusion
of particular information. A similar approach could be done here as well. This proposal instead suggests
that the feature of receiving soft failed events is non-optional, and bumps the endpoint version for
[`/transactions/:id`](https://spec.matrix.org/v1.9/application-service-api/#put_matrixappv1transactionstxnid).
Appservices which listen on the new endpoint therefore give a clear indication to the homeserver that
they support receiving the new information, making migration similar to a registration flag.

The existing `/transactions/:id` endpoint is deprecated and a new `PUT /_matrix/app/v2/transactions/:id`
endpoint is introduced. The new endpoint has the exact same request and response schemas as the deprecated
one. However, the new endpoint includes events which are soft failed by the server in addition to all
other events. Such events are annotated as such:

```json5
{
  // Some fields not shown for brevity.
  "type": "m.room.message",
  "content": { /* ... */ },
  "unsigned": {
    "m.soft_failed": true // NEW!
  }
}
```

When the `m.soft_failed` flag is not provided, not a boolean, or `false`, the event is assumed to be
a regular, non-soft-failed, event. When `true`, the event has been soft failed by the server.

## Potential issues

The endpoint version bump is a bit strange as a concept, but explored here for feedback. It may be
best to use a registration flag instead, though that may imply some level of filtering which in turn
slows down event transmission. This should be validated with code and metrics.

This MSC also brings appservices closer to the room model, introducing them to a concept which typically
only servers are aware of. Future MSCs may wish to explore this further to build more robust monitoring
tooling and bridges. Such considerations may be using a PDU format for events and exposing state resolution
consequences over the transactions API.

## Alternatives

Discussed inline.

**TODO**: Bring alternatives here once discussed in more detail.

## Security considerations

**TODO**: Complete this section.

## Unstable prefix

While this MSC is not considered stable, implementations should use `PUT /_matrix/app/unstable/org.matrix.msc4109/transactions/:id`
instead. The [normal fallback approach](https://spec.matrix.org/v1.9/application-service-api/#unknown-routes)
applies to both the stable and unstable version of this proposal: homeservers would use the new endpoint,
receive an error code, and fall back to an older one in hopes of sending the event. This failure state
should be cached by the server for a medium amount of time to reduce the impact on event transmission.

## Dependencies

This MSC has no direct dependencies.
