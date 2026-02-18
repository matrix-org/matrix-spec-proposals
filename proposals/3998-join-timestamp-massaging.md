# MSC3998: Add timestamp massaging to `/join` and `/knock`

As mentioned in the original
[MSC3316](https://github.com/matrix-org/matrix-spec-proposals/pull/3316) for timestamp
massaging,

> We consciously don't support the `ts` parameter on the various helper
> syntactic-sugar APIs like `/kick` and `/ban`. If a bridge/bot is smart enough to
> be faking history, it is already in the business of dealing with raw events,
> and should not be using the syntactic sugar APIs.

While it's possible to mimic a join/invite/knock for a room that the server already
knows about, this falls apart for a federated action for a room that the server doesn't
know about since it's not possible to specify any `via` servers with the `/state`
endpoint. Currently, if you try with Synapse, it will throw a `404` with the following
error response body:

```json
{
  "errcode": "M_UNKNOWN",
  "error": "Can't join remote room because no servers that are in the room have been provided."
}
```

When writing end-to-end tests, it's useful to have your room appear as though it was
created back in time before your messages were sent and to have stable/consistent
timestamps. If you start using timestamp massaging when sending messages, it can appear
as though those events occurred before the `m.room.member` events used to join federated
rooms. We specifically run into this with the [Matrix Public
Archive](https://github.com/matrix-org/matrix-public-archive/) end-to-end tests.

In real-life scenarios, practically, this hasn't mattered much for content because the
DAG is ordered topologically and not by timestamp but is a semantic inconsistency that
is becoming more important with API's like `/timestamp_to_event` which find events by
their `origin_server_ts`. And makes things tricky for the Matrix Public Archive to
navigate history by date seamlessly assuming good intentions.


## Proposal

Add timestamp massaging to the `/join` and `/knock` endpoints to be able to override the
`origin_server_ts` of sent events. We do this by adding a `ts` querystring parameter
that specifies the value to apply to `origin_server_ts` on the event (UNIX epoch
milliseconds).

 - `POST /_matrix/client/v3/join/{roomId}?ts=123`
 - `POST /_matrix/client/v3/knock/{roomIdOrAlias}?ts=123`

This functionality is restricted to the application service (AS) API to be consistent
with [MSC3316](https://github.com/matrix-org/matrix-spec-proposals/pull/3316). There
could be future considerations to opening this up to any client as it's kinda arbitrary
to restrict it this way and just seems like friction to try to get only people with good
intentions using it.

---

Also related: [MSC3997](https://github.com/matrix-org/matrix-spec-proposals/pull/3997)
proposes adding a `ts` querystring parameter to the `/createRoom` endpoint but for
different reasons.


## Potential issues

*None surmised so far*


## Alternatives

We could alternatively add `via` server parameters to the `/send` and `/state` endpoints
so the server knows how to find the room in question.


## Security considerations

Timestamps should already be considered untrusted over federation, and application
services are trusted server components, so allowing appservices to override timestamps
does not create any new security considerations.


## Unstable prefix

While this feature is in development, the `ts` querystring parameter can be used as
`org.matrix.msc3998.ts`

### While the MSC is unstable

During this period, to detect server support clients should check for the presence of
the `org.matrix.msc3998` flag in `unstable_features` on `/versions`. Clients are also
required to use the unstable prefixes (see [unstable prefix](#unstable-prefix)) during
this time.

### Once the MSC is merged but not in a spec version

Once this MSC is merged, but is not yet part of the spec, clients should rely on the
presence of the `org.matrix.msc3998.stable` flag in `unstable_features` to determine
server support. If the flag is present, clients are required to use stable prefixes (see
[unstable prefix](#unstable-prefix)).

### Once the MSC is in a spec version

Once this MSC becomes a part of a spec version, clients should rely on the presence of
the spec version, that supports the MSC, in `versions` on `/versions`, to determine
support. Servers are encouraged to keep the `org.matrix.msc3998.stable` flag around for
a reasonable amount of time to help smooth over the transition for clients. "Reasonable"
is intentionally left as an implementation detail, however the MSC process currently
recommends *at most* 2 months from the date of spec release.
