# MSC4311: Ensuring the create event is available on invites

Historically, when processing an incoming invite or outgoing knock, safety tooling would parse the room ID despite
[being opaque](https://spec.matrix.org/v1.15/appendices/#room-ids), to determine the server which
originally created the room. If that server was considered abusive, the invite or
knock may be rejected or blocked early by the tooling. Note that checking the domain of the
sender of an invite is inadequate, because the sender may not be on the same server as the
user who created the room.

With [MSC4291](https://github.com/matrix-org/matrix-spec-proposals/pull/4291), room IDs lose their
domain component. This, combined with [Stripped State](https://spec.matrix.org/v1.15/client-server-api/#stripped-state)
recommending rather than requiring the `m.room.create` event, makes the above check harder if not
impossible when the create event is missing or incomplete, as the room ID cannot be confirmed in
MSC4291+ room versions.

To mitigate the problem in the case of invites,
this MSC shifts the `m.room.create` event to a *required* stripped state event, and imposes validation
to ensure the event matches the room. To support the new validation, the `m.room.create` event must
be formatted as a full PDU in the stripped state of [invites](https://spec.matrix.org/v1.15/server-server-api/#put_matrixfederationv1inviteroomideventid)
over federation. Similar treatment is applied to other stripped state events for uniformity.

[Knocks](https://spec.matrix.org/v1.15/server-server-api/#put_matrixfederationv1send_knockroomideventid)
additionally include the full PDU format, though only to ensure symmetry between the two instances of
stripped state. It's not possible to prevent a knock based on stripped state because the server will
have already sent the knock before stripped state is received.


## Proposal

On the Client-Server API, `m.room.create` MUST be provided in [Stripped State](https://spec.matrix.org/v1.15/client-server-api/#stripped-state),
where available. No other changes are proposed to the Client-Server API. For clarity, this means clients
continue to receive events which only have `content`, `sender`, `state_key` (optional), and `type` in
the `invite_room_state`, `knock_room_state`, and wherever else stripped state is used.

Over federation, servers MUST include the `m.room.create` event in the [`invite_room_state`](https://spec.matrix.org/v1.15/server-server-api/#put_matrixfederationv1inviteroomideventid)
and [`knock_room_state`](https://spec.matrix.org/v1.15/server-server-api/#put_matrixfederationv1send_knockroomideventid).
Servers MUST additionally format events in `invite_room_state` and `knock_room_state` as PDUs according
to that room version's event format specification. Together, these changes allow servers to validate
the room ID matches the invite (or knock, though it's already sent by the time validation would happen).

Specifically, including the `m.room.create` event as a full PDU allows servers to calculate the room
ID by hashing the event in MSC4291+ room versions. For other room versions (1 through 11), the server
can at most compare the `room_id` field of the create event with the invite/knock membership event.

If any of the events are not a PDU, not for the room ID specified, or fail [signature checks](https://spec.matrix.org/v1.15/server-server-api/#validating-hashes-and-signatures-on-received-events),
or the `m.room.create` event is missing, the receiving server MAY respond to invites with a `400 M_MISSING_PARAM`
standard Matrix error (new to the endpoint). For invites to room version 12+ rooms, servers SHOULD
rather than MAY respond to such requests with `400 M_MISSING_PARAM`. For knocks, the server SHOULD remove any events from
`knock_room_state` which fail the same validation check before passing the details along to clients.
Ideally, the server would be able to prevent the knock from happening, though by the time the server
can see the `knock_room_state`, the knock has already happened.

**Note**: Servers SHOULD consider their local ecosystems before imposing this validation completely,
per the "Migration" section later in this document.

The `400 M_MISSING_PARAM` error SHOULD be translated to a 5xx error by the sending server over the
Client-Server API. This is done because there's nothing the client can materially do differently to
make the request succeed.

When comparing the room IDs, servers will need to calculate the room ID from the `m.room.create` event
as described by MSC4291 (take the reference hash of the event for an event ID, swap the sigil).


## Potential issues

* Some server implementations allow safety tooling and other applications to hook into them between
  the Federation API and Client-Server API. Such implementations are encouraged to make the create
  event reasonably available in its full form to those applications. Typically, this will be an internal
  representation of the event which still has the capability to serialize down to a PDU.

* Implementations should take care to not unintentionally trust the events contained in `invite_room_state`
  and `knock_room_state`, despite appearing as complete events. This is due to the lack of each event's
  auth chain being included, and reassurance that the events are the current events.

## Alternatives

This proposal fills a potential gap in information created by MSC4291, making the alternatives roughly
equivalent to "don't do this". A possible alternative is in the shape of [MSC4329](https://github.com/matrix-org/matrix-spec-proposals/pull/4329)
where the `/invite` endpoint changes, however the changes are roughly the same as this proposal's.


## Security considerations

Security considerations are made throughout, especially around validating the events included.


## Unstable prefix

This proposal does not require an unstable prefix as the behaviour can be accomplished without overly
affecting client or server implementations.


## Migration

Mentioned above, existing server implementations SHOULD warn rather than fail on invites which don't
have complete PDUs inside `invite_room_state` until their local ecosystem adoption allows for the
full set of validation to be applied. If PDUs are complete, but for a different room, the invite SHOULD
still fail in v12 rooms per the validation above.

This proposal suggests that servers wait no longer than 3 months (or about 1 full spec release cycle)
after this proposal is released to enforce the full validation, though servers may extend this as
needed for their ecosystems to gain support.


## Dependencies

This proposal requires [MSC4291](https://github.com/matrix-org/matrix-spec-proposals/pull/4291) in
order to make any amount of sense.
