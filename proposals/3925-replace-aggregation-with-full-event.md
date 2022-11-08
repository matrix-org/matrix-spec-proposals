# MSC3925: m.replace aggregation with full event

While these events also have been immutable until v1.3, since v1.4 they aren't.
When a client sends a `m.replace` relation, [the server should replace the content of the original event](https://spec.matrix.org/v1.4/client-server-api/#server-side-replacement-of-content).

There are some issues with this requirement:
* Changing the fundamental concept of immutable events is confusing. The server can respond with different event contents for the same `event_id`.
* If an event with `m.replace` relation is deleted, the client would need to detect, if the original content was replaced and possibly needs to fetch the original content.
* There is an additional server call needed, when the replacing event is encrypted, because the server cannot replace the original event content.
* There are also some other issues with this spec paragraph, which are discussed [here](https://github.com/matrix-org/matrix-spec/issues/1299)

## Proposal

Instead of replacing the original content of an event, servers should use the aggregation feature for it.
In fact it is [already used](https://spec.matrix.org/v1.4/client-server-api/#server-side-aggregation-of-mreplace-relationships), 
but only `event_id`, `origin_server_ts` and `sender` are included.
Theoretically this is enough to get the replacing content, but when the event with the `event_id` cannot be found locally it needs to be fetched from the server.
To prevent this additional call to the server, the `m.replace` aggregation should just contain the complete replacing event.

The additional server call is already needed for encrypted events and would be saved by this proposal too.

## Potential issues

* There could be clients which rely on the current behavior.
* It is not as easy for clients like as in the current spec to get the current content of an event by just looking into `content.body`. While this true, it is also a relatively inconsistent behavior. Future replacements of the event would be rendered as "* new content". So the event with the replaced event does look different (without "*") despite the fact, that it is also replaced.

## Alternatives



## Security considerations



## Unstable prefix

I'm not sure if we need an unstable prefix, because the aggregation would just be extended by additional fields.
