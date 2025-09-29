# MSC4191: Account management for OAuth 2.0 API

This proposal builds on the [OAuth 2.0 API](https://spec.matrix.org/v1.15/client-server-api/#oauth-20-api) that was
added in v1.15 of the spec.

The current spec makes reference to the "homeserver's web UI" in several places without defining how that is discovered
nor what you can use it for.

This proposal defines how that discovery happens and a way to deep-link to the account management capabilities of the
homeserver to allow the user to complete the account management operations in a browser independently of the client.

In doing so, this proposal also resolves the issue that there is currently no specced way to delete devices using the
OAuth 2.0 API (because the API endpoints to delete devices are not supported when using the OAuth 2.0 API).

## Proposal

### Additional authentication server metadata

This proposal introduces two new optional fields in the authentication
[server metadata discovery](https://spec.matrix.org/v1.15/client-server-api/#server-metadata-discovery):

- `account_management_uri`: the URL where the user is able to access the account management capabilities of the
   homeserver. This is what is currently referred to as the "homeserver's web UI"
- `account_management_actions_supported`: a JSON array of actions that the account management URL supports

Note that the intent of this proposal is for these values to potentially end up in a OpenID Connect specification, or at
least formally registered in the
[IANA Registry for Server Metadata](https://www.iana.org/assignments/oauth-parameters/oauth-parameters.xhtml#authorization-server-metadata).
This is why the metadata fields are not prefixed with `org.matrix.`, but the actions themselves are.

### Possible actions

The following actions are defined by this MSC:

- `org.matrix.profile` - The user wishes to view/edit their profile (name, avatar, contact details).
- `org.matrix.sessions_list` - The user wishes to view a list of their sessions.
- `org.matrix.session_view` - The user wishes to view the details of a specific session.
- `org.matrix.session_end` - The user wishes to end/logout a specific session.
- `org.matrix.account_deactivate` - The user wishes to deactivate their account.

Subsequent MSCs may extend this list.

### Account management URL parameters

The account management URL (as provided above) may accept the following additional query parameters:

- `action` - Can be used to indicate the action that the user wishes to take, as defined above.
- `device_id` - This can be used to identify a particular session for `org.matrix.session_view` and
  `org.matrix.session_end`. This is the Matrix device ID.

For example, if a user wishes to sign out a session for the device `ABCDEFGH` where the advertised
`account_management_uri` was `https://account.example.com/myaccount` the client could open a link to
`https://account.example.com/myaccount?action=org.matrix.session_end&device_id=ABCDEFGH`.

Not all actions need to be supported by the account management URL, and the client should only use the actions
advertised in the `account_management_actions_supported` array.

## Alternatives

### Add UIA support to OAuth 2.0 API so that the existing delete devices endpoints can be used

n.b. This isn't a complete alternative to this full MSC and instead just considers an alternative way for device
deletion to happen.

The following endpoints are currently not supported when using the OAuth 2.0 API:

- `POST /_matrix/client/v3/delete_devices`
- `DELETE /_matrix/client/v3/devices/{deviceId}`

The reason given in the spec is:

> **WARNING**: Since this endpoint uses User-Interactive Authentication, it cannot be used when the access token
> was obtained via the OAuth 2.0 API.

As an alternative to the proposed `org.matrix.session_end` action the above device deletion endpoints could be instead
be used *if* the [User-interactive API](https://spec.matrix.org/v1.15/client-server-api/#user-interactive-api-in-the-rest-api)
was compatible with the OAuth 2.0 API.

### Advertise the account management capabilities in the well-known discovery

An earlier iteration of [MSC2965](https://github.com/matrix-org/matrix-spec-proposals/pull/2965) (which formed part of
the current OAuth 2.0 API) proposed using a
[well-known style discovery mechanism](https://github.com/sandhose/matrix-spec-proposals/blob/msc/sandhose/oidc-discovery/proposals/2965-auth-metadata.md#discovery-via-existing-well-known-mechanism)
for the account management URL.

For consistency it is proposed that the
[server metadata discovery](https://spec.matrix.org/v1.15/client-server-api/#server-metadata-discovery) API is used
instead.

### Advertise the account management capabilities in a C-S API endpoint

The metadata could be advertised in a metadata endpoint separate to the
[server metadata discovery](https://spec.matrix.org/v1.15/client-server-api/#server-metadata-discovery) mechanism.

## Security considerations

For the `org.matrix.session_end` action the
[security considerations](https://spec.matrix.org/v1.15/client-server-api/#security-considerations-6) that are already
stated for device management apply.

Consequently for the destructive `org.matrix.session_end` and `org.matrix.account_deactivate` actions the server SHOULD
require re-authentication (or authentication through an additional factor) before allowing the user to complete the
action.

Because the format of these links are public and the device IDs are visible to other Matrix users it is trivial for an
attacker to craft a "malicious" link that targets a destructive action. To mitigate this risk, for the destructive
actions (`org.matrix.session_end` and `org.matrix.account_deactivate`) the server MUST inform the user of what the
action is prior to it being executed (in addition to any re-authentication as above).

## Unstable prefixes

Whilst in development the fields in the server metadata discovery should be prefixed as follows:

- `org.matrix.msc4191.account_management_uri` instead of `account_management_uri`
- `org.matrix.msc4191.account_management_actions_supported` instead of `account_management_actions_supported`
