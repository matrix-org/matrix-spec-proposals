# MSC3953: Server capability DAG

## The authority of homeservers

Within Matrix, homeservers inherit any authority that any of the server's users has because of the
ability a server has to impersonate users.
This is especially true when a user on a homserver posses the the power level to
change `m.room.power_levels`, as this means the server can then transfer power
the user posses to any other user or server.

Homeservers also have the authority to generate any number of `m.room.member` state events for any
Matrix room where the `m.room.join_rules` is `public`. On top of this, if we want to restrict who
can generate joins, the `m.room.server_acl` event has to anticipate the existence of any malicious
server (if the allow rule is `*`) and is an entirely reactive measure
(unless the room operates on an `allow` only basis, which very few do).
On top of this there is also a limit to the servers that can be allowed and denied in the
`m.room.server_acl` event.

It is also the norm on Matrix for `events_default` and `users_default` to both be `0`, giving
any new user the ability to post a message without restriction. This is because
`m.room.power_levels` is very inflexible and it is known that by changing `m.room.power_levels`
frequently, the depth of the auth dag is increased. Unfortunately
the depth of an auth dag is a recognised risk for increasing the chance of
a room experiencing a state reset.
A single Matrix event is also just not practical for special casing the capabilities of thousands of
users, given the size limits of events.

We recognize there is some hesitancy to acknowledge the role of the homeserver within Matrix,
because this canonicalises Matrix as decentralised rather than distributed.
We are also aware that recognizing the authority of homeservers may conflict with plans to
"make Matrix p2p".
We are not certain, but we also assume attempts to "make Matrix p2p" merely embed a homeserver within
a client, and also require a Matrix-Matrix bridge to interop with existing Matrix room versions.
As such, we do not think there will be a technical conflict, only a conflict of priorities.

## Reshaping event authorization to canonicalise and manage the authority of homeservers.

### What's going on now

Currently the authority of homeservers within Matrix has to be inferred from which users have
power in the room, and the homeservers that they reside on. As we discussed earlier,
homeservers have the power to impersonate their own users to make changes on their behalf, as well
as to join any new user to the room should the `m.room.join_rule` be `public`,
or they have a user which posses the power level to `invite`.
This means that apart from a few special cases, and particularly for public rooms,
user membership can be considered already entirely virtual, yet it remains
a key part of the authorization dag.

### So?

Instead we propose that membership of users be forgoed entirely and that instead server
membership is the only part of room membership that is relevant to event authorization.[^1]

[^1]: I believe this idea was originally discussed by Kegan and Till before but I got the idea from Kegan. Not
sure that either will be thrilled by me appropriating it in this way.

If we take this view, then what happens to user membership?
In order to keep users out of the auth dag, their membership has to be treated as entirely virtual.
Servers that possess membership, and also possess the capability to send events therefore will
also have the authority to send events with any sender local part.
The same would also apply for the use of any capability, a server can use them under any localpart.

There is somewhat of a precedent for this within Matrix already in the form of application
services that provide bridging for third party users.
Though currently application services must first generate member events for the virtual users before
being able to use them in a room. However, the requirement to do so (as mentioned before)
in the majority of cases provides no barrier. As this is already the reality for the overwhelming
majority of public Matrix rooms, there just are no restrictions in place to control the provisioning
of new users by homeservers.
I would like to reiterate that the reason for canonicalising this relationship
is so that we can control and restrict that. Ignoring, obscuring, delaying and
kicking the relationshihp down the road simply prolongs disaster.


## Proposal

### Overview

- Server Membership, Kicks, Bans and Invites
- Server Capabilities
- Authorization
- User Membership, Profiles and Capabilities

While we entertain some discussion about user membership, profiles and capabilities,
we do not yet provide a specific proposal within this MSC.
We expect there to be competing follow up proposals or an edit to this MSC
once the main implications of the server capability DAG have been discussed and are understood.

### Server Membership, Kicks, Bans and Invites

Server membership

We inherit all of the states from `m.room.member`,
`m.room.server_capability.member` has membership `join`, `invite`, `knock`, `leave`, and `ban`.

