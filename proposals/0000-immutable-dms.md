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
        "rooms": [
            "!room_a:example.org",
            "!room_b:example.org",
            "!room_c:example.org"
        ]
    }
}
```

The event lists all the rooms which are considered DMs by other clients. Ideally, all the rooms
in the list will have been created using the immutable DMs preset defined below. Mapping out
which users are participating in DMs is difficult to represent through JSON, and the identification
of important users is simple, therefore the event is not believed to need more metadata about
the rooms. The event schema additionally supports future expansion in that the array is nested
in a dedicated property, giving room for future changes to the event.

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
      "invite": 50,
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
* Encryption is enabled by default using the `m.megolm.v1.aes-sha2` algorithm.

Clients which support the direct messaging module of the Client-Server API MUST use the new
`m.direct_chats` account data to determine which DMs the user is in. Clients MUST use the power
levels of users in those DMs to determine who they are with: users with power greater than or
equal to `state_default` are considered "important". When a user attempts to start a new direct
chat with an important user, the existing room should be re-used instead. Unimportant users are
all other users in the room, such as bots and personal assistants. Unimportant users do not affect
who the DM is considered to be with.

For example, if Alice and Bob (both power level 50) are in a DM and invite Charlie, Charlie is
not to be considered important for the DM. This means that when Alice or Bob starts a chat with
Charlie, the existing room with all 3 of them will not be re-used. However, if Alice were to start
a chat with Bob, the existing room containing Bob and Charlie would be re-used.

A room must not be considered a DM if the join rules are anything other than `invite`.

Servers SHOULD assist clients by reusing room IDs for known DMs on repeated calls to `/createRoom`
using the same invited users and immutable DM preset.

The rationale for preventing either party from manipulating the room is to ensure that there is
equal representation of the room from both parties (automatically named, automatic avatar, etc).
Users generally expect that a DM will be predictably dressed for searching and scanning, meaning
that the other parties cannot change the aesthetics of the room. For predicatble history and
privacy, the room's history & join rules are locked out from the users. The users can upgrade the
room at any time to escape power level struggles, although this may not maintain the DM status.

Unimportant users MUST NOT be used to name the room (cannot appear in heroes or in automatic naming
for rooms).

Tombstoned (previously upgraded) immutable DMs MUST be removed from the `m.direct_chats` account
data event and cannot be considered an immutable DM. Tombstoned immutable DMs are dead rooms on
the user's account, preserved for history retention.

DMs may involve multiple important users, and are entirely valid in the eyes of this proposal.

#### Upgrading DM rooms

There may come a time where DM rooms need to be upgraded. When DM rooms are upgraded through the
`/upgrade` endpoint, servers MUST preserve the `content` of the previous room's creation event and
otherwise apply the `immutable_direct_chat` preset over the new room. If conflicts arise between
the previous room's state and the state applied by the preset, the preset takes preference over
the previous room's state. Servers can identify whether a room is a DM or not by peeking at the
user's account data: if the room is listed under the upgrading user's `m.direct_chats`, it is
considered a DM. The room does not have to be listed on all user's direct chats, just the user
who is performing the upgrade.

Servers MUST create the new room by using the the room creation rules listed earlier in this
proposal. This means inviting the other parties of the previous room to the new room automatically
and ensuring the room state is as described above.

#### Migrating existing DMs

Existing DMs can be automatically added to the `m.direct_chats` account data event provided they
meet the power level requirements. Most DMs at this point in Matrix will have been created using
the `trusted_private_chat` preset, giving both participants admin (power level 100) rights in the
room, therefore making them eligible for inclusion in the new direct chats account data. Clients
are encouraged to walk the user through the upgrade/migration process instead of automatically
migrating data. This is to prevent potential collisions between clients while the process happens.

Users are encouraged to upgrade their rooms to be immutable: this can be done in two ways. The
first way is altering the power levels and other state events to match the preset defined above.
The second is using the `/upgrade` endpoint with a new field: `preset`. This proposal encourages
clients to use the first method when migrating existing DMs for users, however the second option
is proposed as an addition to the protocol.

The `preset` field on `/upgrade` acts similar to `/createRoom` and the behaviour described above
regarding upgrading a room: the state implied by the `preset` takes precedence over existing state
in the old room. This applies regardless of the preset being used. When not provided, no default
preset is assumed (ie: all applicable state is transferred without any taking precedence over
another).

An upgrade request body can now look like:
```json
{
    "new_version": "5",
    "preset": "immutable_direct_chat"
}
```

An immutable DM room can be upgraded to a mutable room (ie: a `preset` of `public_chat` will
create a new public room, losing the DM status on the room and the users).

After upgrading, the client MUST update the `m.direct_chats` account data event. Similar
behaviour should apply when the other parties join the upgraded room (for the client which
joined/accepted the invite).

The users of the previous room are the seed users for the new room, as described above in
upgrading a DM room.

#### Handling conflicting rooms

The federation invite API allows for a user to receive an invite to an unverified DM room
with potentially conflicting participants with an existing DM room. Altering the invite API
to include signed membership and creation events is one possibility for ensuring that the
room is unique, however that becomes difficult and expansive to maintain (the target server
would likely end up trying to rebuild the room's state by requesting the gaps in the DAG).
Instead, it is proposed that clients check the power levels of the room to determine if the
room should be considered a direct chat. This renders the `is_direct` flag on invites only
useful for aesthetics for rendering invitations - the flag serves no other purpose if this
proposal were to be accepted.

Clients MUST always check the flag when they join a new room, not just when they are accepting
an invite. If the room conflicts with an immutable DM the client already knows about, a tombstone
state event must be sent to the older room with a reference to the newly joined room. If the
tombstone event fails to send, the client MUST consider the room tombstoned anyways.

#### Server assistance

As mentioned previously in this proposal, servers SHOULD already be re-using rooms for which
the user has a direct chat with another set of users. Similar restrictions SHOULD be in place
to ensure that clients do not accidentally add duplicate direct chats to the account data event.

#### Abandoning/leaving rooms

When an important user leaves or gets kicked/banned from the room the room MUST NOT be counted
as a DM anymore by any clients. For example, a 3 person DM where 1 person leaves would cause
all 3 users to lose the DM status on the room. The room is not downgraded to a 2 person DM due
to potential conflicts with existing DMs.

## Tradeoffs / issues

This proposal has a number of downsides which may or may not be acceptable to readers.

#### Clients do all the heavy lifting

Instead of having clients track tombstones, room members, creation events, and account data they
could instead rely on the server to track all this for them. This could take the shape of the
client having read-only access to `m.direct_chats` account data and the server keeping it updated
for the user.

#### This is reliant on trust

A user could remove a room from their direct chats without leaving the room, which the other
users in the room would be unaware of. This could potentially lead to confusion when that user
tries to initiate a new direct chat with the same users, however it is expected that "power users"
(people who are experienced with the protocol) will be the only ones doing this and likely for
good cause.


## Alternative solutions

DMs could be enforced through atuh rule changes and server enforcement, however this feels
far too complicated and over the top for the simplicity of just using a preset to fix rooms.
An example of how this could look is described [here](https://gist.github.com/turt2live/ed0247531d07c666b19dd95f7471eff4).


## Security considerations

Some clients are investigating the usage of immutable DMs for security and privacy related
functionality of their design. For example, client designers are looking into handling key
verification and cross-signing within the immutable DM (if such a concept existed) rather than
in a floating dialog. To accomplish this in a safe and secure way it may be desirable to have
high levels of enforcement regarding immutable DMs. This may increase the user's comfort in
knowing that none of the users in the room can manipulate it. Clients which need this level of
confidence may wish to ignore insecure DMs and attempt to start new ones by upgrading the existing
DM through a predefiend `preset` (ideally acquiring permission first).


## Conclusion

Immutable DMs are a hard problem to solve and involve a bunch of tiny changes to multiple parts
of the specification. Of the options described, this proposal focuses on making immutable DMs
accessible to modern clients without needing complicated migration processes whereas prior drafts
focused on enforcing immutability as much as possible. This proposal is targeted towards being
a balance between complete enforcement and reasonable expectations of users.
