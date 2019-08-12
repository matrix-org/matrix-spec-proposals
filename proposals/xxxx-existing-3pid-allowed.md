# Allowing 3PID Owners to Rebind

This is a proposal to allow 3PID owners to rebind their 3PIDs using the `POST
/_matrix/client/r0/account/3pid/email/requestToken` endpoint. The spec
currently states that if a user tries to call this endpoint with an email
address they already own, then the request should be rejected.

This MSC calls for those requests to be accepted iff the requesting user
currently has the 3PID bound to their Matrix ID, marking them as the user in
control of this 3PID.

This would allow users to bind their 3PIDs to different servers, even if the
homeserver has already been made aware of it.

--- TODO, below ---

## Proposal

*Here is where you'll reinforce your position from the introduction in more detail, as well as cover
the technical points of your proposal. Including rationale for your proposed solution and detailing
why parts are important helps reviewers understand the problem at hand. Not including enough detail
can result in people guessing, leading to confusing arguments in the comments section. The example
here covers why templates are important again, giving a stronger argument as to why we should have
a template. Afterwards, it goes on to cover the specifics of what the template could look like.*

Having a default template that everyone can use is important. Without a template, proposals would be
all over the place and the minimum amount of detail may be left out. Introducing a template to the
proposal process helps ensure that some amount of consistency is present across multiple proposals,
even if each author decides to abandon the template.

The default template should be a markdown document because the MSC process requires authors to write
a proposal in markdown. Using other formats wouldn't make much sense because that would prevent authors
from copy/pasting the template.

The template should have the following sections:

* **Introduction** - This should cover the primary problem and broad description of the solution.
* **Proposal** - The gory details of the proposal.
* **Tradeoffs** - Any items of the proposal that are less desirable should be listed here. Alternative
  solutions to the same problem could also be listed here.
* **Potential issues** - This is where problems with the proposal would be listed, such as changes
  that are not backwards compatible.
* **Security considerations** - Discussion of what steps were taken to avoid security issues in the
  future and any potential risks in the proposal.
* **Conclusion** - A repeat of the problem and solution.

Furthermore, the template should not be required to be followed. However it is strongly recommended to
maintain some sense of consistency between proposals.


## Tradeoffs

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


## Security considerations

*Some proposals may have some security aspect to them that was addressed in the proposed solution. This
section is a great place to outline some of the security-sensitive components of your proposal, such as
why a particular approach was (or wasn't) taken. The example here is a bit of a stretch and unlikely to
actually be worthwhile of including in a proposal, but it is generally a good idea to list these kinds
of concerns where possible.*

By having a template available, people would know what the desired detail for a proposal is. This is not
considered a risk because it is important that people understand the proposal process from start to end.


## Conclusion

*Repeating the problem and solution in different words helps reviewers understand the problem a bit more.
This section should wrap up any loose ends left in the document, as well as cover a brief overview of the
content in each section. Note that the example here doesn't touch on the specific implementation details
described in the "Proposal" section - just the high-level points made there.*

Not having a template for people to follow when making their proposals could lead to large differences
between each MSC. This would make it difficult for reviewers, and there's a potential that some information
could be left out by accident. A template written in the same format the proposal process requires would
give authors the ability to understand how to better explain their own proposal.

A descriptive template would help potential authors comprehend what the proposal process requires by
demonstrating what is expected of a proposal. Although this is more effort up front, it would lead to more
time saved in the future due to questions about the process.
