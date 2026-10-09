# MSC4233: Remembering which server a user knocked through

[Knocking](https://spec.matrix.org/v1.12/client-server-api/#knocking-on-rooms) lets a user request
an invite to a room, which may be one their homeserver is not otherwise in. To knock, the homeserver
completes the [federation knock dance](https://spec.matrix.org/v1.12/server-server-api/#knocking-rooms)
through a server already in the room, located using the `via` parameters on
[`POST /_matrix/client/v3/knock/{roomIdOrAlias}`](https://spec.matrix.org/v1.12/client-server-api/#post_matrixclientv3knockroomidoralias).

Once the knock is pending, the knocking server keeps no record of which server it knocked through.
Since room IDs are [unroutable](https://spec.matrix.org/v1.12/appendices/#room-ids), this breaks the
follow-up operations on the knock:

* Rescinding the knock requires a `make_leave`/`send_leave` dance with a server in the room, but
  [`POST /_matrix/client/v3/rooms/{roomId}/leave`](https://spec.matrix.org/v1.12/client-server-api/#post_matrixclientv3roomsroomidleave)
  takes no `via` parameters and the server no longer knows a server in the room. In practice servers
  rescind the knock locally only, leaving it pending in the room.
* Rejection of the knock never reaches the knocking user, who sees their request as pending forever.
  [MSC2403 de-scoped](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/2403-knock.md#membership-change-to-leave-via-rejecting-a-knock)
  informing the knocking server of a rejection, while suggesting the eventual solution: trust a leave
  event sent by the homeserver the user knocked through.

This proposal requires the knocking server to remember the server that fulfilled the knock, and to
use it to route the rescinded knock and to validate a rejection. There are no client-visible changes.

## Proposal

When a homeserver completes the knock dance on behalf of a user, it MUST remember which server
answered `/send_knock`, for at least as long as the knock remains the user's membership in the room.
Only the most recent knock per user and room need be tracked.

### Rescinding the knock

When a user calls `POST /rooms/{roomId}/leave` for a room in which their membership is a pending
knock and their homeserver is not in the room, the homeserver MUST attempt the
`make_leave`/`send_leave` dance through the remembered server, as though it had been supplied as a
`via` parameter on the request. If no server was remembered (for example the knock predates this
proposal) or the dance fails, the server falls back to generating the leave locally, as today.

Servers SHOULD similarly use the remembered server as an implicit `via` for other room-ID-based
requests the user makes concerning the knocked room, such as the room summary API proposed in
[MSC3266](https://github.com/matrix-org/matrix-spec-proposals/pull/3266).

### Rejecting the knock

When a server in the room creates a leave or ban event for a knocking user whose homeserver is not
in the room, it SHOULD send that event to the knocking user's homeserver in a federation
transaction, which that homeserver would otherwise not receive.

The knocking homeserver cannot fully authenticate such an event, having no room state. It SHOULD
nevertheless accept it as retracting the knock, storing it as an out-of-band leave or ban in the
same way the knock itself was stored, provided all of the following hold:

* the user's current membership in the room is the knock;
* the knock event is referenced in the event's `auth_events`; and
* the event was received from the server the knock was fulfilled through, or from the event
  sender's own homeserver (against whose keys the event's signature is checked as usual).

## Potential issues

Knocks made before servers implement this proposal have no remembered route, so rescinding them
behaves as it does today.

The remembered server may have left the room or gone offline by the time of the rescinded knock, in
which case the fallback leaves the room's copy of the knock pending, as today. Servers MAY
additionally try other servers, for instance those inferred from the senders of the knock's
stripped state events.

## Alternatives

An earlier revision of this proposal returned the remembered servers to clients as a
`knock_servers` array in `/sync`, for clients to replay as `via` parameters on later requests. That
required changes in every client to round-trip routing information the server already holds, and
did not help `/leave`, which takes no `via` parameters. Server-side tracking fixes all clients
without any API change.

Rejection propagation could be left to a separate MSC, but the remembered knock server is exactly what
makes a rejection trustworthy to the knocking server, so both are addressed here.

## Security considerations

The knocking server accepts a leave or ban event it cannot fully authenticate. The conditions above
bound the exposure: the event must be signed by its sender's server, must reference the knock event
(whose ID a server uninvolved in the room has no way to learn), and must arrive from the server
knocked through or from the sender's own server. What cannot be verified is that the sender has the
power level required to kick or ban. A malicious server in the room could therefore show the
knocking user a rejection that did not really happen; the room's actual state is unaffected and the
user may knock again. This matches the trust model servers already apply when accepting out-of-band
rescinded invites.

The storage requirement is bounded: one server name per user and room, for the most recent knock
only.

## Unstable prefix

None required: this proposal adds no new API surface or event fields. Implementations should gate
the new behaviour behind an experimental configuration flag until this proposal is accepted.

## Dependencies

This proposal does not have formal dependencies, though clients bitten by the described bug are most
likely using [MSC3266](https://github.com/matrix-org/matrix-spec-proposals/pull/3266).