```json
{
  "content": {
    "membership": "join"
  },
  "state_key": "matrix.org",
  "sender": "@gnuxie:matrix.org",
  "type": "m.room.server_capability.member"
}
```

The `state_key` names the server name that the membership applies to, the
sender shows which user on the server was responsible for the membership.

### Server Capabilities

#### Events

##### `m.room.base_capabilities` state_key: server name

This event describes the capabilities that a server possess.

Example below can give servers invite and any of its existing capabilities.

```
{
  "events": [
    "m.room.avatar",
    "m.room.canonical_alias",
    "m.room.history_visibility",
    "m.room.name",
    "m.room.base_capabilities"
  ],
  "events_default": true,
  "state_default": false,
  "ban": false,
  "kick": false,
  "invite": true,
  "redact": false,
  "notifications": {}
}
```
By default, events are not sendable.
`events`: Names events that should have dedicated capabilities that entities (servers, users) must
posses to be able to send them.
`events_default`: true if any event not named in `events` should be sendable by an entity possesing
`m.room.server_capability.events_default`.
`state_default`: true if any state event not named in `events` should be sendable by an entity
possessing `m.room.server_capability.state_default`.


### Authorization

These are amendments that must be made to the authorization rules, room version 10.

#### Terminology

A connected capability is an event that is directly linked via a reference in
the event's `auth_events` that is of the same type and also possesses the same capability.
If a connected capability A is connected to another capability B, which is connected to another
capability C, then the capabilities A & B, B & C and A & C can all be considered connected.

#### Rule 4, Membership

4.  If type is `m.room.server_capability.member`:
    1.  If there is no `state_key` property, or no `membership` property in
        `content`, reject.
    2.  If the sending server has an existing `m.room.server_capability.member` event granting
		the sender membership, and the `origin_server_ts` of the event granting the sender's
		membership is greater than or equal to the `origin_server_ts` of this event, reject.
    3.  If `content` has a `join_authorised_via_users_server`
        key:
        1.  If the event is not validly signed by the homeserver of the user ID denoted
            by the key, reject.
    4.  If `membership` is `join`:
        1.  If the only previous event is an `m.room.create` and the
            `state_key` is the creator, allow.
        2.  If the domain of the server of the user id in `sender` does not match `state_key`, reject.
        3.  If the server is banned, reject.
        4.  If the `join_rule` is `invite` or `knock` then allow if
            membership state is `invite` or `join`.
        5.  If the `join_rule` is `restricted` or `knock_restricted`:
            1.  If membership state is `join` or `invite`, allow.
            2.  If the `join_authorised_via_users_server` key in `content`
                is not a user with sufficient permission to invite other
                users, reject.
            3.  Otherwise, allow.
        6.  If the `join_rule` is `public`, allow.
        7.  Otherwise, reject.
    5.  If `membership` is `invite`:
        1.  If the `sender`'s server's current membership state is not `join`,
            reject.
        2.  If *target server*'s membership state is `join` or
            `ban`, reject.
        3.  If the `sender`'s server posses `invite` in their respective `m.room.base_capabilities`
			event, allow.
        4.  Otherwise, reject.
    6.  If `membership` is `leave`:
        1.  If the `sender`'s server matches `state_key`, allow if and only if
            that server's current membership state is `invite`, `join`,
            or `knock`.
        2.  If the `sender`'s server membership state is not `join`,
            reject.
        3.  If the *target server*'s server membership state is `ban`,
            and the `sender`'s server does not possess `ban` within the servers's respective
			`m.room.base_capabilities` event, reject.
        4.  If the `sender` server's first *connected* `m.room.base_capabilities`'s
			`origin_server_ts` is less than the *target server*'s first *connected*
			`m.room.base_capabilities`'s `origin_server_ts` that both possess `kick`, allow.
        5.  Otherwise, reject.
    7.  If `membership` is `ban`:
        1.  If the `sender`'s current membership state is not `join`,
            reject.
        2.  If the `sender`' server's first *connected* `m.room.base_capabilities`'s
			`origin_server_ts` is less than the *target server*'s first *connected*
			`m.room.base_capabilities`'s `origin_server_ts` that both possess `ban`, allow.
        3.  Otherwise, reject.
    8. If `membership` is `knock`:
        1.  If the `join_rule` is anything other than `knock` or
            `knock_restricted`, reject.
        2.  If `sender's server` does not match `state_key`, reject.
        3.  If the `sender`'s current membership is not `ban` or `join`, allow.
        4.  Otherwise, reject.
    9.  Otherwise, the membership is unknown. Reject.

