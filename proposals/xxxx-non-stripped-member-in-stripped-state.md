# MSCXXXX: Non-stripped room member event in stripped state

In the Client-Server API, the response of the [`GET /sync`](https://spec.matrix.org/v1.15/client-server-api/#get_matrixclientv3sync)
endpoint, the `events` array in the `invite_state` for rooms under `invite` and in the `knock_state`
for rooms under `knock` are defined as containing the stripped state of the room.

This stripped state comes over federation, via the
[`PUT /invite`](https://spec.matrix.org/v1.15/server-server-api/#put_matrixfederationv2inviteroomideventid)
and [`PUT /send_knock`](https://spec.matrix.org/v1.15/server-server-api/#put_matrixfederationv1send_knockroomideventid)
endpoints in the Server-Server API.

In the definition of the [stripped state](https://spec.matrix.org/v1.15/client-server-api/#stripped-state)
it is recommended to contain the following state events:

- `m.room.create`
- `m.room.name`
- `m.room.avatar`
- `m.room.topic`
- `m.room.join_rules`
- `m.room.canonical_alias`
- `m.room.encryption`

Although these events are useful to be able to present information about the room, they don't
contain information about the event itself, like the sender of the invite, or when it occurred.

_Note that this specifies behavior that has been implemented for a long time in homeserver
implementations and that clients already rely on._

## Proposal

The `m.room.member` event that was created during the invite or knock process MUST be present in
the `events` of the `invite_state` or `knock_state`. Since servers have access to the whole event,
and for clients to be able to access the time of the event via the `origin_server_ts` field, it
MUST use the same format as can be found in the `events` of `timeline` and `state` for rooms under
`join`. This is the format currently defined as
[`ClientEventWithoutRoomID`](https://spec.matrix.org/v1.15/client-server-api/#get_matrixclientv3sync_response-200_clienteventwithoutroomid).

_Note that the example for the response of `GET /sync` already include the stripped `m.room.member`
event although it is not specified._

Furthermore, clients need to be able to display information about the sender of an invite, like
their display name or avatar. The list of events that should be included in the stripped state is
extended with the stripped `m.room.member` event of the `sender` of the invite.

## Potential issues

By showing more information about the sender of an invite, users might be subject to undesirable
content like abusive language or images. Mitigating this is out of scope of this MSC, and other MSCs
exist for this, like [MSC4278](https://github.com/matrix-org/matrix-spec-proposals/pull/4278).


## Alternatives

No relevant alternatives.


## Security considerations

No potential security issues are known to the author.


## Unstable prefix

None necessary, this is adding existing event types into existing arrays.


## Dependencies

None.
