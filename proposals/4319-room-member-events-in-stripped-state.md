# MSC4139: Room member events in stripped state

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
contain information about the event itself.

The following information can be useful for clients:

- The sender of the invite, including their display name and avatar, to present to the user.
- The time of the invite or knock, to present to the user.
- Whether an invite event was preceded by a knock, if the client wants to auto-accept invites that
  come from knocking.

Furthermore, appservices may want to deduplicate this event received via `/sync` from events
received via `/_matrix/app/v1/transactions`, so they need to be able to identify it uniquely. The
easiest way to do this is to use its `event_id`.

> [!NOTE]
> Part of this proposed change is based on behavior that has been implemented for a long time in
> homeserver implementations and that clients already rely on, but that is currently unspecced.


## Proposal

For clients to be able to get all the details about an invite or knock, a `state` key is added to
the [`InvitedRoom`](https://spec.matrix.org/v1.15/client-server-api/#get_matrixclientv3sync_response-200_invited-room)
and [`KnockedRoom`](https://spec.matrix.org/v1.15/client-server-api/#get_matrixclientv3sync_response-200_knocked-room)
objects. It uses the same format as the [`State`](https://spec.matrix.org/v1.15/client-server-api/#get_matrixclientv3sync_response-200_state)
object in [`JoinedRoom`](https://spec.matrix.org/v1.15/client-server-api/#get_matrixclientv3sync_response-200_joined-room)
and MUST include the `m.room.member` event that was created during the invite or knock process, in
the [`ClientEventWithoutRoomID`](https://spec.matrix.org/v1.15/client-server-api/#get_matrixclientv3sync_response-200_clienteventwithoutroomid)
format.

> [!NOTE]
> Making it mandatory makes sense because this event is the reason why the room appears in `invite`
> or `knock` in the first place. Providing the full event format allows clients to access details
> like the `origin_server_ts`, the `event_id` or the `unsigned` object.

For compatibility with the current client implementations, homeservers SHOULD also include this
event in the `events` array of the `invite_state` or `knock_state` in stripped format.

Clients SHOULD expect the `state` key to be missing and SHOULD look for the `m.room.member` event in
`invite_state` or `knock_state` as a fallback.

> [!NOTE]
> The example for the response of `GET /sync` already includes the stripped `m.room.member` event
> although it is not specified.

Finally, the list of events that should be included in the stripped state is extended with the
stripped `m.room.member` event of the `sender` of the invite. This allows clients to be able to
display information about the sender of an invite, like their display name or avatar.

Example of an `InvitedState` object:

```json
{
  "state": {
    "events": [
      {
        "content": {
          "membership": "invite",
          "displayname": "Alice"
        },
        "type": "m.room.member",
        "state_key": "@alice:example.org",
        "sender": "@bob:example.org",
        "event_id": "$Rqnc-F-dvnEYJTyHq_iKxU2bZ1CI92-kuZq3a5lr5Zg",
        "origin_server_ts": 1432735824653,
        "unsigned": {
          "prev_content": {
            "membership": "knock",
            "displayname": "Alice"
          }
        }
      }
    ]
  },
  "invite_state": {
    "events": [
      {
        "content": {
          "membership": "invite",
          "displayname": "Alice"
        },
        "type": "m.room.member",
        "state_key": "@alice:example.org",
        "sender": "@bob:example.org",
      },
      {
        "content": {
          "m.federate": true,
          "predecessor": {
            "event_id": "$something:example.org",
            "room_id": "!oldroom:example.org"
          },
          "room_version": "11"
        },
        "sender": "@example:example.org",
        "state_key": "",
        "type": "m.room.create",
      },
      {
        "content": {
          "membership": "join",
          "displayname": "Bob"
        },
        "type": "m.room.member",
        "state_key": "@bob:example.org",
        "sender": "@bob:example.org",
      },
    ]
  }
}
```


## Potential issues

This changes the current expectations of clients by moving the `m.room.member` event outside of the
`invite_state` and `knock_state` so they will need to adapt to the change. This is mitigated by
encouraging servers to keep sending the event in these objects.

By showing more information about the sender of an invite, users might be subject to undesirable
content like abusive language or images. Mitigating this is out of scope of this MSC, and other MSCs
exist for this, like [MSC4278](https://github.com/matrix-org/matrix-spec-proposals/pull/4278).


## Alternatives

We could put the full `m.room.member` event in the `events` array of the `invite_state` or
`knock_state`, but mixing event formats in a list is undesirable.

We could put the full `m.room.member` event under another key in the `invite_state` or
`knock_state`, the `state` key was chosen for its similarity with other room objects. It will also
allow to add more events using their full format in the future if needed.

We could add more fields to the stripped state format, but given all the fields that are needed for
the different use cases, it would mean that the stripped state has the same format as normal state.
Using the full event format might give the wrong idea that this state has been validated by the
homeserver, which is currently not possible
(see [this discussion in MSC4311](https://github.com/matrix-org/matrix-spec-proposals/pull/4311#discussion_r2274781824)).
Besides, those fields are really only necessary for the `invite` or `knock` `m.room.member` event.

This doesn't solve the case where a room doesn't have an `m.room.name` or `m.room.canonical_alias`
state event, so [its display name should be computed using the room summary](https://spec.matrix.org/v1.15/client-server-api/#calculating-the-display-name-for-a-room).
This is left to another MSC.


## Security considerations

No potential security issues are known to the author.


## Unstable prefix

While this proposal is not considered stable, implementations should use `org.matrix.msc4319.state`
for the `state` key in `InvitedRoom` and `KnockedRoom`.


## Dependencies

None.
