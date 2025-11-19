# MSC4034: Media limits API, space usage

The original purpose of the `/_matrix/media/v3/config` endpoint was to enable
clients to avoid media upload attempts that will be rejected by the server.
However, the `/_matrix/media/v3/config` endpoint provides only one field,
`m.upload.size`, denoting the maximum file size in bytes that the server will
allow for uploaded files. As noted in the [security
considerations](https://spec.matrix.org/latest/client-server-api/#security-considerations-5)
for the `/_matrix/media/` endpoints:

 > Clients may try to upload a large number of files. Homeservers should limit
 > the number and total size of media that can be uploaded by clients,
 > returning a HTTP 403 error with the `M_FORBIDDEN` code.

In other words, a client's upload may be rejected not only for individual file
size, but also if a total quota on number of files or disk usage has been reached.

This proposal introduces additional fields and endpoints to enable clients to
determine if media uploads may be rejected on the basis of quotas having been
reached. Furthermore,  if/when related proposals to improve privacy and client
control of media content make it into the spec, e.g.
[MSC3916](https://github.com/matrix-org/matrix-spec-proposals/pull/3916), the
endpoints in this proposal will allow clients to better manage the media they
have stored on their homeserver.

## Proposal

The `/_matrix/media/v3/config` endpoint will have two additional, optional
fields corresponding to the total storage space available to the user and the
total number of files the user can store. The 200 response becomes:

| Name | Type | Description |
| ---- | ---- | ----------- |
| `m.upload.size` | `integer` | The maximum size an upload can be in bytes. Clients SHOULD use this as a guide when uploading content. If not listed or null, the size limit should be treated as unknown. |
| `m.storage.size` | `integer` | The total allowable (free+used) storage space for the user in bytes.  If not listed or null, the size limit should be treated as unknown. |
| `m.storage.max_files` | `integer` | The maximum number of files the user may store. If not listed or null, the maximum number of files should be treated as unknown. |

Furthermore, we create a new endpoint `/_matrix/media/v3/usage` endpoint the
client can query to check how much storage has been used:

| Name | Type | Description |
| ---- | ---- | ----------- |
| `m.storage.used` | `integer` | The amount of storage space in bytes used up by the user's media content. If not listed or null, the remaining used space should be treated as unknown. |
| `m.storage.files` | `integer` | The number of files the user has stored on their homeserver. If not listed or null, the number of files stored should be treated as unknown. |

## Potential issues

The matrix spec does not presently recommend servers to keep a permanent record
of which `mxc://` URIs were uploaded by which user -- servers should only keep
track of how many pending uploads a user has. Some implementations, e.g.
Synapse, do this anyway so that it can provide a list of the user's files for
the admin endpoint. However, since all proposed fields are optional, the
endpoint can be added even to servers that do not wish to track which user
created which `mxc://` URIs.

## Alternatives

The alternative is the current approach, which is to just wait until the user
receives a 403 error code when attempting to upload new content. The drawback,
aside from not knowing that this will happen before attempting the upload, is
that the 403 error code on the `/_matrix/media/v3/upload` endpoint does not
specify the precise reason why the content is being rejected.

## Security considerations

None expected.

## Unstable prefix

The new endpoint can be made available at
`/_matrix/media/unstable/org.matrix.msc4034/usage`. The additional fields on
`/_matrix/media/v3/config` can be including in server responses using the `org.matrix.msc4034` namespace, e.g.

```
GET /_matrix/media/v3/config
{
  "m.upload.size": 1024,
  "org.matrix.msc4034.storage.used": 1024,
  "org.matrix.msc4034.storage.files": 10
}
```

## Dependencies

None.