#### Rule 9, `m.room.base_capabilities`

9. If type is `m.room.base_capabilities`:
    1.  If the sending server has an existing `m.room.base_capabilities` event and the
		`origin_server_ts` of the event granting the sender's capability
		is greater or equal than the `origin_server_ts` of this event, reject.
    2.  If any of the properties `events_default`, `state_default`,
        `ban`, `redact`, `kick`, or `invite` in `content` are present and
        not a boolean, reject.
    3.  If the property of `events` or `notifications` in `content` is not an array with values
		that are strings, reject.
    4.  If there is no other `m.room.base_capabilities` event in the room,
	    with any state key, allow.
    5.  For the properties `events_default`, `state_default`,
        `ban`, `redact`, `kick`, `invite`, `notifications` and `events` check if they were added,
        changed or removed. For each found alteration:
        1.  If the capability is being attenuated or granted when the `sender` does not possess
            the capability, reject.
        2.  If the capability is possessed by the target and the sender, and they are not the same,
            and the target has a respective connected capability with a lower `origin_server_ts`
			than the sender, reject.
    6. Otherwise, allow.
10. Otherwise, allow.

#### Replacing Reverse topological power ordering

In order to replace power levels on tie breaks, we propose using the `origin_server_ts` of the
capability. This works so long as it is illegal to grant a capability with an `origin_server_ts`
that is less than the `origin_server_ts` of the granting server's own respective
capability and capabilities can only be granted to a different server (not itself).

#### Mainline ordering

WARNING: I did the find and replace job to see if it made sense, I only think that it does.

Let *B* = *B*<sub>0</sub> be an `m.room.base_capabilities` event.
Starting with *i* = 0, repeatedly fetch *B*<sub>*i*+1</sub>, the
`m.room.base_capabilities` event in the `auth_events` of *B<sub>i</sub>*.
Increment *i* and repeat until *B<sub>i</sub>* has no `m.room.base_capabilities`
event in its `auth_events`.
The *mainline of B*<sub>0</sub> is the list of events
    [*B*<sub>0</sub> , *B*<sub>1</sub>, ... , *B<sub>n</sub>*],
fetched in this way.

Let *e* = *e<sub>0</sub>* be another event (possibly another
`m.room.base_capabilities` event). We can compute a similar list of events
    [*e*<sub>1</sub>, ..., *e<sub>m</sub>*],
where *e*<sub>*j*+1</sub> is the `m.room.base_capabilities` event in the
`auth_events` of *e<sub>j</sub>* and where *e<sub>m</sub>* has no
`m.room.base_capabilities` event in its `auth_events`. (Note that the event we
started with, *e<sub>0</sub>*, is not included in this list. Also note that it
may be empty, because *e* may not cite an `m.room.base_capabilities` event in its
`auth_events` at all.)

Now compare these two lists as follows.
* Find the smallest index *j* ≥ 1 for which *e<sub>j</sub>* belongs to the
   mainline of *B*.
* If such a *j* exists, then *e<sub>j</sub>* = *B<sub>i</sub>* for some unique
  index *i* ≥ 0. Otherwise set *i* = ∞, where ∞ is a sentinel value greater
  than any integer.
* In both cases, the *mainline position* of *e* is *i*.

Given mainline positions calculated from *B*, the *mainline ordering based on* *B*
of a set of events is the ordering,
from smallest to largest, using the following comparison relation on
events: for events *x* and *y*, *x* &lt; *y* if

