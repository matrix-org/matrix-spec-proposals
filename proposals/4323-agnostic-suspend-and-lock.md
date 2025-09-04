# MSC4323: Agnostic user suspension & locking endpoints

Currently the specification outlines error codes for suspended and locked users,
even going as far as to suggest which endpoints can and cannot be executed by suspended users.
However, it does not currently define an endpoint which server administrators can call to suspend
and unsuspend users on their server.
As a result, moderation tooling such as Draupnir and Meowlnir have to implement
implementation-specific calls, which is not sustainable as more implementations other than Synapse
integrate this feature. This is also exacerbated by externally managed accounts that may be
provided by an entirely separate service.

This MSC will outline new endpoints that will allow server administrators to
suspend, unsuspend, lock, and unlock given users.

## Proposal

Note: what defines a "server administrator" is left up to the implementation,
most already have their own systems for defining administrators which rarely has a reason to be
exposed outside of their respective management interfaces.

Taking advantage of [section 10.22 (Server Administration)][p1] of the client-to-server specification,
four new endpoints are introduced:

- `GET /_matrix/client/v1/admin/suspend/{userId}`
- `PUT /_matrix/client/v1/admin/suspend/{userId}`
- `GET /_matrix/client/v1/admin/lock/{userId}`
- `PUT /_matrix/client/v1/admin/lock/{userId}`

These new endpoints complement the already existing
`/_matrix/client/v3/admin/whois/{userId}` endpoint, however, are restricted to only permitting
execution on local users.

The requests and responses are outlined as below. Custom properties may be used provided they
utilise proper namespacing.

The response body of both the `GET` and `PUT` endpoints, as well as the request body of the
`PUT` endpoint should be:

**Suspend**:

```json
{
  "$schema": "https://json-schema.org/draft-07/schema",
  "type": "object",
  "properties": {
    "suspended": {"type": "boolean"}
  },
  "required": ["suspended"]
}
```

For example:

```json
{"suspended": true}
```

**Lock**:

```json
{
  "$schema": "https://json-schema.org/draft-07/schema",
  "type": "object",
  "properties": {
    "locked": {"type": "boolean"}
  },
  "required": ["locked"]
}
```

For example:

```json
{"locked": false}
```

---

Sending a `GET` to the respective endpoints returns `404` with `M_NOT_FOUND` if the
requested user ID is not found. `400` and `M_INVALID_PARAM` is returned if the specified
user ID is valid, but not local to the server. `403` `M_FORBIDDEN` is returned if
the user is not a server administrator. To prevent enumeration, credentials are checked
before validity.

If a user is deactivated, `M_NOT_FOUND` is returned, as deactivated users are not
suspended nor locked, and typically are to be permanently treated as gone.

The server should advertise that these new endppints are available to the authenticated user
by including the following new capability:

```json5
{
  "capabilities": {
    "account_moderation": {
      "suspend": true, // or false
      "lock": true // or false
    }
  }
}
```

The server should only advertise these capabilities if the requesting user is a
server administrator, or otherwise has permission to suspend or lock users.

If the user is already in the state requested by a `PUT` request (e.g. a new
`PUT` request with `{"suspended":true}` is sent for a user that is already suspended),
the server should simply respond with `200 OK` as if a change was made. If metadata surrounding
the action was changed in the request (such as who locked the target), this should still be
reflected.

Servers may choose to retain implementation-specific versions of these endpoints, however should
still implement this uniform endpoint for compatibility.

[p1]: https://spec.matrix.org/v1.15/client-server-api/#server-administration

## Potential issues

This MSC does not outline any additional fields for management, such as action reasons,
temporary actions, etc, which implementation-specific methods may currently have.
This is for the sake of brevity and simplicity, and may be expanded upon
in a future proposal. If implementations need further data, they may use custom properties,
or retain their own endpoints and encourage operators to block these new ones.

## Alternatives

A full user-info endpoint has been suggested, which would include more information about a user's
account that could interest server administrators. While this may happen in future, it would
drastically increase the scope of this proposal and deliberately omitted.

## Security considerations

Server operators who may not want their administrators to be able to suspend/lock users may have
restricted access to implementation-specific endpoints, usually by preventing access at the reverse
proxy. Operators should keep this in mind and apply similar restrictions to these new endpoints
where appropriate.

## Unstable prefix

| Stable | Unstable |
| ------ | -------- |
| `/_matrix/client/v1/admin/...` | `/_matrix/client/unstable/uk.timedout.msc4323/admin/...` |
| `account_moderation` | `uk.timedout.msc4323` |

`locked` and `suspended` in the request/response bodies do not require an unstable prefix
as the entire body is new.

Servers should advertise `"uk.timedout.msc4323":true` in their `/versions` response while this
proposal is unstable. It is left as an implementation detail whether to require authentication
to view this version flag or not.

## Dependencies

None
