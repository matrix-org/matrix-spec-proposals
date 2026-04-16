# MSC4451: Deprecate Notifications Endpoint

The `/_matrix/client/v3/notifications` endpoint was added more than a decade ago. In the meantime,
end-to-end encryption was added, and the server can no longer accurately evaluate notifications for
all events.

Because the server cannot see the event type or event contents of E2EE messages, it cannot reliably
decide whether a given message should trigger a notification. It cannot accurately evaluate push rules
based on event types being visible, or based on mention keywords within the message contents.
As a result, the server's view of notifications is inherently incomplete. It must either miss all
encrypted events, or incorrectly assume that all encrypted events cause notifications.

This means that this endpoint necessarily returns incomplete and incorrect results to the client,
encouraging an incomplete and buggy implementation on the client side.

The endpoint is also relatively unpopular, with few clients using it and few servers implementing it.

[MSC4076](https://github.com/matrix-org/matrix-spec-proposals/pull/4076) (Let E2EE clients calculate app badge counts themselves)
also exists for much the same reason.

## Proposal

Deprecate the `GET /_matrix/client/v3/notifications` endpoint.

In a future version of the Matrix specification, the endpoint will be removed entirely. For now, it
will be marked as deprecated in the specification. Clients are advised to calculate notifications
locally using data stored from sync, locally executing push rules against decrypted event contents
to accurately determine if an event should notify.

## Potential Issues

The few clients using this endpoint will have to start moving towards alternative, more correct
implementations (i.e. using locally stored data and evaluating push rules client-side). If servers
chose to remove the endpoint before it is officially removed from the specification, it could result
in a reduction in functionality for those legacy clients.

## Alternatives

Adding a warning to the specification, and clarifying the limited behavior of the endpoint.
Perhaps clients could use the endpoint to optimise a more complete implementation - however,
it's not possible to skip "correctly" indexing a room because encrypted events can practically
be sent in rooms without the `m.encryption` state event.

## Security considerations

None.

## Unstable prefix

Unneeded, as this is a deprecation of an existing endpoint.

## Dependencies

None.
