# MSC2689: Allow guests to operate in encrypted rooms

MSC751 suggested to allow guests to use several endpoints in order to allow guests to use E2EE.
I found that guests are able to join encrypted rooms and read messages from other members. But when the
guest wants to send an event into the room the client receives an "guest access not allowed" error
for the `/rooms/room_id/members` endpoint. I assume the client tries to read the list of room members
to prepare the encryption of the event for the present members. Tests with a patched Synapse showed that
allowing guests to use this endpoint results in a normal behaviour and enables guests to communicate in
encrypted rooms.


## Proposal

Allow guests to use the `GET /_matrix/client/r0/rooms/<room_id>/members` endpoint to enable them to
operate properly in encrypted rooms.


## Alternatives

The list of room members could also be read from the sync. However that would not work with Lazy Loading.
