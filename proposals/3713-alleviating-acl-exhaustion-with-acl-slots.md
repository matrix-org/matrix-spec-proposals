# MSC3713: Alleviating ACL exhaustion with ACL Slots

## Introduction

This MSC exists for a very simple reason. ACL event capacity exhaustion is a real danger that is 
realistic or at least seems so based on the context of the events that started around 2022-02-03. 
The events in question are not needed to go into but the result is worthy of mention. In a single day the
feline.support perspective of certain matrix.org rooms reported hundreds of ACL revisions and reports of 
ACL capacity starting to be a future concern.

What does this MSC do to address these concerns about a potential ACL exhaustion situation happening in
a room? Well simple it creates the ACL Slots system. This system is intended as a measure that is
acceptable even if it becomes a long term fix. This MSC will not address the flaws of the ACL system
it will only aim to alleviate this singular problem. A future MSC is perfectly welcome to fix any flaws
in the ACL system that it identifies. 

This system works by sending `m.room.server_acl` events with the state key of `X`
X represents the slot number used by a given ACL event. The exact number of slots is tied to the
room version in use and this MSC suggests that a future room version augments the auth rules to make it 
illegal to send a ACL with a key that is outside of the allowed slot range for the room version. 
The reason that its tied to room versions is simple. All servers should be able to know the max amount
ACL events that they need to keep track of for a given room and it should not change therefore tie it to
the room version the room uses. For existing rooms the auth rules wont help us but instead homeservers 
will just ignore any event that is outside the accepted range.


## Proposal

As stated in the introduction this system works by sending a modified variant of the `m.room.server_acl`
event. This modified version has only a single change. We put the state key to `X`
the X is the decimal value for the ACL in question inside of the range of 0 - Room Version MAX Value.

For existing room versions at the time of writing this MSC aka Room Versions 1-9 a max value of 32 ACL

events is set. Future room versions are allowed to change this value and are encouraged to if a need or
desire exists. The reason for 512 is well simple its an arbitrary number that Cat thought sounded good.
The number is big enough to make it very hard to exhaust and that is the important part. But also small
enough as to not be completely unreasonable in size. 

The process for applying would be the same as today but you combine all the ACL slots contents that are 
in the same field so all the contents of all the `"allow"` field gets combine and the same goes for
`"deny"` the `"allow_ip_literals"` attribute is only defined inside of the `m.room.server_acl` event with
a state key `0`.

For backward compatibility under this MSC the `m.room.server_acl` state event with a blank key would still
be useable as a fall back. Homeservers that implement this MSC should upon detecting any `m.room.server_acl`
with a slot state key not apply the contents of the `m.room.server_acl` with a blank key if a 
`m.room.server_acl` with a key of `0` exists. 

The ACL event with the key of `0` is special due to that its recommended that its 
always a clone of the non slot `m.room.server_acl` event as to maintain an ACL list that is backwards 
compatible even if the list is incomplete when in this mode. 

Example event for Slot 0
```
{
  "content": {
    "allow": [
      "*"
    ],
    "allow_ip_literals": false,
    "deny": [
      "*.evil.com",
      "evil.com"
    ]
  },
  "event_id": "$example0:example.org",
  "origin_server_ts": 1432735824653,
  "room_id": "!example_room:example.org",
  "sender": "@example:example.org",
  "state_key": "0",
  "type": "m.room.server_acl",
  "unsigned": {
    "age": 1234
  }
}
```
Example Event for Slot 1
```
{
  "content": {
    "allow": [
      "*"
    ],
    "deny": [
      "*.evil.org",
      "evil.org"
    ]
  },
  "event_id": "$example1:example.org",
  "origin_server_ts": 1432735824653,
  "room_id": "!example_room:example.org",
  "sender": "@example:example.org",
  "state_key": "1",
  "type": "m.room.server_acl",
  "unsigned": {
    "age": 1234
  }
}
```

## Potential issues

Potential issues well that this needs support is an obvious one but the author is not aware of that many
issues with this MSC that aren't already issues known about the ACL system it self. This MSC after all 
aims to only alleviate exhaustion as a potential concern and not fix any problems of the ACL system. 

## Alternatives

There are other ideas floating around the author is aware of but considers completely out of the question
like the idea to increase the event size just to accommodate ACL. This MSC exists to serve as an 
alternative to this idea. 

## Security considerations

By limiting the slot count the attack of just consuming a completely obscene amount of ram is somewhat
mitigated but yes its a threat that ACL can eat a copious amount of ram when loaded into ram.

The Author is not aware of any additional new problems this MSC introduces that don't already exist with
todays ACL system.

## Unstable prefix

Unstable implementations should use the event type of `support.feline.msc3713.rev3.room.server_acl`

The first revision of this MSC had implementations use the state key of 
`support.feline.msc3713.rev1.room.server_acl.slot.X` and 
`support.feline.msc3713.rev1.room.server_acl` as the event type.

Revision 2 is also now historical.
Revision 2 used `support.feline.msc3713.rev2.room.server_acl` as the event type and 
`support.feline.msc3713.rev1.room.server_acl.slot.X` as the State key.

Due to the assumption that no implementations ever existed for revision 1 and revision 2 no support is needed for it.

## Dependencies

The author of this MSC is not aware of this MSC having any MSCs pending merging into the spec as 
dependencies.
