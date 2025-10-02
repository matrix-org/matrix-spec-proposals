# MSC4363: OAuth step up authentication

Homeservers may want to enforce re-authentication to guard access to potentially severe user actions
such as deactivating an account or logging out all devices. Prior to the [OAuth APIs] introduced in
Matrix 1.15, this was handled by an API called [User-Interactive Authentication (UIA)]. UIA is
incompatible with the new [OAuth APIs], however, leading to suboptimal workarounds such as
[MSC4312].

Fortunately, OAuth itself provides a scheme for elevating access rights with [RFC9470] (OAuth 2.0
Step Up Authentication Challenge Protocol). The present proposal generalizes [RFC9470] for use with
Matrix.

## Proposal

The following description assumes that the client has authenticated via the [OAuth APIs].

When a homeserver determines that the authentication event associated with the access token
presented on a request is insufficient, it MAY respond with HTTP 401 and a new error code
`M_INSUFFICIENT_USER_AUTHENTICATION`. Three optional top-level properties are allowed in the
response to convey the authentication requirements challenge back to the client:

- `acr_values`: A space-separated string listing the authentication context class reference (ACR)
  values in order of preference.[^1] The protected resource requires *one* of these values for the
  authentication event associated with the access token.
- `max_age`: A non-negative integer specifying the allowable elapsed time in seconds since the last
  active authentication event associated with the access token.
- `scope`: A space-separated string listing the *full* set of scopes that are required to access the
  protected resource.

The following is an example of an error response that requests authentication using either any 2FA
method, or, failing that, password-based authentication. Additionally, a maximum elapsed time since
authentication of 5 minutes is required. The ACR values were taken from [Okta's reference].

``` json5
{
  "errcode": "M_INSUFFICIENT_USER_AUTHENTICATION",
  "error": "Additional authentication required to complete request",
  "acr_values": "urn:okta:loa:2fa:any urn:okta:loa:1fa:pwd",
  "max_age": 300
}
```

A client receiving a challenge SHOULD use the `acr_values`, `max_age` and `scope` properties to
construct a new authorization request. For this purpose, `acr_values` and `max_age` are added to the
[current list of request parameters] using the same definition given above. If the challenge doesn't
include any scopes, the client SHOULD use the same scopes it used during login on the authorization
request.

Following successful authorization, the client's previous access token SHOULD be invalidated and a
new, more privileged, token be issued. The new token SHOULD have a short lifetime. The client can
then use the new token to repeat the original request but may also use it for other API requests.
Renewing the token SHOULD produce a less privileged token again. This approach ensures that
implementations can continue to maintain only a single access token per device as they do today.

### Aspects that are out of scope

This proposal consciously leaves a number of things undefined.

Firstly, the act of evaluating whether or not an access token meets a resource's requirements is
left as an implementation detail of the homeserver. As per [RFC9470], this can, for instance, be
achieved by encoding the access token with additional properties in JWT format. Alternatively, if
the homeserver delegates authorization to an external authorization server, a dedicated token
introspection endpoint could be used.

Furthermore, no concrete ACR values are specified. Again, this is an implementation detail of the
homeserver as ACR values are not intended for introspection by clients.

Finally, it is left up to the homeserver to determine how exactly the `acr_values`, `max_age` and
`scope` parameters are used during authentication. Implementations should, however, note the
recommendations in [RFC9470].

## Potential issues

None apparent.

## Alternatives

Rather than extending the existing [standard error response], the error and parameters could be
communicated via the `WWW-Authenticate` header as suggested in [RFC9470]. Reusing the example from
above, the header would look like this:

``` http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer error="insufficient_user_authentication",
  error_description="Additional authentication required to complete request",
  acr_values="urn:okta:loa:2fa:any urn:okta:loa:1fa:pwd",
  max_age="300"
```

Switching to the header would break with the established error mechanism in Matrix, however. As a
middleground, the header could also be used *on* standard error responses. It's unclear though what
advantages it would bring to have two different mechanisms that convey the same information.

Rather than replacing the current access token, a new token could be issued without invalidating the
existing one. The client would then use the new token only for repeating the original request and
continue using the old token for all other requests. This enables one-shot tokens but would mean
that implementations have to start managing more than one token per device. Moreover, homeservers
could also achieve one-shot-like semantics by re-applying this proposal's step-up process to the new
token.

A [previous version] of [MSC2967] used the `insufficient_scope` error code from [RFC6750] (The OAuth
2.0 Authorization Framework: Bearer Token Usage) to communicate missing scopes back to the client.
This is comparable to but less flexible than the present proposal as it lacks ACRs and token age.

Finally, the scheme proposed in [MSC4312] (ab)uses UIA to deeplink into the homeserver's account
management web UI. This is less flexible and powerful than OAuth step up authentication, however. It
is also contrary to the idea of standardizing authentication in Matrix on OAuth mechanisms.

## Security considerations

The security impact of this proposal largely follows [RFC9470].

Depending on the concrete values used in the `acr_values` parameter, it is possible to leak
information about the authenticated user, the protected resource, the authorization server, and any
other context-specific data. This risk can be controlled by implementations deciding on the values.

To prevent leaking required properties of an authorization token to an actor who has not proven they
can obtain a token, homeservers SHOULD NOT return a challenge without verifying the client presented
a valid token.

## Unstable prefix

While this MSC is not considered stable, the following replacements should be used in the
homeserver's error response:

- `M_INSUFFICIENT_USER_AUTHENTICATION` → `org.matrix.msc4363.M_INSUFFICIENT_USER_AUTHENTICATION`
- `acr_values` → `org.matrix.msc4363.acr_values`
- `max_age` → `org.matrix.msc4363.max_age`
- `scope` → `org.matrix.msc4363.scope`

The new authorization request parameters should not use prefixes since they follow standard OAuth.

[^1]: As defined in the [OIDC core specification], the authentication context conveys information
    about how authentication takes place (e.g., what authentication method(s) or assurance level to
    meet).

  [OAuth APIs]: https://spec.matrix.org/v1.15/client-server-api/#oauth-20-api
  [User-Interactive Authentication (UIA)]: https://spec.matrix.org/v1.16/client-server-api/#user-interactive-authentication-api
  [MSC4312]: https://github.com/matrix-org/matrix-spec-proposals/pull/4312
  [RFC9470]: https://datatracker.ietf.org/doc/rfc9470/
  [Okta's reference]: https://developer.okta.com/docs/guides/step-up-authentication/main/
  [current list of request parameters]: https://spec.matrix.org/v1.15/client-server-api/#login-flow
  [standard error response]: https://spec.matrix.org/v1.16/client-server-api/#standard-error-response
  [previous version]: https://github.com/matrix-org/matrix-spec-proposals/pull/2967/commits/544d75b413277f14393a635ea17be3d0d49529c5
  [MSC2967]: github.com/matrix-org/matrix-doc/pull/2967
  [RFC6750]: https://datatracker.ietf.org/doc/html/rfc6750
  [OIDC core specification]: https://openid.net/specs/openid-connect-core-1_0.html#Terminology
