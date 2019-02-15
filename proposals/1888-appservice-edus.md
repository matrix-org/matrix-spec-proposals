# MSC1888: Proposal to send EDUs to appservices

*Note: This proposal is not ready for review yet and merely is a brief note on what I propose to do.*

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

```javascript
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

This proposal would extend the `PUT /_matrix/app/v1/transactions/` endpoint to include
a new key `ephemeral` to match the CS APIs `/sync`.

*Note: Does m.typing bath user_ids together like that? Looks strange*

```javascript
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

*Note: How do we determine when to send an EDU? If the room_id is shared by any AS user?*

## Tradeoffs

TBD, but probably some.

## Potential issues

TBD, but probably some.

## Security considerations

TBD, but probably some.

## Conclusion

TBD, and there definiely will be one.
