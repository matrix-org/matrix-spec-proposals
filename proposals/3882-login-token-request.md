# MSC3882: Allow an existing session to sign in a new session

In [MSC3906](https://github.com/matrix-org/matrix-spec-proposals/pull/3906) a proposal is made to allow a user to login
on a new device using an existing device by means of scanning a QR code.

In order to support the above proposal a mechanism is needed where by the new device can obtain a new access token that
it can use with the Client-Server API.

It is proposed that the current `m.login.token` mechanism is extended to allow the issuance of a login token by an
existing client session.

## Proposal

Add a new POST endpoint to the Client-Server API that issues a time limited `m.login.token` token:

`POST /login/token`

```json
{
    "login_token": "<login token>",
    "expires_in": 120
}
```

This new endpoint should be protected by user interactive authentication (UIA). However the the homeserver admin may
choose to disable UIA if they deem suitable alternative protections are in place.

The values returned are:

- `login_token` - required, the token to use with `m.login.token`
- `expires_in` - required, how long until the token expires in seconds

This token can then be used as per the existing [Login spec](https://spec.matrix.org/v1.6/client-server-api/#login) as follows:

`POST /login`

```json
{
  "type": "m.login.token",
  "token": "<login token>"
}
```

## Potential issues

None identified.

## Alternatives

If Matrix was already using OIDC as per [MSC3861](https://github.com/matrix-org/matrix-spec-proposals/pull/3861) then we
could use the device authorization grant flow which allows for a new device to be signed in using an existing device.

## Security considerations

A malicious client could use the mechanism to spawn more than one session. For this reason the endpoint should by default
be placed behind user interactive authentication.

## Unstable prefix

While this feature is in development the new endpoint should be exposed using the following unstable prefix:

- `/_matrix/client/unstable/org.matrix.msc3882/login/token`

Additionally, the feature is to be advertised as unstable feature in the `GET /_matrix/client/versions`
response, with the key `org.matrix.msc3882` set to `true`. So, the response could look then as
following:

```json
{
    "versions": ["r0.6.0"],
    "unstable_features": {
        "org.matrix.msc3882": true
    }
}
```

## Dependencies

None.
