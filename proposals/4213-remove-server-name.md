# MSC4213: Remove `server_name` parameter

[MSC4156] deprecated the `server_name` parameter on [`/_matrix/client/v3/join/{roomIdOrAlias}`]
and [`/_matrix/client/v3/knock/{roomIdOrAlias}`] in favor of a new parameter `via`. This change
shipped in [Matrix v1.12]. In line with the [deprecation policy], the `server_name` parameter
is now eligible for removal from the spec.


## Proposal

The deprecated `server_name` parameter is removed from [`/_matrix/client/v3/join/{roomIdOrAlias}`]
and [`/_matrix/client/v3/knock/{roomIdOrAlias}`].


## Potential issues

None. Servers can continue advertising support for earlier versions of the spec that included
`server_name` via [`/_matrix/client/versions`].

As of writing, the following stable implementations of [MSC4156] are known to the author:

- synapse: https://github.com/element-hq/synapse/pull/17650
- dendrite: https://github.com/matrix-org/dendrite/pull/3438
- matrix-js-sdk: https://github.com/matrix-org/matrix-js-sdk/pull/4381
- ruma: https://github.com/ruma/ruma/pull/1891
- trixnity: https://gitlab.com/trixnity/trixnity/-/merge_requests/478


## Alternatives

None.


## Security considerations

None.


## Unstable prefix

None.


## Dependencies

None.


[`/_matrix/client/v3/join/{roomIdOrAlias}`]: https://spec.matrix.org/v1.12/client-server-api/#post_matrixclientv3joinroomidoralias
[`/_matrix/client/v3/knock/{roomIdOrAlias}`]: https://spec.matrix.org/v1.12/client-server-api/#post_matrixclientv3knockroomidoralias
[`/_matrix/client/versions`]: https://spec.matrix.org/v1.10/client-server-api/#get_matrixclientversions
[Matrix v1.12]: https://spec.matrix.org/v1.12/changelog/v1.12/
[MSC4156]: https://github.com/matrix-org/matrix-spec-proposals/pull/4156
[deprecation policy]: https://spec.matrix.org/v1.12/#deprecation-policy
