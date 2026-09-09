# MSC4526: Improve OAuth 2.0 refresh token grant error handling

The [OAuth 2.0 API] requires clients to use short-lived access tokens which are renewed using the [refresh token grant].
The specification currently tells clients how to handle a failed refresh as follows:

> The client MUST handle access token refresh failures as follows:
>
> - If the refresh fails due to network issues or a `5xx` HTTP status code from the server, the client should retry the
>   request with the old refresh token later.
> - If the refresh fails due to a `4xx` HTTP status code from the server, the client should consider the session logged
>   out.

Considering a session logged out is a destructive and effectively irreversible action: the client typically discards the
session along with any state bound to it, including its encryption keys and device information. If the user has no
working key backup, an erroneous logout means permanent loss of access to encrypted message history.

The problem is that a `4xx` status code is a poor signal for "this session no longer exists". A great many things that
have nothing to do with the validity of the refresh token produce a `4xx` response, for example:

- A client bug producing a malformed request (`400 invalid_request`), which will affect every session of every user of
  that client.
- Rate limiting (`429`), which the server is explicitly permitted to apply.
- Captive portals, transparent proxies, TLS-terminating gateways and VPN appliances, which may return `403`, `407` or
  `451` for requests they intercept, often with an HTML body.

In all of these cases the refresh token is very likely still valid, and the correct behaviour is to retry later — just
as for a `5xx` response — rather than to destroy the session and the user's encryption keys.

OAuth 2.0 already provides a precise signal for the case the current text is trying to capture. [RFC 6749 section 5.2]
defines the `invalid_grant` error code for exactly this:

> The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid,
> expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another
> client.

This proposal therefore changes the rule from "any `4xx`" to "an `invalid_grant` error response", and states the
corresponding requirement on servers so that clients can rely on that signal.

## Proposal

The client-side error handling rules for the [refresh token grant] are updated as follows:

The client MUST handle access token refresh failures as follows:

- If the refresh fails with an OAuth 2.0 error response from the server with an `error` of `invalid_grant`, the client
  MUST consider the session logged out.
- If the refresh fails due to network issues or a `5xx` HTTP status code from the server, the client SHOULD retry the
  request with the old refresh token later.
- In any other case, including a `4xx` HTTP status code that is not accompanied by an `invalid_grant` error response,
  the client MUST NOT consider the session logged out, and SHOULD retry the request with the old refresh token later.

For the purposes of these rules, an OAuth 2.0 error response is one whose body is a JSON object with a string-valued
`error` member, as per [RFC 6749 section 5.2]. Unrecognised error codes, including any registered in the future via the
[OAuth Extensions Error Registry], MUST NOT be treated as ending the session, so that the default behaviour on an
unknown error remains the non-destructive one.

Servers are already required to return OAuth 2.0 error responses rather than [standard Matrix error responses] at the
`token_endpoint`: the [OAuth 2.0 API] is "based on the OAuth 2.0 industry standard introduced in [RFC 6749]", and the
[API standards] that would otherwise mandate the Matrix format explicitly do not apply to it. So that clients are able
to rely on the above, the server MUST return an OAuth 2.0 `invalid_grant` error response when the presented refresh
token is unknown, expired or revoked. This includes the case where the session has been revoked, whether by the user,
by an administrator, via [token revocation], or because the server considered the session compromised following the
replay of an old, invalidated refresh token.

Conversely, the server MUST NOT return an OAuth 2.0 `invalid_grant` error response for transient conditions such as rate
limiting, an internal error, or an unavailable dependency.

These rules concern only the [refresh token grant]. The `token_endpoint` is shared with the other grant types, and the
error codes those grants use are unaffected: in particular, the [device authorisation grant] continues to use
`authorization_pending`, `slow_down`, `access_denied` and `expired_token` as defined in [RFC 8628 section 3.5] while a
client polls for the outcome of authorisation.

Because an `invalid_grant` response is now unconditionally destructive, the server SHOULD NOT treat the presentation of
the refresh token immediately preceding the current one — that is, the token that was invalidated by the most recent
successful refresh — as a replay for the purposes of considering the session compromised. The [refresh token grant]
already requires that such a retry be possible.