1.  the mainline position of *x* is **greater** than
    the mainline position of *y* (i.e. the auth chain of
    *x* is based on an earlier event in the mainline than *y*); or
2.  the mainline positions of the events are the same, but *x*'s
    `origin_server_ts` is *less* than *y*'s `origin_server_ts`; or
3.  the mainline positions of the events are the same and the events have the
    same `origin_server_ts`, but *x*'s `event_id` is *less* than *y*'s
    `event_id`.


### User Membership, Profiles and Capabilities

We discuss several ways that membershp, profiles and capabilities could be modeled
for Matrix users.
This section is much more informal than the rest as most of this is design work and WIP.

#### Unchecked room state

One option would be to keep user membershp events `m.room.member` and introduce
a copy of `m.room.base_capabilities` for users. However, we believe this will be problematic
as it will be impossible for a server to check that there is an associated
`m.room.member` event for each remote user without also bringing these checks into
authorization rules, which undermines the entire proposal.
Therefore there would have to be the possibility for inconsistencies between
which users have capabilities and the actions that the server has taken on their behalf.
The most obvious example is that a server can generate events in a room for a user without
an associated `m.room.member` event existing.

#### Out of DAG API

Given that the membership of users is entirely a the authority of the server,
it makes more sense to take the opportunity for profile, membership and use specific capability
lookups to happen via an API that is out of channel (ie this information should not
be encoded as room state at all). This would make sense, until an associated server
disappears from the room. If profile information is not part of the room state,
then the hisotry of that information is lost forever. This could be considered an acceptable
compromise, if state events continue to have a problem with scaling.

#### Limited auth rules for users with attenuated capabilities

One way to solve a problem where a server could deliberately ignore a member ban
or the attenuation of one of its users capabilities (compared to the server)
is to include member specific check into the auth only when the member's capabilities
(through `base_capabilities` or `membership`) differ from their server's.

This would probably require the introduction of an event representing `base_capabilities`
for all users on the server by default, which are checked for any event that doesn't match
a member specific `base_capabilities`.

You would also need to consider whether a member ban was applicable in the first place,
member bans might just need to be replaced with a reference to an `m.policy.rule.user`.

##### Something that would work

In addition to the `m.room.base_capabilities` representing the authority of the server.
We extend `m.room.base_capabilities`, using an mxid as the `state_key` for
user specific capabilities.
We extend `m.room.base_capabilities` for a new event `m.room.user_default_capabilities`
with the state key of the server.

Then any event sent from a server will first have its sender used to search for
an entry to `m.room.base_capabilities`. If there is an entry, then the event
is authorized against that.
Otherwise `m.room.user_default_capabilities` is used.

#### Other options

One thing to learn from these different options is that servers need
the ability to infer membership, profiles and capabilities of remote users
in circumstances where a remote server isn't providing consistent information,
and room administrators must be given the opportunity to ban servers that continue
to provide inconsistent information about their users.

## Potential issues

We are sure they exist, and welcome suggestions but have not listed them yet.

- Additional checks may be required to ensure the server is representing its user's presence
  in the room consistently
- We don't provide clear semantics for user level bans or attenuation of their capabilities
- What is the process for transferring a capability to a user via a server from the perspective
  of a client?
- This is a pretty big breaking change, no client is equipped to deal with this,
  even if a legacy DAG is emulated somehow.

## Alternatives

We are sure they exist, and welcome suggestions but have not listed them yet.

## Security considerations

- What impact does this have on smaller rooms such as DMs? It is already understood that
  a server can invite any other member to a DM in current room versions,
  but there may be even more possibilities under this proposal.
- What on earth are you doing with the `origin_server_ts`?
  This is a good question. Since we no longer have power levels,
  We need to have a way of tie breaking when two servers have the same capabilities,
  and one moves to remove the other. Now the idea is that if you
  have had the capability the "longest", then you should come out on top.
  It's not clear yet whether `origin_server_ts` is the best way to encode this.
  Especially if these can be subject to an overflow attack?


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
