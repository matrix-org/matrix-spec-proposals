# MSC3882: Allow an existing session to sign in a new session

In [MSC3906](https://github.com/matrix-org/matrix-spec-proposals/pull/3906) a proposal is made to allow a user to login
on a new device using an existing device by means of scanning a QR code.

In order to support the above proposal a mechanism is needed where by the new device can obtain a new access token that
it can use with the Client-Server API.

It is proposed that the current `m.login.token` mechanism is extended to allow the issuance of a login token by an
existing client session.

## Proposal

Add a new optional POST endpoint to the Client-Server API that issues a single-use, time-limited `m.login.token` token:

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

The availability of the new API endpoint should be determined via a new `m.get_logintoken`
[capability](https://spec.matrix.org/v1.6/client-server-api/#capabilities-negotiation).

This capability has a single flag, `enabled`, to denote whether the `/login/get_token` API is available or not.
Cases for disabling might include security restrictions imposed by the homeserver admin.

An example of the capability API’s response for this capability is:

```json
{
  "capabilities": {
    "m.get_logintoken": {
      "enabled": true
    }
  }
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

n.b. A homeserver admin may deem that they have suitable protections in place and offer the endpoint without UIA auth as described
in the existing spec:

> A request to an endpoint that uses User-Interactive Authentication never succeeds without auth. Homeservers may allow requests
> that don’t require auth by offering a stage with only the m.login.dummy auth type, but they must still give a 401 response to
> requests with no auth data.

## Unstable prefix

While this feature is in development the new endpoint should be exposed using the following unstable prefix:

- `/_matrix/client/unstable/org.matrix.msc3882/login/get_token`

The capability should use the unstable prefix:

- `org.matrix.msc3882.get_logintoken`

For reference - an earlier revision of this proposal used an unstable prefix of
`/_matrix/client/unstable/org.matrix.msc3882/login/token` with an unstable feature advertised as `org.matrix.msc3882`
set to `true`. This may be referred to as "revision zero" in existing implementations.

## Dependencies

None.
