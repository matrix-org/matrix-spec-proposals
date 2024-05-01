# MSC4025: Local user erasure requests

Long ago a need arose for having a user specify that they'd like to not just deactivate their account,
but also *erase* as much of their content as possible for largely GDPR purposes. This got implemented
in the matrix-js-sdk as [PR #649](https://github.com/matrix-org/matrix-js-sdk/pull/649), but never
quite made it to the spec.

Back in 2018 the proposal process was very different (technically didn't actually exist at the time
the js-sdk PR was written). A [spec omission issue](https://github.com/matrix-org/matrix-spec/issues/297)
was opened to track the missing property, however [an attempt](https://github.com/matrix-org/matrix-spec-proposals/pull/1290)[^1]
to do the documentation got blocked on having a larger GDPR-centric proposal.

Eventually, [MSC2438](https://github.com/matrix-org/matrix-spec-proposals/pull/2438) was drafted,
presumably to be that GDPR/erasure-specific MSC the prior spec PR was waiting for. Unfortunately, it
appears to have gotten stuck in various stages of drafting.

It's highly regrettable that yet another spec change from 2018 has managed to go unspecified for so
long. Theoretically, the change could go through as a spec PR (much like the one linked above) rather
than as a proposal, however there is significant interest in giving the feature a formal chance to be
*rejected* as a solution under the modern spec proposal process.

This MSC serves as that opportunity. While a more comprehensive system could be designed, such as in
MSC2438, this MSC has a very narrow and specific scope of what was implemented back in 2018. For the
spec process, this translates to accepting the feature as-is, or rejecting it and flagging the client
behaviour non-compliant.

## Proposal

A new optional boolean is added to the request body of [`POST /deactivate`](https://spec.matrix.org/v1.7/client-server-api/#post_matrixclientv3accountdeactivate):
`erase`. It defaults to `false` and signifies whether the user would like their content to be erased
as much as possible.

Erasure does *not* mean issuing redactions for all of the user's sent events, but does mean that any
users (or servers) which join the room after the erasure request are served redacted copies of those
events. Users which had visibility on the event prior to the erasure are able to see unredacted copies.

The server should additionally erase any non-event data associated with the user, such as account
data and [contact 3PIDs](https://spec.matrix.org/v1.7/client-server-api/#adding-account-administrative-contact-information).

This is in line with what Synapse does, as referenced [here](https://github.com/matrix-org/synapse/issues/8185).

This is also what is described by the [matrix.org blog post](https://matrix.org/blog/2018/05/08/gdpr-compliance-in-matrix)
on GDPR compliance.

## Potential issues

Erasure requests are not sent over federation in this model, meaning servers which already have an
unredacted copy of the event will continue to serve that to their users after the erasure happened.
Servers are expected to be informed out of band of erasure requests that affect them, if they affect
them.

## Alternatives

[MSC2438](https://github.com/matrix-org/matrix-spec-proposals/pull/2438) is the leading alternative,
however as specified in the introduction for this proposal, the desired outcomes of this MSC are either
acceptance as-written or rejection. Ideally, if rejected, another MSC or idea is marked as the suitable
alternative.

Redactions could be sent for all the user's events, however this has obvious performance impact on
servers and rooms. The [matrix.org blog](https://matrix.org/blog/2018/05/08/gdpr-compliance-in-matrix)
discusses how redactions and GDPR Right to Erasure interact (or rather, how they aren't the same).

## Security considerations

This feature was originally introduced primarily in response to the GDPR Right to Erasure requirement
within the European Union. The privacy benefits apply to all users of the ecosystem and there's no clear
reason to region-lock or otherwise leave this as an implementation detail for EU-operated homeservers.

There are however consequences of GDPR erasure that are not covered by this proposal, such as the
deletion of server logs, forwarding the request, etc. Server operators are encouraged to seek legal
advice on how to handle this form of erasure request (and whether it qualifies under GDPR's Right to
Erasure requirements). The general recommendation is to enforce the erasure request as much as possible
on the local homeserver, including redacting/purging server logs, appservice data, etc.

## Unstable prefix

Even more regrettably than having unspecified behaviour, this feature was implemented before unstable
namespaces existed. Implementations can use `erase` without prefix.

<!-- Footnotes below here (github draws this as a real line in the rendered view) -->

[^1]: Readers should note that the spec-proposals repo used to contain both the spec itself and proposals
to change the spec. This was later split into dedicated repos, but closed PRs and issues were not migrated.
