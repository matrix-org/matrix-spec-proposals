# MSC4023: Thread ID for second-order relation

Events that have a non-thread relation to other events (eg. reactions) are
considered to be in the thread that their parent event is in.
[MSC3981](https://github.com/matrix-org/matrix-spec-proposals/pull/3981)
defines a way to recursively load such relations with the `/relations` API
but for such events, it is impossible for a client to know what thread the
event is in when it arrives from `/sync` unless it already has, or fetches,
the parent event. This means performing another client-server API request to
fetch the parent event which is inefficient.

This proposal wants to reduce the amount of work required for clients to partition
events with certainty.

## Proposal

Whenever a server returns events in the client-server API, it adds a `thread_id`
property to the `unsigned` field of the event with the ID of the event's thread root
as defined in MSC3440. This applies to any endpoint that returns events including
`/sync` and `/messages`.

```jsonc
{
  "unsigned": {
    "thread_id": "$event_id"
  }
}
```

All events that are not part of a thread should fill the `thread_id` property with
the special value `main` – as defined in MSC3771.

If a server does not have the first-order event, the unsigned `thread_id` property
should be filled with a `null` value.

## Potential issues

### Database query performances

This could have performance implications on the server side, requiring more work
to be performed when fetching events in a room.

### Missing first-order relation

It is possible that a server will have the second-order event, but not have the
first-order event (eg, it has received a reaction over federation, but has not
yet received the event being reacted to).

## Alternatives

If "[MSC3051: A scalable relation format](https://github.com/matrix-org/matrix-spec-proposals/pull/3051)"
were to be adopted, second-order relations could specify their thread directly as one of the relationships,
in which case this MSC would become unnecessary. However, that MSC is a longer term evolution of the protocol
and will take time for the ecosystem to adopt. This MSC is intended as a much shorter term fix.

## Security considerations

No security considerations

## Unstable prefix

While this MSC is not considered stable by the specification, implementations _must_ use
`org.matrix.msc4023.thread_id` in place of `thread_id`.

## Dependencies

This MSC does not have dependencies
