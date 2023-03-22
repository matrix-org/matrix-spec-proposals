# MSC3882: Allow an existing session to sign in a new session

In [MSC3906](https://github.com/matrix-org/matrix-spec-proposals/pull/3906) a proposal is made to allow a user to login
on a new device using an existing device by means of scanning a QR code.

In order to support the above proposal a mechanism is needed where by the new device can obtain a new access token that
it can use with the Client-Server API.

It is proposed that the current `m.login.token` mechanism is extended to allow the issuance of a login token by an
existing client session.

## Proposal

Add a new POST endpoint to the Client-Server API that issues a single-use, time-limited `m.login.token` token:

`POST /_matrix/client/v1/login/get_token`

The client should send an empty JSON object for the body of the `POST` request (apart from
the `auth` property used in user-interactive authentication).

As detailed in the security selection below, this new endpoint should be protected by user interactive authentication
(UIA) as detailed in the existing
["User-interactive API in the REST API"](https://spec.matrix.org/v1.5/client-server-api/#user-interactive-api-in-the-rest-api)
section of the spec.

Once UIA has been completed a `200` response with JSON body is returned. The body contains the following fields:

- `login_token` - required, the token to use with `m.login.token`
- `expires_in_ms` - required, how long until the token expires in milliseconds

An example response is as follows:

```http
HTTP/1.1 200 OK
Content-Type: application/json
```

```json
{
    "login_token": "<login token>",
    "expires_in_ms": 120000
}
```

This token can then be used as per the existing [Login spec](https://spec.matrix.org/v1.6/client-server-api/#login) as follows:

```http
POST /_matrix/client/v3/login HTTP/1.1
Content-Type: application/json
```

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

A malicious client could use the mechanism to spawn more than one session. The following mitigations should be applied:

1. The homeserver must only allow the token to be used for a single login. If the user wishes to sign in multiple
 additional clients a token must be issued for each client.

2. The homeserver should enforce
[user interactive authentication](https://spec.matrix.org/v1.6/client-server-api/#user-interactive-authentication-api)
by default for the new endpoint. The purpose being that consent is obtained from the user for each additional client.

3. The homeserver should enforce rate-limiting in accordance with the existing
[spec](https://spec.matrix.org/v1.6/client-server-api/#rate-limiting). It may be appropriate for the homeserver admin to
to configure a low limit ("low" relative to other enforced limits). For example, a rate of once per minute could be appropriate.

If a homeserver admin deems that they have a suitable alternative to UIA in place, they can make use of
["dummy auth"](https://spec.matrix.org/v1.6/client-server-api/#dummy-auth) and have the homeserver respond with a response similar to:

```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json
```

```json
{
  "flows": [
    {
      "stages": ["m.login.dummy"]
    }
  ],
  "params": {},
  "session": "xxxxxx"
}
```

The client can then complete UIA without requiring action from the user by sending the following JSON request body:

```http
POST /_matrix/client/v1/login/get_token HTTP/1.1
Content-Type: application/json
```

```json
{
  "auth": {
    "type": "m.login.dummy",
    "session": "xxxxxx"
  }
}
```

## Unstable prefix

While this feature is in development the new endpoint should be exposed using the following unstable prefix:

- `/_matrix/client/unstable/org.matrix.msc3882/login/get_token`

Additionally, the feature is to be advertised as unstable feature in the `GET /_matrix/client/versions` response, with
the key `org.matrix.msc3882.r1` set to `true`. (The `r1` in the feature name is used to indicate that the server implements the first revision of this proposal)

So, the response could look then as following:

```json
{
    "versions": ["r0.6.0"],
    "unstable_features": {
        "org.matrix.msc3882.r1": true
    }
}
```

For reference - an earlier iteration of this proposal used an unstable prefix of
`/_matrix/client/unstable/org.matrix.msc3882/login/token` with an unstable feature advertised as `org.matrix.msc3882`
set to `true`.

## Dependencies

None.
