# MSC4540: `m.admin` capability

The Matrix specification has a concept of a "server admin": a special class of user with the ability to use
administrative functionality on their homesever, such as the [Server Administration] endpoints.
This proposal adds a new [capability] that clients may use to determine if their user is a server admin
and may access administrative functionality.

## Proposal

A new `m.admin` capability is introduced, with these top-level fields:

| Name             | Type       | Description                                 |
| ---------------- | ---------- | ------------------------------------------- |
| `allowed_scopes` | `[string]` | The admin scopes this client has access to. |

If the `m.admin` capability is not present, the client MUST behave as if it is present and `allowed_scopes` is empty.

The strings in the `allowed_scopes` field are OAuth scopes representing the administrative functionality that the
server will allow the client to access. If the client authenticated using OAuth authentication, it MUST use OAuth
step up authentication, as outlined in [MSC4363], to request one or more of the listed scopes before it attempts
to access administrative functionality. Otherwise, if the client authenticated using legacy authentication, it SHOULD
assume that it already has access to any administrative functionality protected by the listed scopes. In all cases,
the client MUST NOT attempt to access administrative functionality protected by a scope which is not listed.

The client SHOULD show or hide UI for interacting with administrative functionality based off the scopes
listed in `allowed_scopes`. It SHOULD NOT show UI that would require a scope that is not listed in `allowed_scopes`.
When interacting with such UI, the client will need to use step-up authentication to request any applicable scopes
before attempting to perform administrative actions.

The client MAY indicate in its UI that the authorized user is a server administrator if `allowed_scopes` is not empty.

Although step-up authentication can be used with any OAuth scope, `allowed_scopes` is only intended to include scopes
pertaining to server administration. These scopes are special in that the server may unilaterally refuse to grant
them to clients if the authorizing user is not actually a server administrator.
Scopes for other purposes should generally be granted as long as the user consents, so there would be no reason to
list them in a capability.

At the time of writing, the only OAuth scope which provides access to administrative functionality is the
`urn:matrix:client:server_administration` scope proposed in [MSC4484]. If this scope, or its unstable identifier,
is present in `allowed_scopes`, clients SHOULD show all UI pertaining to the Server Administration endpoints.

The [`m.account_moderation` capability] is superseded by `m.admin` and should be deprecated for removal in a future
spec version.

## Potential issues

Clients using legacy authentication must have at least a limited understanding of OAuth scopes and their meanings
to understand the `m.admin` capability. Since legacy authentication is rapidly being phased out, this is deemed
to be an acceptable compromise.

## Alternatives

Clients could show administrative UI by default and make administrative requests sight unseen, as they do
today. This creates a poor user experience by showing users buttons that don't work, an issue which
this proposal seeks to alleviate.

More fields could be added to the existing `m.account_moderation` capability. This could work fine
for legacy devices, but it does not cleanly map to allowed scopes for OAuth devices, meaning that
clients supporting OAuth either have to infer which scopes are allowed from the fields on `m.account_moderation`
or blindly attempt to acquire scopes as they do today.

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

[capability]: https://spec.matrix.org/v1.19/client-server-api/#capabilities-negotiation
[Server Administration]: https://spec.matrix.org/v1.19/client-server-api/#server-administration
[BooleanCapability]: https://spec.matrix.org/v1.19/client-server-api/#get_matrixclientv3capabilities_response-200_booleancapability
[MSC4484]: https://github.com/matrix-org/matrix-spec-proposals/pull/4484
[MSC4363]: https://github.com/matrix-org/matrix-spec-proposals/pull/4363
[`m.account_moderation` capability]: https://spec.matrix.org/v1.19/client-server-api/#get_matrixclientv3capabilities_response-200_accountmoderationcapability