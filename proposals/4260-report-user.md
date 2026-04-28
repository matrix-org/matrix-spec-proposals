# MSC4260: Reporting users (Client-Server API)

[MSC4151 (merged)](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/4151-report-room.md)
added an endpoint to report entire rooms to the server admin, expanding upon the existing report event
API. To fully complement this set of APIs, this proposal introduces a Client-Server API endpoint to
report entire users, independent of rooms.

Like MSC4151, the scope of this MSC is intentionally narrow to facilitate quick traversal through the
MSC process. Other, future, MSCs may be required to build out even more APIs for reporting content.

Also like MSC4151, it is expected that a future series of MSCs will revamp reporting in Matrix.

## Proposal

Taking inspiration from [`POST /rooms/:roomId/report/:eventId`](https://spec.matrix.org/v1.10/client-server-api/#post_matrixclientv3roomsroomidreporteventid),
a new endpoint is introduced:

```
POST /_matrix/client/v3/users/:userId/report
{
  "reason": "<user-supplied, may be empty>"
}
```

`reason` is a human-readable string describing the reason for the report. The string may be blank,
but *must* be provided (to align with `/report/:eventId`).

**Note**: `score` is not carried over from `/report/:eventId` because it has not proven useful. A
future MSC may introduce it. The same was done in MSC4151 for `/rooms/:roomId/report`.

There are no restrictions on who can report a user: knowing the user ID is sufficient. This is to
ensure that results from the user directory, invites, links, etc can all be reported. If the user
does not exist on the server, the endpoint returns `404 M_NOT_FOUND`. Otherwise, `200` with `{}` as
a response body. If a user doesn't exist and the server wishes to hide that detail, it MAY return a
successful (`200`) response instead.

Like `/report/:eventId`, handling of the report is left as a deliberate implementation detail.

### Examples

**Note**: Some clients may need to `encodeURIComponent` (or similar) the user ID to use it in a path
parameter.

```
POST /_matrix/client/v3/users/@alice:example.org/report
{"reason":"bad person"}

> 200 OK
> {}
```

```
POST /_matrix/client/v3/users/@alice:example.org/report
{"reason":""}

> 200 OK
> {}
```

```
POST /_matrix/client/v3/users/@alice:example.org/report
{"reason":""}

> 404 OK
> {"errcode":"M_NOT_FOUND","error":"User does not exist"}
```

## Safety considerations

* Server admins may be exposed to harmful content through `reason`. This is an existing issue with
  the reporting module, and difficult to fix. Applications which expose report reasons of any kind
  are encouraged to place disclosures in the user experience path. For example, a page explaining
  that the tool may contain harmful content before allowing the user temporary access, or the use of
  spoiler tags on report reasons/content.

* Clients MAY add reported users to the [ignore list](https://spec.matrix.org/v1.13/client-server-api/#ignoring-users)
  to both discourage duplicate reports and to remove the harmful content from the user's view, where
  possible. This may require filtering user directory responses and local timeline filtering.

* Users may report other users instead of events in any specific room, particularly during a harmful
  content spam wave. Administrators and safety teams should aim to clean up a user's events if they
  take action against the account, where appropriate.

* 'Report flooding' is more easily possible with this new endpoint, where many users report a user
  with the hope of getting them kicked off the server. Automated decision making is not recommended
  for this endpoint to prevent consequences like this from happening. Teams may wish to consider using
  reversible options like [suspension](https://spec.matrix.org/v1.13/client-server-api/#account-suspension)
  and [locking](https://spec.matrix.org/v1.13/client-server-api/#account-locking).

## Potential issues

* Within the Trust & Safety environment, it is well known that `reason` alone is insufficient for an
  informed report. Self-triage categories and mandatory `reason` for some of those categories help
  improve a safety team's ability to handle a report. These features are not included in this proposal
  as they require further thought and consideration - a future MSC may expand (or even deprecate) the
  report endpoints to support this added information.

* While reports against non-local users are permitted, this MSC does not introduce a way for those
  reports to transit federation to the target's server. This is considered an issue for another MSC,
  like [MSC3843](https://github.com/matrix-org/matrix-spec-proposals/pull/3843) or
  [MSC4202](https://github.com/matrix-org/matrix-spec-proposals/pull/4202).

* Whether a user exists on the server is revealed through the new endpoint. Servers have the option
  to mask this detail by ignoring the report.

## Alternatives

* If the client is aiming to report a user within a room, reporting the membership event within that
  room may be suitable. If the user is aiming to report a broad pattern of behaviour, or a profile
  concern spanning multiple rooms/communities, a more generic API is preferred. A dedicated API is
  also required when users are shown outside the context of a room, such as during invites (when event
  IDs may not be known) or when looking for users/friends to chat to.

* [MSC4202](https://github.com/matrix-org/matrix-spec-proposals/pull/4202) discusses the idea of
  reporting profiles generally, and aims to work within the context of a room. Introducing a new
  dedicated endpoint is compatible with MSC4202's objectives.

## Security considerations

* Rate limiting is strongly recommended for this new endpoint.

* Authentication is required for this new endpoint.

* Guest access is not permitted for this new endpoint to reduce spam. A future MSC may change this
  out of necessity. MSC4151 and the original report events API are likely similarly affected.

* Servers which opt to hide the existence of a user on the new endpoint should consider implementing
  a constant time function to avoid unintentionally disclosing that a user exists by processing the
  request slower.

## Unstable prefix

While this proposal is not considered stable, implementations should use `/_matrix/client/unstable/org.matrix.msc4260/users/:userId/report`
instead. Clients should note the [`M_UNRECOGNIZED` behaviour](https://spec.matrix.org/v1.13/client-server-api/#common-error-codes)
for servers which do not support the (un)stable endpoint.

## Dependencies

This MSC has no direct dependencies.
