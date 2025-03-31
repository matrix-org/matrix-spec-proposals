# MSC4191: Account management deep-linking

This proposal is part of the broader [MSC3861: Next-generation auth for Matrix, based on OAuth 2.0/OIDC](https://github.com/matrix-org/matrix-spec-proposals/pull/3861).

With the move to the next-generation auth, the homeserver no longer provide dedicated endpoints to perform account management actions.
This proposal introduce a way to deep-link to the account management capabilities of the homeserver.

## Proposal

### Additional authentication server metadata

This proposal introduces two new fields in the authentication server metadata:

- `account_management_uri`: the URL where the user is able to access the account management capabilities of the authentication server
- `account_management_actions_supported`: a JSON array of actions that the account management URL supports

Note that the intent of this proposal is to potentially end up in a OpenID Connect specification, or at least formally registered in the [IANA Registry for Server Metadata](https://www.iana.org/assignments/oauth-parameters/oauth-parameters.xhtml#authorization-server-metadata).
This is why the metadata fields are not prefixed with `org.matrix.`, but the actions themselves are.

### Possible actions

The following actions are defined by this MSC:

- `org.matrix.profile` - The user wishes to view their profile (name, avatar, contact details).
- `org.matrix.sessions_list` - The user wishes to view a list of their sessions.
- `org.matrix.session_view` - The user wishes to view the details of a specific session.
- `org.matrix.session_end` - The user wishes to end/logout a specific session.
- `org.matrix.account_deactivate` - The user wishes to deactivate their account.
- `org.matrix.cross_signing_reset` - The user wishes to reset their cross-signing keys.

Subsequent MSCs may extend this list.

### Account management URL parameters

The account management URL may accept the following additional query parameters:

- `id_token_hint` - An ID Token that was previously issued to the client; the issuer uses it as a hint for which user is requesting to manage their account.
  If the requesting user is not logged in then it is used as a login hint; if a different user/identity is already logged in then warn the user that they are accessing a different account.
- `action` - Can be used to indicate the action that the user wishes to take, as defined above.
- `device_id` - This can be used to identify a particular session for `session_view` and `session_end`. This is the Matrix device ID.

For example, if a user wishes to sign out a session for the device `ABCDEFGH` where the advertised account management URL was `https://account.example.com/myaccount` the client could open a link to `https://account.example.com/myaccount?action=org.matrix.session_end&device_id=ABCDEFGH`.

Not all actions need to be supported by the account management URL, and the client should only use the actions advertised in the `account_management

## Alternatives

### Keep the current capabilities

XXX

### Advertise the account management capabilities in the well-known discovery

XXX

### Advertise the account management capabilities in a C-S API endpoint

XXX

## Security considerations

TBD

## Unstable prefixes

TBD
