# MSC4252: Extensible Events modification: State event handling

[MSC1767 (accepted; not merged)](https://github.com/matrix-org/matrix-spec-proposals/pull/1767) introduced
a concept of Extensible Events to Matrix, with a specific recommendation that state events *not* be
treated as extensible except on a case-by-case basis. During review of [MSC3765](https://github.com/matrix-org/matrix-spec-proposals/pull/3765),
it was thought that the recommendation may need to be changed - this MSC captures that thinking, which
is similarly captured in [this comment](https://github.com/matrix-org/matrix-spec-proposals/pull/3765#discussion_r1915778656)
on MSC3765.

## Proposal

MSC1767 is modified to permit clients to use content blocks to render unknown state event types in
rooms. Clients SHOULD render such events in a way where the user is not confused by the event being
rendered. An example approach may be to add a small decoration to say "this message may appear differently
to other users".

## Potential issues

Clients may render state events in a confusing way for users, allowing senders to 'trick' the user
into believing something was said. For example, sending `m.room.topic` state events with `m.text` of
`Alice has been promoted to Admin`. Per the proposal, clients should find a way to de-confuse the
user, or otherwise handle unknown (state) event types more safely. Or, render specified event types
and avoid the issue entirely 😇.

## Alternatives

The obvious one is the current text of MSC1767, as of writing:

> Unknown state event types generally should not be parsed by clients. This is to prevent situations
> where the sender masks a state change as some other, non-state, event. For example, even if a state
> event has an `m.text` content block, it should not be treated as a room message.

## Security considerations

Implied by potential issues.

## Unstable prefix

While this proposal is not considered stable, clients should follow MSC1767's unstable prefix guidance.

Clients are encouraged to experiment with UI/UX which de-confuses users.

## Dependencies

This MSC has no dependencies which aren't already accepted.
