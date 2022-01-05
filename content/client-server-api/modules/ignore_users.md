---
type: module
---

### Ignoring Users

With all the communication through Matrix it may be desirable to ignore
a particular user for whatever reason. This module defines how clients
and servers can implement the ignoring of users.

#### Events

{{% event event="m.ignored_user_list" %}}

#### Client behaviour

To ignore a user, effectively blocking them, the client should add the
target user to the `m.ignored_user_list` event in their account data
using [`/user/<user_id>/account_data/<type>`](/client-server-api/#put_matrixclientv3useruseridaccount_datatype). Once ignored, the client will no longer receive events sent by
that user, with the exception of state events. The client should either
hide previous content sent by the newly ignored user or perform a new
`/sync` with no previous token.

Invites to new rooms by ignored users will not be sent to the client.
The server may optionally reject the invite on behalf of the client.

State events will still be sent to the client, even if the user is
ignored. This is to ensure parts, such as the room name, do not appear
different to the user just because they ignored the sender.

To remove a user from the ignored users list, remove them from the
account data event. The server will resume sending events from the
previously ignored user, however it should not send events that were
missed while the user was ignored. To receive the events that were sent
while the user was ignored the client should perform a fresh sync. The
client may also un-hide any events it previously hid due to the user
becoming ignored.

#### Server behaviour

Following an update of the `m.ignored_user_list`, the sync API for all
clients should immediately start ignoring (or un-ignoring) the user.
Clients are responsible for determining if they should hide previously
sent events or to start a new sync stream.

Servers must still send state events sent by ignored users to clients.

Servers must not send room invites from ignored users to clients.
Servers may optionally decide to reject the invite, however.