## Potential issues

### Change in server behaviour

A server that does not follow the requirements above and instead signals a revoked session with, say, a `401` and a
standard Matrix error response will now cause clients to retry indefinitely, leaving the user with a session that
appears to be perpetually offline instead of being cleanly logged out. However, such a server is already violating
[RFC 6749] and not compliant with the Matrix spec.

### Transition for clients

This proposal deliberately does not carve out a transitional allowance for clients to keep treating, say, a `401` with
an `M_UNKNOWN_TOKEN` `errcode` as ending the session. Such an allowance would preserve exactly the property the proposal
sets out to remove: a response that an on-path attacker, captive portal or misbehaving intermediary can produce, and
which destroys the user's encryption keys when they do. Servers that signal revocation this way should be fixed, and in
the meantime their users are left with a stale session rather than lost message history, which is the less damaging of
the two failures.

If a client is currently only checking the HTTP status code of the response, it will now need to parse the response body
in order to distinguish an ended session from a temporary failure. Until it is updated to do so, it will continue to
behave as it does today.

### Retry behaviour not specified

Neither this MSC nor the current specification says how long a client should keep retrying before giving up, nor what
retry schedule to use, such as an exponential backoff. I believe this is left deliberately as an implementation
decision, since it depends on the client's platform and on how the client presents the error to the user. It should be
noted that giving up MUST NOT mean silently discarding the session.

### Rate-limit response for OAuth 2.0 endpoints is not defined

[RFC 6749 section 5.2] defines no error code for rate limiting. As such, it is currently unclear what is the expected
behaviour. Should servers be returning a `429` status code, a `Retry-After` header, and a [standard Matrix error
response][standard Matrix error responses] with an `errcode` of `M_LIMIT_EXCEEDED`?

Currently the [OAuth 2.0 API] is explicitly carved out of the [API standards] where the [rate limiting] is described.

It would be reasonable to extend this MSC to include defining this expected behaviour if reviewers are so inclined.

## Alternatives

### Do nothing

Clients that implement the specification as written will discard sessions, and encryption keys along with them, in
response to routine and recoverable network conditions. This leaves client authors with a choice between following the
specification and protecting their users' data, which is not a choice the specification should be asking them to make.

### Treat additional error codes as ending the session as well

No other error code defined by [RFC 6749 section 5.2] is a statement about the refresh token itself: the rest describe a
problem with the request, the client registration, or the server's configuration, none of which implies that the session
has gone away. Quoting that section's definition of each code:

- `invalid_client` — **session retained.** "Client authentication failed (e.g., unknown client, no client authentication
  included, or unsupported authentication method)." This is a statement about the client rather than about the grant.
  The [dynamic client registration flow] already requires that a server "MUST NOT delete client registrations that have
  an active session", so for an active session this indicates a server-side problem, and the session may well still
  exist.
- `unauthorized_client` — **session retained.** "The authenticated client is not authorized to use this authorization
  grant type." Since support for the refresh token grant is mandatory for both of the other grant types, this indicates
  a server-side problem. Discarding the session would not help either, as a newly established session would be equally
  unable to refresh.
- `unsupported_grant_type` — **session retained.** "The authorization grant type is not supported by the authorization
  server." As above.
- `invalid_request` — **session retained.** "The request is missing a required parameter, includes an unsupported
  parameter value (other than grant type), repeats a parameter, includes multiple credentials, utilizes more than one
  mechanism for authenticating the client, or is otherwise malformed." This is a client bug, or the result of an
  intermediary rewriting the request; the refresh token is unaffected.
- `invalid_scope` — **session retained.** "The requested scope is invalid, unknown, malformed, or exceeds the scope
  granted by the resource owner." Not applicable to a refresh request that does not narrow the scope, and in any case
  not a statement about the refresh token.

### Introduce a Matrix-specific signal

