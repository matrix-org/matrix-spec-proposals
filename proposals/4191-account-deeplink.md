# MSC4191: Account management deep-linking

This proposal builds on the [OAuth 2.0 API](https://spec.matrix.org/v1.15/client-server-api/#oauth-20-api) that was
added in v1.15 of the spec.

This proposal introduce a way to deep-link to the account management capabilities of the homeserver to allow the user to
complete the account management operations in a browser independently of the client.

This proposal also attempts to resolve the issue that the API endpoints to delete devices are not supported when using
the OAuth 2.0 API.

## Proposal

### Additional authentication server metadata

This proposal introduces two new optional fields in the authentication
[server metadata discovery](https://spec.matrix.org/v1.15/client-server-api/#server-metadata-discovery):

- `account_management_uri`: the URL where the user is able to access the account management capabilities of the
   authentication server
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

Consequently for the destructive `org.matrix.session_end` and `org.matrix.account_deactivate` actions the server should
require re-authentication (or authentication through an additional factor) before allowing the user to complete the
action.

## Unstable prefixes

Whilst in development the fields in the server metadata discovery should be prefixed as follows:

- `org.matrix.msc4191.account_management_uri` instead of `account_management_uri`
- `org.matrix.msc4191.account_management_actions_supported` instead of `account_management_actions_supported`
