# MSC3987: Push actions clean-up

There are [two defined push rule actions](https://spec.matrix.org/v1.6/client-server-api/#actions)
which are of dubious use:

* `coalesce` is defined, but unused in the spec and not implemented on any homeservers [^1]
  or clients [^2] beyond validating it or treating it identically to `notify`.
* `dont_notify` is a no-op, but frequently used as a way to denote do nothing.
  It is clearer to provide an empty list of actions to avoid a situation where
  additional actions are given with it, e.g. `["notify", "dont_notify"]` is
  currently valid, but does not make sense. [^3]

## Proposal

The `coalesce` push rule action is removed from the Matrix specification.

The `dont_notify` push rule action is deprecated. Homeservers and clients should
ignore it. Any [pre-defined rules](https://spec.matrix.org/v1.6/client-server-api/#actions)
which include the `dont_notify` action are redefined to have an empty list of actions:

* `.m.rule.master`
* `.m.rule.suppress_notices`
* `.m.rule.member_event`

It is recommended that homeservers continue accepting the `coalesce` and `dont_notify`
actions, but ignore them during processing. (Treating them as no-ops.) A future
Matrix spec version should remove them completely.

## Potential issues

A client might attempt to create a push rule with a `coalesce` or `dont_notify`
action that homeservers will reject as an unknown action.

## Alternatives

Do nothing and continue propagating confusion.

## Security considerations

None.

## Dependencies

None.

[^1]: [Dendrite](https://github.com/search?q=repo%3Amatrix-org%2Fdendrite+CoalesceAction+NOT+path%3A%2F_test.go%24%2F&type=code),
[Synapse](https://github.com/search?q=repo%3Amatrix-org%2Fsynapse+coalesce+language%3ARust&type=code&l=Rust),
[Conduit](https://gitlab.com/search?search=coalesce&nav_source=navbar&project_id=22083768&group_id=4616224&search_code=true&repository_ref=next),
[Construct](https://github.com/matrix-construct/construct/blob/4ecf1ef037ecc1a5d1e3a1049d9a63cb0a6f3455/matrix/push.cc#L739-L740)..

[^2]: [matrix-js-sdk](https://github.com/search?q=repo%3Amatrix-org/matrix-js-sdk%20Coalesce&type=code),
[matrix-ios-sdk](https://github.com/search?q=repo%3Amatrix-org%2Fmatrix-ios-sdk%20coalesce&type=code),
[matrix-rust-sdk](https://github.com/matrix-org/matrix-rust-sdk/commit/59edc22a35c4ef162ea0a8cafccdf25e37ab1070),
[matrix-android-sdk2](https://github.com/search?q=repo%3Amatrix-org/matrix-android-sdk2%20ACTION_COALESCE&type=code),
[Ruma](https://github.com/search?q=repo%3Aruma/ruma%20Coalesce&type=code).

[^3]: It has been noted on recent MSCs that new rules should not use `dont_notify`,
see [MSC3786](https://github.com/matrix-org/matrix-spec-proposals/pull/3786#discussion_r864607531),
[MSC2153](https://github.com/matrix-org/matrix-spec-proposals/pull/2153#discussion_r450188777) /
[MSC2677](https://github.com/matrix-org/matrix-spec-proposals/pull/2677#discussion_r879701007).
