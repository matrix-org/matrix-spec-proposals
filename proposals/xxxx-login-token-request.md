# MSCxxxx: Allow an existing session to sign in a new session

todo

## Proposal

Add a new POST endpoint to the Client-Server API that issues a time limited `m.login.token` token:

`POST /login/token`

```json
{
    "login_token": "<login token>",
    "expires_in": 3600
}
```

This new endpoint MAY be protected by user interactive authentication.

This token can then be used as per the existing Login spec of the Client-Server API as follows:

`POST /login`

```json
{
  "type": "m.login.token",
  "token": "<login token>"
}
```

## Potential issues

todo

## Alternatives

If Matrix was already using OIDC as per [MSC3861](https://github.com/matrix-org/matrix-spec-proposals/pull/3861) then we could use the device authorization grant flow which allows for a new device to be signed in using an existing device.

## Security considerations

A malicious client could use the mechanism to spawn more than one session. For this reason the endpoint can be placed behind user interactive authentication.

## Unstable prefix

tbd

## Dependencies

None.
