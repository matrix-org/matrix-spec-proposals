# Proposal to add timestamp massaging to the spec
Bridges often want to override message timestamps to preserve the timestamps from
the remote network. The spec used to have a concept of [timestamp massaging], but
it was excluded from the release due to not being properly specified. Synapse
still implements it and it is widely used in bridges.

[MSC2716] was originally going to add timestamp massaging to the spec, but it
pivoted to focusing solely on batch sending history. This MSC simply copies the
proposed `ts` query param from the [original MSC2716].

[timestamp massaging]: https://matrix.org/docs/spec/application_service/r0.1.2#timestamp-massaging
[MSC2716]: https://github.com/matrix-org/matrix-doc/pull/2716
[original MSC2716]: https://github.com/matrix-org/matrix-doc/blob/94514392b118dfae8ee6840b13b83d2f8ce8fcfc/proposals/2716-importing-history-into-existing-rooms.md

## Proposal
As per the original version of MSC2716:

> We let the AS API override ('massage') the `origin_server_ts` timestamp
> applied to sent events. We do this by adding a `ts` querystring parameter on
> the `PUT /_matrix/client/r0/rooms/{roomId}/send/{eventType}/{txnId}`
> and `PUT /_matrix/client/r0/rooms/{roomId}/state/{eventType}/{stateKey}`
> endpoints, specifying the value to apply to `origin_server_ts` on the event
> (UNIX epoch milliseconds).
>
> We consciously don't support the `ts` parameter on the various helper
> syntactic-sugar APIs like /kick and /ban. If a bridge/bot is smart enough to
> be faking history, it is already in the business of dealing with raw events,
> and should not be using the syntactic sugar APIs.

The spec should also make it clear that the `ts` query param won't affect DAG
ordering, and MSC2716's batch sending should be used when the intention is to
insert history somewhere else than the end of the room.

## Potential issues
None.

## Alternatives
The new MSC2716 could technically be considered an alternative, but it can only
be used for history, while this proposal also supports overriding timestamps of
new messages. In practice, bridges will likely use both: Batch sending for
filling history and timestamp massaging for new messages.

## Security considerations
Timestamps should already be considered untrusted over federation, and
application services are trusted server components, so allowing appservices
to override timestamps does not create any new security considerations.

## Unstable prefix
`org.matrix.msc3316.ts` may be used as the query parameter. However, the `ts`
parameter is already used in production for the `/send` endpoint, which means
the unstable prefix should only be used for the `/state` endpoint.
