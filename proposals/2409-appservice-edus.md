# MSC2409: Proposal to send EDUs to appservices

*Node: This proposal is a continuation of [MSC1888](https://github.com/matrix-org/matrix-doc/pull/1888)
and deprecates that one.*

The appservice /transaction API currently supports pushing PDU events (regular message and state events)
however it doesn't provison for EDU events (typing, presence and more). This means that bridges cannot
react to Matrix users who send any typing or presence information in a room the service is part of.

There is an interest amongst the community to have equal bridging on both sides of a bridge, so that
read reciepts and typing notifications can be seen on the remote side. To that end, this proposal
specifiys how these can be pushed to an appservice.

## Proposal

### Changes to the /transaction/ API

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
`ephemeral` to match the CS APIs `/sync`.

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
old implementations may mistake them for PDUs and could cause undefined behaviour.
While `events` may now be a somewhat misleading name, this is an acceptable tradeoff.

### Expectations of when an EDU should be pushed to an appservice

It is not clear at face value what should be pushed to an appservice. An appservice
registers interests in rooms and (usually) it's own users, however EDU events are not
tied to a single room in all situtations and as such there needs to be a specified way of
forwarding these events.

An EDU should be sent to an appservice if the `room_id` is shared by any of the registered appservices
users, if possible. For EDUs where that isn't the case, that is `m.presence`, the EDU should be sent
if the sender is present in a room that is shared by any of the registered appservices users.

## Potential issues

Determining which EDUs to transmit to the appservice could lead to quite some overhead on the
homeservers side. Additionally, more network traffic is produced, potentially straining the local
network and the appservice more.

## Security considerations

The homeserver needs to accuratley determine which EDUs to send to the appservice, as to not leak
any metadata about users. Particularly `m.presence` could be tricky, as no `room_id` is present in
that EDU.
