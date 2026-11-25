# MSC4586: Flag to explicitly persist URL preview assets

URL preview assets (external images that are proxied by the homeserver) have always been ephemeral
in Synapse, and Synapse supported URL previews before they were added to the specification.
[MSC4095: Bundled URL previews][MSC4095] also amended URL preview behaviour to state that clients
SHOULD re-upload assets retrieved from the [`/_matrix/client/v1/media/preview_url`][spec-preview] if
they are going to be bundled into the final event, in order to benefit from encryption, but also so
that the content URIs included in the bundle are guaranteed to be persistent.

[spec-preview]: https://spec.matrix.org/v1.19/client-server-api/#get_matrixclientv1mediapreview_url
[MSC4095]: https://github.com/matrix-org/matrix-spec-proposals/pull/4095

This proposal introduces a new flag to the URL preview endpoint, `persist_assets`, which will
ask that the server retains the preview assets forever[^1], which removes the need for clients to
re-upload content in unencrypted rooms.

[^1]: It is common practice for homeservers to apply media retention limits to both local and remote
media. "Forever" in this case refers to the normal retention lifetime provided by the deployment, it
does not mean that the server is required to ignore any retention configuration.

## Proposal

A new query parameter is added to [`GET /_matrix/client/v1/media/preview_url`][spec-preview]:
`persist_assets`. The value is a boolean, and defaults to `false` when omitted.

When receiving `?persist_assets=true`, homeserver SHOULD retain content downloaded from external
sites forever[^1], rather than cleaning it up on a more aggressive schedule. Without the query
parameter (or with a `false` value), the URL preview assets may be subject to
routine garbage collection.

Clients that do not [bundle URL previews][MSC4095] SHOULD NOT request persistent assets, as they
have no use for them (since they typically request new previews on demand instead).

Clients that bundle URL previews SHOULD NOT request persistent assets **when the destination room is
encrypted**. This is because the client will still need to re-upload the downloaded assets as
encrypted media - ephemeral assets will also mean the unencrypted content's lifetime is shorter,
which reduces the amount of time potentially sensitive content can reside on the server.

Clients that bundle URL previews SHOULD request persistent assets when sending URL previews to
unencrypted rooms. These assets do not need re-encrypting, so the URI returned by the server can be
used forever without needing a client to modify it.

## Potential issues

Clients that do not understand this proposal will not request persistent media, and this may invoke
surprising behaviour in some clients (e.g. suddenly missing preview thumbnails). This is considered
acceptable as this was already the case when using Synapse
(see: [`element-hq/element-web#30238](https://github.com/element-hq/element-web/issues/30238)), so
the functional difference should be minimal.

Clients may end up asking the server to persist a lot of external assets that may never be viewed
again. Servers are encouraged to treat external assets as remote media, and apply standard media
retention policies as normal[^1] to avoid excessive buildup of unused media.

## Alternatives

None

## Security considerations

None

## Unstable prefix

`uk.timedout.msc4586.persist_assets` MUSt be used as a query parameter instead of `persist_assets`
while this proposal is unstable.

Servers MUST advertise `uk.timedout.msc4586` in their `unstable_features` section of
`/_matrix/client/versions`, so that clients can determine whether the persist feature is supported.
If this proposal is accepted, `uk.timedout.msc4586.stable` can be advertised transitionally until
the proposal is included in a specification release to use the stable values.

Clients MUST ensure that the unstable prefix or a relevant specification version is advertised in
the client versions endpoint before using the flag. No advertisement means the feature is
unsupported, the query parameter will be ignored, and the client will be sad when the external
assets disappear in the future.

## Dependencies

None
