# MSC4323: Agnostic user suspension & locking endpoints

Currently the specification outlines error codes for suspended and locked users,
even going as far as to suggest which endpoints can and cannot be executed by suspended users.
However, it does not currently define an endpoint which server administrators can call to suspend
and unsuspend users on their server.
As a result, moderation tooling such as Draupnir and Meowlnir have to implement
implementation-specific calls, which is not sustainable as more implementations other than Synapse
integrate this feature.

This proposal will outline new endpoints that will allow server administrators to
suspend, unsuspend, lock, and unlock given users.

## Proposal

> [!IMPORTANT]
> What defines a "server administrator" is left up to the implementation itself as most already have
> their own systems for defining administrators (e.g. Synapse has a database flag, Conduit has room
> membership) which rarely has a reason to be exposed outside of their respective management
> interfaces.

Complementing [section 10.22 (Server Administration)][p1] of the client-to-server specification,
four new endpoints are introduced:

- `GET /_matrix/client/v1/admin/suspend/{userId}`
- `PUT /_matrix/client/v1/admin/suspend/{userId}`
- `GET /_matrix/client/v1/admin/lock/{userId}`
- `PUT /_matrix/client/v1/admin/lock/{userId}`

These new endpoints are similar to [`GET /_matrix/client/v3/admin/whois/{userId}`][p2] in that they
are clearly defined as administration endpoints, however are restricted to only permitting
execution on local server users.

### New endpoint definitions

The response body of both the `GET` and `PUT` endpoints, as well as the request body of the
`PUT` endpoints, are defined below. Custom properties may be used provided they utilise
[proper namespacing][p3] in their fields.

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

The server can advertise that these new endpoints are available for the authenticated user
to actively use by including the following new capability:

```json5
{
  "capabilities": {
    "account_moderation": {
      "suspend": true, // or false if unavailable/unimplemented
      "lock": true // or false if unavailable/unimplemented
    }
  }
}
```

This allows clients to determine whether they are able to suspend/lock users on this homeserver,
allowing them to do things like dynamically show or hide a "suspend user" button, etc.

The capability should not be advertised at all if both `suspend` and `lock` would be `false`.
Omitting a key is equivalent to it being `false`.

### Errors and restrictions

Sending a request to the respective endpoints returns:

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

This proposal does not outline any metadata fields for management, such as action reasons,
temporary actions, authors, etc, which implementation-specific methods may currently have.
This is for the sake of brevity and simplicity, and may be expanded upon by a future proposal.

This proposal is also written under the assumption that all server administrators are equal, and
cannot be suspended or locked. If a server permits such actions against a privileged user, without
stripping their privileges, conflicting behaviours may be encountered.

## Alternatives

A full "user-info" endpoint has been suggested, which would include more information about a user's
account that could interest server administrators. This proposal focuses solely on providing
tooling with the capability to suspend and lock without needing to maintain several
implementation-specific versions of their code, and adding a full-fleged user-info endpoint is
almost entirely out of scope.

## Security considerations

Adding these new endpoints may provide a path to circumvent restrictions previously imposed on
implementation-specific versions of the suspend and lock endpoints (such as them being blocked off
at the reverse proxy) - server developers will likely want to ensure that their users are made
appropriate aware of this (via release notes or some other similar high-visibility channel) so that
they can apply those same restrictions to these new endpoints if necessary.

These endpoints also increase the compromise value of an administrator account, as an attacker who
breaches one of these accounts will be able to suspend or lock other users on the server. While
the attacker would not be able to lock out other administrators, a single-administrator homeserver
may be vulnerable to a temporary takeover if the sole administrator account is breached and
the deployment cannot be secured & have the change reverted quickly.
It may possibly also allow an attacker to disable other room-level moderation tooling, such as
moderation bots, assuming those tools are not also server administrators.

## Unstable prefix

| Stable | Unstable |
| ------ | -------- |
| `/_matrix/client/v1/admin/...` | `/_matrix/client/unstable/uk.timedout.msc4323/admin/...` |
| `account_moderation` | `uk.timedout.msc4323` |

`locked` and `suspended` in the request/response bodies do not require an unstable prefix
as the entire body is new.

Servers should advertise `"uk.timedout.msc4323":true` in their `/versions` response while this
proposal is unstable in order to advertise support for this new feature.
It is left as an implementation detail whether to require authentication to view this version flag
or not, as the capabilities endpoint requires authentication regardless.

## Dependencies

None
