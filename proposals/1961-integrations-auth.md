# MSC1961: Integration manager authentication

A set of common APIs needs to be defined for clients to be able to interact with an integration
manager. This proposal covers the authentication portion of that API.

**Note**: this proposal is part of a larger "Integrations API" which has not yet been defined.
See [MSC1956](https://github.com/matrix-org/matrix-doc/pull/1956) for details.


## Proposal

All specified APIs (except `/register`) will take an `Authorization` header with a `Bearer` token returned
from a call to `/register`. This token is used to authorize the request and to identify who is making the
request. The token may also be specified as the `access_token` query string parameter, similar to the
Client-Server API.

#### POST `/_matrix/integrations/v1/account/register`

Exchanges an OpenID object for a token which can be used to authorize future requests to the manager.

Request body is an OpenID object as returned by `/_matrix/client/r0/user/:userId/openid/request_token`.

Response is:
```json
{
    "token": "OpaqueString"
}
```

The token should consist of URL-safe base64 characters. Integration managers should be careful to validate
the OpenID object by ensuring the `/_matrix/federation/v1/openid/userinfo` response has a `sub` which belongs
to the `matrix_server_name` provided in the original OpenID object.

Applications which register for a token are responsible for tracking which integration manager they are for.
This can usually be done by tracking the hostname of the integration manager and matching a token with it.

#### GET `/_matrix/integrations/v1/account`

Gets information about the token's owner, such as the user ID for which it belongs.

Besides a token, no other information is required for the request.

Response is:
```json
{
    "user_id": "@alice:example.org"
}
```

The `user_id` is the user ID which was represented in the OpenID object provided to `/register`. Integration
managers may be interested in also supplying information about the user's credit balance for paid integrations
here. Preferably, custom information is stored under a namespaced key like so:
```json
{
    "user_id": "@alice:example.org",
    "org.example.paid.integrations": {
        "credit": 20000
    }
}
```

#### POST `/_matrix/integrations/v1/account/logout`

Logs the token out, rendering it useless for future requests.

Request body is an empty object. Response body is also an empty object if successful.


## Security considerations

Clients should be sure to call `/logout` where possible when the user is logging out or no longer needs access
to a given manager. Clients should additionally be cautious about which managers they register for tokens with,
as some integration managers may be untrusted.
