# MSC2403: Add "knock" feature
Many people are in invite-only rooms. Sometimes, someone wants to join such a
room and can't, as they aren't invited. This proposal adds a feature for a
user to indicate that they want to join a room.

# Proposal
This proposal implements the reserved "knock" membership type for the
`m.room.member` state event. This state event indicates that when a user
knocks on a room, they are asking for permission to join. Like all membership
events, it contains an optional "reason" parameter to specify the reason you
want to join. Like other membership types, the parameters "displayname" and
"avatar_url" are optional. This membership can be sent by users who aren't
currently in said room. An example for the membership would look like the
following:
```json
{
  "membership": "knock",
  "displayname": "Alice",
  "avatar_url": "mxc://example.org/avatar",
  "reason": "I want to join this room as I really love foxes!"
}
```

After a knock in a room, a member of the room can invite the knocker, or they
can decide to reject it instead.

## Client-Server API
A new endpoint is introduced in the Client-Server API: `POST
/_matrix/client/r0/knock/{roomIdOrAlias}`. This allows the client to state
their intent to knock on a room.

Additionally, extensions to the `GET /_matrix/client/r0/sync` endpoint are
introduced. These allow a client to receive information about the status of
their knock attempt.

### `POST /_matrix/client/r0/knock/{roomIdOrAlias}`
Or the knocking equivalent of
[`POST
/_matrix/client/r0/join/{roomIdOrAlias}`](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-join-roomidoralias).

The path parameter (`roomIdOrAlias`) is either the room ID or the alias of
the room you want to knock on. Additionally, several `server_name` parameters
can be specified via the query parameters. The post body accepts an optional
string parameter, `reason`, which is the reason you want to join the room. A
request could look as follows:

```json
POST /_matrix/client/r0/knock/%23foxes%3Amatrix.org?server_name=matrix.org&server_name=elsewhere.ca  HTTP/1.1
Content-Type: application/json

{
  "reason": "I want to join this room as I really love foxes!"
}
```

This endpoint requires authentication and can be rate limited.


#### Responses:
##### Status code 200:
The user knocked successfully. The room ID of the knocked on room is returned. Example
reply:
```json
{
  "room_id": "!ZclcEpFTORTjmWIrqH:matrix.org"
}
```

##### Status code 403:
The user wasn't allowed to knock (e.g. they are banned). Example error reply:
```json
{
  "errcode": "M_FORBIDDEN",
  "error": "The user isn't allowed to knock in this room."
}
```

##### Status code 404:
The room was not found. Example error reply:
```json
{
  "errcode": "M_NOT_FOUND",
  "error": "Unknown room."
}
```

### Extensions to `GET /_matrix/client/r0/sync`

