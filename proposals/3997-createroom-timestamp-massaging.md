# MSC3997: Add timestamp massaging to `/createRoom`

[Timestamp massaging is an existing
concept](https://spec.matrix.org/v1.5/application-service-api/#timestamp-massaging)
introduced by [MSC3316](https://github.com/matrix-org/matrix-spec-proposals/pull/3316)
for the `/send?ts=123` and `/state?ts=123` endpoint in order to override the
`origin_server_ts` of sent events.

But timestamp massaging is impossible for the primordial events created by `/createRoom`
like `m.room.create`, the initial creator `m.room.member`, `m.room.power_levels`, etc;
and room creation can't be mimicked with `/send`/`/state`.

When writing end-to-end tests, it's useful to have your room appear as though it was
created back in time before your messages were sent and to have stable/consistent
timestamps. If you start using timestamp massaging when sending messages, it can appear
as though those events occurred before the `m.room.create` and other primordial events.
We specifically run into this with the [Matrix Public
Archive](https://github.com/matrix-org/matrix-public-archive/) end-to-end tests.

In real-life scenarios, practically, this hasn't mattered much for content because the
DAG is ordered topologically and not by timestamp but is a semantic inconsistency that
is becoming more important with API's like `/timestamp_to_event` which find events by
their `origin_server_ts`. And makes things tricky for the Matrix Public Archive to
navigate tombstone and predecessor room upgrade history by date assuming good
intentions.

This idea is tracked in Synapse by https://github.com/matrix-org/synapse/issues/15346

## Proposal

Add timestamp massaging to the `/createRoom` endpoint to be able to override the
`origin_server_ts` of all primordial events created with that call. We do this by adding
a `ts` querystring parameter on `POST /_matrix/client/v3/createRoom?ts=123` specifying
the value to apply to `origin_server_ts` on the event (UNIX epoch milliseconds).

This functionality is restricted to the application service (AS) API to be consistent
with [MSC3316](https://github.com/matrix-org/matrix-spec-proposals/pull/3316). There
could be future considerations to opening this up to any client as it's kinda arbitrary
to restrict it this way and just seems like friction to try to get only people with good
intentions using it.

---

Also related: [MSC3998](https://github.com/matrix-org/matrix-spec-proposals/pull/3998)
proposes adding a `ts` querystring parameter to the `/join` and `/knock` endpoints but
for different reasons.

## Potential issues

*None surmised so far*


## Alternatives

*None at the moment*


## Security considerations

Timestamps should already be considered untrusted over federation, and application
services are trusted server components, so allowing appservices to override timestamps
does not create any new security considerations.


## Unstable prefix

While this feature is in development, the `ts` querystring parameter can be used as
`org.matrix.msc3997.ts`

### While the MSC is unstable

During this period, to detect server support clients should check for the presence of
the `org.matrix.msc3997` flag in `unstable_features` on `/versions`. Clients are also
required to use the unstable prefixes (see [unstable prefix](#unstable-prefix)) during
this time.

### Once the MSC is merged but not in a spec version

Once this MSC is merged, but is not yet part of the spec, clients should rely on the
presence of the `org.matrix.msc3997.stable` flag in `unstable_features` to determine
server support. If the flag is present, clients are required to use stable prefixes (see
[unstable prefix](#unstable-prefix)).

### Once the MSC is in a spec version

Once this MSC becomes a part of a spec version, clients should rely on the presence of
the spec version, that supports the MSC, in `versions` on `/versions`, to determine
support. Servers are encouraged to keep the `org.matrix.msc3997.stable` flag around for
a reasonable amount of time to help smooth over the transition for clients. "Reasonable"
is intentionally left as an implementation detail, however the MSC process currently
recommends *at most* 2 months from the date of spec release.
