# MSC3383: Include destination in X-Matrix Auth Header

Currently, a federation request can't be validated mid-flight without talking
to both the originating server and the destination server. The originating
server needs to be asked for its key, and the destination server for its
`server_name`, because the `Host` header does not necessarily contain the
`server_name` of the destination server, if delegation via `.well-known` is
being used.

This hasn't been a problem so far, as the `server_name` of the destination is
usually known when validating the `Authorization` header, it's the
`server_name` of the matrix server that's doing the validation. But there's two
scenarios where this might not be the case: Forward proxies (that act as an API
gateway for enforcing additional rules), or Matrix Homeservers implementing
vhosting and have multiple `server_name`s pointing to the same `Host`.

## Proposal

In addition to the currently present `origin`, `key` and `sig` fields, the
`Authorization` header of the scheme `X-Matrix` used in the Matrix S2S API
should also include a `destination` field, which contains the `server_name` of
the Matrix Homeserver that the request is being sent to.

## Potential issues

Server implementations could theoretically be affected by this change,
depending on how the header is parsed, which would cause failures in verifying
the authenticity of the requests. This would be fatal, as it would mean that
federation would stop working. Luckily, from an initial assessment, it seems
that all major implementations work here, the parsing implementations in
Synapse, Dendrite, Conduit, Sydent and SyTest looks like it'd gracefully handle
this addition without any trouble.

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
