# MSC3784 Using room type of m.policy for policy rooms

## Introduction

Matrix already has [Moderation Policy Lists](https://spec.matrix.org/v1.17/client-server-api/#moderation-policy-lists)
which describe policy recommendations through state events. In typical usage,
these policy recommendations tend to appear in dedicated rooms, though are not
required to.

Having the policy recommendations in dedicated rooms helps clients better understand
the purpose of a room, and potentially hide it if the client knows it can't do
much with that dedicated purpose. For example, a messaging client might want to
hide policy list rooms by default to avoid showing "non-conversational" rooms to
the user.

This proposal introduces a [room type](https://spec.matrix.org/v1.17/client-server-api/#types)
to denote such dedicated rooms.

## Proposal

Rooms dedicated to containing policy list recommendations SHOULD use a newly
defined `m.policy` room type. How clients choose to (not) handle the new type is
left as an implementation detail.

Where the `m.policy` room type is used, conversation is not expected.
Clients SHOULD note that moderation policies can appear in rooms without the `m.policy` type,
where conversation could be present.

## Potential issues

Clients which have dedicated UX for policy rooms might not be able to apply that
UX to rooms missing the `m.policy` room type. They can try to look for recommendation
state events contained in the room, though if their dedicated UX is invasive then
it may hide conversation being had in the room. This proposal does not attempt to
make rooms without the `m.policy` room type, but still contain policy recommendations,
invoke any dedicated UX a client might have - clients can choose how/if they handle
this case.

## Alternatives

Peeking over federation, like in [MSC2444](https://github.com/matrix-org/matrix-spec-proposals/pull/2444),
can help clients identify rooms which contain policy list recommendation state
events. However, as identified above, this may be insufficient to properly
identify rooms *dedicated* to containing those state events.

## Security considerations

This change is largely informative and carries no direct security impact. Clients
which interpret the `m.policy` room type will need to consider security in their
implementations. For example, if hiding the rooms then notifications in those
rooms will need some consideration.

## Unstable prefix

If you want to implement this MSC before its merged you're free to use the unstable type of
`support.feline.policy.lists.msc.v1`.

After this MSC is merged, implementations may stop recognizing the unstable room type.
Since room types are immutable, rooms created using the unstable type could become "unsupported"
if support for the unstable prefix is removed after the proposal is merged.

## Dependencies

The Author is not aware of any unstable MSC dependencies for this MSC.