We could introduce something like the `soft_logout` flag used by the legacy [`POST /_matrix/client/v3/refresh`]
endpoint. It is unnecessary here, as OAuth 2.0 already defines a suitable signal, and adding one would make the Matrix
OAuth 2.0 API harder to implement with off-the-shelf OAuth libraries.

### Also apply this to the legacy `/refresh` endpoint

The [legacy refresh flow] has a similar problem: "If the error response does not include a `soft_logout: true` property,
the client should consider the user as being logged out" means that a `429` from `/refresh` also destroys the session.
The equivalent fix would be to treat only an `M_UNKNOWN_TOKEN` `errcode` as ending the session. This is deliberately
left out of scope here to keep this proposal focused on the OAuth 2.0 API, but I think it would be reasonable to fix
both at once if reviewers are so inclined.

## Security considerations

The change makes clients less eager to discard a session, so a session that has genuinely been revoked may persist on
the client for longer than it does today. This does not extend the lifetime of any credential: the access token is
short-lived and, once expired, the client cannot make authenticated requests, and every refresh attempt fails. In other
words, the session is inert while it is retained; retaining it only delays the local cleanup, and the server remains
fully in control of when the session stops working.

Conversely, the current "remote wipe" behaviour is itself a weakness. An attacker who can inject or force a `4xx`
response — an on-path attacker able to interfere with the connection to the `token_endpoint`, or the operator of a
captive portal or intercepting proxy — can currently cause clients to discard sessions and their encryption keys,
resulting in permanent loss of access to encrypted history for users without a working key backup. Requiring a properly
formed `invalid_grant` response raises the bar for that attack: the response must come from a party able to produce a
valid TLS response from the server, which is the party legitimately entitled to end the session.

Requiring a specific error code does not itself make the signal authentic. That remains the responsibility of TLS, as it
does for every other part of the API.

The requirement that servers not return `invalid_grant` for transient conditions matters for availability: a server
that returns `invalid_grant` when it is merely overloaded would log out its entire user base, and with encryption keys
being discarded, that is not a failure that can be undone by fixing the server.

The lack of specificity over retry semantics could contribute towards a denial of service by clients tightly retrying.
As noted above, the retry schedule is left to implementations, but clients would be well advised to use a backoff.

## Unstable prefix

None required. This proposal introduces no new endpoint, parameter or error code, and nothing here needs to be gated on
a spec version or advertised through `unstable_features`: the new client behaviour is strictly less destructive than the
current rule, so a client may adopt it immediately without regard to which servers it talks to, and a server that
already returns `invalid_grant` for a revoked session is already interoperable with clients that have not yet been
updated.

## Dependencies

None.

[API standards]: https://spec.matrix.org/v1.19/client-server-api/#api-standards
[rate limiting]: https://spec.matrix.org/v1.19/client-server-api/#rate-limiting
[OAuth 2.0 API]: https://spec.matrix.org/v1.19/client-server-api/#oauth-20-api
[dynamic client registration flow]: https://spec.matrix.org/v1.19/client-server-api/#dynamic-client-registration-flow
[refresh token grant]: https://spec.matrix.org/v1.19/client-server-api/#refresh-token-grant
[device authorisation grant]: https://spec.matrix.org/v1.19/client-server-api/#device-authorisation-grant
[standard Matrix error responses]: https://spec.matrix.org/v1.19/client-server-api/#standard-error-response
[token revocation]: https://spec.matrix.org/v1.19/client-server-api/#token-revocation
[legacy refresh flow]: https://spec.matrix.org/v1.19/client-server-api/#refreshing-access-tokens
[`POST /_matrix/client/v3/refresh`]: https://spec.matrix.org/v1.19/client-server-api/#post_matrixclientv3refresh
[RFC 6749]: https://datatracker.ietf.org/doc/html/rfc6749
[RFC 6749 section 5.2]: https://datatracker.ietf.org/doc/html/rfc6749#section-5.2
[RFC 8628 section 3.5]: https://datatracker.ietf.org/doc/html/rfc8628#section-3.5
[OAuth Extensions Error Registry]: https://www.iana.org/assignments/oauth-parameters/oauth-parameters.xhtml#extensions-error
