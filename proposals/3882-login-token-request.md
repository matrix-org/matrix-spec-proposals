# MSC3882: Allow an existing session to sign in a new session

In [MSC3906](https://github.com/matrix-org/matrix-spec-proposals/pull/3906) a proposal is made to allow a user to login
on a new device using an existing device by means of scanning a QR code.

In order to support the above proposal a mechanism is needed where by the new device can obtain a new access token that
it can use with the Client-Server API.

It is proposed that the current `m.login.token` mechanism is extended to allow the issuance of a login token by an
existing client session.

## Proposal

### New API endpoint POST /login/get_token

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

### Determining the availability of the new API endpoint

As this new API endpoint is optional, clients should determine whether the endpoint is available
before prompting the user to try using it.

There are two usage scenarios to consider:

1. The user wishes to sign in on a Matrix client.
2. The user wishes to use an already signed in Matrix client to sign in another client.

In scenario 2 the client is already authenticated. For scenario 1 the client is not yet authenticated.

#### Scenario 1: The user wishes to sign in on a Matrix client

The client wants to determine if it *may* be possible to sign in by getting a login token from an
existing session.

It is proposed that the unauthenticated client can determine if the new API endpoint *may* be available
as part of the existing
[`GET /_matrix/client/v3/login`](https://spec.matrix.org/v1.6/client-server-api/#get_matrixclientv3login)
API endpoint.

As the `m.login.token` mechanism is used to redeem the login token, the client can first determine if the
`m.login.token` is advertised as a flow in the `GET /_matrix/client/v3/login` response. Then it can check a
new boolean field `get_login_token` to determine if the capability *may* be available.

An example of the proposed `GET /_matrix/client/v3/login` response is:

```json
{
  "flow": [
    {
      "type": "m.login.token",
      "get_login_token": true
    }
  ]
}
```

In this case the mechanism could be available and so the client could prompt the user to try using it.

#### Scenario 2: The user wishes to use an already signed in Matrix client to sign in another client

The client is already authenticated. The client can determine whether it is able and allowed to sign in
another client by checking the
[capabilities](https://spec.matrix.org/v1.6/client-server-api/#capabilities-negotiation)
advertised by the homeserver.

Where the client is authenticated the client can determine whether the new API endpoint is available
via the [capability negotiation](https://spec.matrix.org/v1.6/client-server-api/#capabilities-negotiation)
mechanism.

The homeserver can then decide on a per user basis if the capability is available or not. For example,
it could implement a policy based on some risk criteria around the user’s account, session, or device.

A new capability `m.get_login_token` is proposed. This capability has a single boolean flag, `enabled`, to
denote whether the `/login/get_token` API is available or not.

An example of the capability API’s response for this capability is:

```json
{
  "capabilities": {
    "m.get_login_token": {
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

While this feature is in development the following unstable prefixes should be used:

- API endpoint `/_matrix/client/v1/login/get_token` => `/_matrix/client/unstable/org.matrix.msc3882/login/get_token`
- capability `m.get_login_token` => `org.matrix.msc3882.get_login_token`
- login flow field `get_login_token` => `org.matrix.msc3882.get_login_token`

For reference - an earlier revision of this proposal used an unstable prefix of
`/_matrix/client/unstable/org.matrix.msc3882/login/token` with an unstable feature advertised 
in the response to `GET /_matrix/client/versions` as `org.matrix.msc3882`
set to `true`. This may be referred to as "revision zero" in existing implementations.

## Dependencies

None.
