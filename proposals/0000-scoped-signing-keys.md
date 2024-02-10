# MSC0000: Scoped signing keys

Matrix uses signing keys to authorize [requests](https://spec.matrix.org/v1.9/server-server-api/#authentication)
between servers and [events](https://spec.matrix.org/v1.9/server-server-api/#signing-events) in a room.
Servers can additionally expose multiple signing keys through the [key exchange system](https://spec.matrix.org/v1.9/server-server-api/#retrieving-server-keys).
All exposed signing keys can currently be used for either purpose: requests or events.

Following a principle of lease privilege, large distributed servers (one logical homeserver represented
by several physical servers) may prefer to narrow the capabilities of a given key. These scoped keys
can then be given to individual services within the overall homeserver system to perform exactly what
is required.

As an example, if a homeserver wishes to run an independent media repository service, that service
does not require an ability to sign events. Having a key which *can* sign events is potentially a
security risk if that system were to experience a breach of some kind.

This proposal introduces a scope to signing keys, allowing large deployments to segment their infrastructure
with narrow-access keys.

**Note**: As of writing, there are very few if any servers which actually require this functionality.
Deployments are typically monolothic, where a single (or localized to the physical server) signing
key is required to operate the service. A more suitable infrastructure for this MSC would be a
service-oriented deployment or one that uses AWS IAM to limit access to resources (for example).

## Proposal



## Potential issues

*Not all proposals are perfect. Sometimes there's a known disadvantage to implementing the proposal,
and they should be documented here. There should be some explanation for why the disadvantage is
acceptable, however - just like in this example.*

Someone is going to have to spend the time to figure out what the template should actually have in it.
It could be a document with just a few headers or a supplementary document to the process explanation,
however more detail should be included. A template that actually proposes something should be considered
because it not only gives an opportunity to show what a basic proposal looks like, it also means that
explanations for each section can be described. Spending the time to work out the content of the template
is beneficial and not considered a significant problem because it will lead to a document that everyone
can follow.


## Alternatives

*This is where alternative solutions could be listed. There's almost always another way to do things
and this section gives you the opportunity to highlight why those ways are not as desirable. The
argument made in this example is that all of the text provided by the template could be integrated
into the proposals introduction, although with some risk of losing clarity.*

Instead of adding a template to the repository, the assistance it provides could be integrated into
the proposal process itself. There is an argument to be had that the proposal process should be as
descriptive as possible, although having even more detail in the proposals introduction could lead to
some confusion or lack of understanding. Not to mention if the document is too large then potential
authors could be scared off as the process suddenly looks a lot more complicated than it is. For those
reasons, this proposal does not consider integrating the template in the proposals introduction a good
idea.


## Security considerations

*Some proposals may have some security aspect to them that was addressed in the proposed solution. This
section is a great place to outline some of the security-sensitive components of your proposal, such as
why a particular approach was (or wasn't) taken. The example here is a bit of a stretch and unlikely to
actually be worthwhile of including in a proposal, but it is generally a good idea to list these kinds
of concerns where possible.*

By having a template available, people would know what the desired detail for a proposal is. This is not
considered a risk because it is important that people understand the proposal process from start to end.

## Unstable prefix

*If a proposal is implemented before it is included in the spec, then implementers must ensure that the
implementation is compatible with the final version that lands in the spec. This generally means that
experimental implementations should use `/unstable` endpoints, and use vendor prefixes where necessary.
For more information, see [MSC2324](https://github.com/matrix-org/matrix-doc/pull/2324). This section
should be used to document things such as what endpoints and names are being used while the feature is
in development, the name of the unstable feature flag to use to detect support for the feature, or what
migration steps are needed to switch to newer versions of the proposal.*

## Dependencies

This MSC builds on MSCxxxx, MSCyyyy and MSCzzzz (which at the time of writing have not yet been accepted
into the spec).
