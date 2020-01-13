# MSC2403: Add "knock" feature
Many people are in invite-only rooms. Sometimes, someone wants to join such a room and can't, as
they aren't invited. This proposal adds a feature for this user to indicate that they want to join
said room.

# Proposal
This proposal implements the reserved "knock" membership type for the `m.room.member` state event.
This state event indicates that a user knocks a room, that is asking for permission to join. It
contains an optional "reason" parameter to specify the reason you want to join. Like other
memtership types the parameters "displayname" and "avatar_url" are optional. This membership can
be set from users who aren't currently in said room. An example for the membership would look as
follows:
```json
{
  "membership": "knock",
  "displayname": "Alice",
  "avatar_url": "mxc://example.org/avatar",
  "reason": "I want to join this room as I really love foxes!"
}
```

After a knock is received in a room it is expected to be displayed in the timeline, similar to other
membership changes. Clients can optionally add a way for users of a room to review all current
knocks. After a knock in a room a member of the room can invite the knocker.

To be able to implement this properly two new endpoints need to be added, one in the client-server
API and one in the server-server API.

## Restrictions
There are restrictions to being able to set this membership.

### Current membership
Only users without a current membership or with their current membership being "leave" can knock a
room. This means that a user that is banned or currently in the room can't knock on it.

### Join Rules
The `join_rule` of `m.room.join_rules` must be set to "invite". This means that people can't knock
in public rooms. Additionaly the new join rule "private" is introduced. This is so that people can,
when creating a new room, prevent anyone from knocking.

### Power levels
The default power level for "knock" is 0. If a user has a too low power level to knock they aren't
allowed to do this. As power levels can be set for users not currently in the room this can be used
as a way to limit who can knock and who can't.

#### Example:
`@alice:example.org` CAN knock, but `@bob:example.org` can't: The (incomplete) content of
`m.room.power_levels` is as follows:
```json
{
  "users": {
    "@alice:example.org": 1
  },
  "users_default": 0,
  "knock": 1
}
```

## Client-Server API
The new endpoint for the client-server API is `POST /_matrix/client/r0/rooms/{roomId}/knock`.
The path parameter (`roomId`) is the room you want to knock. It is required. The post body accepts
an optional parameter, `reason`, which is the reason you want to join the room. A request could look
as follows:

```
POST /_matrix/client/r0/rooms/%21d41d8cd%3Amatrix.org/knock  HTTP/1.1
Content-Type: application/json

{
  "reason": "I want to join this room as I really love foxes!"
}
```

### Responses:
#### Status code 200:
The user knocked successfully. Empty reply:
```json
{}
```

#### Status code 400:
This request was invalid, e.g. bad JSON. Example reply:
```json
{
  "errcode": "M_UNKNOWN",
  "error": "An unknown error occurred"}
```

#### Status code 403:
The user wasn't allowed to knock (e.g. they are banned). Error reply:
```json
{
  "errcode": "M_FORBIDDEN",
  "error": "The user isn't allowed to knock in this room."
}
```

#### Status code 429:
This request was rate-limited. Example reply:
```json
{
  "errcode": "M_LIMIT_EXCEEDED",
  "error": "Too many requests",
  "retry_after_ms": 2000
}
```

## Server-Server API
The new endpoint for the server-server API is `PUT /_matrix/federation/v2/knock/{roomId}/{eventId}`.
The path parameters are the room id you want to knock and the event id of the knock event. The post
body consists of an `event` parameter, which is the knock event. A request could look as follows:

```
PUT /_matrix/federation/v2/knock/%21abc123%3Amatrix.org/%24abc123%3Aexample.org  HTTP/1.1
Content-Type: application/json

{
  "event": {
    "sender": "@alice:example.org",
    "origin": "example.org",
    "origin_server_ts": 1234567890,
    "type: "m.room.member",
    "state_key": "@alice:example.org",
    "content": {
      "membership": "knock",
      "displayname": "Alice",
      "avatar_url": "mxc://example.org/avatar",
      "reason": "I want to join this room as I really love foxes!"
    }
  }
}
```

### Responses
#### Status code 200:
The knock was performed successfully. The knock event is sent back with the "event" key.
```json
{
  "event": {
    "sender": "@alice:example.org",
    "origin": "example.org",
    "origin_server_ts": 1234567890,
    "type": "m.room.member",
    "state_key": "@alice:example.org",
    "content": {
      "membership": "knock",
      "displayname": "Alice",
      "avatar_url": "mxc://example.org/avatar",
      "reason": "I want to join this room as I really love foxes!"
    }
  }
}
```

#### Status code 400:
This request was invalid, e.g. bad JSON. Example reply:
```json
{
  "errcode": "M_UNKNOWN",
  "error": "An unknown error occurred"}
```

#### Status code 403:
The user wasn't allowed to knock. Error reply:
```json
{
  "errcode": "M_FORBIDDEN",
  "error": "The user isn't allowed to knock in this room."
}
```

# Potential issues
This new feature would allow users to spam rooms that they don't partake in. That is why this proposal
adds both the new join rule and the new power level, in order to allow room admins to mitigate such
potential spam.

# Alternatives
As for the join rule "invite", instead the join rule "knock" could be introduced, meaning the room
is like "invite" only that people can also knock. The difference is for existing rooms: With this
proposal people can knock in existing "invite" rooms, with the alternative suggestion they can't.

# Security considerations
None. This doesn't allow users access to a room in any way.
