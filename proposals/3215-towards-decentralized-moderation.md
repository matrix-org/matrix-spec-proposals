# MSC3215: Aristotle: Moderation in all things

On large public channels (e.g. Matrix HQ), we have too many users abusing the room:
  - Spammers
  - Bullies
  - Invite spammers
  - ...

The Matrix community doesn't have enough moderators to handle all of this, in particular during
weekends/outside of office hours.

In an ideal world, we should not need to rely upon human moderators being awake to react to
such abuse, as many users tend to report these types of abuse very quickly. One could imagine,
for instance, that if 25 long-standing users of Matrix HQ report the same message of a new
user as spam, said user will be banned temporarily or permanently from the room and/or the
server as a spammer.

This proposal does NOT include a specific policy for kicking/banning. Rather, it redesigns the abuse
reporting mechanism to:

- decentralize it;
- produce formatted data that can be consumed by bots to decide whether action should be taken
    against a user.

This proposal redesigns how abuse reports are posted, routed and treated to make it possible to
use bots to react to simple cases.

The expectation is that this will allow the Matrix community to experiment with bots that deal
with abuse reports intelligently.


## Proposal

Matrix specs offer a mechanism to report abuse. In this mechanism:

1. a user posts an abuse report for an event;
2. hopefully, the homeserver administrator for the user's homeserver will handle the abuse report.

In the current state, this mechanism is insufficient:

1. If the abuse report concerns an event in an encrypted room, the homeserver administrator typically
    does not have access to that room, while a room moderator would, hence cannot act upon that report.
2. Many homeserver administrators do not wish to be moderators, especially in rooms in which they
    do not participate themselves.
3. As the mechanism does not expose an API for reading the abuse reports, it is difficult to experiment
    with bots that could help moderators.
4. As the mechanism is per-homeserver, reports from two users of the same room that happen to have accounts
    on distinct homeservers cannot be collated.
5. There is no good mechanism to route a report by a user to a moderator, especially if they live on different
    homeserver.


This proposal redesigns the abuse report spec and suggested behavior as follows:

- Any room can opt-in for moderation.
- Rooms that opt-in for moderation have a moderation room (specified as a state event). These moderation
    rooms may be shared between several rooms and there may be a default moderation room for a homeserver.
- Posting an abuse report on a specific event from a room with moderation sends a data message to the
    moderation room.
- As there may still be a need to report entire rooms, the current abuse report API remains in place for
    reporting entire rooms, although it is expected that further MSCs will eventually deprecate this API.

While this is not part of the MSC, the expectation is that the community may start experimenting with bots that
can be invited to moderation rooms act upon abuse reports:
    - a bot could pick these data messages and turn them into human-readable reports including context
        and buttons to let moderators easily ignore/kick/ban/redact;
    - a bot could collate reports, ignore those from recently registered users, and decide to kick/ban
        reported users if some threshold is exceeded;
    - ...

### Invariants

- Each room MAY have a state event `m.room.moderation_room`. If specified, this is the room ID towards which
    abuse reports MUST be sent. As rooms may be deleted `m.room.moderation_room` MAY be an invalid room ID.

```jsonc
{
    "state_key": "m.room.moderation_room",
    "type": "m.room.moderation_room",
    "content": {
        "room_id": XXX, // The room picked for moderation.
    }
    // ... usual fields
}
```

### Client behavior


#### Opting in for moderation

When a user Alice creates a room or when a room moderator accesses the room's configuration, they MAY opt-in for moderation.
When they do, they MUST pick a moderation room. The client SHOULD check that the moderation room is a room in which Alice
has a powerlevel sufficient for sending messages.

This room ID is materialized as a state event `m.room.moderation_room`, as described above.

Similarly, if a moderator has opted in for moderation in a room, a moderator MAY opt out of moderation for that room.
This is materialized as deleting `m.room.moderation_room`.

#### Reporting an event

Any member of a room that supports moderation MAY report an event from that room, by sending a `m.abuse.report` event
with content

| event_id | **Required** id of the event being reported. |
| room_id  | **Required** id of the room in which the event took place. |
| nature   | **Required** The nature of the event, see below. |
| comment  | Optional. String. A freeform description of the reason for sending this abuse report. |

`nature` is an enum:

