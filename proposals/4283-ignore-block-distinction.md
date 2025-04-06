# MSC4283: Distinction between Ignore and Block

When discussing features around user safety, terminology like *ignore*, *block*, *filter*, and *mute*
is typically used. Though the terminology is consistent, the definitions are not.

In a similar effort to [MSC4161](https://github.com/matrix-org/matrix-spec-proposals/pull/4161), this
proposal aims to clarify the definitions used from a technical perspective. Clients can, but SHOULD
NOT, use different terminology for their users.

## Proposal

The following terms are to be used by developers and the Matrix Specification itself. Effort has been
made to avoid dramatic spec text changes with this proposal.

**Ignore** means to filter the receipt of an action without giving indication to the sender that filtering
has happened. This filtering can be done server-side or client-side, though server-side is more popular
as of writing. For example, *ignoring* an invite means that the invite enters a black hole never to
be seen by the intended recipient.

Other platforms and protocols may call *ignores* "mutes" or "filters". Avoid these terms as they
conflict with other parts of the Matrix Protocol (namely, with notifications and `/sync`).

**Block** means to prevent the sender from completing an action. This is typically done server-side,
but with some work, can be done client-side. Reusing the invite example, the sender would get explicitly
told "you cannot send this invite" instead of it appearing successful with an *ignore*.

Other platforms may call *blocks* "ignores", which is mildly confusing, but swapping the terminology
would involve significant edits to the specification and its implementations.

### Example flow: Invites

Happy path:

1. Alice searches for Bob in the user directory.
2. Alice creates a room and invites Bob to it, having found their user ID in the directory.
3. Bob receives the invite in their client.
4. Bob accepts (or rejects) the invite eventually.

A *block* could be imposed at steps 1 or 2 (or both):

* At step 1, Alice gets told that Bob has blocked them and cannot be invited. It's also possible that
  Bob just doesn't show up at all until Alice enters the full user ID for Bob, at which point the
  client says "@bob:example.org has blocked you".
* At step 2, Alice's invite (and possibly room creation too) fails because Bob blocked them. Alice
  sees this in the error message.

An *ignore* would be imposed between steps 2 and 3: instead of failing to complete the invite, the
invite is received by Bob's server, but the path never reaches step 3. Bob's server (or client) simply
no-ops the delivery of the invite, leaving Alice to think that Bob is, well, *ignoring them*.

### Example flow: Messages

Once in a room together, the happy path would be:

1. Alice sends a message.
2. Bob receives that message in their client.

A *block* could be imposed such that Alice's client explicitly says "Bob did not receive this message",
and either Bob's client or server would further *ignore* the message. For encrypted messages, Alice
might not even be able to claim One-Time Keys (or similar) for Bob prior to sending.

An *ignore* would take the shape of allowing Alice to claim OTKs, and possibly even deliver key material
to Bob, but Bob's client or server would prevent the message from appearing. Some clients may elect
to minimize the message rather than completely hide it to retain some conversation context. Placeholders
like "This message is hidden because you have ignored this user." are encouraged in that case.

## Potential issues

Other platforms and protocols may use yet more different terminology, and could be confusing to
developers trying to bridge with or transition from those places. Noted in the above proposal, it's
preferred to instead maintain the *ignore* definition that is currently in use by Matrix rather than
rework existing features and functionality.

## Alternatives

Significant alternatives are discussed inline in this proposal.

## Security and safety considerations

Whether to use blocks or ignores (or both!) may carry some security and privacy considerations. Because
blocks are known to both parties, this may expose the intended target to increased or alternative
forms of abuse.

## Unstable prefix

No unstable prefix is required for this proposal because it's purely definitions.

## Dependencies

No direct dependencies. This proposal would benefit from a [MSC4270](https://github.com/matrix-org/matrix-spec-proposals/pull/4270)-style
glossary, however.