In [the response to
`/sync`](https://matrix.org/docs/spec/client_server/r0.6.1#get-matrix-client-r0-sync)
is a `rooms` field. This is a dictionary which currently contains keys
`join`, `invite` and `leave`, which each provide information to the client on
various membership states regarding the user.

It is proposed to add a fourth possible key to `rooms`, called `knock`. Its
value is a mapping from room ID to room information. The room information is
a mapping from a key `knock_state` to another mapping with key `events` being
a list of `StrippedStateEvent`. `StrippedStateEvent`s are defined as state
events that only contain the `sender`, `type`, `state_key` and `content`
keys.

Note that while `join` and `leave` keys in `/sync` use `state`, we use
`knock_state` here. This mirrors `invite`s use of `invite_state`.

These stripped state events contain information about the room, most notably
the room's name and avatar. A client will need this information to show a
nice representation of pending knocked rooms. The recommended events to
include are the join rules, canonical alias, avatar, name and encryption
state of the room, rather than all room state. This behaviour matches the
information sent to remote homeservers when remote users are invited to a
room.

This prevents unneeded state from the room leaking out, and also speeds
things up (think not sending over hundreds of membership events from big
rooms).

Also note that like `invite_state`, state events from `knock_state` are
purely for giving the user some information about the current state of the
room that they have knocked on. If the user was previously in the room, the
state events in `knock_state` are not intended to overwrite any historical
state. This applies storage of state on both the homeserver and the client.

The following is an example of knock state coming down `/sync`.

Request:
```
GET /_matrix/client/r0/sync HTTP/1.1
Content-Type: application/json
```

Response:
```json
{
  ...
  "rooms": {
    "knock": {
      "!abcdefghijklmo:example.com": {
        "knock_state": {
          "events": [
            {
              "content": {
                "join_rule": "knock"
              },
              "sender": "@room_admin:example.com",
              "state_key": "",
              "type": "m.room.join_rules"
            },
            {
              "content": {
                "name": "Some cool room"
              },
              "sender": "@room_admin:example.com",
              "state_key": "",
              "type": "m.room.name"
            },
            {
              "content": {
                "url": "mxc://example.com/xyz54321"
              },
              "sender": "@room_admin:example.com",
              "state_key": "",
              "type": "m.room.avatar"
            },
            {
              "content": {
                "avatar_url": "mxc://example.org/abc1234",
                "displayname": "Knocking User",
                "membership": "knock"
              },
              "sender": "@knocking_user:example.org",
              "state_key": "@knocking_user:example.org",
              "type": "m.room.member",
            }
          ]
        }
      }
    }
  },
  ...
}
```

### Changes regarding the Public Rooms Directory

A problem arises for discovery of knockable rooms. Ideally one wouldn't have
to send their colleagues a room ID for a room that they need to knock on. One
of these methods for room discovery is the [public rooms
directory](https://matrix.org/docs/spec/client_server/r0.6.1#get-matrix-client-r0-publicrooms),
which allows us to explore a list of rooms we may be able to join.

The spec does not prevent us from adding rooms with 'knock' join_rules to the
public rooms directory. However, a user attempting
to join a room in the directory will not know whether to directly attempt a
join, or to knock first. The current content of a `PublicRoomsChunk` does not
contain this information:

```json
{
  "avatar_url": "mxc://bleecker.street/CHEDDARandBRIE",
  "guest_can_join": false,
  "name": "CHEESE",
  "num_joined_members": 37,
  "room_id": "!ol19s:bleecker.street",
  "topic": "Tasty tasty cheese",
  "world_readable": true
}
```

Therefore this proposal adds `join_rule` as a new, optional field to a
`PublicRoomsChunk`. The `join_rule` of knockable rooms will be `knock`,
thus giving clients the information they need to attempt entry of a
room when a client selects it. It also allows clients to display
knockable rooms differently than publicly joinable ones.

For backwards compatibility with old servers, the default value of
`join_rule` is `public`.

### Push Rules

To help knocks be noticed earlier, it would be nice to send a push
notification to those in the room who can act on a knock when it
comes in, rather than everyone in the room. This would require a
push rule to fire only when that user's power level is high enough to
accept or reject a knock.

With the current push rules implementation it is possible to place a
condition on the sender's power level, but unfortunately the same does
not exist for event recipients.

This MSC thus does not propose any changes to push rules at this time,
but acknowledges that it would be useful for a future MSC to address when
the underlying push rules architecture can support it.


## Server-Server API
Similarly to [join](https://matrix.org/docs/spec/server_server/r0.1.4#joining-rooms)
and [leave](https://matrix.org/docs/spec/server_server/r0.1.4#leaving-rooms-rejecting-invites)
over federation, a ping-pong game with two new endpoints is introduced: `make_knock`
and `send_knock`. Both endpoints must be protected via server ACLs.

### `GET /_matrix/federation/v1/make_knock/{roomId}/{userId}`

Asks the receiving server to return information that the sending server will
need to prepare a knock event.

Request format:

| Parameter | Type | Description |
|-----------|------|-------------|
| Path parameters:
| roomId | string | Required. The room ID that should receive the knock.
| userId | string | Required. The user ID the knock event will be for.
| Query Parameters:
| ver | [string] | Required. The room versions the sending server has support for.

Note that `GET /_matrix/federation/v1/make_join/{roomId}/{userId}` does not make `ver`
a required query parameter for backwards compatibility reasons. We have no such restrictions.


Response Format:

| Parameter | Type | Description |
|-----------|------|-------------|
| room_version | string | The version of the room where the server is trying to knock.
| event | Event Template | An unsigned template event. May differ between room versions.

#### Responses
##### Status code 200:
Returns a template to be used to knock on rooms. May depend on room version.
```json
{
  "room_version": "2",
  "event": {
    "type": "m.room.member",
    "room_id": "!somewhere:example.org",
    "content": {
      "membership": "knock"
    },
    "state_key": "@someone:example.org",
    "origin": "example.org",
    "origin_server_ts": 1549041175876,
    "sender": "@someone:example.org"
  }
}
```

##### Status code 400:
This request was invalid, e.g. bad JSON. Example reply:
```json
{
  "errcode": "M_INCOMPATIBLE_ROOM_VERSION",
  "error": "Your homeserver does not support the features required to join this room",
  "room_version": "3"
}
```

##### Status code 403:
This request is forbidden, e.g. the user is banned from the room. Example reply:
```json
{
  "errcode": "M_FORBIDDEN",
  "error": "You are not allowed to knock on this room"
}
```

##### Status code 404:
The room is unknown to the remote server. Example reply:
```json
{
  "errcode": "M_NOT_FOUND",
  "error": "Unknown room"
}
```

### `PUT /_matrix/federation/v1/send_knock/{roomId}/{eventId}`
Submits a signed knock event to the resident homeserver for it to accept into
the room's graph. Note that event format may differ between room versions.

Note that in the past all `send_*` federation endpoints were updated to `/v2`
to remove a redundant HTTP error code from the return body. While we don't
have the same redundancy here, we start off at `/v1` for this new endpoint
as per
[MSC2844](https://github.com/matrix-org/matrix-doc/pull/2844).

Request format:

| Parameter | Type | Description |
|-----------|------|-------------|
| Path parameters:
| roomId | string | Required. The room ID that should receive the knock.
| eventId | string | Required. The event ID for the knock event.

The JSON body is expected to be the full event.

Response Format:

| Parameter | Type | Description |
|-----------|------|-------------|
| `knock_room_state` | [StrippedStateEvent] | Required. State events providing public room metadata

A request could look as follows:
```json
PUT /_matrix/federation/v1/send_knock/%21abc123%3Amatrix.org/%24abc123%3Aexample.org HTTP/1.1
Content-Type: application/json

{
  "sender": "@someone:example.org",
  "origin": "matrix.org",
  "origin_server_ts": 1234567890,
  "type": "m.room.member",
  "state_key": "@someone:example.org",
  "content": {
    "membership": "knock",
    "displayname": "Alice",
    "avatar_url": "mxc://example.org/avatar",
    "reason": "I want to join this room as I really love foxes!"
  }
}
```

#### Response:
##### Status code 200:
The event was successfully accepted into the graph by the homeserver that
received the knock. It must then send this knock into the room, before
responding to the knocking homeserver, indicating the knock succeeded.

The response contains `StrippedStateEvent`s with room metadata (room name,
avatar ...) that the knocking homeserver can pass to the client. The event
types that can be sent here should match those of the `/sync` extensions
mentioned above.

This is loosely based on the
[federated invite](https://matrix.org/docs/spec/server_server/r0.1.4#put-matrix-federation-v2-invite-roomid-eventid)
request content.
```json
{
  "knock_room_state": [
    {
      "content": {
        "join_rule": "knock"
      },
      "sender": "@room_admin:example.com",
      "state_key": "",
      "type": "m.room.join_rules"
    },
    {
      "content": {
        "name": "Some cool room"
      },
      "sender": "@room_admin:example.com",
      "state_key": "",
      "type": "m.room.name"
    },
    {
      "content": {
        "url": "mxc://example.com/xyz54321"
      },
      "sender": "@room_admin:example.com",
      "state_key": "",
      "type": "m.room.avatar"
    },
    {
      "content": {
        "avatar_url": "mxc://example.org/abc1234",
        "displayname": "Knocking User",
        "membership": "knock"
      },
      "sender": "@knocking_user:example.org",
      "state_key": "@knocking_user:example.org",
      "type": "m.room.member",
    }
  ]
}
```

##### Status code 403:
This request is forbidden, e.g. the user is banned from the room. Example reply:
```json
{
  "errcode": "M_FORBIDDEN",
  "error": "You are not allowed to knock on this room"
}
```

##### Status code 404:
The room is unknown to the remote server. Example reply:
```json
{
  "errcode": "M_NOT_FOUND",
  "error": "Unknown room"
}
```

## Restrictions
There are restrictions to being able to set this membership, as well as
accepting or denying the knock.  A formal description of the changes to the auth rules is given below;
first we summarise the semantics of the proposed changes.

### Current membership
Only users without a current membership or with their current membership
set to "knock" or "leave" can knock on a room. This means that a user that
is banned, is invited or is currently in the room cannot knock on it.

### Join Rules
This proposal makes use of the existing "knock" join rule. The value of
`join_rule` in the content of the `m.room.join_rules` state event for a room
must be set to "knock" for a knock to succeed. This means that existing rooms
will need to opt into allowing knocks in their rooms. Other than allowing
knocks, a join rule of "knock" is functionally equivalent to that of
"invite", except that it additionally allows external users to change their
membership to "knock" under certain conditions.

### Auth rules

Each room version defines the auth rules which should be applied in that room version.
This MSC proposes a new room version with the following changes to the [auth
rules from room version 6](https://matrix.org/docs/spec/rooms/v6#authorization-rules-for-events):

* Under "5. If type is `m.room.member`", insert the following after "e. If membership is `ban`":

  ```
  f. If `membership` is `knock`:
    i. If the `join_rule` is anything other than `knock`, reject.
    ii. If `sender` does not match `state_key`, reject.
    iii. If the `sender`'s membership is not `ban`, `invite` or `join`, allow.
    iv. Otherwise, reject.
  ```

Note that:
    - Both the `sender` and `state_key` fields are set to the user ID of the knocking
      user. This is different to an `invite` membership event, where the `sender` is the inviter and
      the `state_key` is the invitee.
    - f.ii is justified as one user should not be able to knock on behalf of
      another user.
    - f.iii is justified as knocks should not be allowed if the knocking user
      has been banned from the room, is invited to the room or if they are already
      in the room.
    - Knocks are not restricted by power level like invites are. The `join_rules`
      are already used to enforce whether someone can or cannot knock. However,
      power level rules do apply when approving or denying the knock, as discussed
      in the Membership Changes section below.

Additionally, note that redactions of knock events are not a concern, as
`membership` keys are excluded from being redacted as defined by all current
room versions.

## Membership changes
Once someone has sent a `knock` membership into the room, the membership for
that user can be transitioned to the following possible states:
 - `invite`: In this case, the knock was accepted by someone inside the room
   and they are inviting the knocker into the room.
 - `leave`: In this case, similar to how kicks are handled, the knock has
   been rejected. Alternatively, the knocking user has rescinded their knock.
 - `ban`: In this case, the knock was rejected and the user has been prevented
   from sending further knocks.

Let's talk about each one of these in more detail.

### Membership change to `invite`

The knock has been accepted by someone in the room.

The user who is accepting the knock must have the power level to perform
invites. The accepting user's homeserver will then send an invite - over federation if
necessary - to the knocking user. The knocking user may then join the room as
if they had been invited normally.

To accept a knock, the client should call [`POST
/_matrix/client/r0/rooms/{roomId}/invite`](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-rooms-roomid-invite)
with the user ID of the knocking user in the JSON body.

If the knocking user is on another homeserver, then the homeserver of the
accepting user will call [`PUT
/_matrix/federation/v2/invite/{roomId}/{eventId}`](https://matrix.org/docs/spec/server_server/r0.1.4#put-matrix-federation-v2-invite-roomid-eventid)
on the knocking homeserver to inform it that the knock has been accepted.

The knocking homeserver should assume an invite to a room it has knocked on means
that its knock has been accepted, even if the invite was not explicitly
related to the knock attempt.

Note that client or homeserver implementations are free to automatically
accept this invite given they're aware that it's the result of a previous
knock. In case of failing to auto-accept an invite on the homeserver, it's
recommended for homeservers to pass the invite down to the client so that it
may try at a later point (or reject the potentially broken invite) at the user's
discretion.

### Membership change to `leave` via rejecting a knock

The knock has been rejected by someone in the room.

To reject a knock, the rejecting user's client must call [`POST
/_matrix/client/r0/rooms/{roomId}/kick`](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-rooms-roomid-kick)
with the user ID of the knocking user in the JSON body. Rejecting a knock
over federation has a slight catch, though.

When the knocking user is on another homeserver, the homeserver of the
rejecting user needs to send the `leave` event over federation to the
knocking homeserver. However, this is a bit tricky as it is currently very
difficult to have events from a room propagate over federation when the
receiving homeserver is not in the room. This is due to the remote homeserver
being unable to verify that the event being sent is actually from a
homeserver in the room - and that the homeserver in the room had the required
power level to send it. This is a problem that currently affects other,
similar operations, such as disinviting or unbanning a federated user. In
both cases, they won't be notified as their homeserver is not in the room.

While we could easily send the leave event as part of a generic
transaction to the remote homeserver, that homeserver would have no way to
validate the `prev_events` and `auth_events` that the event references. We
could send those events over as well, but those will also reference other
events that require validation and so on.

A simple thing we could easily do here is to trust the leave event implicitly
if it is sent by the homeserver we originally knocked through. We know this
homeserver is (or at least was) in the room, so they're probably telling the
truth. This is almost an edge case though, as while you'll knock through one
homeserver in the room, there's no guarantee that the admin that denies your
knock will be on the same homeserver you knocked through. Perhaps the
homeserver you knocked through could listen for this and then send the event
back to you - but what if it goes offline in the meantime?

As such, informing remote homeservers about the rejection of knocks over
federation is de-scoped for now, and left to a future MSC which can solve
this class of problem in a suitable way. Rejections should still work for the
homeservers that are in the room, as they can validate the leave event for
they have access to the events it references.

### Membership change to `leave` via rescinding a knock
The knocking user has rescinded their knock.

To rescind a knock, the knocking user's client must call [`POST
/_matrix/client/r0/rooms/{roomId}/leave`](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-rooms-roomid-leave).
To rescind a knock over federation, the knocking homeserver must complete
a [`make_leave`, `send_leave` dance](
https://matrix.org/docs/spec/server_server/r0.1.4#leaving-rooms-rejecting-invites)
with a homeserver in the room.

### Membership change to `ban`

The knock has been rejected by someone in the room and the user has been
banned, and is unable to send further knocks.

This one is fairly straightforward. Someone with the appropriate power levels
in the room bans the user. This will have the same effect as rejecting the
knock, and in addition prevent any further knocks by this user from being
allowed into the room.

If the user is unbanned, they will be able to send a new knock which could be
accepted.

To ban the user, the client should call [`POST
/_matrix/client/r0/rooms/{roomId}/ban`](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-rooms-roomid-ban) with the user ID of the knocking user in the JSON body.

Informing the knocking user about the update is the same as rejecting the
knock.

# Potential issues
This new feature would allow users to send events into rooms that they don't
partake in. That is why this proposal enables the `knock` join rule, in
order to allow room admins to opt in to this behaviour.

# Alternatives
The possibility of initiating a knock by sending EDUs between users instead of sending
a membership state event into a room has been raised. This is an ongoing discussion
occurring at https://github.com/matrix-org/matrix-doc/pull/2403/files#r573180627.

# Client UX recommendations
After a knock is received in a room, it is expected to be displayed in the
timeline, similar to other membership changes. Clients can optionally add a way
for users of a room to review all current knocks.

Please also note the recommendations for clients in the "Security considerations"
section below.

# Security considerations
Clients must take care when implementing this feature in order to prevent
simple abuse vectors that can be accomplished by individual users. For
instance, when a knock occurs, clients are advised to hide the reason until
the user interacts with the client in some way (e.g. clicking on a "show
reason" button). The user should reveal the reason only if they choose to.

It is recommended to not display the reason by default as else this would
essentially allow outsiders to send messages into the room.

It is still theoretically possible for a homeserver admin to create many users
with different user IDs or display names, all spelling out an abusive
message, and then having each of them knock in order.

Clients should also do their best to prevent impersonation attacks. Similar to
joins, users can set any displayname or avatar URL they'd like when knocking on
a room. Clients SHOULD display further information to help identify the user,
such as User ID, encryption verification status, rooms you share with the user,
etc. Care should be taken to balance the importance of preventing attacks while
avoiding overloading the user with too much information or raising false
positives.

Another abuse vector is allowed by the ability for users to rescind knocks.
This is to help users in case they knocked on a room accidentally, or simply
no longer want to join a room they've knocked on. While this is a useful
feature, it also allows users to spam a room by knocking and rescinding their
knocks over and over. Particularly note-worthy is that this will generate
state events that homeservers in the room will need to process. And while
join/leave state changes will do the same in a public room, the act of
knocking is much lighter than the act of joining a room.

In both cases, room admins should employ typical abuse mitigation tools, such
as user bans and server ACLs. Clients are encouraged to make employing these
tools easy even if the offensive user or server is not present in the room.

# Unstable prefix

An unstable feature flag is not required due to this proposal's requirement
of a new room version. Clients can check for a room version that includes
knocking via the Client-Server API's [capabilities
endpoint](https://matrix.org/docs/spec/client_server/r0.6.1#get-matrix-client-r0-capabilities).
Experimental implementation should use `xyz.amorgan.knock` as a room version identifier.

The new endpoints should contain an unstable prefix during experimental
implementation. The unstable counterpart for each endpoint is:

C-S knock:

* `POST /_matrix/client/knock/{roomIdOrAlias}`
* `POST /_matrix/client/unstable/xyz.amorgan.knock/knock/{roomIdOrAlias}`

S-S make_knock:

* `GET /_matrix/federation/v1/make_knock/{roomId}/{userId}`
* `GET /_matrix/federation/unstable/xyz.amorgan.knock/make_knock/{roomId}/{userId}`

S-S send_knock:

* `PUT /_matrix/federation/v1/send_knock/{roomId}/{eventId}`
* `PUT /_matrix/federation/unstable/xyz.amorgan.knock/send_knock/{roomId}/{eventId}`

Finally, an unstable prefix is added to the key that comes down `/sync`,
the join rule for rooms and the `content.membership` key of the member
event sent into rooms when a user has knocked successfully. Instead of
`knock`, experimental implementations should use `xyz.amorgan.knock`.