- `abuse.disagreement`: disagree with other user;
- `abuse.toxic`: toxic behavior, including insults, unsollicited invites;
- `abuse.illegal`: illegal behavior, including child pornography, death threats,...;
- `abuse.spam`: commercial spam, propaganda, ... whether from a bot or a human user;
- `abuse.room`: report the entire room, e.g. for voluntarily hosting behavior that violates server ToS;
- `abuse.other`: doesn't fit in any category above.

We expect that this enum will be amended by further MSCs.

The rationale for requiring a `nature` is twofold:

- a Client may give to give a users the opportunity to think a little about whether the behavior they is truly abuse;
- this gives the Client the ability to split between
    - `abuse.room`, which should be routed to an administrator;
    - `abuse.disagreement`, which may better be handled by blurring messages from offending user;
    - everything else, which needs to be handled by a room moderator or a bot.

Any `m.abuse.report` message sent to a moderation room is an abuse report.

This proposal does not specify behavior when `m.room.moderation_room` is not set or when the room doesn't exist.


### Server behavior

#### Routing messages

When user Alice attempts to send a `m.abuse.report` message _M_ to room _R_:

- if Alice is not a member of _M_`.room_id`, reject the message;
- if room _M_.`room_id` does not have a state event `m.room.moderation_room`, reject the message;
- if room _M_.`room_id` has a state event `m.room.moderation_room` and its value is other than _R_, reject the message;
- if event _M_.`event_id` did not take place in room _M_`.room_id`, reject the message;
- if Alice could not witness event _M_.`event_id`, reject the message;
- otherwise, send the message to room _R_ **even if Alice is not a member of room _R_**.

### Possible bot behavior

This section is provided as an illustration of the spec, not as part of the spec.

A possible setup would involve two bots, both members of a moderation room _MR_.

- A classifier bot consumes `m.abuse.report` messages, discards messages from users who have joined recently or never
    been active in the room (possible bots/sleeping bots), then collates reports against users. If there are more than
    e.g. 10 reports in the last hour against a single user, post a `m.policy.rule.user` message in the same room specifying that the user
    should undergo temporary ban.
- Another bot consumes `m.policy.rule.user` messages and implement bans.

## Open questions

- If all the moderators of room _R_ leave its moderation room _MR_ or are kick/banned from _MR_, we can end up with an orphan
    room _R_, which sends its moderation on _MR_ but doesn't have moderators in _MR_. Do we need to handle this?
- Should we allow the members or moderators of a moderation room _MR_ to reject a room _R_ from moderation? If so,
    how do we implement this?

## Security considerations

### Routing

This proposal introduces a (very limited) mechanism that lets users send (some) events to a room without being part of that
room. There is the possibility that this mechanism could be abused.

We believe that it cannot readily be abused for spam, as these are structured data messages, which are usually not visible to members
of the moderation room.

However, it is possible that it can become a vector for attacks if combined with a bot that treats said structured data messages.

### Revealing oneself

If a end-user doesn't understand the difference between `abuse.room` and other kinds of abuse report, there is the possibility
that this end-user may end up revealing themself by sending a report against a moderator or against the room to the very
moderators of that room.

### Snooping administrators

Consider the following case:

- homeserver compromised.org is administered by an evil administrator Marvin;
- user @alice:compromised.org is a moderator of room _R_ with moderation room _MR_;
- user @bob:innocent.org is a member of room _R_;
- @bob:innocent.org posts an abuse report _AR_ to _MR_;
- Marvin may achieve access to the metadata on report _AR_, including:
    - the fact that @bob:innocent.org has reported something to room _AR_;
- Marvin also has access to the metadata on _R_, including:
    - the fact that _MR_ is the moderation room for _R_;
    - the fact that @charlie:toxic.org was just banned from _R_;
- Marvin may deduce that @bob:innocent.org has reported @charlie:toxic.org.

It is not clear how bad this is.

It is also not clear how to decrease the risk.

### Snooping bots

As bots are invited to moderation rooms, a compromised bot has access to all moderation data for that room.

## Alternatives

MSC 2938 (by the same author) has previously been posted to specify a mechanism for reporting events to room moderators. The current MSC is considered
    - simpler to implement;
    - more reliable (it does not need to roll out its own federation communication);
    - less specialized.

I am not aware of other proposals that cover the same needs.

## Unstable prefix

During experimentation

- `m.room.moderation_room` will be prefixed `org.matrix.msc3215.room.moderation_room`;
- `m.abuse.report` will be prefixed `org.matrix.msc3215.abuse.report`;
- `abuse.*` will be prefixed `org.matrix.msc3215.abuse.nature.*`.

