# MSC4465: On-Demand Fetch for Missing Events

When a homeserver joins a room it lacks prior history for, it is often missing historical
event PDUs that may be relevant or visible to users (e.g. via [`m.room.pinned_events`][pins],
replies, etc.). Many implementations respond to [requests for unknown events][CS_get_evt]
with `M_NOT_FOUND` is it does not exist locally, which this MSC addresses.

When conversation within the room refers to prior (pinned) events that a member does
not have access to, this increases friction and eliminates one of the primary use
cases of referencing events: to share important historical information with new room
participants.

This proposal supersedes [MSC4463][MSC4463] by generalizing it to all forms of references,
including message replies.

## Proposal

If a server receives a request to [`/_matrix/client/v3/rooms/{roomId}/event/{eventId}`][CS_get_evt]
for an `eventId` it is not aware of, it SHOULD attempt to fetch the event from other
servers in the room and return it to the client.

Homeservers MAY use backfill or the [`/_matrix/federation/v1/event/{eventId}`][SS_get_evt] for this
purpose. Homeservers use a best-effort mechanism to select servers believed to have the event (such
as the alias server or room moderators' servers), but this is left as an implementation decision
as with all other forms of backfill.

## Potential issues

Some server implementations do not handle outlier events well, which this may create in the DAG
if the server chooses to persist these events.

## Alternatives

Fetching referenced events in room state on join: [MSC4463][MSC4463]

## Security considerations

N/A

## Unstable prefix

N/A, this MSC does not introduce any new identifiers and only serves to provide a
recommendation to server implementations.

## Dependencies

None.

[CS_get_evt]: https://spec.matrix.org/v1.18/client-server-api/#get_matrixclientv3roomsroomideventeventid
[pins]: https://spec.matrix.org/v1.18/client-server-api/#mroompinned_events
[SS_get_evt]: https://spec.matrix.org/v1.18/server-server-api/#get_matrixfederationv1eventeventid
[MSC4463]: https://github.com/matrix-org/matrix-spec-proposals/pull/4463
