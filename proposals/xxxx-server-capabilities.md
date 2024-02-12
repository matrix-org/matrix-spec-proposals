# MSC0000: Participation based authorization for servers in the Matrix DAG

This is a proposal for the representation of servers and their basic responsibilities in the Matrix
DAG. This MSC does not define or ammend a state resolution algorithm, since there are serveral possible
routes that can be explored with other MSCs. 

## Context

### The role of the existing `m.room.member` for a user

- Reperesents a desire for the user's server to be informed of new events.
- Represents the capability for the server to participate in the room on behalf of the user by sending PDU/EDUs.
- Represents the capability for the user to backfill in relation to visibility.
  + it is unclear to me whether `m.room.history_visibility` restricts a server's ability to backfill or not.
- Reperesents profile and participation information, who they are, why they are in the room, avatar, displayname.

## Proposal


### Considerations for ammending the make_join handshake

When a joining server is instructed to join a room, the joining server sends an EDU `m.server.knock`
to any available resident servers that the joining is aware of. 

The server then waits until it receives an `m.server.participation` event with the state_key
containing the joining server's name from any resident server that is participating in the room.

When `m.server.participation`'s `participation` field has the value `permitted`, then
the can use `make_join` and `send_join`. However, `send_join` could be ammended in another MSC so
that a server is able to produce an `m.server.subscription` configuration event, rather than an
`m.room.member` event for a specific user. This is so that a server can begin the process of joining
the room in advance of a user accepting or joining the room via a client, in order to improve the
response time. 

### The: `m.server.knock` EDU

Knock is an EDU to make a client in a resident server aware of the joining server's intent to join
the room. A client can then arbritrarily research the reputation of the joining server before deciding
whether resident servers of the room should accept any PDU whatsoever from the joining server.
Currently in room V11 and below, it is not possible for room operators to stop a new server from
sending multiple PDUs to a room without first knowing of, and anticipating a malicious server's existence.
This is a fact which has already presented major problems in Matrix's history, and the only protection
has been faith.

This propsal does not just aim to remove the risk of spam joins for members from the same server,
but also spam joins from many servers at the same time.
While it is seen as technically difficult to accuire user accounts in a large number of Matrix
homeservers, it is still possible and has happened before. For example, servers can be compromised
via a common exploit or existing servers that have weak registration requirements can be exploited,
and this has happened already in Matrix's history.

Having an EDU allows us to accept a knock arbritrarily with a clients, probably automated bots
like Draupnir. We can then arbitrarily research the reputation of the server before deciding
to accept. This also conveniently keeps auth_rules around retricted join rules clean and simple.

The `m.server.knock` EDU can be treated as idempotent by the receiver, although the effect should probably
expire after some subjective (to the receiver) duration.

```
{
  "content": {
    "room_id": "!example:example.com",
  },
  "edu_type": "m.server.knock"
}
```

### The `m.server.participation` event, `state_key: ${serverName}`

This is a capbility that allows the state_key'd server to send `m.server.subscription`, it is sent
to accept the `m.server.knock` EDU. The event can also be used to make a server aware of a room's
existance, so that it can be optionally preload and cache a room before the server's users discover it.

Why ban is not required: maybe because policies can be used to ignore the `knock` EDU?
We shouldn't call it membership anyhow, because being banned in current DAG implies membership,
you get force joined etc. Here it shouldn't imply that whatsoever, the servers shouldn't
know that they are banned unless we want to tell them why. Ok this might be wrong actually (not 
leting them know). However, there is a use case where we need to be able to ban a server without
letting them know about the rooms existence, only when they find the room should they know.
If they are already in the room, when they send federation events they could be told somehow,
unsure if this requires s-s api changes though.

`participation` can be one of `permitted` or `ban`. FIXME: figure out eager ban vs lazy ban for not
alerting the joining server until necessary.


##### `m.server.subscription` state_key: server

This is a configuration event that uses the `m.server.participation` capability to manage
the server's subscription to the event stream. It is not an authorization event.

FIXME: This can probably be merged with `m.server.participation`, since it would be
kinda the same as membership's invite where initially it is sent by someone else and this isn't
seen as an issue. We have to take note to avoid force join by only allowing the sender that doesn't
match to set it to `ban` and `invite`. Actually, I don't know about this, it doesn't feel right
there's something about having this be something that isn't an auth_event that makes it more elegant.
I'm not sure about this, since if `m.server.participation` is rewritten to be something else

### Rethinking capabilities

Can we make capabilities such that the auth rules themselves can be repesented as events
e.g. `m.server.subscription` requires the presence of `m.server.participation` with
the key for the server and a field with a specific value? Probably not in this MSC but it would
make attenuating capabilities a lot cooler.


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
