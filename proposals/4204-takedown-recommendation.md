# MSC4204: `m.takedown` moderation policy recommendation

Currently there is one specified moderation policy recommendation,
`m.ban`[^spec-ban-recommendation].

> When this recommendation is used, the entities affected by the rule should be
> banned from participation where possible. The enforcement of this is
> deliberately left as an implementation detail to avoid the protocol imposing
> its opinion on how the policy list is to be interpreted. However, a suggestion
> for a simple implementation is as follows:

[^spec-ban-recommendation]:
    https://spec.matrix.org/v1.11/client-server-api/#mban-recommendation

In practice this recommendation is used by the moderation bots to store banned
rooms, users and servers alongside a reason for the ban.

This has provided the ability to create versatile policy lists that can ban
matrix users for any recorded reason. Not only for spam, illegal content, csam,
but softer reasons such as moderation disputes, timeouts, interventions,
disagreements.

Unfortunately, because the `m.ban` recommendation has such a broad use, and its
implementation has the same outcome for any consequence, it is the expectation
that a `reason` is provided for each `m.ban`.

This reason inadvertently allows the subject of the moderation policy to be
classified among categories of abuse, which can be undesirable. For example, a
user called `@yarrgh:example.com` could be banned for the reason `piracy`. Which
would identify `@yarrgh:example.com` as a pirate. This is problematic because it
would allow other pirates to identify `@yarrgh:example.com` and join forces. In
other situations, it may cause harm or legal ramifications if
`@yarrgh:example.com`'s reputation has been damaged and they are not a pirate at
all.

Additionally, if `@yarrgh:example.com` is known to been smuggling contraband via
matrix events or media, then there is no mechanism to mark this content as
plunder that should be seized.

A compounding issue is Moderation bots currently use the `reason` of the ban to
determine whether to redact a user's events or not. Which doesn't allow for a
free-form use of the `reason` where redaction is required.

## Proposal

We introduce a new policy recommendation, `m.takedown`, reserved for purging
entities and any associated content. When `m.takedown` is used, a `reason`
SHOULD NOT be embedded into the same policy event[^bluesky].

We provide guidance for how the `m.takedown` recommendation is expected to be
consumed by typical moderation tooling or clients. This is to set expectations
for policy list curators for how the recommendation should behave and the
severity of the consequences. We also provide guidance to allow tool
implementers to understand the context of the recommendation's use. Moderation
tools or clients are free to interpret the recommendation differently, for
example if they are aware of a conflicting policy or they are configured to
implement harsher or more liberal consequences for the recommendation.

If the entity of the rule is a user:

- Applied to a user: The user and all associated messages, media, invitations
  are hidden and removed from local storage or caches. If the user enforcing the
  recommendation is a moderator in the room in common with the target, then
  messages may be shown with a warning behind spoiler text.

- Applied to a room: The user is banned from the room and all of their recent
  messages redacted.

- Applied to a server: The user is not allowed to send invites to users on the
  server. Any associated media is quarantined or removed, if the user is
  resident then the user is considered for deactivation or suspension.

If the entity of the rule is a room:

- Applied to a user: The user is parted from the room, and be unable to rejoin
  it. Any invitations to the room are hidden and ignored. Any media associated
  with the room are purged from local storage or caches.

- Applied to a room: No-op because a room can't take itself down.

- Applied to a server: The room is purged from the server and resident users are
  prevented from joining. Invitations to the room are blocked.

If the entity of the rule is a server:

- Applied to a user: Invitations originating from from users on the server are
  hidden. Media uploaded from users resident to the target server are removed
  from local storage or caches and never displayed. Messages originating from
  the server could be hidden entirely or behind spoiler text.

- Applied to a room: The server is added as a denied server in the ACLs. All
  room members resident to the target server are banned from the room and have
  their recent messages redacted.

- Applied to a server: The enforcing server should avoid federating with the
  target server as much as possible by blocking invites from the target server
  and not sending traffic unless strictly required (no outbound invites). Any
  media associated with the server is quarantined or removed.

[^bluesky]:
    This is inspired by work going into bluesky
    https://docs.bsky.app/blog/2024-protocol-roadmap#protocol-stability-milestone

## Potential issues

- It is anticipated that some consequences of recommending `m.takedown` against
  an entity are irreversible, and can have a huge impact on the history of a
  Matrix room if implemented naively. The most common use case for the
  recommendation will be to replace the use of `m.ban` with the reason `spam`
  targeting a user, which in Mjolnir causes the target user to be banned from
  protected rooms and their messages to be redacted.

- Because the `reason` is no longer present, a higher degree of trust is
  required when applying some consequences to these policies. An attempt to
  document the reason privately exists through
  [MSC4206 Moderation policy auditing and context](https://github.com/matrix-org/matrix-spec-proposals/pull/4206).

- The lack of classification from the `reason` field is insufficient to prevent
  direct identification of some entities. For example `@yarrgh:example.com` is
  evidently a pirate because of the presence of the phrase `yarrgh` embedded
  within their mxid. An attempt to alleviate this concern exists through
  [MSC4205 Hashed moderation policy entities](https://github.com/matrix-org/matrix-spec-proposals/pull/4205).

## Alternatives

- `m.ban` Could continue to be used with a more specific reason, but this
  presents problems for automated and semi-automated responses because the
  reasons are not standardised.

- `m.ban` A `takedown` reason could be given on `m.ban` policies. This is pretty
  ad-hoc.

## Security considerations

- `m.takedown` can have severe consequences for entities, policies could be
  created maliciously against innocent users on popular policy rooms. This could
  increase the reward of infiltrating moderation focussed communities. Tools
  that naively implement the recommendation without safeguards, such as manual
  approval, for the most severe consequences could be exploited. Additionally,
  moderation tools ask for confirmation when the associated entity is known to
  be an active participant of the community being protected.

## Unstable prefix

`org.matrix.msc4204.takedown` -> `m.takedown`.
