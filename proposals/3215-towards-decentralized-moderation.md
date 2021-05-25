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

- Each room MAY have a state event `m.room.moderated_by`. If specified, this is the room ID towards which abuse reports MUST be sent. As rooms may be deleted `m.room.moderated_by` MAY be an invalid room ID. A room that has a state event `m.room.moderated_by` supports moderation. Users who wish to set this state event MUST be have a Power Level sufficient to kick and ban users.

```jsonc
{
    "state_key": "m.room.moderated_by",
    "type": "m.room.moderated_by",
    "content": {
        "room_id": XXX, // The room picked for moderation.
        "user_id": XXX, // The bot in charge of forwarding reports to `room_id`.
    }
    // ... usual fields
}
```

- Each room MAY have state events `m.room.moderator_of`.

```jsonc
{
    "state_key": XXX, // XXX is the ID of the Community Room, i.e. the room being moderated, or empty if we wish to define the default user id in charge of forwarding reports to this room.
    "type": "m.room.moderation.moderator_of",
    "content": {
        "user_id": XXX, // The bot in charge of forwarding reports to this room.
    }
    // ... usual fields
}
```

### Client behavior

#### Opting in for moderation

When a user Alice creates a room ("the Community Room") or when a room moderator accesses the Community Room's configuration,
they MAY opt-in for moderation. When they do, they MUST pick a Moderation Room. The Client SHOULD check that:
- the Moderation Room is a room in which Alice has a powerlevel sufficient for sending messages;
- the Moderation Room has a state event `m.room.moderation.moderator_of`.

If Alice has opted-in for moderation, mased on the Moderation Room's Room ID and `m.room.moderation.moderator_of`, the Client
MUST create a state event `m.room.moderated_by` (see above) in the Community Room.

Similarly, if a moderator has opted in for moderation in a Community Room, a moderator MAY opt out of moderation for that
Community Room. This is materialized as deleting `m.room.moderated_by`.

#### Rejecting moderation

A member of a Moderation Room may disconnect the Moderation Room from a Community Room by removing state event `m.room.moderation.moderator_of`, `XXX`. This may serve to reconfigure moderation if a Community Room is deleted
or grows sufficiently to require its dedicated moderation team/bots.

#### Reporting an event

Any member of a Community Room that supports moderation MAY report an event from that room, by sending a `m.abuse.report` event
with content

| field    | description |
|----------|-------------|
| event_id | **Required** id of the event being reported. |
| room_id  | **Required** id of the room in which the event took place. |
| moderated_by_id | **Required** id of the moderation room, as taken from `m.room.moderated_by`. |
| nature   | **Required** The nature of the event, see below. |
| reporter | **Required** The user reporting the event. |
| comment  | Optional. String. A freeform description of the reason for sending this abuse report. |

`nature` is an enum:

- `m.abuse.nature.disagreement`: disagree with other user;
- `m.abuse.nature.toxic`: toxic behavior, including insults, unsollicited invites;
- `m.abuse.nature.illegal`: illegal behavior, including child pornography, death threats,...;
- `m.abuse.nature.spam`: commercial spam, propaganda, ... whether from a bot or a human user;
- `m.abuse.nature.room`: report the entire room, e.g. for voluntarily hosting behavior that violates server ToS;
- `m.abuse.nature.other`: doesn't fit in any category above.

We expect that this enum will be amended by further MSCs.

The rationale for requiring a `nature` is twofold:

- a Client may give to give a users the opportunity to think a little about whether the behavior they report truly is abuse;
- this gives the Client the ability to split between
    - `abuse.room`, which should be routed to an administrator (in the current MSC, using the existing moderation API);
    - `abuse.disagreement`, which may better be handled by blurring messages from offending user;
    - everything else, which needs to be handled by a room moderator or a bot.

To send an `m.abuse.report`, the Client posts the `m.abuse.report` message as DM to the `user_id` specified in the 
`m.room.moderated_by`.

This proposal does not specify behavior when `m.room.moderated_by` is not set or when the `user_id` doesn't exist.

### Built-in routing bot behavior

Users should not need to join the moderation room to be able to send `m.abuse.report` messages to it, as it would
let them snoop on reports from other users. Rather, we introduce a built-in bot as part of this specification: the
Routing Bot.

1. When the Routing Bot is invited to a room, it always accepts invites.
2. When the Routing Bot receives a message other than `m.abuse.report`, it ignores the message.
3. When the Routing Bot receives a message _M_ with type `m.abuse.report` from Alice:
    - If the Routing Bot is not a member of _M_`.moderated_by_id`, reject the message.
    - If _M_.`reporter` is not Alice, reject the message.
    - If room _M_.`moderated_by_id`  does not contain a state event `m.room.moderation.moderator_of`/`XXX`, where `XXX`
        is _M_.`room_id`, reject the message. Otherwise, call _S_ this state event.
    - If _S_ does not have type `m.room.moderation.moderator_of`, reject the message.
    - If _S_ is missing field `user_id`, reject the message.
    - If _S_.`user_id` is not the id of the Routing Bot, reject the message.
    - Copy the `content` of _M_ as a new `m.abuse.report` message in room _M_.`room_id`.

