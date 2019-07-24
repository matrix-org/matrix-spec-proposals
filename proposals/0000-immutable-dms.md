# Immutable DMs

In the messaging space it is common for apps to expose exactly 1 chat for a conversation
between two users, and in some cases a specific set of users. Matrix currently does not
adequately support this as it allows for multiple rooms to represent a DM between two users.
Although supporting multiple chats with individuals is potentially useful for some use cases,
clients are increasingly wanting to be able to support exactly one DM for a user.

The Fractal team has previously published a blog post for the Banquets versus Barbecues use
cases (available [here](https://blogs.gnome.org/tbernard/2018/05/16/banquets-and-barbecues/)).
In short, Banquets are public rooms and Barbecues are DMs and small private chats (family,
friends, colleagues, etc). This proposal aims to address the lacking Barbecue support in
Matrix.

Any messaging app is likely to have a similar desire as Fractal to differentiate DMs from
all the noise, and Riot in particular is looking at using the DM between users for a more
personal experience within the app (such as key verification between users). This proposal
focuses on immutable DMs between users to assist in identifying the "One True DM" between
users and prevent the room's scope from increasing.

For comparison to Matrix, the following chat apps/platforms all support and encourage a
single DM between users. They all redirect the user to an existing chat with the target
user, creating a new DM if needed.

* Slack
* Discord
* IRC
* Telegram
* Gitter
* Facebook Messenger
* Twitter
* Hangouts
* Instagram
* Rocket.Chat
* Steam
* WhatsApp
* SMS
* and probably many others...

Platforms which allow/encourage users to have multiple DMs with a specific person are:
* Matrix (currently)
* Email
* XMPP (technically speaking)

This proposal covers how clients and servers can work together to encourage and have exactly
one DM between users. These are known as immutable DMs as users are unable to alter the rooms
to make them become regular rooms (they'll always be DMs).

**Disclaimer**: this proposal explores the most extreme direction immutable rooms could take,
up to and including altering event auth rules to achieve immutability and consistency. Not
every aspect of this proposal is required for it to move forward.

## Proposal

The existing direct chat module in Matrix allow for multiple users in a direct chat and multiple
rooms to act as a direct chat between users. Rooms are identified by the `m.direct` account data
event and through invites using a similar property. More information about direct chats as they
currently stand in Matrix can be read here: https://matrix.org/docs/spec/client_server/r0.5.0#id185

The `m.direct` account data event is to be deprecated and replaced with `m.direct_chats` (defined
below). The reason for replacing rather than extending the existing event type is account data
cannot be versioned, and `m.direct` was not created with extensibility in mind: one would have
to encode information in the form of user IDs to be compatible with existing clients. Therefore,
a new event type is introduced. Clients which support immutable DMs should ignore `m.direct`
entirely.

`m.direct_chats` looks as follows:
```json
{
    "type": "m.direct_chats",
    "content": {
        "direct": {
            "@alice:example.org": "!room_a:example.org",
            "@bob:example.org": "!room_b:example.org"
        },
        "group": {
            "!room_c:example.org": ["@alice:example.org", "@bob:example.org"]
        }
    }
}
```

The event maps target users to rooms. Rooms under the `group` property are mapped by room ID
as a hopefully key to find the room or cache it in an easier structure for the client. The
account data is not meant to be a source of truth, just a faster lookup than clients scanning
room state. Clients are responsible for maintaining this account data. (**TODO: If we make it
part of the protocol like below, should the server manage this?**).

Clients rendering the account data event above would result in something like so:

![alice-bob-over-banquet](https://i.imgur.com/h4BHZSw.png)

In order to make the rooms immutable, a new preset, `immutable_direct_chat`, is introduced. The
preset has the following effects on the room state:

* Join rules of `invite`.
* History visibility of `shared`.
* Guest access of `can_join`.
* Power levels with the following non-default structure:
  ```json
  {
      "events_default": 0,
      "state_default": 50,
      "users_default": 0,
      "ban": 100,
      "invite": 100,
      "kick": 100,
      "redact": 50,
      "notifications": {
          "room": 50
      },
      "events": {
          "m.room.name": 100,
          "m.room.avatar": 100,
          "m.room.topic": 100,
          "m.room.history_visibility": 100,
          "m.room.power_levels": 100,
          "m.room.join_rules": 100,
          "m.room.encryption": 100,
          "m.room.canonical_alias": 100
      },
      "users": {
          <see below>
      }
  }
  ```
* Users invited to the room get power level 50.
* The room creation event gets a field of `m.direct` containing an array of users that were
  invited to the room. The generated invited users array overrides any values in the
  `creation_content`.
* Encryption is enabled by default using the `m.megolm.v1.aes-sha2` algorithm.

The power level event content described above is applied *after* the users are invited. If it
wasn't, the users could not be invited. When using the immutable DM preset, servers MUST ignore
the `power_level_content_override` field of the `/createRoom` request.

The `m.direct` field of a creation event is to be preserved by the redaction algorithm (provided
[MSC2176](https://github.com/matrix-org/matrix-doc/pull/2176) doesn't ban redactions of the
create event, in which case this requirement is satisfied).

Clients SHOULD use the `m.direct` field on the creation event to determine if the room is a DM.
The power levels created by the preset reinforce this restriction. A room must not be considered
a DM if the join rules are anything other than `invite`.

Servers SHOULD assist clients by reusing room IDs for known DMs on repeated calls to `/createRoom`
using the same invited users and immutable DM preset.

The rationale for preventing either party from manipulating the room is to ensure that there is
equal representation of the room from both parties (automatically named, automatic avatar, etc).
Users generally expect that a DM will be predictably dressed for searching and scanning, meaning
that the other parties cannot change the aesthetics of the room. For predicatble history and
privacy, the room's history & join rules are locked out from the users. The users can upgrade the
room at any time to escape power level struggles, although this may not maintain the DM status.

Bots and assistant users are not handled in this proposal - see the tradeoffs section for more
information on this. Invites are disabled as a result.

Tombstoned (previously upgraded) immutable DMs MUST be removed from the `m.direct_chats` account
data event and cannot be considered an immutable DM. Tombstoned immutable DMs are dead rooms on
the user's account, preserved for history retention. This applies later in this proposal when
the server is required to make decisions on immutable DM rooms.

#### Upgrading DM rooms

There may come a time where DM rooms need to be upgraded. When DM rooms are upgraded through the
`/upgrade` endpoint, servers MUST preserve the `content` of the previous room's creation event and
otherwise apply the `immutable_direct_chat` preset over the new room. If conflicts arise between
the previous room's state and the state applied by the preset, the preset takes preference over
the previous room's state.

Servers MUST create the new room by using the the room creation rules listed earlier in this proposal
(`/createRoom`, but applying power level changes after invites). This means inviting the other
parties of the previous room to the new room automatically and ensuring the room state is as
described above.

#### Migrating existing DMs

Existing DMs cannot be added to the `m.direct_chats` account data event because they are lacking
the `m.direct` field on the creation event. In order to combat this, a new parameter is to be
added to the `/upgrade` endpoint: `preset`. This behaves similar to the above section on
upgrading rooms: the state implied by the `preset` overrides the previous room's state to more
easily return a room to its defaults.

When `preset` is not provided, no default is assumed unless the room was an immutable DM. When
the `preset` is explicitly given as `immutable_direct_chat`, the rules about upgrading a room
above take affect.

An upgrade request body can now look like:
```json
{
    "new_version": "5",
    "preset": "immutable_direct_chat"
}
```

An immutable DM room can be upgraded to a mutable room (ie: a `preset` of `public_chat` will
create a new public room, losing the DM status on the room and the users).

After upgrading, the client SHOULD update the `m.direct_chats` account data event. Similar
behaviour should apply when the other parties join the upgraded room.

The users of the previous room are the seed users for the new room, as described above in
upgrading a DM room.

#### Auth rule changes

In order to enforce that only the invited users are ever in the immutable DM, servers MUST
reject membership events for members not listed in the `m.direct` array on the creation
event.

#### Handling conflicting rooms

The federation invite API allows for a user to receive an invite to an unverified DM room
with potentially conflicting participants with an existing DM room. Altering the invite API
to include signed membership and creation events is one possibility for ensuring that the
room is unique, however that becomes difficult and expansive to maintain (the target server
would likely end up trying to rebuild the room's state by requesting the gaps in the DAG).
Instead, it is proposed that clients when joining a room check for the `m.direct` field on
the creation event.

Clients MUST always check the flag when they join a new room, not just when they are accepting
an invite. If the room conflicts with an immutable DM the client already knows about, a tombstone
state event must be sent to the older room with a reference to the newly joined room. If the
tombstone event fails to send, the client and server MUST consider the room tombstoned anyways.


## Tradeoffs / issues

This proposal has a number of downsides which may or may not be acceptable to readers.

#### Bots aren't supported

This proposal doesn't support bots or personal assistants. They both end up being treated as
first-class users, resulting in a group DM. This proposal doesn't cover trying to identify
unimportant users, however in future when bots can be identified this module can be adapted.

One possible option which requires minimal changes (unlike [MSC1206](https://github.com/matrix-org/matrix-doc/issues/1206))
is to have the Integration Manager suggest/expose the bots it supports and for clients to
include the list of relevant users in an `unimportant_invites` array on `/createRoom`. The
invites would go out normally to the bots, however they would not have power or identification
as part of the immutability of the DM. How a user adds a bot after the DM is created is
undefined, hence the limitation being listed here rather than being described as a solution
in the proposal.

Invites after the DM is created could potentially be handled by automatically treating them
as unimportant (doesn't affect the room name, avatar, etc). The unimportant users would not
have anythign higher than a default power level in the room.

#### Clients do all the heavy lifting

Instead of having clients track tombstones, room members, creation events, and account data they
could instead rely on the server to track all this for them. This could take the shape of the
client having read-only access to `m.direct_chats` account data and the server keeping it updated
for the user.

#### Migration plan sucks real bad

Upgrading your DMs sounds like a horrible way to slow down the server and feels tedious. Clients
would additionally have to put in a non-trivial amount of work to migrate users, handling common
cases of users with hundreds (and thousands) of direct chats.


## Alternative solutions

This proposal is intentionally written at the far side of the spectrum where enforcement is an
essential part of how the DM works. Just as easily this could be flagged as a state event in
the room (`m.room.direct`?) which when combined with an invite-only room results in a cosmetic
immutable DM.

This proposal could also take a stance somewhere in the middle in the spectrum and mix cosmetic
requirements with enforcement, however not to the point of altering the auth rules for rooms.


## Security considerations

Some clients are investigating the usage of immutable DMs for security and privacy related
functionality of their design. For example, client designers are looking into handling key verification
and cross-signing within the immutable DM (if such a concept existed) rather than in a floating
dialog. To accomplish this in a safe and secure way it may be desirable to have high levels of
enforcement regarding immutable DMs. This may increase the user's comfort in knowing that none
of the users in the room can manipulate it.


## Conclusion

Immutable DMs are a hard problem to solve and involve a bunch of tiny changes to multiple parts
of the specification for full enforcement.
