# MSC4238: Pinned events read marker

Currently, messages are pinned using the `m.room.pinned_events` state event (see
[specification](https://spec.matrix.org/v1.12/client-server-api/#mroompinned_events)). However, when new messages are
pinned by the super user, other users can not detect newly pinned messages.

It primarily happen because `m.room.pinned_events` does not have any information that can help users detect the change.
Resulting in users having no visual clues about newly pinned message. To cope with it they either have to mentally
remember the total number of pinned message or discovery of `m.room.pinned_events` state event in clients timeline
reminds them to check for possibly new pinned messages.

## Proposal

Client should set read marker in user's room account data (see
[specification](https://spec.matrix.org/v1.12/client-server-api/#put_matrixclientv3useruseridroomsroomidaccount_datatype))
after detecting that the user has read the pinned messages. The `type` of this account data is `m.read.pinned_events`
and body content look like: 
```json
{
   "event_id": "$xyz"
}
```
where `$xyz` is the `event_id` of `m.room.pinned_events` state event, signifying all pinned events as read.

Subsequently, when client receives the new `m.room.pinned_events` state event, it can fetch the previously marked state
event using the
[/rooms/{roomId}/event/{event}](https://spec.matrix.org/v1.12/client-server-api/#get_matrixclientv3roomsroomideventeventid)
endpoint. It can then identify the newly pinned messages by filtering the received state event for event IDs that are
not present in the previously marked state event.


## Potential issues
Unknown

## Alternative
Unknown

## Security considerations
Unknown

## Unstable prefix
`org.matrix.msc4238.read.pinned_events` for `m.read.pinned_events`