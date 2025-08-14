# MSC0000: Inviting with authorization

One of the purposes of [MSC4311](https://github.com/matrix-org/matrix-spec-proposals/pull/4311) is
to restore access to the server name of the room's creator(s), allowing decision making to happen
about whether the invite is for a room the target user may (not) want to join. This signal is typically
used in conjunction with other signals, such as the room name, topic, alias, and user sending the
invite.

This proposal is an alternative to MSC4311. Instead of using stripped state to communicate the create
event to the receiving server (and later, clients), the create event is included alongside the invite
event itself for review. This allows stripped state to remain as an untrusted information source, and
defers decisions around whether stripped state should be stripped at all to a later MSC or future
iteration of MSC4311.


## Proposal

A new endpoint, `PUT /_matrix/federation/v3/invite/:roomId` is created, copying the majority of the
specification from the [existing v2 endpoint](https://spec.matrix.org/v1.15/server-server-api/#put_matrixfederationv2inviteroomideventid).
The only changes are:

* The `{eventId}` path parameter is removed because it is an uneccessary footgun in modern room
  versions. The event ID can instead be calculated from hashing the event in the request body.
* The new endpoint MUST only be used in room versions 3 and above due to the above. The older v2 or
  v1 variants would need to be used for room versions 1 and 2.
* The request body now takes the following shape:

  ```jsonc
  {
    "event": {
      "type": "m.room.member",
      "state_key": "@target:example.org",
      "sender": "@sender:remote.example.org",
      "content": {
        "membership": "invite"
      }
      // ... and other fields required for a full PDU
    },
    "invite_room_state": [
      // As already defined today, with no changes.
    ],
    "state": [ // new!
      {
        "type": "m.room.create",
        "state_key": "",
        // ... and other fields required for a full `m.room.create` PDU
      }
    ]
  }
  ```

  **Note**: `room_version` is dropped as it's now implied by the `state[indexOf "m.room.create"]` event.

The new `state` array contains PDUs formatted according to the room version's specification. It MUST
contain at least `m.room.create`, and may in future include further events (and their authorization
events) to replace `invite_room_state` - servers MUST tolerate arrays with more than a single entry.

Servers SHOULD NOT populate `invite_room_state` with an `m.room.create` event. Receiving servers MUST
append the `m.room.create` event from `state` to `invite_room_state` for clients to access, or MUST
replace the `m.room.create` event in `invite_room_state` if an `m.room.create` event was already
specified. The new `m.room.create` event in `invite_room_state` SHOULD be formatted like any other
[stripped state](https://spec.matrix.org/v1.15/client-server-api/#stripped-state) event.

Servers MUST NOT append/replace other non-create events from `state` to `invite_room_state` unless
they can fully verify that event's `auth_events`. Verifying the `auth_events` may involve asking the
remote server for the missing events (which it may deny visibility to while the invite is not technically
sent), or looking at the remainder of the `state` array to see if there's enough answers there.

Servers MUST additionally ensure the `m.room.create` event in `state` is for the room ID described
in both the URL path and `event`. For room versions 3 through 11 this means ensuring the `room_id`
on the create event matches. For room version 12 and above, servers will need to hash the create
event and calculate the room ID instead.

If there are multiple/no `m.room.create` events in `state`, or the room IDs don't match, or the create
event has a non-empty string `state_key`, the request is rejected with `400 M_INVALID_PARAM`.

The 200 OK response is otherwise unchanged from the v2 variant.

The v1 endpoint is deprecated by this MSC (it wasn't deprecated previously), though the v2 endpoint
remains undeprecated so it remains available to room version 1 and 2 rooms.


## Potential issues

* Not deprecating the v2 endpoint is a bit not-great, but adding an event ID footgun to the v3 endpoint
  is a bigger concern in the opinion of the author (though not by much).

* Servers may still attempt to confuse or disorient remote servers and their clients by sending different
  create events in `state` and `invite_room_state`. It's critical that servers do the replacement
  behaviour described in the proposal to avoid becoming confused.


## Alternatives

Noted briefly in the proposal, instead of just the `m.room.create` event, `state` could contain the
entire (recursive) auth chain for the `event`. Auth chains can be incredibly long however, so other
improvements to DAG representation may be needed to fully utilize this. It's further unclear how
helpful the auth chain would be to the receiving server if it were to receive it.

MSC4311 remains the other obvious alternative, either formatting all events or just the create event
as PDUs in the stripped state.


## Security considerations

The requirements imposed by this MSC are intended to prevent servers from allowing invites to go through
for rooms other than the one described by the invite event.


## Unstable prefix

While this proposal is not considered stable, implementations should use `/_matrix/federation/unstable/org.matrix.msc0000/invite/:roomId` instead of the v3 endpoint.


## Dependencies

None applicable.
