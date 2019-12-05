# MSC 2379: Add /versions endpoint to Appservice API. 

Bridges do not have a way to specify what version of the spec they support. This means that if the path
of any of the appservice endpoints were to change in the spec, homeservers would not be able to
intelligently discover the paths that a bridge supports.

## Proposal

A new endpoint is required, which is `/versions`. This is nearly identical to the
[C-S API](https://matrix.org/docs/spec/client_server/r0.6.0#get-matrix-client-versions) endpoint
but lacks a `unstable_features` key.

All bridges SHOULD implement this endpoint and specify which version(s) of the `AS` API they support. 
The homeserver MUST send requests to the endpoints specified by that version of the AS spec.

Homeservers may optionally support a 404 response to this endpoint, which will make it use the legacy paths used
by Synapse `<=1.6.X`.

The legacy paths omit the /_matrix/app/{version} prefix entirely for:

    - `/_matrix/app/{version}/transactions/{txnId}` becomes  `/transactions/{txnId}`
    - `/_matrix/app/{version}/users/{userId}` becomes  `/users/{userId}`
    - `/_matrix/app/{version}/rooms/{roomAlias}` becomes  `/rooms/{roomAlias}`

Additionally, the `{version}` for the Third party network routes is always set to `unstable`.

It should be reiterated that support for this is up to the homeserver implemetor. Homeservers may
refuse to load appservices that do not include this `key`.

## Potential issues

Keeping a 'legacy' mode around in the spec sucks, because it's horribly non-compliant to the version system.
However, most of the ecosystem has been modeled over Synapse behaviours which means this spec change would break
support for bridges if implemented by Synapse. This option remains the most pragmatic option. In a future version
of the spec, this mode could be removed.

## Alternatives

This proposal previously used the `registration` file as a way to specify the supported version, but
this was dropped as it was hard for the bridge to be authoritive over what version it supports. Typically
the registration format is generated once by the bridge and then handled by the homeserver. If a bridge were
to update and require a new version of the AS API, the registration data would need to be updated/regenerated.

## Security considerations

None
