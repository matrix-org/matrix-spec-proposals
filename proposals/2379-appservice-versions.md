# MSC 2379: Add supported appservice version to registration information. 

The [AS registration format](https://matrix.org/docs/spec/application_service/r0.1.2#registration) does
not have a way to specify what version of the spec that bridges support. This means that if the path
of any of the appservice endpoints were to change in the spec, homeservers would not be able to
intelligently discover the paths that a bridge supports.

## Proposal

The `registration` file should contain one new key: `as_version`.

The value of the key should be set to the AS API version (`rX.X.X`) that the bridge supports. This
key SHOULD be specified by all bridges. When set, the homeserver MUST send requests to the endpoints
specified by that version of the AS spec.

Homeservers may optionally support an omitted value, which will make it support the legacy paths used
by Synapse `<=1.6.X`.

The legacy paths omit the /_matrix/app/{version} prefix entirely for:

    - `/_matrix/app/{version}/transactions/{txnId}` becomes  `/transactions/{txnId}`
    - `/_matrix/app/{version}/users/{userId}` becomes  `/users/{userId}`
    - `/_matrix/app/{version}/rooms/{txnId}` becomes  `/rooms/{roomAlias}`

Additionally, the `{version}` for the Third party network routes is always set to `unstable`.

It should be reiterated that support for this is up to the homeserver implemetor. Homeservers may
refuse to load appservices that do not include this `key`.

## Potential issues

Keeping a 'legacy' mode around in the spec sucks, because it's horribly non-compliant to the version system.
However, most of the ecosystem has been modeled over Synapse behaviours which means this spec change would break
support for bridges if implemented by Synapse. This option remains the most pragmatic option. In a future version
of the spec, this mode could be removed.

## Alternatives

A /versions endpoint could be defined for the bridge to host, but this feels overcomplicated when the
registration format could also work.


## Security considerations

None
