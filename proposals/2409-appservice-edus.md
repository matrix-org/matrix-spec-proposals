# MSC2409: Proposal to send typing, presence and receipts to appservices

*Note: This proposal is a continuation of [MSC1888](https://github.com/matrix-org/matrix-doc/pull/1888)
and deprecates that one.*

The [appservice /transactions API](https://spec.matrix.org/v1.11/application-service-api/#put_matrixappv1transactionstxnid)
currently supports pushing PDU events (regular message and state events)
however it doesn't provision for EDU events (typing, presence and receipts). This means that bridges cannot
react to Matrix users who send any typing or presence information in a room the service is part of.

There is an interest amongst the community to have equal bridging on both sides of a bridge, so that
read receipts and typing notifications can be seen on the remote side. To that end, this proposal
specifies how these can be pushed to an appservice.

## Proposal

### Changes to the registration file

In order that appservices don't get flooded with EDUs, appservices have to opt-in to receive them by
setting `receive_ephemeral` to true. A registration file could look like following:

```yaml
id: "IRC Bridge"
url: "http://127.0.0.1:1234"
as_token: "30c05ae90a248a4188e620216fa72e349803310ec83e2a77b34fe90be6081f46"
hs_token: "312df522183efd404ec1cd22d2ffa4bbc76a8c1ccf541dd692eef281356bb74e"
sender_localpart: "_irc_bot"
# We want to receive EDUs
receive_ephemeral: true
namespaces:
  users:
    - exclusive: true
      regex: "@_irc_bridge_.*"
  aliases:
    - exclusive: false
      regex: "#_irc_bridge_.*"
  rooms: []
```

For now, receiving EDUs is all-or-nothing. A future MSC may add more granular
filtering capabilities for appservices.

### Changes to the /transactions/ API

The `PUT /_matrix/app/v1/transactions/{txnId}` API currently supports sending PDUs
via the `events` array.

```json
{
  "events": [
    {
      "content": {
        "membership": "join",
        "avatar_url": "mxc://domain.com/SEsfnsuifSDFSSEF#auto",
        "displayname": "Alice Margatroid"
      },
      "type": "m.room.member",
      "event_id": "$143273582443PhrSn:domain.com",
      "room_id": "!jEsUZKDJdhlrceRyVU:domain.com",
      "sender": "@example:domain.com",
      "origin_server_ts": 1432735824653,
      "unsigned": {
        "age": 1234
      },
      "state_key": "@alice:domain.com"
    }
  ]
}
```

This proposal would extend the `PUT /_matrix/app/v1/transactions/` endpoint to include a new key
`ephemeral` to behave similar to the various sections of the CS API `/sync` endpoint. The `ephemeral` key
MAY be omitted entirely if there are no ephemeral events to send.

```json
{
  "ephemeral": [
    {
      "type": "m.typing",
      "room_id": "!jEsUZKDJdhlrceRyVU:domain.com",
      "content": {
        "user_ids": [
          "@alice:example.com"
        ]
      }
    },
    {
      "type": "m.receipt",
      "room_id": "!jEsUZKDJdhlrceRyVU:domain.com",
      "content": {
        "$1435641916114394fHBLK:matrix.org": {
          "m.read": {
            "@rikj:jki.re": {
              "ts": 1436451550453
            }
          }
        }
      }
    }
  ],
  "events": [
    // ...
  ]
}
```

The reason for a new key rather than bundling the events into `events` is that
existing appservices may mistake them for PDUs and might behave erratically.
While `events` may now be a somewhat misleading name, this is an acceptable tradeoff.

The array is effectively a combination of the `presence` and `ephemeral` sections of the
client-server `/sync` API. User-defined ephemeral events don't exist yet, which means there are
only three event types that can currently occur:
[`m.presence`](https://spec.matrix.org/v1.11/client-server-api/#mpresence),
[`m.typing`](https://spec.matrix.org/v1.11/client-server-api/#mtyping),
and [`m.receipt`](https://spec.matrix.org/v1.11/client-server-api/#mreceipt).

This proposal does not cover any other types of events which are sent as EDUs in the federation API,
such as to-device events or other e2ee features. Those are left to a separate MSC.

EDUs are formatted the same way as they are in C-S sync, with the addition of the `room_id` field
for room-scoped EDUs (`m.typing` and `m.receipt`). `room_id` is not present in the C-S API because
sync nests EDUs inside a room object, but appservices get a flat list of events in all rooms.

### Expectations of when an EDU should be pushed to an appservice

It is not clear at face value what should be pushed to an appservice. Appservices claim
namespaces of users which registers "interest" in the rooms where those users reside, as
well as claiming namespaces of rooms for explicit interest. However, not all EDUs are
associated with a single room (presence, etc).

If the EDU is capable of being associated to a particular room (i.e. `m.typing` and `m.receipt`),
it should be sent to the appservice under the same rules as regular events (interest in the room
means sending it). For EDUs which are not associated with a particular room, the appservice
receives the EDU if it contextually *would* apply. For example, a presence update for a user an
appservice shares a room with (or is under the appservice's namespace) would be sent to the
appservice.

For `m.receipt`, private read receipts (`m.read.private`) should only be sent for users within the
appservice's namespaces. Normal read receipts and threaded read receipts are always sent.

## Potential issues

Determining which EDUs to transmit to the appservice could lead to quite some overhead on the
homeserver side. Additionally, more network traffic is produced, potentially straining the local
network and the appservice more. As such, appservices have to opt-in to receive EDUs.

## Security considerations

The homeserver needs to accurately determine which EDUs to send to the appservice, as to not leak
any unnecessary metadata about users. Particularly `m.presence` could be tricky, as no `room_id` is present in
that EDU.

## Unstable prefix

In the transaction body, instead of `ephemeral`, `de.sorunome.msc2409.ephemeral` is used.

In the registration file, instead of `receive_ephemeral`, `de.sorunome.msc2409.push_ephemeral` is used.
