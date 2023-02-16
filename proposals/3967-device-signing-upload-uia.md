# MSC3967: Do not require UIA when first uploading cross signing keys

When a user first sets up end-to-end encryption cross-signing, their client uploads their cross-signing keys to the server.

This [upload operation](https://spec.matrix.org/v1.6/client-server-api/#post_matrixclientv3keysdevice_signingupload) requires a higher level of security by applying User-Interactive Auth (UIA) to the endpoint.

This creates a usability issue at the point of user registration where a client will typically want to immediately set up cross-signing for a new user.

The issue is that the client will immediately need the user to re-authenticate even though the user just authenticated.

This usability issue has given rise to workarounds such as a [configurable grace period](https://matrix-org.github.io/synapse/latest/usage/configuration/config_documentation.html#ui_auth) (`ui_auth`.`session_timeout`) in Synapse whereby UIA will not be required for uploading cross-signing keys where authentication has taken place recently.

This proposal aims to provide for a standard way to address this UIA usability issue with respect to setting up cross-signing.

## Proposal

For the `POST /_matrix/client/v3/keys/device_signing/upload` endpoint the Homeserver should only require User-Interactive authentication (UIA) if a user has an existing cross-signing master key uploaded to the Homeserver.

## Potential issues

The Client-Server API [spec](https://spec.matrix.org/v1.6/client-server-api/#user-interactive-api-in-the-rest-api) states:

> A request to an endpoint that uses User-Interactive Authentication never succeeds without auth. Homeservers may allow requests that don’t require auth by offering a stage with only the m.login.dummy auth type, but they must still give a 401 response to requests with no auth data.

Does this mean that the endpoint can't simply give back a `200` response in the case that `auth` was not given as an input? If this is case then the existing Synapse behaviour of allowing a UIA grace period is probably also non-compliant.

## Alternatives

There has been some discussion around how to improve the usability of cross-signing more generally. It may be that an alternative solution is to provide a way to set up cross-signing in a single request.

## Security considerations

This change could be viewed as a degradation of security at the point of setting up cross-signing in that it requires less authentication to upload cross-signing keys on first use.

However, this degradation needs to be weighed against the typical real world situation where a Homeserver will be appling a grace period and so allow a malicious actor to bypass UIA for a period of time after each authentication.

## Unstable prefix

Not applicable as a client behaviour need not change.

## Dependencies

None.
