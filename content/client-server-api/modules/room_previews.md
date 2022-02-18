---
type: module
---

### Room Previews

It is sometimes desirable to offer a preview of a room, where a user can
"lurk" and read messages posted to the room, without joining the room.
This can be particularly effective when combined with [Guest Access](#guest-access).

Previews are implemented via the `world_readable` [Room History
Visibility](#room-history-visibility). setting, along with a special version of the [GET
/events](#get_matrixclientv3events) endpoint.

#### Client behaviour

A client wishing to view a room without joining it should call [GET
/rooms/:room\_id/initialSync](#get_matrixclientv3roomsroomidinitialsync),
followed by [GET /events](#get_matrixclientv3events). Clients will need to do
this in parallel for each room they wish to view.

Clients can of course also call other endpoints such as [GET
/rooms/:room\_id/messages](#get_matrixclientv3roomsroomidmessages)
and [GET /search](#post_matrixclientv3search) to
access events outside the `/events` stream.

{{% http-api spec="client-server" api="peeking_events" %}}

#### Server behaviour

For clients which have not joined a room, servers are required to only
return events where the room state at the event had the
`m.room.history_visibility` state event present with
`history_visibility` value `world_readable`.

#### Security considerations

Clients may wish to display to their users that rooms which are
`world_readable` *may* be showing messages to non-joined users. There is
no way using this module to find out whether any non-joined guest users
*do* see events in the room, or to list or count any lurking users.