### Possible Moderation Bot behavior

This section is provided as an illustration of the spec, not as part of the spec.

A possible setup would involve two Moderation Bots, both members of a moderation room _MR_.

- A Classifier Bot consumes `m.abuse.report` messages, discards messages from users who have joined recently or never
    been active in the room (possible bots/sleeping bots), then collates reports against users. If there are more than
    e.g. 10 reports in the last hour against a single user, post a `m.policy.rule.user` message in the same room specifying that the user
    should undergo temporary ban.
- A Ban Bot consumes `m.policy.rule.user` messages and implements bans.

## Security considerations

### Routing, 1

This proposal introduces a (very limited) mechanism that lets users send (some) events to a room without being part of that room. There is the possibility that this mechanism could be abused.

We believe that it cannot readily be abused for spam, as these are structured data messages, which are usually not visible to members of the moderation room.

However, it is possible that it can become a vector for attacks if combined with a bot that treats said structured data messages, e.g. a Classifier Bot and/or a Ban Bot.

### Routing, 2

The Routing Bot does NOT have access to priviledged information. In particular, it CANNOT check whether:
    - Alice is a member of _M_.`room_id`.
    - Event _M_.`event_id` took place in room _M_.`room_id`.
    - Alice could witness event _M_.`event_id`.

This means that **it is possible to send bogus abuse reports**. This is already the case with the current Abuse Report API but this is probably something that SHOULD BE ASSESSED before merging this spec.

#### Possible solution: an API to provide/check certificates

We could expose an API to provide a certificate that Alice has witnessed
an event and another API to check the certificate.

As of this writing, this API is NOT part of the MSC but rather a proof of concept that the problem of bogus abuse reports could be solved without major changes to the protocol.

##### Providing a certificate

```
POST /_matrix/client/r0/rooms/{room_id}/witness/{event_id}/certificate
```

- Authentication required: True
- Rate limitation: True

If Alice is the authenticated user and has witnessed `event_id` in room `room_id`, then this call returns a certificate.

###### Response format

| Parameter   | Type   | Description |
|-------------|--------|-------------|
| certificate | string | a certificate that may later be checked by the same homeserver, possibly a tuple (user_id, room_id, event_id, salt) encrypted with the homeserver's private key |

We then extend `m.abuse.report` with

| field | description |
|-------|-------------|
| certificate | **Required** The certificate provide by this API. |


##### Verifying a certificate

```
POST /_matrix/client/r0/rooms/{room_id}/witness/{event_id}/check/{user_id}
```

- Authentication required: True
- Rate limitation: True

###### Request format

| Parameter   | Type   | Description |
|-------------|--------|-------------|
| room_id     | RoomID | the room in which the event is said to have taken place |
| user_id     | UserID | the user who claims to have witnessed the event |
| event_id    | EventID| the event |
| certificate | string | a certificate issued by the `witness/.../certificate` API |

The request succeeds if and only if `certificate` confirms that user `user_id` witnessed event `event_id` in room `room_id`.

The Classifier Bot SHOULD call this API to confirm that the abuse report is legit.

### Revealing oneself

If a end-user doesn't understand the difference between `m.abuse.nature.room` and other kinds of abuse report, there is the possibility
that this end-user may end up revealing themself by sending a report against a moderator or against the room to the very
moderators of that room.

The author believes that this is a problem that can and should be solved by UX.

### Snooping administrators (user homeserver)

Consider the following case:

- homeserver compromised.org is administered by an evil administrator Marvin;
- user @alice:compromised.org is a member of Community Room _CR_;
- user @alice:compromised.org posts an abuse report against @bob:somewhere.org as DM to the Routing Bot;
- Marvin can witness that @alice:compromised.org has sent a message to the Routing Bot
    but cannot witness the contents of the message (assuming encryption);
- as @alice:compromised.org is a member of _CR_, Marvin can witness when @bob:somewhere.org is kicked/banned,
    even if _CR_ is encrypted;
- Marvin can deduce that @alice:compromised.org has denounced @bob:somewhere.org.

This is BAD. However, this is better as the current situation in which Marvin can directly read the report posted by @alice:compromised.org using the reporting API. Furthermore, this problem will not show up in Matrix P2P.

If necessary, a hardened Client could make deductions harder/increase deniability by randomly sending bogus abuse reports to the Routing Bot.

### Snooping administrators (moderator homeserver)

Consider the following case:

- homeserver compromised.org is administered by an evil administrator Marvin;
- user @alice:compromised.org is a moderator of room _CR_ with moderation room _MR_;
- user @bob:innocent.org is a member of room _R_;
- @bob:innocent.org posts an abuse report as DM to the Routing Bot;
- Marvin does not witness this;
- Marvin sees that the Routing Bot posts a message to _MR_ but the metadata does not
    contain any data on @bob:innocent.org;
- if the room is encrypted, Marvin cannot determine that @bob:innocent.org has posted
    an abuse report.

