
# MSC4309: Finalised delayed events on sync

## Proposal

A new optional key, `delayed_events_finalised`, is added to the response body of `/sync`. The shape of its
value is equivalent to that of the response body of `GET /_matrix/client/v1/delayed_events/finalised`.
It is an array of the syncing user's delayed events that were sent or failed to be sent after the
`since` timestamp parameter of the associated `/sync` request, or all of them for full `/sync`s.
When no such delayed events exist, the `delayed_events_finalised` key is absent from the `/sync` response.

A new key, `delayed_events_finalised`, is defined for `POST /_matrix/client/v3/user/{userId}/filter`.
Its value is a boolean which, if set to `false`, causes an associated `/sync` response to exclude
any `delayed_events_finalised` key it may have otherwise included.

The only delayed events included in `delayed_events_finalised` are ones that have been retained by the homeserver,
as per the same retention policies as for the `GET /_matrix/client/v1/delayed_events/delayed_events_finalised` endpoint.
Additionally, a homeserver may discard finalised delayed events that have been returned by a `/sync` response.

The `delayed_events_finalised` key is added to the request bodies of the appservice API `/transactions` endpoint.
It has the same content as the key for `/sync`, and contains all of the target appservice's delayed events
that were sent or failed to be sent since the previous transaction.

## Potential issues

Adding a new section to sync might be a quiet large task for homeservers for a feature that is not used a lot.

## Alternatives

The current `GET` finalized delayed events endpoint can already be used to fetch finalized events.
Only if an unexpected error occurs the client is blind and an update on sync would be helpful.

The client can schedule a call to the `GET` delayed events endpoint once it expects the delayed event to have been sent.
This would allow the client to know if it was successful a bit later.

## Security considerations

This returns the exact same data as the `GET` finalized delayed events endpoint.

## Unstable prefix

`org.matrix.msc4140.finalised_delayed_events` should be used as keys of /sync, /filter instead of `finalised_delayed_events`.

## Dependencies

This MSC builds on [MSC4140](https://github.com/matrix-org/matrix-spec-proposals/pull/4140).
