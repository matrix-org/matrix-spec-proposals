# MSC4126: Deprecation of query string auth

Presently, the Client-Server API allows clients to provide their access token via the `Authorization`
request header or via an `access_token` query string parameter, described [here](https://spec.matrix.org/v1.10/client-server-api/#using-access-tokens).
Clients are already encouraged to use the header approach, though the query string option exists for
largely backwards compatibility reasons.

The query string approach is subject a number of security, usability, and practical concerns, discussed
on [matrix-spec#1780](https://github.com/matrix-org/matrix-spec/issues/1780):

* The query string of an HTTP request is often logged by the client itself, middleware reverse proxy,
  and application/homeserver as well. Though some of these layers may be aware of this issue, they
  can trivially accidentally break to log sensitive credentials again. By contrast, headers are not
  typically logged by default.

* Users often copy and paste URLs from their clients to either get support or provide direct links
  to content/media. While the media angle is largely expected to be resolved with [MSC3916](https://github.com/matrix-org/matrix-spec-proposals/pull/3916),
  users are currently able to right click images in their client and copy the URL - if this URL
  includes authentication in the query string, the user will likely end up disclosing their access
  token. The same scenario applies when copy/pasting request logs out of a client when getting
  support.

* Having two ways of doing things could lead to compatibility issues, where a client using the query
  string approach is tried against a server which only supports the header. The client ends up not
  working, leading to subpar user experience.

* Most clients have already adopted the header approach, largely forgetting that the query string
  even exists. Continuing to support the query string option leaves some maintenance burden for what
  is effectively unused code.

* Matrix has [decided](https://matrix.org/blog/2023/09/matrix-2-0/) to adopt OIDC for authentication,
  which is based on OAuth 2.0, which [advises against](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics#section-4.3.2)
  the query string approach.

With these conditions in mind, this proposal sets the query string approach on a path towards removal
from the Matrix specification. This affects the Client-Server API and [Identity Service API](https://spec.matrix.org/v1.10/identity-service-api/#authentication)
as both support the approaches described above.

## Proposal

For both the Client-Server API and Identity Service API, the `access_token` query string authentication
parameter becomes *deprecated*, and SHOULD NOT be used by clients (as already stated in the specification).
Deprecation is required for at least 1 spec version before removal under the [deprecation policy](https://spec.matrix.org/v1.10/#deprecation-policy).

Removal from the specification requires a second MSC and at least 1 specification release to pass. This
is currently described as [MSC4127](https://github.com/matrix-org/matrix-spec-proposals/pull/4127).

## Potential issues

Clients which rely on the query string approach may stop working. This is considered acceptable for
the purposes of this MSC.

## Alternatives

Most alternatives are not practical as they would maintain the security risk described in the introduction
for this proposal.

Alterations to the deprecation policy may be discussed in a future MSC to make this sort of removal
easier.

## Security considerations

Security considerations are described throughout this proposal.

## Unstable prefix

This proposal cannot feasibly have an unstable prefix. Clients are already discouraged from using
query string authentication and should switch to `Authorization` as soon as possible, regardless of
this MSC.

## Dependencies

This MSC has no direct dependencies itself. [MSC4127](https://github.com/matrix-org/matrix-spec-proposals/pull/4127)
requires this MSC to land first.
