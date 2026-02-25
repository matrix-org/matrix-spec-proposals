# MSCXXXX: Request state via `/messages`

Today, clients use
[`GET /_matrix/client/v3/rooms/{roomId}/messages`](https://spec.matrix.org/v1.6/client-server-api/#get_matrixclientv3roomsroomidmessages)
to fetch historical events from a room's timeline. The client can optionally provide a `from` and/or `to`
pagination token and a `limit` parameter in order to define a chunk of the timeline to return. This chunk
of events includes both state and non-state events.

The response of `/messages` today includes room state that was modified in the requested chunk, but it does not
include what the state of the room was at the beginning of the chunk. Thus, clients aren't able to tell what
the historical state of the room was at a given event, unless they make a separate request to
[`GET /_matrix/client/v3/rooms/{roomId}/context/{eventId}`](https://spec.matrix.org/v1.6/client-server-api/#get_matrixclientv3roomsroomidcontexteventid). If a client needs to know the state of the room at each historical
message, then doing so doubles the requests a client needs to perform to display the timeline.

But clients don't make `/context` requests when paginating the timeline today - so why is this needed now, you may ask?
The truth is that there are lots of potential use cases that are not currently possible in a performant manner. Some
use cases for clients knowing that state of a given event while paginating are:

- Self-destructing messages
    - If you wanted to set a room-wide timer for messages sent in a room to be automatically deleted (like
      [MSC2228](https://github.com/matrix-org/matrix-spec-proposals/pull/2228) calls for), that would be
      best done by modifying the room state. When the room's state was changed is important, as the self-destruct timer
      may be changed throughout the life of the room. When paginating through message history, clients will need to know
      the state of the room at the time the message was sent in order to display when a given message will self-destruct.
      Currently clients could only do this by making a `/context` request for every event returned by `/messages`, which
      would be very slow.
- The color of messages should be set to something specific at that point in the timeline
- In general when you want to change how messages are displayed globally in the room... might be useful for
  self-destructing messages use case actually...
    - Depending on what the state of the room was when a message was sent, the client would assign a given
      expiry time. That works for /messages yes. But what about the initial timeline? I guess you'd have to spider back. 
- If you want to room-specific, arbitrary information to a user that has historical significance.
    - We already do this for membership information, which is special-cased on whether lazy-load members
      is enabled. But if it's not enabled... how do we construct old membership information? Maybe we spider.
- ...?
- Displaying profile information about a user next to their message from the point in time that message was sent.

The last point clients already do today. This is possible due to `/messages`
already returning `m.room.member` state events in the `state` field of its
response for the senders of the events in the returned chunk (if lazy loading
is enabled).

Does `dir` influence which state should be returned? Ideally not I would say, 


*Note: Text written in italics represents notes about the section or proposal process. This document
serves as an example of what a proposal could look like (in this case, a proposal to have a template)
and should be used where possible.*

*In this first section, be sure to cover your problem and a broad overview of the solution. Covering
related details, such as the expected impact, can also be a good idea. The example in this document
says that we're missing a template and that things are confusing and goes on to say the solution is
a template. There's no major expected impact in this proposal, so it doesn't list one. If your proposal
was more invasive (such as proposing a change to how servers discover each other) then that would be
a good thing to list here.*

*If you're having troubles coming up with a description, a good question to ask is "how
does this proposal improve Matrix?" - the answer could reveal a small impact, and that is okay.*

There can never be enough templates in the world, and MSCs shouldn't be any different. The level
of detail expected of proposals can be unclear - this is what this example proposal (which doubles
as a template itself) aims to resolve.


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
* **Potential issues** - This is where problems with the proposal would be listed, such as changes
  that are not backwards compatible.
* **Alternatives** - This section lists alternative solutions to the same
  problem which have been considered and dismsissed.
* **Security considerations** - Discussion of what steps were taken to avoid security issues in the
  future and any potential risks in the proposal.

Furthermore, the template should not be required to be followed. However it is strongly recommended to
maintain some sense of consistency between proposals.


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
