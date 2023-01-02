# MSC3383: Include destination in X-Matrix Auth Header

Currently, a federation request can't be
[validated](https://spec.matrix.org/v1.2/server-server-api/#request-authentication)
mid-flight without some
convoluted workarounds, because federation requests don't contain the
`server_name` of the destination. The `Host` header does not necessarily contain
the `server_name` of the destination server, if delegation via `.well-known` is
being used. It's currently possible to get the `server_name` by making a
request to `/_matrix/key/v2/server/{keyId}`, and then resolving the delegation
for the contained `server_name` back to the `Host` included in the original
request.

This hasn't been a problem so far, as the `server_name` of the destination is
usually known when validating the `Authorization` header, it's the
`server_name` of the matrix server that's doing the validation. But there's two
scenarios where this might not be the case: Forward proxies (that act as an API
gateway for enforcing additional rules), or Matrix Homeservers implementing
vhosting and have multiple `server_name`s pointing to the same `Host`.

### Example: rule enforcing forward proxy

Let's assume we have an organization running a matrix server in a protected
network, that doesn't have direct internet access. The organization only allows
access to the internet through a forward proxy enforcing additional security
measures.

For matrix federation, it's supposed to verify the matrix servers are on a list
of allowed `server_name`s. As explained in the introduction, the `server_name`
is not contained in the request, so verifying these requests is not possible
without the workaround described in the introduction.

Alternatively to that, it'd be also possible to keep a map for allowed
`server_name`s to `Host` headers, but that needs to be updated regularly, to
make sure it doesn't get stale.

Both of these workarounds are more complicated than they need to be. If the
`server_name` was included in the `Authorization` header, these workarounds
could be completely avoided.

## Proposal

In addition to the currently present `origin`, `key` and `sig` fields, the
`Authorization` header of the scheme `X-Matrix` used in the Matrix S2S API MUST
also include a `destination` field, which contains the `server_name` of the
Matrix Homeserver that the request is being sent to.

A Matrix Homeserver receiving a request over the S2S API SHOULD gracefully
handle requests that do not include the `destination` field in the
`Authorization` header for backwards compatibility.

When a matrix homeserver receives a request over the S2S API for a
`destination` that is not the `server_name` (or one of the `server_name`s in
case of vhosting) of itself, it should deny that request with an HTTP status
code 401 - Unauthorized.

## Potential issues

Server implementations could theoretically be affected by this change,
depending on how the header is parsed, which would cause failures in verifying
the authenticity of the requests. This would be fatal, as it would mean that
federation would stop working. Luckily, from an initial assessment, it seems
that all major implementations work here, the parsing implementations in
Synapse, Dendrite, Conduit, Sydent and SyTest looks like it'd gracefully handle
this addition without any trouble. The other way around is also a concern: Newer
implementation might be confronted with federating with an old implementation,
which does not send the `destination` in it's auth headers. This is explicitly
mentioned in the proposal though, advocating for graceful handling of these
situations if possible.

## Alternatives

For the forward proxy scenario, it'd be possible to use the
`/_matrix/key/v2/server` endpoint for fetching the `server_name` when receiving
a request. After that though, the `server_name` has to be resolved back to a
`Host`, for making sure that the domain owner of `server_name` actually intends
for requests for `server_name` to go to the host in `Host`. This is
unnecessarily complex and prone to error, which is why it'd be better to have
that included.

For the vhosting scenario, it'd be possible to have a different hostname to
delegate to for each vhost. That means that wildcard DNS records and
certificates have to be used though, to make it manageable to allow anyone
pointing a `server_name` against a certain service. This is a limitation that
might be problematic in certain setups, which is why I'd be better to not force
that.

## Security considerations

I can't think of anything required in this section for this MSC, but I'm open
to input.
