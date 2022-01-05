---
type: module
---

### Server Notices

Homeserver hosts often want to send messages to users in an official
capacity, or have resource limits which affect a user's ability to use
the homeserver. For example, the homeserver may be limited to a certain
number of active users per month and has exceeded that limit. To
communicate this failure to users, the homeserver would use the Server
Notices room.

The aesthetics of the room (name, topic, avatar, etc) are left as an
implementation detail. It is recommended that the homeserver decorate
the room such that it looks like an official room to users.

#### Events

Notices are sent to the client as normal `m.room.message` events with a
`msgtype` of `m.server_notice` in the server notices room. Events with a
`m.server_notice` `msgtype` outside of the server notice room must be
ignored by clients.

The specified values for `server_notice_type` are:

`m.server_notice.usage_limit_reached`
The server has exceeded some limit which requires the server
administrator to intervene. The `limit_type` describes the kind of limit
reached. The specified values for `limit_type` are:

`monthly_active_user`
The server's number of active users in the last 30 days has exceeded the
maximum. New connections are being refused by the server. What defines
"active" is left as an implementation detail, however servers are
encouraged to treat syncing users as "active".

{{% event event="m.room.message$m.server_notice" %}}

#### Client behaviour

Clients can identify the server notices room by the `m.server_notice`
tag on the room. Active notices are represented by the [pinned
events](#mroompinned_events) in the server notices room. Server notice
events pinned in that room should be shown to the user through special
UI and not through the normal pinned events interface in the client. For
example, clients may show warning banners or bring up dialogs to get the
user's attention. Events which are not server notice events and are
pinned in the server notices room should be shown just like any other
pinned event in a room.

The client must not expect to be able to reject an invite to join the
server notices room. Attempting to reject the invite must result in a
`M_CANNOT_LEAVE_SERVER_NOTICE_ROOM` error. Servers should not prevent
the user leaving the room after joining the server notices room, however
the same error code must be used if the server will prevent leaving the
room.

#### Server behaviour

Servers should manage exactly 1 server notices room per user. Servers
must identify this room to clients with the `m.server_notice` tag.
Servers should invite the target user rather than automatically join
them to the server notice room.

How servers send notices to clients, and which user they use to send the
events, is left as an implementation detail for the server.
