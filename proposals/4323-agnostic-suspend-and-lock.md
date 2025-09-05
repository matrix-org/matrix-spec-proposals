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

These new endpoints complement the already existing administrator-only endpoint,
[`/_matrix/client/v3/admin/whois/{userId}`][p2], however are restricted to only permitting
execution on local users.

The requests and responses are outlined as below. Custom properties may be used provided they
utilise [proper namespacing][p3].

### New endpoint definitions

The response body of both the `GET` and `PUT` endpoints, as well as the request body of the
`PUT` endpoints should be:

**Suspend**:

A single key, `suspended`, with a boolean indicating if the target account is suspended:

```json
{"suspended": true}
```

**Lock**:

A single key, `locked`, with a boolean indicating if the target account is locked:

```json
{"locked": false}
```

### New capability definition

The server should advertise that these new endpoints are available for the authenticated user
to actively use by including the following new capability:

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

This allows clients to determine whether they are able to suspend/lock users on this homeserver,
allowing them to do things like dynamically show or hide a "suspend user" button, etc.

Implementations may choose to allow disabling the capability advertisement if their configuration
disables the new endpoints altogether in some form, but how and when this happens is left to the
implementation.

### Errors and restrictions

Sending a `GET` to the respective endpoints returns:

- `400 / M_INVALID_PARAM`: The user ID does not belong to the local server.
- `403 / M_FORBIDDEN`: The requesting user is not a server administrator, is trying to suspend/lock
  their own account, or the target user is another administrator.
- `404 / M_NOT_FOUND`: The user ID is not found, or is deactivated.

In order to prevent user enumeration, implementations have to ensure that authorization is checked
prior to trying to do account lookups.

[p1]: https://spec.matrix.org/v1.15/client-server-api/#server-administration
[p2]: https://spec.matrix.org/v1.15/client-server-api/#get_matrixclientv3adminwhoisuserid
[p3]: https://spec.matrix.org/v1.15/appendices/#common-namespaced-identifier-grammar

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

These endpoints also increase the compromise value of an administrator account, as an attacker who
breaches one of these accounts will be able to suspend or lock other users on the server. While
the attacker would not be able to lock out other administrators, this may still result in
frustration for anyone affected by it. It may possibly also allow an attacker to disable other
room-level moderation tooling, such as moderation bots, presuming those tools are not also server
administrators.

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