This is GOOD.

### Interfering administrator (user homeserver)

Consider the following case:

- homeserver compromised.org is administered by an evil administrator Marvin;
- user @alice:compromised.org is a member of Community Room _CR_;
- if there is no moderator for _CR_ on compromised.org, Marvin cannot set `m.room.moderated_by`, hence cannot replace the moderation room or the Routing Bot.

This is GOOD.

### Interfering administrator (moderator homeserver)

Consider the following case:

- homeserver compromised.org is administered by an evil administrator Marvin;
- user @alice:compromised.org joins a moderation room _MR_;
- user @bob:innocent.org is a member of room _CR_, with moderation room _MR_;
- Marvin can impersonate @alice:compromised.org and set `m.room.moderation.moderator_of`
    to point to a malicious bot EvilBot;
- when @alice:compromised.org becomes moderator for room _CR_ and sets _MR_ as moderation room, EvilBot becomes the Routing Bot;
- when @bob:innocent.org sends an abuse report through EvilBot, Marvin has access to the full abuse report.

This is BAD.

Variant:

- homeserver compromised.org is administered by an evil administrator Marvin;
- user @alice:compromised.org is a moderator of room _CR_ with moderation room _MR_;
- Marvin can impersonate @alice:compromised.org and set `m.room.moderation.moderated_by`
    to point to a moderation room under its control;
- Marvin has access to all abuse reports in _MR_.

Variant:

- homeserver compromised.org is administered by an evil administrator Marvin;
- user @alice:compromised.org is a moderator of room _CR_ with moderation room _MR_;
- Marvin can impersonate @alice:compromised.org and invite an evil moderator or bot to _MR_ ;
- Marvin has access to all abuse reports in _MR_.

I cannot find any solution to these problems: as long as an administrator can impersonate a moderator, they can access all moderation data past the date of impersonation.

A similar problem already shows up without this MSC, insofar as the administrator can impersonage a user of _CR_ e.g. while they're asleep and invite an evil user to witness everything that happens in _CR_.

It feels like the only solution to both problems is beyond the scope of this MSC and is essentially Matrix P2P.

### Snooping bots

As bots are invited to moderation rooms, a compromised bot (whether it's Routing Bot,
Classifier Bot or Ban Bot) has access to all moderation data for that room.

## Alternatives

### MSC 2938
MSC 2938 (by the same author) has previously been posted to specify a mechanism for reporting events to room moderators. The current MSC is considered
    - more reliable (it does not need to roll out its own federation communication);
    - less specialized/more general.

I am not aware of other proposals that cover the same needs.

### Alternative to the Routing Bot

The "knocking" protocol is an example of an API that lets users inject state events in a room in which they do
not belong. It is possible that we could follow the example of this protocol and implement a similar "abuse" API.

However, this would require implementing yet another new communication protocol based on PDUs/EDUs, including a
(small) custom encryption/certificate layer and another retry mechanism. The author believes that this would entail
a higher risk and result in code that is harder to test and trust.

### Priviledged Routing Bot

The Routing Bot CANNOT check whether:
    - Alice is a member of _M_.`room_id`.
    - Event _M_.`event_id` took place in room _M_.`room_id`.
    - Alice could witness event _M_.`event_id`.

The Synapse Admin API currently offers all the features necessary to check whether
Alice is a member of _M_.`room_id` and whether event _M_.`event_id` took place in room _M_.`room_id` and could easily be extended to allow checking whether Alice could witness event _M_.`event_id`.

One idea could be to somehow make the Routing Bot a priviledged user with *partial* access to the Admin API to all the homeservers involved. This feels like a lost fight, though, a strong risk that homeserver administrators will fail to properly configure the Routing Bot, and a very strong risk to privacy of all users if the Routing Bot is somehow compromised.

The author believes that this is too risky.

### Priviledged Classifier Bot

Instead of the Routing Bot checking whether the abuse report is legitimate, we could delegate the problem to the Classifier Bot. The risks and difficulties are essentially the same as with the Routing Bot.

The author believes that this is too risky.

### One Routing Bot per homeserver

If the Routing Bot was attached to a specific homeserver, giving it the ability to check whether a user from the same homeserver is sending a legitimate abuse report would be simple and most likely riskless.

However, this means that one Routing Bot per homeserver member of the Community Room needs to be invited to each Moderation Room. In particular, this would expose all the content of the Moderation Room to this Routing Bot and to the administrator of every homeserver member of the Community Room.

A malicious administrator on *any* homeserver involved in the Community Room could therefore deanonymize every abuse report without visible tampering.

## Unstable prefix

During experimentation

- `m.room.moderation.moderated_by` will be prefixed `org.matrix.msc3215.room.moderation.moderated_by`;
- `m.room.moderation.moderator_of` will be prefixed `org.matrix.msc3215.room.moderation.moderator_of`;
- `m.abuse.report` will be prefixed `org.matrix.msc3215.abuse.report`;
- `m.abuse.nature.*` will be prefixed `org.matrix.msc3215.abuse.nature.*`.

