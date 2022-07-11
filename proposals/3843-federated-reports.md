# MSC3843: Reporting content over federation

Clients can currently [report content](https://spec.matrix.org/v1.3/client-server-api/#reporting-content)
to their homeserver, however these reports don't currently translate over federation to affected
servers.

Some content might want to be reported directly to the server which generated it, or tooling on a
given server could find it desirable to generate a report to be sent to a specific server. For example,
if a homeserver plugin detected spam then it might wish to report that directly to the server which
generated the content, bypassing any local report handling which might be attached to the local server's
client-server API endpoint.

## Proposal

Mirroring the client-server API a bit, we introduce a new endpoint for reporting events in rooms over
federation: `POST /_matrix/federation/v1/rooms/{roomId}/report/{eventId}`. To report a whole room the
caller would reference the `m.room.create` event. To report a user within the context of that room the
caller would use the `m.room.member` event for that user. Otherwise, the potentially objectionable
content's event ID would be used to report that content.

The new endpoint takes very similar body parameters to the client-server API, though with the `score`
notably missing and `reason` being explicitly required. For example:

```
POST /_matrix/federation/v1/rooms/!bad:example.org/report/$spammyspam
{"reason":"This message is spam"}
```

`reason` cannot be blank, unlike the client-server API.

It is intentional that the original reporter is not sent over federation, however given the endpoint
is authenticated using the server's name it may still be possible to identify the original reporter.
If the homeserver holds exactly one known user then there's a pretty good chance they reported the
content.

How the report is handled is deliberately left as an implementation detail. Homeservers might wish to
add the record to their existing reports table/system, or create a new handling pipeline for it.
Similarly, when to call this endpoint is also left as an implementation detail. It may not be desirable
for all client-server `/report` calls to be proxied over federation, for example.

The content being reported *should* originate from the server it is being reported to, but that is
not a requirement. It may be valid to notify other homeservers that there is spam in a room to help
all affected users, for example. It is up to the implementation if it wants to handle content generated
from other servers - if it doesn't, it can respond with an `M_UNACTIONABLE` error code (new with this
proposal) and an HTTP `400` status. Further, if the server just doesn't want to deal with federated
reports at all it can return a `400` `M_UNACTIONABLE` error for everything.

Homeservers are strongly encouraged to rate limit the number of reports which come in. A possible
approach might be to limit servers to 10 reports per minute, or similar.

## Potential issues

This could open up servers to receiving spammy or abusive reports, however given most servers have
a federation-capable reporting mechanism already (email, community room, etc) this is not expected
to have much of an impact. The added recommendation that things be rate limited also helps a lot.

## Alternatives

Briefly while writing this proposal it was considered to expose a shared policy room between the servers,
where somehow Server A and Server B negotiate a room where they can publish
[policy rules](https://spec.matrix.org/v1.3/client-server-api/#moderation-policy-lists) that the other
side picks up and actions, if needed. This feels overly complex for the time being, but if proven useful
could be explored in a different MSC.

## Security considerations

Servers should protect themselves from abusive or spammy reports. Rate limiting and rejecting content
that didn't originate from itself will help a lot on that.

Like with the client-server API, servers should be cautious about hooking up automated responses to
reported content. Without the added context of *who* made the report, it's very possible that the content
is being reported 40 times by the same person rather than 40 different people - this could easily trip
an automated response of spam handling or deactivation if not careful.

## Unstable prefix

While this MSC is not considered stable, implementations should use `/_matrix/federation/unstable/org.matrix.msc3843/rooms/{roomId}/report/{eventId}`
as the endpoint. The body stays as-proposed.

## Dependencies

None relevant.
