# MSC4417: URL Previews via Appservices

Matrix provides an API to do a "URL Preview" whereby the client can ask the homeserver to perform a
URL lookup, and return some presentation data to show a hint as to what the URL contains. This is
performed server-side as not all clients are able to perform their own lookup (e.g. Web clients are
usually prevented by [CORS](https://developer.mozilla.org/en-US/docs/Glossary/CORS)).

In most cases, servers can only do unauthenticated requests which means that URL previews become mostly
useless in environments where a lot of resources are blocked behind things such as SSO. For many reasons,
it's neither plausible to augment the client to do these lookups nor modify the homeserver to support
specific services.

This proposal suggests using a new Appservice API to offload URL lookups to services that already
have authenticated access on behalf of a user, are homeserver agnostic by design, and can even generate
previews without making any HTTP hits for better privacy (e.g. by using local caches).

## Proposal

A new endpoint is introduced on the Application Service API `GET /_matrix/app/v1/media/preview_url`, which takes:

 - (**required**) `url`  which must be a URI that conforms to [RFC3986](https://datatracker.ietf.org/doc/html/rfc3986), matching the C-S API endpoint.
 - (optional) `user_id` which must be the user who requested the preview. For future proofing this may be omitted if the HS doesn't know which user requested (e.g. anonymous access or federated request)

The response format should match that of [`GET /_matrix/client/v1/media/preview_url`](https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv1mediapreview_url).

Additionally, the registration file also includes a new RegEx pattern, `preview_urls`:

```yaml
id: "GitHub Bridge"
...
namespaces:
  users:
    ...
  aliases:
    ...
  preview_urls:
    - regex: "https:\/\/github.com.*"
      exclusive: false
```

When a homeserver receives a request to preview a URL via `GET /_matrix/client/v1/media/preview_url`, it MUST
first check all appservices to see if any contain a matching entry in `namespaces.preview_urls`. For each matching
appservice, the homeserver should make a request to `/_matrix/app/v1/media/preview_url`.

The appservice should handle the request appropriately by sending a HTTP 200 response with
the required data. If the AS response with another status code, the homeserver should try the next
matching application service **UNLESS** the namespace is marked as exclusive. If no service can handle the request,
then the homeserver MAY perform a lookup itself.

The homeserver MAY choose to respect any caching headers returned by the application service, but it MUST
also ensure caches are keyed by the user who requested it. It's also acceptable for the homeserver to avoid
caching the request in favour of the application service handling the caching.

### Media

[URL Previews require](https://spec.matrix.org/latest/client-server-api/#get_matrixclientv1mediapreview_url) that
the `og:image` specified in OpenGraph data be in MXC format. The appservice MUST do this upload step and respond
to the homeserver with a MXC URI.

## Potential issues

### Performance

There would be a small penalty paid on URL previews made as the homeserver would need to make extra requests to
appservices, potentially magnifying the impact whenever a client requests a preview.

This is potentially countered by the homeserver applying sane rate limits on the C-S API per user, and the
appservice applying sane caching on the same requests. Since the appservice is expected to have greater context
about the specific service being requested, it may be able to handle this with greater effect.

## Alternatives

### Clients perform their own URL Previews

The obvious alternative to this is that clients perform their own URL previews, which is the most privacy preserving mechanism
as no backend service other than the URL host itself will see the request, however:

  - This is not possible for pure web clients, which is still a large number of Matrix users.
  - Clients may not want to store the authentication details of a wide array of services.
  - For sites that do not follow the opengraph standard, it may be hard for clients to support. Appservices can be specific and workaround this.

### [MSC4095 Bundled URL previews](https://github.com/matrix-org/matrix-spec-proposals/pull/4095)

Another proposal exists which suggests that Matrix events instead bundle the URL preview data, which again is useful
from privacy perspective because it reduces the leakage of event information, but would not be suitable for authenticated
services as it would also expose this information to everyone in the room.

## Security considerations

### Encrypted Rooms

While this proposal does not seek to change the advice on
[`GET /_matrix/client/v1/media/preview_url`](https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv1mediapreview_url)
where "Clients should consider avoiding this endpoint for URLs posted in encrypted rooms", it's worth
mentioning that this feature would therefore be primarily useful to unencrypted rooms which is not the
direction much of Matrix is moving towards.

Due to the limitations mentioned in the introduction, it's not easy to provide an alternative mechanism
to handle URL previews without reducing the user's privacy. Therefore, this proposal will continue to build
upon this method.

### Increased surface area

URL previews being broadcast to interested appservices means that it's possible for those services to
track what users are doing on their clients. However, this is already reasonably possible by simply
configuring an AS to read all events for a user, or listening for read receipts / presence. The regex
pattern matching is a reasonable defence to limit the amount of information appservices receive.

## Unstable prefix

While this proposal is unstable:
 - `GET /_matrix/app/preview_url` becomes `GET GET /_matrix/app/unstable/uk.half-shot.msc4417/preview_url`
 - `namespaces` -> `preview_urls` becomes `namespaces` -> `uk.half-shot.msc4417.preview_urls`

## Dependencies

None.
