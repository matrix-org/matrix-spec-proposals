# MSC4311: Ensuring the create event is available on invites and knocks

Historically, when processing an invite or knock, safety tooling would parse the room ID despite
[being opaque](https://spec.matrix.org/v1.15/appendices/#room-ids) to determine the server which
originally created the room. If that server was considered abusive, the incoming invite or outbound
knock may be rejected or blocked early by the tooling. This approach is preferred because the user
sending the invite may not be on the same server as the user who created the room, though both sender
and creator are checked by safety tooling.

With [MSC4291](https://github.com/matrix-org/matrix-spec-proposals/pull/4291), room IDs lose their
domain component. This, combined with [Stripped State](https://spec.matrix.org/v1.15/client-server-api/#stripped-state)
recommending rather than requiring the `m.room.create` event, makes the above check harder if not
impossible when the create event is missing or incomplete, as the room ID cannot be confirmed in
MSC4291+ room versions.

This MSC shifts the `m.room.create` event to a *required* stripped state event, and imposes validation
to ensure the event matches the room. To support the new validation, the `m.room.create` event must
be formatted as a full PDU in the stripped state of [invites](https://spec.matrix.org/v1.15/server-server-api/#put_matrixfederationv1inviteroomideventid)
over federation. This is not applied to other events for reasons described later in the proposal.

[Knocks](https://spec.matrix.org/v1.15/server-server-api/#put_matrixfederationv1send_knockroomideventid)
additionally include the full PDU format, though only to ensure symmetry between the two instances of
stripped state. It's not possible to prevent a knock based on stripped state because the server will
have already sent the knock before stripped state is received.


## Proposal

On the Client-Server API, `m.room.create` MUST be provided in [Stripped State](https://spec.matrix.org/v1.15/client-server-api/#stripped-state),
where available. No other changes are proposed to the Client-Server API.

Over federation, for room versions affected by [MSC4291](https://github.com/matrix-org/matrix-spec-proposals/pull/4291),
the `m.room.create` event MUST be included in [`invite_room_state`](https://spec.matrix.org/v1.15/server-server-api/#put_matrixfederationv1inviteroomideventid)
and [`knock_room_state`](https://spec.matrix.org/v1.15/server-server-api/#get_matrixfederationv1make_knockroomiduserid)
and MUST be a properly-formatted PDU according to that room version's event format specification. The
full PDU format is used to ensure that receiving applications can independently verify the room ID
by calculating the reference hash of the create event themselves.

If the `m.room.create` event is not present, not a PDU, or not for the room ID specified, the server
MUST fail to continue processing the invite or knock. For invites, this is a `400 M_MISSING_PARAM`
standard Matrix error (new to the endpoint). For knocks, this means the server drops the `make_knock`
response and never completes a `send_knock`. For both operations, the associated Client-Server API
request is failed with `500 M_BAD_STATE`. A 4xx error isn't used for the Client-Server API because
there's nothing the client can materially do differently to fix that request.

For room versions *not* affected by MSC4291, servers SHOULD include the properly-formatted `m.room.create`
PDU. This is not made mandatory to avoid a situation where servers trust data that shouldn't be trusted
for the reasons described by MSC4291.

To determine whether a room is "affected" by MSC4291, servers MUST inspect the `room_id` rather than
the create event's `room_version`. Specifically, a room ID with a domain component is *not* affected
while one without a domain component (and happens to be `!<43 unpadded urlsafe base64 chars>`) *is*
affected. This is done to ensure the server is not potentially confused by a malicious server providing
a create event for a different, unaffected, room.

When a room is affected, the server MUST validate the `m.room.create` event as follows for the purposes
of the above:

1. If the event has a `room_id`, reject.
2. If the event does not otherwise comply with the event format for its self-described room version,
   reject.
3. If the event fails [signature checks](https://spec.matrix.org/v1.15/server-server-api/#validating-hashes-and-signatures-on-received-events),
   reject. The content hash check MAY be skipped as the event can safely be redacted prior to all of
   these checks.
4. If the event's [reference hash](https://spec.matrix.org/v1.15/server-server-api/#calculating-the-reference-hash-for-an-event)
   does not match the event ID contained in the room ID, reject.
5. Otherwise, allow.


## Potential issues

* This technique is not applied to other state events present in stripped state. A future MSC or
  series of MSCs is expected to address this particular concern. Specifically, future work is expected
  to make it easier for applications to independently verify other events included in "stripped" state
  when they become formatted as full PDUs too. (A rename from "stripped state" to something else may
  also be required at that stage.) Until then, the other events are left in their stripped form to
  indicate that they are explicitly untrusted data.

* Some server implementations allow safety tooling and other applications to hook into them between
  the Federation API and Client-Server API. Such implementations are encouraged to make the create
  event reasonably available in its full form to those applications. Typically, this will be an internal
  representation of the event which still has the capability to serialize down to a PDU.


## Alternatives

This proposal fills a potential gap in information created by MSC4291, making the alternatives roughly
equivalent to "don't do this".


## Security considerations

Security considerations are made throughout, especially in areas where an implementation may accidentally
trust data it shouldn't.


## Unstable prefix

This proposal does not require an unstable prefix as the behaviour can be accomplished without overly
affecting client or server implementations.


## Migration

*This section is non-normative for spec writing purposes. It only affects implementations which have
implemented room version 12 upon its release.*

Room version 12 contains MSC4291 and is expected to be used in production prior to this proposal
becoming stable itself. To account for this, servers SHOULD treat "MUST" as "MAY" throughout this
proposal, with the exception of the Client-Server API changes, until 1 full spec release cycle has
passed since this MSC's own release in the specification.

This translates to a timeline anywhere between 2 and 6 months, depending on ecosystem rollout. An
example *possible* release schedule is:

1. August 2025 - Matrix 1.16 is released with Room Version 12.
2. October 2025 - Matrix 1.17 is released with this proposal; servers use "MAY" keywords.
3. January 2026 - Matrix 1.18 is released; servers switch to "MUST" keywords.

Servers MAY switch to "MUST" keywords early if their local ecosystems are prepared for the change.


## Dependencies

This proposal requires [MSC4291](https://github.com/matrix-org/matrix-spec-proposals/pull/4291) in
order to make any amount of sense.
