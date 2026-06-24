# MSC4494: Membership-based invite blocking

[MSC4380] introduced *invite blocking*: a way to disable or enable invites to one's account at the
flip of a switch. This is in an effort to combat ongoing abuse of the room invite system,
which commonly manifests in the form of unsolicited invites.
This proposal will introduce a new "default action" for `m.invite_permission_config`,
which allows users to have finer grained control over who can send them invites,
based on what rooms they share with them.

This is taking inspiration from other platforms which allow their users to restrict who can send
them direct messages or friend requests based on where on the platform the "invitee" may know the
"inviter". As Matrix does not have a concept of "friends", the presence of mutual rooms which are
private is assumed to be a heuristic that can indicate an elevated level of "trust" (i.e. the
invitee is more likely to know who the inviter is).

[MSC4380]: https://github.com/matrix-org/matrix-spec-proposals/pull/4380

## Proposal

A new `default_action` for `m.invite_permission_config` is introduced: `deny_public`.

`deny_public` is intended to prevent invites being sent by users who only share public rooms with
the receiver. It is fairly easy for an attacker to scrape a room's member list,
and don't even have to join the room they want to scrape if it is world readable.
As such, it's not uncommon to see users joining public rooms and then sending direct message
requests to random people in the room list, or recently in the timeline. This action would limit the
pool of users a member can receive invites from to only those which share a room with a
non-`public` join rule (i.e. `invite`, `knock`, `restricted`, or `knock_restricted`), which are
typically room with higher membership standards[^1].

[^1]: Since `restricted` rooms are usually used to require prospective members join a (public) space
first, they are usually effectively `public` with an extra step. However, since this is not their
only use in the wild, they are still included.

When receiving an invite to a user with the `default_action` configured in their invite blocking
configuration, the server will filter the mutual rooms the invitee and inviter share. If none of
them have a join rule that is not `public`, the homeserver MUST reject the invitation. Otherwise,
the invite is permitted (but still subject to ignore lists and other factors).

## Potential issues

A determined malicious user could somewhat easily work their way into the slightly wider window
within which invites would be permitted, allowing them to propagate abuse once again. The risk of
this is deemed acceptable, as the new value is opt-in, and would require that the abusive user
not only already knows of some private rooms which their target is a member of, but is also able to
join them themself.

The default behaviour of unrecognised `default_action`s is *allow* - clients must ensure they do not
set `deny_public` unless the server explicitly advertises support for it.

Requiring mutual non-public rooms may prove a barrier for contacting users of importance, such as
room moderators, or server administrators. This is no different to if the important user was
blocking all invites, and it is assumed such users will either have an alternative method of invite
blocking (for example, via [synapse-http-antispam]), or expect that users will seek out initial
contact through an alternative channel (for example, mentioning them, asking to DM).

[synapse-http-antispam]: https://github.com/maunium/synapse-http-antispam

## Alternatives

Using the membership of mutual *encrypted* rooms was considered during the drafting of this
proposal, however the overlap between non-public and encrypted rooms was deemed too high for the
additional complexity to be of benefit.

## Security considerations

None.

## Unstable prefix

`uk.timedout.msc4494.deny_public` should be used as the `default_action` value while this proposal
is unstable, switching to `deny_public` after it becomes stable.

Homeservers MUST advertise `uk.timedout.msc4494` in their `/_matrix/client/versions` response while
this proposal is unstable, as clients have to know if the value is supported before setting it.
Once the proposal is stable, but not yet in a spec version, `uk.timedout.msc4494.stable` should be
advertised instead.

## Dependencies

None
