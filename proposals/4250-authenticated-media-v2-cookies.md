# MSC4250: Authenticated media v2 (Cookie authentication for Client-Server API)

With the introduction of authenticated media in Matrix 1.11, some browser environments became unable
to view *unencrypted* media because they were unable to append the required `Authorization` header.
Specifically, in Firefox Private Browsing Mode (and similar for non-Chromium browsers),
[Service Workers](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API) are unavailable,
leaving the client two options:

1. Buffer *all* media into a [Blob](https://developer.mozilla.org/en-US/docs/Web/API/Blob), like they
   typically do for encrypted media; or
2. Show errors, infinite spinners, or another indication that the media will never arrive.

Option 2 is obviously not great, but option 1 isn't far off: clients will experience abnormally high
memory usage just to show user/room avatars and thumbnails, and will not be able to benefit from
[`Range` requests](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Range) to stream data
to the user. For example, if a user wishes to download a 10mb PDF, the client would need to download
the entire PDF into a Blob first, then serve that to the user (assuming it doesn't crash due to an
arbitrary memory limit first). This could take quite a while depending on network conditions too,
holding even more memory if the user tries to switch to another room while the download is still
happening.

Ideally, the spec can give the affected clients a third option to allow the non-trivial number of
affected users a chance at seeing media again. This proposal is heavily inspired by
[issue #1949](https://github.com/matrix-org/matrix-spec/issues/1949) which explores some potential
options in this area, and puts forward [Cookies](https://en.wikipedia.org/wiki/HTTP_cookie) as the
best way to solve the issue. This is an opt-in authentication mechanism for specific Client-Server API
endpoints, allowing the client to access the protected resources.

## Background

Readers not familiar with authenticated media should read the following resources:

* https://matrix.org/blog/2024/06/26/sunsetting-unauthenticated-media/
* https://matrix.org/blog/2024/06/20/matrix-v1.11-release/
* https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/3916-authentication-for-media.md
* https://spec.matrix.org/v1.13/client-server-api/#content-repo-client-behaviour

## Proposal

The Client-Server API's [authentication mechanisms](https://spec.matrix.org/v1.13/client-server-api/#client-authentication)
are expanded to include an opt-in cookie for specific endpoints. Clients which present a valid cookie,
valid access token, or both to the affected endpoints are considered authenticated for that request.

Clients opt into the cookie authentication by setting the `?set_auth_cookie=true` query parameter when
calling [`/sync`](https://spec.matrix.org/v1.13/client-server-api/#get_matrixclientv3sync) or
[`/whoami`](https://spec.matrix.org/v1.13/client-server-api/#get_matrixclientv3accountwhoami) (for
clients which don't sync). When `set_auth_cookie` is `true` on these two endpoints, servers SHOULD
use [`Set-Cookie`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie) to set an
implementation-specific authentication cookie. Servers MAY decline to set a cookie for any implementation-
specific reason, such as seeing the cookie is already retained by the client, or a local security
policy denies the use of cookies.

When setting cookies, servers SHOULD scope the cookie to a specific domain, and apply a relatively
short expiration (minutes, not hours). Using the `Path` and `Secure` parameters is also recommended.

Servers SHOULD note that some browsers and cookie jar implementations may restore expired cookies, and
SHOULD therefore check expiration against an internal database rather than rely on the client-supplied
value.

When `set_auth_cookie` is `false`, not present, or any other value, the server SHOULD NOT set any
authentication cookies.

Clients MAY then use the cookie to authenticate themselves on future requests. If an endpoint not
listed below receives the cookie, the server MUST ignore the cookie and rely solely on any provided
access tokens instead. If an endpoint *is* listed below, the server MUST honour the cookie as valid
authentication. If an endpoint listed below receives *both* an access token and cookie authentication,
the server MUST verify that the same user (and device, if applicable) is identified by both. Clients
SHOULD NOT send both an access token and cookie if they can avoid it, however.

The endpoints which explicitly accept cookie authentication are:

* [`GET /_matrix/client/v1/media/download/{serverName}/{mediaId}`](https://spec.matrix.org/v1.13/client-server-api/#get_matrixclientv1mediadownloadservernamemediaid)
* [`GET /_matrix/client/v1/media/download/{serverName}/{mediaId}/{fileName}`](https://spec.matrix.org/v1.13/client-server-api/#get_matrixclientv1mediadownloadservernamemediaidfilename)
* [`GET /_matrix/client/v1/media/thumbnail/{serverName}/{mediaId}`](https://spec.matrix.org/v1.13/client-server-api/#get_matrixclientv1mediathumbnailservernamemediaid)

Other endpoints may be appended to the above list in future MSCs.

The set of endpoints is limited to narrow the scope of common attacks, like Cross-Site Scripting and
Cross-Site Request Forgery when cookies are handled improperly.

If the cookie is invalid, expired, or doesn't belong to the same user as the provided access token,
the server MUST respond with a `401 M_UNKNOWN_TOKEN` error (like with regular access token auth).

### Examples

A user acquires a cookie:

```
GET /_matrix/client/v3/account/whoami?set_auth_cookie=true
Authorization: Bearer $token

-> 200 OK
-> Set-Cookie: example_auth=token; Expires=Thu, 31 Oct 2021 07:28:00 GMT; Secure; HttpOnly; Domain=matrix-client.example.org; Path=/_matrix/client/v1/media/; SameSite=Strict
```

A user making a normal, cookie-less, request:
```
GET /_matrix/client/v1/media/download/example.org/abc123
Authorization: Bearer $token

-> 200 OK
```

A user authenticating with a cookie instead:
```
GET /_matrix/client/v1/media/download/example.org/abc123
Cookie: example_auth=token

-> 200 OK
```

A user authenticating with both a cookie and access token (same user ID owning both):
```
GET /_matrix/client/v1/media/download/example.org/abc123
Authorization: Bearer $token
Cookie: example_auth=token

-> 200 OK
```

A user authenticating with both a cookie and access token, but each token belongs to a different user:
```
GET /_matrix/client/v1/media/download/example.org/abc123
Authorization: Bearer $token
Cookie: example_auth=token

-> 401 M_UNKNOWN_TOKEN
```

A user authenticating to an unlisted endpoint using a cookie and access token, with each token belonging
to a different user:
```
GET /_matrix/client/v1/account/whoami
Authorization: Bearer $token
Cookie: example_auth=token

-> 200 OK
-> {"user_id": "@user_who_owns_authorization_header_token:example.org"}
```

A user supplying an expired or useless cookie, and no other form of authentication:
```
GET /_matrix/client/v1/media/download/example.org/abc123
Cookie: not_auth=token

-> 401 M_MISSING_TOKEN
```

## Potential issues

Private browsers tend to obliterate all their stored cookies upon all private tabs being closed. They
also obliterate all other account/session details though, so this is the least of the user's concerns.

Some browsers may still reject cookies entirely. With cookies being fairly prominent in the wild though,
this may be an elective pain point for users.

Mobile and non-browser clients may not be able to use cookies out of the gate. This should be fine
though, as they also typically have better control of request headers and can therefore set `Authorization`
as needed.

Users may be confused why a media link works for them, but not their friend. This is a feature of
authenticated media generally, where homeservers aren't used as CDNs. Media should be downloaded and
sent externally, or forwarded/re-sent within Matrix, instead.

## Alternatives

As discussed in [issue #1949](https://github.com/matrix-org/matrix-spec/issues/1949), the following
major alternatives exist. Some additional minor alternatives are discussed in the slides for
[this Matrix Conference 2024 talk](https://2024.matrix.org/documents/talk_slides/LAB4%202024-09-21%2010_45%20Travis%20Ralston%20-%20Authenticated%20Media%20&%20How%20to%20ship%20spec%20features.pdf).

### Timed/hashed query parameters

This is a common practice for accessing CDN-served content, where a time-limited or single-use expiring
key is appended to the URL which authenticates the user. Discord and other messaging platforms also
use this to serve their media.

This proposal discounts timed query parameters due to the keys appearing in server logs, and potential
client-side hashing requirements to generate URLs.

### Replacing the authentication mechanism entirely for media

Implied throughout issue #1949 is a *replacement* to how media authentication is done rather than an
additive mechanism. This proposal prefers to introduce something additive, at increased threat/risk
surface, to avoid having to migrate significant portions of the ecosystem to yet another different
mechanism.

## Security considerations

Cookie authentication can be dangerous if handled improperly: cookies set by other sites or subdomains
could interfere with a user's ability to call the Client-Server API, or change the identity of a user
requesting a piece of media, causing a potential flag on their account for downloading something they
shouldn't (if a server tracks this).

Security of the cookie is left as an implementation detail, like how access token refresh periods and
formatting are left as implementation details. Some implementations may choose insecure values, like
73 year expiration or being valid on any domain. Implementations are encouraged to not do that.

The scope of cookie authentication is intentionally limited to reduce the amount of surface area a
compromised cookie has. This may be an unnecessary limitation, and discussion about whether to extend
cookie auth to the entire Client-Server API is encouraged.

## Unstable prefix

While this proposal is not considered stable, implementations should use `org.matrix.msc4250.set_auth_cookie`
instead of `set_auth_cookie` throughout this proposal. Cookie keys/values are not subject to unstable
namespacing due to being implementation details.

## Dependencies

This proposal has no direct dependencies.
