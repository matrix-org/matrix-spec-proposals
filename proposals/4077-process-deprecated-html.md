# MSC4077: Improved process for handling deprecated HTML features

The Matrix specification [defines](https://spec.matrix.org/v1.8/client-server-api/#mroommessage-msgtypes)
a subset of HTML which clients *should* use when rendering messages, limiting the possibility for
Cross-Site Scripting (XSS) and similar attacks. Clients are always welcome to use a different subset
in both their send and receive paths, however in practice the recommended set of HTML has become the
baseline standard for support among Matrix client developers.

Additionally, to fix issues like [tags being deprecated](https://github.com/matrix-org/matrix-spec/issues/1492),
the existing spec process would require an entire MSC to add or remove the tag. This has precedent
through [MSC2422](https://github.com/matrix-org/matrix-spec-proposals/pull/2422) and
[MSC2184](https://github.com/matrix-org/matrix-spec-proposals/pull/2184), where additional HTML
features are analyzed from a security perspective. For example, whether XSS attacks are more probable
or flooding/disruption attempts are made easier.

This proposal adjusts the MSC process to explicitly allow changes to the supported HTML tags where
the WHATWG has deprecated a feature in favour of another, enabling more rapid iteration and reducing
paperwork for everyone involved.

## Proposal

Where the WHATWG has deprecated a feature of the HTML specification, a Matrix spec PR *may* bypass the
MSC process to use the modern feature instead. In the case of [issue#1492](https://github.com/matrix-org/matrix-spec/issues/1492),
the spec PR is explicitly able to add the `s` tag and remove the `strike` tag. Note that such changes
can also bypass the [deprecation policy](https://spec.matrix.org/v1.8/#deprecation-policy) in this way.

It is left to the discretion of the spec PR reviewer as to whether an MSC is required. In general, an
MSC should be requested when the replacement HTML feature is not quite the same as the old feature.
The reviewer *may* also decide whether to keep supporting the old, deprecated, feature for some time.
For example, replacing `strike` with `s` may mean that both tags are supported for 1-2 Matrix spec
versions before `strike` can be dropped.

For clarity, an MSC is always required to add net-new features to the HTML subset, or to remove a
feature entirely. An example of this is [MSC2398](https://github.com/matrix-org/matrix-spec-proposals/pull/2398).
These changes are subject to interoperability and security review, and cannot bypass the MSC process.

## Potential issues

The author notes that this MSC might not need to exist under the banner of pragmatism, however for all
the effort to *not* write an MSC, an MSC has been written for review.

## Alternatives

Critically, without agreement that replacing deprecated HTML features can happen outside the MSC process,
changes to the HTML subset become slow and burdensome for no apparent gain.

## Security considerations

Special care and attention is expected to be taken by spec PR reviewers to ensure that changes are
safe and in line with the semantics of this proposal's guidance.

## Unstable prefix

Not applicable. This is a process MSC.

## Dependencies

None applicable.
