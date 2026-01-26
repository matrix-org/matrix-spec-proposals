# MSC4322: Simple Media Self-Redaction

Currently, clients are able to create MXCs and upload media but are unable to remove that
media without the help of a server administrator. As [MSC3911 (Linking media to events)][3911]
is still a ways away from being finished, media is currently retained *forever*,
even when the user deletes all events that contained the media in the first place.
This proposal outlines a simple method to allow clients to redact their media at their discretion.

## Proposal

> [!NOTE]
> "Redact" is used in the same sense as *event redaction* - the actual data is removed
> and often made generally inaccessible, however the unique identifier and possibly metadata still
> remains. You may also read "redact" as "delete" or "remove" in a higher level reading of this
> proposal.

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT",
"RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in
[RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

### Client-to-server changes

A new client-to-server endpoint, `POST /_matrix/client/v1/media/redact/{server_name}/{media_id}`,
is created. It must respond with a `200 OK` response and an empty body (`{}`) upon success.

This endpoint must ensure that the user calling it is the same user that created the media URI,
or a user with an appropriate permission override (for example, a server administrator).
Implementations may federate the media redaction
(see [server-to-server changes](#server-to-server-changes)), however must only do so when the media
URI belongs to the same server.

Implementations may rate-limit calls to the endpoint in order to prevent a user
causing strain on disk operations, optionally omitting the rate-limit for administrators.

This endpoint may be treated similarly to the [redact event][spec_redact] endpoint, allowing
implementations to optionally retain the redacted media for a period of time, however choosing
not to serve it. This must not be read as a "quarantine", as redactions must be permanent, even
if delayed. Once a redaction has been made, if the server chooses to retain the media, it must not
be served to any client, or federation requests. Susbequent requests to the redact endpoint
are treated as a no-op, and the server must return a `200 OK` response with an empty body.

For internal annotation, the redact endpoint may include an optional `reason` parameter.
This parameter should either be a string, or omitted entirely, not null.

Implementations **must not** re-use MXC URIs which have been redacted.
See [security considerations](#security-considerations) for more information.

Suspended users should be permitted to redact their media, like events, but locked users must not
be capable of the same action. As guests are only have immutable media access, they are not
permitted to redact it.

### Server-to-server changes

In order to know which servers to federate a redaction to, the server may wish to take a log of which
servers download media (typically done by recording the origin of
the [`GET /_matrix/federation/v1/media/download/{media_id}`][spec_s2s_download] endpoint).

When a media redaction is performed, the server should send an EDU to every remote that downloaded
the media. For this, the new EDU type `m.media_redaction` is created, shaped as follows:

```json
{
   "type": "m.media_redaction",
   "media_id": "opaque_identifier"
}
```

Upon receiving this EDU, servers MUST remove the media from the data store, refusing to serve it
to clients in succeeding requests. Servers SHOULD make a note of which media IDs are redacted
in order to prevent lookups for known redacted media, however this is not required, as the origin
should serve `404 / M_NOT_FOUND` on the media afterwards anyway.

> [!TIP]
> Media IDs are only unique per origin, so ensure your file lookup is scoped correctly.
> For example, if a transaction came from `server.example`, with the `media_id` of
> `foobar`, that could be turned into `mxc://server.example/foobar`.

## Potential issues

1. Clients are also not notified of media redactions, but most clients only keep a small
   cache of media anyway (if any at all) - this proposal is written under the assumption that the
   primary use-case is users redacting their media soon after redacting an associated event,
   somewhat voiding this concern.
2. Abusive users may upload abusive media and then attempt to delete it after their victim
   has retrieved the media. This is remediated by retention, in a similar vein to redacted
   message retention.
3. This side-steps power level forbidden redaction mechanisms. This is seen as a
   technicality rather than a problem, since until #3911, media is not tied to events
   (and thus power levels) anyway.

## Alternatives

This proposal will be superseded by [MSC3911][3911] by nature,
however it fills a gap that is currently missing in functionality in a simpler,
easier to implement manner.

The suggestion for the method+route `DELETE /_matrix/client/v1/media/{server_name}/{media_id}`
has both been considered and suggested, however, the current layout for media controls looks like

1. `POST /media/create`
2. `POST /media/upload`
3. `PUT /media/upload/{sn}/{mid}`
4. `GET /media/download/{sn}/{mid}`
5. `GET /media/thumbnail/{sn}/{mid}`

So adding in `DELETE /media/{sn}/{mid}` would not fit the current pattern. Additionally,
`POST` is used instead of `DELETE`, since semantically speaking, there is already nothing at
`/media/redact/{server_name}/{media_id}`.

A future MSC may be created to unify the media endpoints, however in an effort to keep this MSC
as simple as possible, it will not be done here.

## Security considerations

As mentioned in [potential issues](#potential-issues), abusive users may upload abusive media,
and then redact it before an administrator can investigate. This is remediated by retention.

Additionally, implementations are forbidden from re-using MXC URIs, as without linked media,
there is no way to know if a URI is still referenced somewhere. As a result, if it is, and a new
piece of media replaces it, an attacker may be able to upload abusive media (such as malware) in
place of a previously trusted entity.

## Unstable prefix

| Stable | Unstable replacement |
| ------ | -------------------- |
| `/_matrix/client/v1/media/redact/{server_name}/{media_id}` | `/_matrix/client/unstable/uk.timedout.msc4322/media/redact/{server_name}/{media_id}` |
| `/_matrix/federation/v1/media/redact/{server_name}/{media_id}` | `/_matrix/federation/unstable/uk.timedout.msc4322/media/redact/{server_name}/{media_id}` |

## Dependencies

None

<!--        -->

[3911]: https://github.com/matrix-org/matrix-spec-proposals/pull/3911
[spec_redact]: https://spec.matrix.org/v1.15/client-server-api/#put_matrixclientv3roomsroomidredacteventidtxnid
[spec_s2s_download]: https://spec.matrix.org/v1.15/server-server-api/#get_matrixfederationv1mediadownloadmediaid
