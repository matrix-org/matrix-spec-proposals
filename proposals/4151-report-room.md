# MSC4151: Reporting rooms (Client-Server API)

The specification [already contains](https://spec.matrix.org/v1.10/client-server-api/#reporting-content)
a module for being able to report events, though this functionality does not extend to rooms. Being
able to report rooms is important for user safety: clients have room directories, invite lists,
links to rooms, etc which all don't have an event ID to reference. If the client has *any* event ID
for the room, it can use the existing 'report event' API to report the room instead. However, this
only works if the user has visibility on the event ID being reported too.

These constraints are in addition to the legal obligations of clients to provide a safe user experience.
In some countries, such as the UK, it is required that users be able to report *any* kind of content
they see, and some app stores require similar reporting functionality for mobile apps. These obligations
impose further obligations not discussed in this proposal. For example, actually handling the reports
and informing the reporter how long it will take to process their request. These obligations are
expected to be discussed in a future, larger, MSC series which revamps reporting in Matrix.

This proposal introduces an endpoint for reporting rooms, expanding the capabilities of the reporting
module. The scope of this proposal is intentionally narrow to ensure quick traversal of the MSC process.
Other, future, MSCs may further expand the suite of endpoints available to clients (like reporting
users, media, etc).

## Proposal

Taking inspiration from [`POST /rooms/:roomId/report/:eventId`](https://spec.matrix.org/v1.10/client-server-api/#post_matrixclientv3roomsroomidreporteventid),
a new endpoint is introduced:

```
POST /_matrix/client/v3/rooms/:roomId/report
{
  "reason": "<user-supplied, optional>"
}
```

`reason` is a human-readable string describing the reason for the report. The string may be blank,
but *must* be provided (to align with `/report/:eventId`).

**Note**: `score` is not carried over from `/report/:eventId` because it has not proven useful. A
future MSC may introduce it.

There are no restictions on who can report a room: knowing the room ID is sufficient. This is to
ensure that results from the room directory, invites, links, etc can all be reported. If the room
does not exist on the server, the endpoint returns `404 M_NOT_FOUND`. Otherwise, `200` with `{}` as
a response body.

Like `/report/:eventId`, handling of the report is left as a deliberate implementation detail.

## Safety considerations

* Server admins may be exposed to harmful content through `reason`. This is an existing issue with
  the reporting module, and difficult to fix. Applications which expose report reasons of any kind
  are encouraged to place disclosures in the user experience path. For example, a page explaining
  that the tool may contain harmful content before allowing the user temporary access, or the use of
  spoiler tags on report reasons/content.

* Clients should hide rooms the user reports by default to both discourage duplicate reports and to
  remove the harmful content from the user's view, where possible. This may require filtering room
  directory responses and room lists for the user, or an "ignore room API" like [MSC3840](https://github.com/matrix-org/matrix-doc/pull/3840).

  If the user is joined to a room, the client may wish to offer the user an option to leave the room.

* Users may report whole rooms instead of events in that room, particularly during a harmful content
  spam wave. Administrators and safety teams should be cautious to avoid shutting down or banning
  whole rooms, as the room may be legitimate otherwise. Automated decision making is not suggested
  for a similar reason.

* 'Report flooding' is more easily possible with this new endpoint, where many users report a room
  with the hope of getting it shut down/banned. Mentioned a few times in this proposal, automated
  decision making is not recommended for this endpoint to prevent consequences like this from
  happening.

## Potential issues

* Within the Trust & Safety environment, it is well known that `reason` alone is insufficient for an
  informed report. Self-triage categories and mandatory `reason` for some of those categories help
  improve a safety team's ability to handle a report. These features are not included in this proposal
  as they require further thought and consideration - a future MSC may expand (or even deprecate) the
  report endpoints to support this added information.

* Reports are not federated. This is considered an issue for another MSC, like [MSC3843](https://github.com/matrix-org/matrix-spec-proposals/pull/3843).

* Whether the local server is participating in a room is revealed through the new endpoint. The endpoint
  is only available to local users however, and other ways of finding out the same information may
  already be possible in Matrix (not verified). It is not immediately clear that disclosing this
  information to local clients would cause harm to the server or its users. A future reporting over
  federation proposal may wish to consider hiding the server's participation state, however.

## Alternatives

* Mentioned in the introduction, if a client has an event ID for something in the room, it can typically
  use the existing event report endpoint to report the room. For example, using the creation event,
  the user's own join event, or the most recent message in the room. This only works if the user is
  able to see that event in the room, and further only if the client even has an event ID. Areas of
  the client like the room directory do not expose an event ID the client could use. If they did, the
  user may not have sufficient visibility on the event to be able to report it.

* The event report API could be relaxed to support an empty string for the event ID, though this feels
  effectively like a new endpoint anyways. This MSC introduces such an endpoint.

* The event report API's history visibility check could also be removed, though, as per
  [MSC2249](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/2249-report-require-joined.md),
  this is intentional behaviour.

## Security considerations

* Rate limiting is strongly recommended for this new endpoint.

* Authentication is required for this new endpoint.

## Unstable prefix

While this proposal is not considered stable, implementations should use `/_matrix/client/unstable/org.matrix.msc4151/rooms/:roomId/report`
instead. Clients should note the [`M_UNRECOGNIZED` behaviour](https://spec.matrix.org/v1.10/client-server-api/#common-error-codes)
for servers which do not support the (un)stable endpoint.

## Dependencies

This MSC has no direct dependencies.
