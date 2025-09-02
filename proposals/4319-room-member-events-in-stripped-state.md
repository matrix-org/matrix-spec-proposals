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

_Note that part of this proposed change specifies behavior that has been implemented for a long time
in homeserver implementations and that clients already rely on._


## Proposal

For clients to be able to get details about an invite or knock, the `m.room.member` event that was
created during the invite or knock process MUST be present in the `events` of the `invite_state` or
`knock_state`. Making it mandatory makes sense because this event is the reason why the room appears
in `invite` or `knock` in the first place.

_Note that the example for the response of `GET /sync` already include the stripped `m.room.member`
event although it is not specified._

The stripped state event format is modified in the Client-Server and Server-Server APIs to include
the optional `origin_server_ts`. This property is optional for backwards-compatibility but servers
MUST include the `origin_server_ts` if they have it. It means that in the `/sync` response, stripped
state received over federation might lack this field if the other server didn't send it, but the
`m.room.member` event should always have it, since the server always has this event as a PDU.

In the Client-Server API, the optional `unsigned` property is also added, identical to the one in
other event formats. This property is mostly expected for the `m.room.member` event, for clients to
be able to follow the transitions between membership states by looking at `prev_content`.

Example of an `m.room.member` in `invite_state`:

```json
{
  "content": {
    "membership": "invite",
    "displayname": "Alice"
  },
  "type": "m.room.member",
  "state_key": "@alice:example.org",
  "sender": "@bob:example.org",
  "origin_server_ts": 1432735824653,
  "unsigned": {
    "prev_content": {
      "membership": "knock",
      "displayname": "Alice"
    }
  }
}
```

Finally, the list of events that should be included in the stripped state is extended with the
stripped `m.room.member` event of the `sender` of the invite. This allows clients to be able to
display information about the sender of an invite, like their display name or avatar.


## Potential issues

By showing more information about the sender of an invite, users might be subject to undesirable
content like abusive language or images. Mitigating this is out of scope of this MSC, and other MSCs
exist for this, like [MSC4278](https://github.com/matrix-org/matrix-spec-proposals/pull/4278).


## Alternatives

We could put the full `m.room.member` event in the `invite_state` or `knock_state`, but mixing event
formats in a list is undesirable.

We could also put the full `m.room.member` event someplace else, like in a `state` property similar
to rooms under `join` or `leave`. It would have the added benefit that homeservers wouldn't need to
edit the stripped state that was received over federation. However this change would not be
compatible with the current ecosystem where clients already depend on all events being in the
`invite_state` or `knock_state`.


## Security considerations

No potential security issues are known to the author.


## Unstable prefix

None necessary, this is adding existing event types into existing arrays.


## Dependencies

None.
