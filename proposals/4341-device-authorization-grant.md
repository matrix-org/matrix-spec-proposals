# MSC4341: Support for RFC 8628 Device Authorization Grant

The current [OAuth 2.0 API](https://spec.matrix.org/v1.15/client-server-api/#oauth-20-api) requires the user to complete
authentication using a web browser on the device where the Matrix client is running.

This can be problematic if the device does not have a built in web browser or the user wishes to use a different device.
It also causes issues in scenarios where catching the redirect back to the client is hard, like in CLI apps, or
desktop apps with no redirect custom schemes.

[RFC 8628](https://datatracker.ietf.org/doc/html/rfc8628) defines the OAuth 2.0 Device Authorization Grant which can be
used for this purpose.

## Proposal

Homeservers MAY advertise the [RFC 8628 OAuth 2.0 Device Authorization Grant](https://datatracker.ietf.org/doc/html/rfc8628) in the [list of supported
grant types](https://spec.matrix.org/v1.15/client-server-api/#grant-types) in the Client-Server API.

This grant requires the client to know the following authorization server metadata:

- `grant_types_supported` - this would include `urn:ietf:params:oauth:grant-type:device_code`
- `device_authorization_endpoint` - this would be added to the [table of fields for the 200 response](https://spec.matrix.org/v1.15/client-server-api/#server-metadata-discovery)
- `token_endpoint` - this is already included in the spec

To use this grant, homeservers and clients MUST:

- Support the device authorization grant as per RFC 8628.
- Support the refresh token grant.

The [login flow section](https://spec.matrix.org/v1.15/client-server-api/#login-flow) would need to be updated to
reflect that more than one login grant type exists.

As with the existing authorization code grant, when authorization is granted to a client, the homeserver MUST issue a
refresh token to the client in addition to the access token.

The access token and refresh token should have the same lifetime constraints as described for the authorization
code grant in the current [spec](https://spec.matrix.org/v1.15/client-server-api/#refresh-token-grant).

### Sample flow

The user wishes to login to a Matrix client on a device that doesn't have a web browser built in (e.g. a TV), but wishes
to complete the login on another device (e.g. a smartphone).

1. The Matrix client [discovers the OAuth 2.0 server metadata](https://spec.matrix.org/v1.15/client-server-api/#server-metadata-discovery).

This step is as per the current Matrix spec, but as per [RFC 8628 section 4](https://datatracker.ietf.org/doc/html/rfc8628#section-4)
it should include the value `urn:ietf:params:oauth:grant-type:device_code` in the `grant_types_supported` field and specify
a `device_authorization_endpoint` field.

2. The Matrix client  [registers itself as a client with the homeserver](https://spec.matrix.org/v1.15/client-server-api/#client-registration).

This step is as per the current Matrix spec.

3. The Matrix client sends a Device Authorization Request to the `device_authorization_endpoint` as per [RFC 8628 section 3.1](https://datatracker.ietf.org/doc/html/rfc8628#section-3.1).

The `client_id` should be as per the registration step above, and the `scope` as described in the current [spec](https://spec.matrix.org/v1.15/client-server-api/#scope).

e.g.

```http
POST /oauth2/device HTTP/1.1
Host: account.matrix.org
Content-Type: application/x-www-form-urlencoded

client_id=my_client_id&scope=urn%3Amatrix%3Aclient%3Aapi%3A%2A%20urn%3Amatrix%3Aclient%3Adevice%3AABCDEGH
```

4. The homeserver responds to the Matrix client with the Device Authorization Response as per [RFC 8628 section 3.2](https://datatracker.ietf.org/doc/html/rfc8628#section-3.2).

For example:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "device_code": "GmRhmhcxhwAzkoEqiMEg_DnyEysNkuNhszIySk9eS",
  "user_code": "WDJB-MJHT",
  "verification_uri": "https://account.matrix.org/link",
  "verification_uri_complete": "https://account.matrix.org/link?user_code=WDJB-MJHT",
  "expires_in": 1800,
  "interval": 5
}
```

It is recommended that the server provides a `verification_uri_complete` such that the user does not need to type in the
`user_code`.

5. The Matrix client device conveys the returned `verification_uri_complete` (and/or `verification_uri`+`user_code`) to
the user.

Exactly how the client does this depends on the specific device characteristics and use case.

For example, for a CLI application the `verification_uri` and `user_code` could be displayed as text for the user to
type into their other device.

Or, another example would be the `verification_uri_complete` (with fallback to the `verification_uri`) could be encoded
and displayed as a QR code for scanning on the other device (e.g. on a TV).

6. The user opens the `verification_uri_complete` (or `verification_uri`) on their other device that has a web browser.

The user then completes authentication and authorization for the login.

7. Whilst the user is doing this, the Matrix client starts polling the `token_endpoint` for an outcome.

Frequency of polling is determined by the `interval` value returned in the Device Authorization Response from step 4.

The poll request made by the client is the Device Access Token Request from [RFC 8628 section 3.4](https://datatracker.ietf.org/doc/html/rfc8628#section-3.4).

e.g.

```http
POST /oauth2/token HTTP/1.1
Host: account.matrix.org
Content-Type: application/x-www-form-urlencoded

grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Adevice_code&device_code=GmRhmhcxhwAzkoEqiMEg_DnyEysNkuNhszIySk9eS&client_id=my_client_id
```

The server in turn responds with the Device Access Token Response as per [RFC 8628 section 3.5](https://datatracker.ietf.org/doc/html/rfc8628#section-3.5).

Whilst the authorization is still outstanding a `authorization_pending` (or `slow_down` in the case of rate limiting)
error code will be returned.

If the authorization is rejected then the `access_denied` error code will be returned.

If the authorization does not complete within the `expires_in` timeframe then the `expired_token` error code will be returned.

For a successful authorization the response will be an access token and refresh token as described in the current Matrix
[spec](https://spec.matrix.org/v1.15/client-server-api/#login-flow).

8. The Matrix client refreshes the access token with the refresh token grant when it expires.

This is as per the current spec.

9. The Matrix client revokes the tokens when the users wants to log out of the client.

This is as per the current spec.

## Potential issues

Some literature refers to the Device Authorization Grant as the
[Device Code](https://oauth.net/2/grant-types/device-code/) grant type or [Device Flow](https://curity.io/resources/learn/oauth-device-flow/).
This MSC uses the name from the actual RFC.

Otherwise, none identified.

## Alternatives

I'm not aware of any other standardised OAuth grant types that would be suitable as an alternative.

### Requiring support for the new grant type

We could make it mandatory that new grant type is supported by Matrix homeservers.

As currently proposed it is optional and discoverable via the `grant_types_supported` metadata.

### Make `verification_uri_complete` be mandatory

RFC 8628 makes makes `verification_uri_complete` optional, but we could make it mandatory. This could improve the UX for some
use cases.

## Security considerations

[RFC 8628 section 5](https://datatracker.ietf.org/doc/html/rfc8628#section-5) contains various security considerations
that homeserver and client implementors should consider.

Additionally, [RFC 9700](https://datatracker.ietf.org/doc/html/rfc9700) Best Current Practice for OAuth 2.0 Security
mentions clickjacking as a consideration for the server and advises on appropriate measures.

## Unstable prefix

Although the response from the server metadata discovery endpoint is modified, because
[we already defined it](https://spec.matrix.org/v1.15/client-server-api/#get_matrixclientv1auth_metadata) as being
[RFC 8414](https://datatracker.ietf.org/doc/html/rfc8414) it isn't appropriate to introduce unstable prefixes.

## Dependencies

None.
