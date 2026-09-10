# MSC4540: `m.admin` capability

The Matrix specification has a concept of a "server admin": a special class of user with the ability to use
administrative functionality on their homesever, such as the [Server Administration] endpoints.
This proposal adds a new capability that clients may use to determine if their user is a server admin
and may access administrative functionality.

## Proposal

A new `m.admin` capability is introduced, with these top-level fields:

| Name             | Type       | Description                                                                  |
| ---------------- | ---------- | ---------------------------------------------------------------------------- |
| `legacy_access`  | `boolean`  | Whether this legacy device may use all admin functionality.                  |
| `allowed_scopes` | `[string]` | The admin scopes this OAuth device may request using step-up authentication. |

For devices using legacy authentication:
- The server MUST supply the `legacy_access` field. The server MUST NOT supply the `allowed_scopes` field.
- If the `legacy_access` field is `true`, the device is permitted to access all Matrix functionality
  that is restricted to server admins, including but not limited to the Server Administration endpoints.
  The client SHOULD use the value of `legacy_access` to show or hide UI for interacting with administrative
  functionality.
- If the `m.admin` capability is not present, the device MUST behave as if `legacy_access` is `false`.

For devices using OAuth authentication:
- The server MUST supply the `allowed_scopes` field. The server MUST NOT supply the `legacy_access` field.
- The strings in the `allowed_scopes` field are scopes that the device may request, using OAuth step-up authentication
  as defined in [MSC4363], to access administrative functionality. The exact functionality enabled depends on
  the scope.
- The client SHOULD show or hide UI for interacting with administrative functionality based off the scopes
  listed in `allowed_scopes`. It SHOULD NOT show UI that would require a scope that is not listed in `allowed_scopes`.
  When interacting with such UI, the client will need to use step-up authentication to request any applicable scopes
  before attempting to perform administrative actions.
- The client MAY indicate in its UI that the authorized user is a server administrator if `allowed_scopes` is not empty.
- If the `m.admin` capability is not present, the device MUST behave as if `allowed_scopes` is empty.

Although step-up authentication can be used with any OAuth scope, `allowed_scopes` is only intended to include scopes
pertaining to server administration. These scopes are special in that the server may unilaterally refuse to grant
them to clients if the authorizing user is not actually a server administrator.
Scopes for other purposes should generally be granted as long as the user consents, so there would be no reason to
list them in a capability.

At the time of writing, the only OAuth scope which provides access to administrative functionality is the
`urn:matrix:client:server_administration` scope proposed in [MSC4484]. If this scope, or its unstable identifier,
is present in `allowed_scopes`, clients SHOULD show all UI pertaining to the Server Administration endpoints.

## Potential issues

This proposal assumes that, for legacy authentication, a user may either use all administrator functionality
or none of it. Because legacy authentication does not have a mechanism for scoped access, this is deemed to be
an acceptable compromise.

## Alternatives

Clients could show administrative UI by default and make administrative requests sight unseen, as they do
today. This creates a poor user experience by showing users buttons that don't work, an issue which
this proposal seeks to alleviate.

## Security considerations

This proposal does not affect the actual process of authenticating a user in any way, and merely
provides a more direct way for clients to determine if they _could_ perform administrative actions
that doesn't require a "try it and see" approach. Therefore, it has no impact on security.

## Unstable prefix

While this proposal is unstable, the following unstable identifiers should be used:

| Stable    | Unstable                         |
| --------- | -------------------------------- |
| `m.admin` | `org.continuwuity.msc4540.admin` |

No unstable feature flag is necessary, as the presence of the `org.continuwuity.msc4540.admin`
capability indicates that a server supports this MSC. If the capability is not present, clients
should behave as they do today.

## Dependencies

This proposal depends on [MSC4484] and [MSC4363].

[Server Administration]: https://spec.matrix.org/v1.19/client-server-api/#server-administration
[BooleanCapability]: https://spec.matrix.org/v1.19/client-server-api/#get_matrixclientv3capabilities_response-200_booleancapability
[MSC4484]: https://github.com/matrix-org/matrix-spec-proposals/pull/4484
[MSC4363]: https://github.com/matrix-org/matrix-spec-proposals/pull/4484