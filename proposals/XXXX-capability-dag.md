# MSC0000: Replacing power levels with capabilities.

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

## The authority of homeservers

Within Matrix, homeservers inherit any authority that any of its users has because of the power to
impersonate users. This is especially true when a user on a homserver posses the the power level to
change `m.room.power_levels`, as this means the server can then transfer power to any of its users.

Homeserver also have the authority to generate any number of `m.room.member` state events for any
Matrix room where the `m.room.join_rules` is `public`. On top of this, if we want to restrict who
can generate joins, the `m.room.server_acl` event has to anticipate the existance of any malicious
server (if the allow rule is `*`) and is an entirely reactive measure.
On top of this there is also a limit to the servers that can be allowed and denied in the
`m.room.server_acl` event.

It is also the norm on Matrix for `events_default` and `users_default` to both be 0, giving
any new user the ability to post a message without restriction. This is because
`m.room.power_levels` is very inflexible and it is known that by changing it frequently,
you increasce the depth of the auth dag which is a recognised risk for increasing the
chance of experiencing a state reset.
A single Matrix event is also just not practical for special casing the capabilities of thousands of
users.

We recognize there is some hesitancy to acknowledge the role of the homeserver within Matrix,
because it poses questions about how distributed vs decentralised Matrix is.
We also worry what recognizing the authority of homeservers would do for plans to "make Matrix p2p".
As far as we are aware, attempts to "make Matrix p2p" merely provide a homeserver with the client.
So we do not see a cause for conflict.

## Reshaping event authorization to canonicalise and manage the authority of homeservers.

### What's going on now

Currently the authority of homeservers within Matrix has to be inferred from which users have
power in the room, and the homeservers that they are on. As we discussed earlier,
homeservers have the power to impersonate users to make changes on their behalf, as well
as to join any new user to the room should the `m.room.join_rule` be `public`
or they have a user which posses the power level to `invite`.
This means that apart from a few special cases, membership is entirely (a word,
that's like transparent, but basically it isn't relevant to a homserver once it already
has a user that is in the room). Yet it remains part of the auth dag.

### So?

Instead we propose that membership of users be forgoed entirely and that instead server
membership is the only part of membership that is relevant to event authorization
(I believe this idea has been discussed by Kegan and Till before but I got the idea from Kegan).

If we take this view, then what happens to user membership?
In order to keep users out of the auth dag, their membership has to be treated as entirely
[well, it's not ephemeral and it's not cosmetic].
Servers who are members who have the capability to send events have the authority
to send these events with any sender local part.

There is somewhat of a precedent for this within Matrix already in the form of application
services that provide bridging capability. Though currently these must first generate member events.

As far as we are aware, this is already the reality for the overwhelming majority of public
Matrix rooms, there just are no restrictions in place to control the provisioning of new users
by homeservers. I would like to reiterate that the reason for canonicalising this relationship
is so that we can control and restrict that. Ignoring, obscuring, delaying and
kicking the relationshihp down the road doesn't.

### A note about join conditions

FIXME

We basically want to allow join conditions to be deferred to client logic by
taking away capabilities on join.

Wait isn't joining without capabilities just knocking? Kinda tbh.
Though knocking is much more inflexible.

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

### Overview

- Server Membership, Kicks, Bans and Invites
- Server Capabilities
- Auhorization
- User Membership and Profiles
- User capabilities

### Server membership

Server membership

`m.room.server_capability.member` has membership `join`, `invite`, `knock`, `leave`, and `ban`.

#### `m.room.server_capability.member`

Instead `m.room.member` is replaced by `m.room.server_capability.member`

. o O ( should membership be tracked serpetley from.-- NO membership IS a capability)

. o O ( Capabilities are all bound by membership though? )

. o O ( capability and not capabilities bc less depth = easier )

. o O ( history visability being a capability is surely better than
....... relying on membership for that, right? not asserting that yet though )

The state key is the server name.


### Capabilities


#### `m.room.user_capability.member`

Not part of the auth dag since the authority is based entirely on the server even in current DAG.
Is always a subset of the capabilities granted to a server.

#### Events

##### `m.room.base_capabilities` state_key mxid or server name

If it's an mxid, then it's not an auth event.
If it's a server name, then it is an auth event.

Example below can give servers invite and any of its existing capabilities.

```
{
  "events": [
    "m.room.avatar",
    "m.room.canonical_alias",
    "m.room.history_visibility",
    "m.room.name",
    "m.room.base_capabilities"
  ],
  "events_default": true,
  "state_default": false,
  "ban": false,
  "kick": false,
  "invite": true,
  "redact": false,
  "notifications": {}
}
```
By default, events are not sendable.
`events`: Names events that should have dedicated capabilities that entities (servers, users) most posses to be able to send them.
`events_default`: true if any event not named in `events` should be sendable by an entity possesing `m.room.server_capability.events_default`.
`state_default`: true if any state event not named in `events` should be sendable by an entity posessing `m.room.server_capability.state_default`.

### Authorization rules

4. 4. If the `sender` possess the capability for `invite`.

5. 4. If the sender has the capability for `kick` and the target user

### Replacing Reverse topological power ordering

so instead of using power levels on tie breaks i'm gonna use origin_server_ts of the capability and
capabilities can't be granted to yourself only removed so this should be ok, also make it illegal
for auth chain origin_server_ts to be less than the event before it.

### Handling redactions

### Last member with a given capability problem.

if you're the last member to have a capability, if iti s taken away from you
it must be taken away from the server surely?

### Custom capabilities

custom caps have to be referenced by an auth event. The way to cheese this is to have an auth event
called `m.room.capability_description` with state key of the event type of the new custom entity e.g.
`org.matrix.mjolnir.command_me` then you can use your custom capability event type with a state key
that's an mxid or server id (`org.matrix.mjolnir.command_me`, `@meow:matrix.org`)

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

### Mate, how to keep servers in check.

There actually is nothing in place to keep servers in check already in regards
to joined users and things like a server sharing history or refusing to ban a user.

Well, that's not entirely true. In cases of kick, mute, ban, if the server does
ignore those, the other servers won't see it. We're moving to a system
where we don't check that at all.
But we can just ban the server i guess. That's something that
the current dag doesn't effectively allow.

Maybe members become part of the auth dag when their capabilities differ from the server.
That includes being banned.


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
