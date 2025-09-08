# MSC2964: Usage of OAuth 2.0 authorization code grant and refresh token grant

This proposal is part of the broader [MSC3861: Next-generation auth for Matrix, based on OAuth 2.0/OIDC][MSC3861].

This MSC in particular defines how clients can leverage the OAuth 2.0 authorization code grant to gain access to the Matrix Client-to-Server API.

## Proposal

### Prerequisites

This proposal requires the client to know the following authorization server metadata about the homeserver:

- `authorization_endpoint`: the URL where the user should be sent to initiate the login flow
- `token_endpoint`: the URL where the client is able to exchange the authorization code for an access token
- `response_types_supported`: a JSON array of response types supported by the authorization endpoint
- `grant_types_supported`: a JSON array of grant types supported by the authorization endpoint defined in [RFC8414] and used in [RFC6749]
- `response_mode_supported`: a JSON array of response modes supported by the authorization endpoint

All of those metadata values are well-defined in [RFC8414] and used in various RFCs like [RFC6749].

The discovery of the above metadata is out of scope for this MSC, and is currently covered by [MSC2965](https://github.com/matrix-org/matrix-doc/pull/2965).

The client must also have a `client_id` to use with this flow.
How the client obtains this is out of scope for this MSC, and is currently covered by [MSC2966](https://github.com/matrix-org/matrix-doc/pull/2966).

### Authorization code grant

As per [RFC6749], the authorization code grant lets the client obtain an access token through a browser redirect.

Because this flow has various parameters and security improvements added by other specifications, this describes what is enforced and required to support by the client and the homeserver.

Homeservers and clients must:

- support PKCE using the `S256` code challenge method as per [RFC7636]
- support the auth code flow as per [RFC6749] section 4.1
- support the refresh token grant as per [RFC6749] section 6
- use pre-registered, strict redirect URIs
- use the `fragment` response mode as per [OAuth 2.0 Multiple Response Type Encoding Practices] for clients with an HTTPS redirect URI

### Refresh token grant

When authorization is granted to a client, the homeserver must issue a refresh token to the client in addition to the access token.

The access token must be short-lived and should be refreshed using the `refresh_token` when expired, as described in [RFC6749] section 6.

The homeserver should issue a new refresh token each time one is used, and invalidate the old one.
It should do this only if it can guarantee that in case a response with a new refresh token is not received and stored by the client, retrying the request with the old refresh token will succeed.

The homeserver should consider that the session is compromised if an old, invalidated refresh token is being used, and should revoke the session.

The client must handle access token refresh failures as follows:

 - If the refresh fails due to network issues or a `5xx` HTTP status code from the server, the client should retry the request with the old refresh token later.
 - If the refresh fails due to a `4xx` HTTP status code from the server, the client should consider the session logged out.

### Sample flow

#### Flow parameters

The client must know the following parameters, through ways described in [MSC2965], [MSC2966] and [MSC2967]:

- `authorization_endpoint`: the URL where the user is able to access the authorization endpoint to initiate the login flow
- `token_endpoint`: the URL where the user is able to access the token endpoint to exchange the authorization code for an access token
- `client_id`: the unique identifier allocated for the client
- `redirect_uri`: the URI where the user is redirected after the authorization flow used by this client
- `scope`: the scope of the access token to request
- `response_mode`: the response mode to use, either `fragment` or `query`. It must be `fragment` if the `redirect_uri` is an HTTPS URI, and can be `query` otherwise

It needs to generate the following values:

- a random value for the `state`
- a cryptographically random value for the `code_verifier`

#### Authorization request

It then constructs the authorization request URL using the `authorization_endpoint` value, with the following query parameters:

- The `response_type` value set to `code`
- The `client_id` value
- The `redirect_uri` value
- The `scope` value
- The `state` value
- The `response_mode` value
- The `code_challenge` computed from the `code_verifier` value using the SHA-256 algorithm, as described in [RFC7636]
- The `code_challenge_method` set to `S256`

This authorization request URL must be opened in the user's browser:

- For web-based clients, this can be done through a redirection or by opening the URL in a new tab
- For native clients, this can be done by opening the URL:
  - using the system browser
  - through platform-specific APIs when available, such as [`ASWebAuthenticationSession`](https://developer.apple.com/documentation/authenticationservices/aswebauthenticationsession) on iOS or [Android Custom Tabs](https://developer.chrome.com/docs/android/custom-tabs) on Android

The rationale for using the system browser is explained in [MSC3861], under "Motivation" → "Benefits of authenticating end-users through the system browser".

##### Sample authorization request

Sample authorization request (broken down into multiple lines for readability), with the following values:

- `authorization_endpoint` set to `https://account.example.com/oauth2/auth`, obtained through [MSC2965]
- `client_id` set to `s6BhdRkqt3`, obtained through [MSC2966]
- `redirect_uri` set to `https://app.example.com/oauth2-callback`
- `state` set to `ewubooN9weezeewah9fol4oothohroh3`
- `response_mode` set to `fragment`
- `code_verifier` set to `ogie4iVaeteeKeeLaid0aizuimairaCh`
- `code_challenge` computed as `72xySjpngTcCxgbPfFmkPHjMvVDl2jW1aWP7-J6rmwU`
- `scope` set to `urn:matrix:client:api:* urn:matrix:client:device:AAABBBCCCDDD` (full access to the C-S API, using the `AAABBBCCCDDD` device ID, as per [MSC2967])

```
https://account.example.com/oauth2/auth?
    client_id     = s6BhdRkqt3 &
    response_type = code &
    response_mode = fragment &
    redirect_uri  = https://app.example.com/oauth2-callback &
    scope         = urn:matrix:client:api:* urn:matrix:client:device:AAABBBCCCDDD &
    state         = ewubooN9weezeewah9fol4oothohroh3 &
    code_challenge        = 72xySjpngTcCxgbPfFmkPHjMvVDl2jW1aWP7-J6rmwU &
    code_challenge_method = S256
```

#### Callback

Once completed, the user is redirected to the `redirect_uri`, with either a successful or failed authorization in the URL fragment or query parameters.
Whether the parameters are in the URL fragment or query parameters is determined by the `response_mode` value:

- if set to `fragment`, the parameters will be placed in the URL fragment, like `https://example.com/callback#param1=value1&param2=value2`
- if set to `query`, the parameters will be in placed the query string, like `com.example.app:/callback?param1=value1&param2=value2`

To avoid disclosing the parameters to the web server hosting the `redirect_uri`, clients should use the `fragment` response mode if the `redirect_uri` is an HTTP/HTTPS URI with a remote host.

In both success and failure cases, the parameters will have the `state` value used in the authorization request.

##### Successful authorization callback

Successful authorization will have a `code` value.

Sample successful authorization:

```
https://app.example.com/oauth2-callback#state=ewubooN9weezeewah9fol4oothohroh3&code=iuB7Eiz9heengah1joh2ioy9ahChuP6R
```

##### Failed authorization callback

Failed authorization will have the following values:

- `error`: the error code
- `error_description`: the error description (optional)
- `error_uri`: the URI where the user can find more information about the error (optional)

Sample failed authorization:

```
https://app.example.com/oauth2-callback#state=ewubooN9weezeewah9fol4oothohroh3&error=access_denied&error_description=The+resource+owner+or+authorization+server+denied+the+request.&error_uri=https%3A%2F%2Ferrors.example.com%2F
```

#### Token request

The client then exchanges the authorization code to obtain an access token using the token endpoint.

This is done by making a POST request to the `token_endpoint` with the following parameters, encoded as `application/x-www-form-urlencoded` in the body:

- The `grant_type` set to `authorization_code`
- The `code` obtained from the callback
- The `redirect_uri` used in the authorization request
- The `client_id` value
- The `code_verifier` value generated at the start of the authorization flow

The server replies with a JSON object containing the access token, the token type, the expiration time, and the refresh token.

The access token must be short-lived and should be refreshed using the `refresh_token` when expired.

##### Sample token request

```
POST /oauth2/token HTTP/1.1
Host: account.example.com
Content-Type: application/x-www-form-urlencoded
Accept: application/json

grant_type=authorization_code
  &code=iuB7Eiz9heengah1joh2ioy9ahChuP6R
  &redirect_uri=https://app.example.com/oauth2-callback
  &client_id=s6BhdRkqt3
  &code_verifier=ogie4iVaeteeKeeLaid0aizuimairaCh
```

```json
{
  "access_token": "2YotnFZFEjr1zCsicMWpAA",
  "token_type": "Bearer",
  "expires_in": 299,
  "refresh_token": "tGz3JOkF0XG5Qx2TlKWIA",
  "scope": "urn:matrix:client:api:* urn:matrix:client:device:AAABBBCCCDDD"
}
```

#### Token refresh

When the access token expires, the client must refresh it by making a POST request to the `token_endpoint` with the following parameters, encoded as `application/x-www-form-urlencoded` in the body:

- The `grant_type` set to `refresh_token`
- The `refresh_token` obtained from the token response
- The `client_id` value

The server replies with a JSON object containing the new access token, the token type, the expiration time, and a new refresh token.
The old refresh token is no longer valid and should be discarded.

##### Sample token refresh

```
POST /oauth2/token HTTP/1.1
Host: account.example.com
Content-Type: application/x-www-form-urlencoded
Accept: application/json

grant_type=refresh_token
  &refresh_token=tGz3JOkF0XG5Qx2TlKWIA
  &client_id=s6BhdRkqt3
```

```json
{
  "access_token": "2YotnFZFEjr1zCsicMWpAA",
  "token_type": "Bearer",
  "expires_in": 299,
  "refresh_token": "tGz3JOkF0XG5Qx2TlKWIA",
  "scope": "urn:matrix:client:api:* urn:matrix:client:device:AAABBBCCCDDD"
}
```

### User registration

Users can register themselves by initiating an authorization code flow with the `prompt=create` parameter as defined in [Initiating User Registration via OpenID Connect 1.0](https://openid.net/specs/openid-connect-prompt-create-1_0.html).

Whether the homeserver supports this parameter is advertised by the `prompt_values_supported` authorization server metadata.

## Potential issues

For a discussion on potential issues please see [MSC3861]

## Alternatives

The authorization flow could make use of [RFC9126: OAuth 2.0 Pushed Authorization Request][RFC9126] as a way to future-proof the flow.
This could help with granting very specific permissions to the client in combination with [RFC9396: OAuth 2.0 Rich Authorization Requests][RFC9396].

As Matrix clients are 'public clients' in the sense of [RFC6749] section 2.1, this proposal would not benefit from the security aspects of [RFC9126].
It could, although, give better feedback to clients when they are trying to start an invalid or unauthorized flow.

Other alternatives for the global proposal are discussed in [MSC3861].

## Security considerations

Since this touches one of the most sensitive parts of the API, there are a lot of security considerations to keep in mind.

The [OAuth 2.0 Security Best Practice](https://tools.ietf.org/html/draft-ietf-oauth-security-topics-16) IETF draft outlines many potential attack scenarios. Many of these scenarios are mitigated by the choices enforced in the client profiles outlined in this MSC.
It motivates the following decisions in this profile:

 - Using strict redirect URIs validation helps mitigate the risk of open redirection attacks.
 - Using the `code` response mode, alongside PKCE mitigates the risk in cases of redirection hijacking.
 - Usage of short-lived access tokens, along with rotation of refresh tokens mitigates the impact of leaked tokens.
 - Using the system browser to authenticate users lowers the risk of credentials exfiltration by the client.

## Unstable prefix

None as part of this MSC.

## Dependencies

- [MSC2965]
- [MSC2966]
- [MSC2967]

[RFC6749]: https://tools.ietf.org/html/rfc6749
[RFC7636]: https://tools.ietf.org/html/rfc7636
[RFC8414]: https://tools.ietf.org/html/rfc8414
[RFC9126]: https://tools.ietf.org/html/rfc9126
[RFC9396]: https://tools.ietf.org/html/rfc9396
[MSC2965]: https://github.com/matrix-org/matrix-spec-proposals/pull/2965
[MSC2966]: https://github.com/matrix-org/matrix-spec-proposals/pull/2966
[MSC2967]: https://github.com/matrix-org/matrix-spec-proposals/pull/2967
[MSC3861]: https://github.com/matrix-org/matrix-spec-proposals/pull/3861
[OAuth 2.0 Multiple Response Type Encoding Practices]: https://openid.net/specs/oauth-v2-multiple-response-types-1_0.html
