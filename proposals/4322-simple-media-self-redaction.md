# MSC4322: Simple Media Self-Redaction

Currently, clients are able to create MXCs and upload media, however, are unable to remove that
media without the help of a server administrator. As [MSC3911][3911] is still a ways away from being
finished, media is currently retained *forever*, even when the user deletes the event that
contained the media in the first place. This proposal outlines a simple method to allow clients
to redact their media at their discretion.

## Proposal

Note: "Redact" is used in the same sense as event redaction, i.e. the actual data is removed
and often made generally inaccessible, however the unique identifier and possibly metadata still
remains. You may also read "redact" as "delete" or "remove" in a higher level reading of this
proposal.

### Client-to-server changes

#### Delete media endpoint

A new client-to-server endpoint, `POST /_matrix/client/v1/media/redact/{server_name}/{media_id}`,
should be created. It should respond with a `200 OK` response, and an empty body upon success.

This endpoint must ensure that the user calling it is the same user that created the media URI,
or a user with an appropriate permission override (for example, a server administrator).
Implementations may choose to federate the media redaction (see
[server-to-server changes](#server-to-server-changes)), however should only do so when the media
URI belongs to the same server. If the media URI belongs to a different server, it should only
be deleted locally (and not re-fetched).

Implementations may rate-limit calls to the endpoint in order to prevent a user
causing strain on disk operations, however this is not required.

This endpoint should be treated similarly to the [redact event][spec_redact] endpoint, allowing
implementations to optionally retain the redacted media for a period of time, however choosing
not to serve it. This must not be read as a "quarantine", as redactions must be permanent, even
if delayed. Once a redaction has been made, if the server chooses to retain the media, it should
not be served to any clients, or federation requests. Susbequent requests to the redact endpoint
should be treated as a no-op, and the server should return a `200 OK` response
with an empty body.

For internal annotation, the redact endpoint may include an optional `reason` parameter.
This parameter should either be a string, or omitted entirely.

Implementations **must not** re-use MXC URIs which have been redacted.
See [security considerations](#security-considerations) for more information.

#### List media endpoint

Some clients may wish to provide clients with a way to list media that they have uploaded,
potentially in an effort to allow users to manage their media quota. Another, **optional**, endpoint is defined - `GET /_matrix/client/v1/media/list/{user_id}`.
Non-privileged users should only be able to list their own media, however privileged users
(such as server administrators) may be able to list media for other users.
Listing media of remote users must not be allowed, and should return a `400 Bad Request` response
with an error code of `M_INVALID_PARAM`.

This new endpoint should return an object of media IDs, following the following schema:

<details>
<summary>JSON Schema</summary>

```json
{
  "$schema": "https://json-schema.org/draft-07/schema",
  "type": "object",
  "properties": {
    "files": {
      "type": "object",
      "description": "",
      "properties": {
        "media_id_N": {
          "type": "object",
          "properties": {
            "size": {
              "type": "integer",
              "description": "Size on disk (in bytes)"
            },
            "filename": {
              "type": "string",
              "description": "The originally provided file name, if any"
            },
            "created_at": {
              "type": "number",
              "description": "The origin timestamp in unix milliseconds"
            }
          }
        }
      }
    }
  },
  "required": [
    "files"
  ]
}
```

</details>

For example:

```json
{
   "files": {
      "media_id_1": {
         "size": 123456,
         "filename": "example.jpg",
         "created_at": 1700000000000
      },
      "media_id_2": {
         "size": 654321,
         "created_at": 1700000001000
      }
   }
}
```

### Server-to-server changes

A new authenticated federation endpoint,
`POST /_matrix/federation/v1/media/redact/{server_name}/{media_id}`,
should be created in order to allow a server to notify other servers that a piece of media
has been redacted. The same rules apply as client-to-server (e.g. a server may retain the media),
however, the receiveing server **must** ensure that the calling server is the same server
that the media URI belongs to. For example, `a.example` cannot redact media that belongs to
`b.example`.

In order to know which servers to federate a redaction to, the server should take a log of which
servers download media (typically done by recording the origin of
the [`GET /_matrix/federation/v1/media/download/{media_id}`][spec_s2s_download] endpoint).
When a redaction is made, the server should then send a federation request to each of the servers
that has previously downloaded the media ID, notifying them that the media has been redacted.

## Potential issues

1. Clients are also not notified of media redactions, but most clients only keep a small
   cache of media anyway (if any at all) - this MSC is written under the assumption that the
   primary use-case is users redacting their media soon after redacting an associated event,
   voiding this concern.
2. Abusive users may upload abusive media and then attempt to delete it after their victim
   has retrieved the media. This is remediated by retention, in a similar vein to redacted
   message retention.
3. This side-steps power level forbidden redaction mechanisms. This is seen as a
   technicality rather than a problem, since until #3911, media is not tied to events
   (and thus power levels) anyway.

## Alternatives

This MSC will be superseded by [MSC3911][3911] by nature, however it fills a gap that is currently
missing in functionality in a simpler, easier to implement manner.

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
piece of media replaces it, an attacker may be able to strike lucky and engage a phishing attack
by making it appear as if a trusted member of a community had uploaded media that they had not.

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
