# MSC4154: Request max body size

When making requests to the homeserver, clients have a lot of freedom to include large strings and
similar. Homeserver implementations may not be prepared for long text fields, for example, and may
encounter issues or present errors to clients.

This proposal aims to place a *minimum* expectation into the specification on request sizes rather
than trying to limit individual field types to certain lengths. The obvious disadvantage is that
most endpoints accept only a few fields, so whatever limit is chosen for the whole request will need
to also apply to the database level - an API with a single field which ends up in the database will
need that column to support nearly the entire body size, as a user could feasibly pad their request
out to meet the limit.

## Proposal

A request body size limit of 1,000,000 bytes (1 MB) MUST be expected by clients on *all* Client-Server
API endpoints. If a request exceeds this limit, the client SHOULD be presented with a `413 M_TOO_LARGE`
error. The `M_TOO_LARGE` error code [already exists](https://spec.matrix.org/v1.10/client-server-api/#other-error-codes).

Servers MAY raise this limit to higher than 1 MB, but SHOULD NOT lower it below 1 MB.

This limit is applied before any endpoint-specific considerations, such as
[event size limits](https://spec.matrix.org/v1.10/client-server-api/#size-limits).

*Note*: The 1 MB requirement is fairly arbitrary. It's just what
[nginx does by default](https://nginx.org/en/docs/http/ngx_http_core_module.html#client_max_body_size).
Critically, the limit *must* be more than the 65,536 bytes permitted for events at a minimum.

Response sizes from servers are *not* affected by this proposal. For example, a `/sync` response may
exceed 1 MB.

## Potential issues

None perceived. By using a default already found in popular reverse proxy software, clients will be
subject to these limits unintentionally today. This proposal improves the error response in these
cases, hopefully.

## Alternatives

Per-field or field type size restrictions may be a better fit, though open a can of worms on what
the 'right' size should be. Limiting strings to 512 KB (for example) may mean some APIs generate way
more than 1 MB of JSON, running into the nginx default request body limit. This also doesn't address
clients including off-spec fields in their requests, such as a `/login` containing namespaced fields:
can the client send an infinite number of 512 KB strings, or is there a limit? What is that limit?

## Security considerations

This proposal technically fixes a security concern regarding unbounded requests.

## Unstable prefix

It is difficult to implement this MSC in a namespaced way. Clients may already be encountering `413`
errors without the Matrix standardized error response, and so should generally expect to receive such
errors.

## Dependencies

None relevant.
