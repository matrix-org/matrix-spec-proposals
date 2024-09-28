# MSC2409: Proposal to send EDUs to appservices

*Node: This proposal is a continuation of [MSC1888](https://github.com/matrix-org/matrix-doc/pull/1888)
and deprecates that one.*

The [appservice /transactions API](https://matrix.org/docs/spec/application_service/r0.1.2#put-matrix-app-v1-transactions-txnid)
currently supports pushing PDU events (regular message and state events)
however it doesn't provison for EDU events (typing, presence and more). This means that bridges cannot
react to Matrix users who send any typing or presence information in a room the service is part of.

There is an interest amongst the community to have equal bridging on both sides of a bridge, so that
read reciepts and typing notifications can be seen on the remote side. To that end, this proposal
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

Note that the EDU is otherwise formatted as it would for client-server API transport.

To-device messages are a bit special as they are aimed at a particular user/device ID
combo. These events are annotated by the server with a `to_device_id` and `to_user_id`
field at the top level of the message for transport to the appservice:

```json5
{
  "type": "org.example.to_device_event_type",
  "sender": "@alice:example.com",
  "to_user_id": "@_irc_bob:example.org",
  "to_device_id": "ABCDEF123",
  "content": {
    "hello": "world"
  }
}
```

Unlike other ephemeral events, to-device messages are included at a top level `to_device`
array in the transaction. If there are no messages to be sent, the array can be omitted.
This is primarily due to how to-device messages work over federation: they get wrapped in
an EDU (`m.direct_to_device`) but that parent EDU is stripped out before sending the message
off to clients. This can lead to potential conflict where if down the line we support EDUs
and to-device messages with the same event type: consumers would be uncertain as to whether
they are handling an EDU or to-device message.

A complete example of the transaction with all 3 arrays populated would be:

```json5
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
    }
  ],
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
  ],
  "to_device": [
    {
      "type": "org.example.to_device_event_type",
      "sender": "@alice:example.com",
      "to_user_id": "@_irc_bob:example.org",
      "to_device_id": "ABCDEF123",
      "content": {
        "hello": "world"
      }
    }
  ]
}
```

### Expectations of when an EDU should be pushed to an appservice

It is not clear at face value what should be pushed to an appservice. Appservices claim
namespaces of users which registers "interest" in the rooms where those users reside, as
well as claiming namespaces of rooms for explicit interest. However, not all EDUs are
associated with a single room (presence, etc).

If the EDU is capable of being associated to a particular room (i.e. `m.typing` and `m.receipt`), it should be sent to the
appservice under the same rules as regular events (interest in the room means sending it).
For EDUs which are not associated with a particular room, the appservice receives the EDU
if it contextually *would* apply. For example, a presence update for a user an appservice
shares a room with (or is under the appservice's namespace) would be sent to the appservice.

To-device messages for devices belonging to the appservice's user namespaces should always
be sent.

### Implementation detail: when to delete a to-device message

Not defined by this MSC is an explicit algorithm for when to delete a to-device message (mark
it as sent). This is left as an implementation detail, though a suggested approach is as
follows:

* If the message is sent to a user under an appservice's *exclusive* namespace, mark it as sent
  and delete it. Note that retried transactions will still need to include the message.
* If the message is sent to a user under an appservice's *inclusive* namespace, mark it as sent
  to the appservice but do not delete it until a `/sync` request is completed which includes the
  message. Note that retried transactions will still need to include the message.

This approach is largely to align with how namespaces are used by appservices in practice, but
is not applicable to all scenarios (and thus is an implementation detail). The majority of known
appservices use exclusive namespaces, which typically also means that those users will not be
calling `/sync`. Because of this, the server may never get another opportunity to delete the
messages until it has confirmed that the appservice received the transaction successfully. Inclusive
namespaces are typically used when the appservice wants to impact a subset of users, but without
controlling those users explicitly. Typically, inclusive users are also calling `/sync` and so
the appservice should be CC'd on the to-device messages that would normally go down `/sync`.

## Potential issues

Determining which EDUs to transmit to the appservice could lead to quite some overhead on the
homeservers side. Additionally, more network traffic is produced, potentially straining the local
network and the appservice more. As such, appservices have to opt-in to receive EDUs.

## Security considerations

The homeserver needs to accurately determine which EDUs to send to the appservice, as to not leak
any metadata about users. Particularly `m.presence` could be tricky, as no `room_id` is present in
that EDU.

## Unstable prefix

In the transaction body, instead of `ephemeral`, `de.sorunome.msc2409.ephemeral` is used.

In the transaction body, instead of `to_device`, `de.sorunome.msc2409.to_device` is used.

In the registration file, instead of `receive_ephemeral`, `de.sorunome.msc2409.push_ephemeral` is used.
