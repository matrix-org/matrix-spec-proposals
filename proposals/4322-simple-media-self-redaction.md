# MSC4322: Simple Media Self-Redaction

Currently, clients are able to create MXCs and upload media, however, are unable to remove that
media without the help of a server administrator. As [MSC3911][3911] is still a ways away from being
finished, media is currently retained *forever*, even when the user deletes the event that
contained the media in the first place. This proposal outlines a simple method to allow clients
to redact their media at their discretion.

## Proposal

A new endpoint, `POST /_matrix/client/v1/media/redact/{server_name}/{media_uri}`, should be created.
This endpoint must ensure that the user calling it is the same user that created the media URI.
Implementations may rate-limit calls to the endpoint in order to prevent a user
causing strain on disk operations, however this is not required.

This endpoint should be treated similarily to the [redact event][spec_redact] endpoint, allowing
implementations to optionally retain the redacted media for a period of time, however choosing
not to serve it. This must not be read as a "quarantine", as redactions must be permanent, even
if delayed.

Implementations **must not** re-use MXC URIs which have been redacted.
See [security considerations](#security-considerations) for more information.

## Potential issues

1. Remote servers are not necessarily notified of the redacted media, and as such may retain
   the media in their cache, potentially indefinitely. This *can* be resolved by telling
   servers to log which remote servers request media over authentication, however that will
   add significant complexity to this MSC, which ideally will be avoided.
2. Clients are also not notified of media redactions, but most clients only keep a small
   cache of media anyway (if any at all) - this MSC is written under the assumption that the
   primary use-case is users redacting their media soon after redacting an associated event,
   voiding this concern.
3. Abusive users may upload abusive media and then attempt to delete it after their victim
   has retreived the media. This is remediated by retention, in a similar vein to redacted
   message retention.
4. This side-steps power level forbidden redaction mechanisms. This is seen as a
   technicality rather than a problem, since until #3911, media is not tied to events
   (and thus power levels) anyway.

## Alternatives

This MSC will be superseded by [MSC3911][3911] by nature, however it fills a gap that is currently
missing in functionality in a simpler, easier to implement manner.

## Security considerations

As mentioned in [potential issues](#potential-issues), abusive users may upload abusive media,
and then redact it before an administrator can investigate. This is remediated by retention.

Additionally, implementations are forbidden from re-using MXC URIs, as without linked media,
there is no way to know if a URI is still referenced somewhere. As a result, if it is, and a new
peice of media replaces it, an attacker may be able to strike lucky and engage a phishing attack
by making it appear as if a trusted member of a community had uploaded media that they had not.

## Unstable prefix

| Stable | Unstable replacement |
| ------ | -------------------- |
| `/_matrix/client/v1/media/redact/{server_name}/{media_id}` | `/_matrix/client/unstable/uk.timedout.msc4322/media/redact/{server_name}/{media_id}` |

## Dependencies

None

<!--        -->

[3911]: https://github.com/matrix-org/matrix-spec-proposals/pull/3911
[spec_redact]: https://spec.matrix.org/v1.15/client-server-api/#put_matrixclientv3roomsroomidredacteventidtxnid
