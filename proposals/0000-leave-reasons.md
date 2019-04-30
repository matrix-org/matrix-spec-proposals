# Proposal to add reasons for leaving a room

This proposal intends to solve [#1295](https://github.com/matrix-org/matrix-doc/issues/1295). Currently
people can be kicked from a room for a human-readable reason, but when voluntarily leaving the `reason`
is not considered. 

## Proposal

Like when kicking someone, `m.room.member` events with `membership: leave` can have a string `reason`.
The reason is a human-readable string of text which clients should display to users of the room, providing
users with the ability to leave a room for a reason of their choosing. The field is optional.

Having such a field gives Matrix better compatibility with other networks such as IRC which use the leave
reason to communicate connection problems ("ping timeout", etc). Although Matrix doesn't have a need for a
persistent connection to remain in the room, having a reason can improve the bridge experience.

An example of a partial leave event with reason would be:
```json
{
  "type": "m.room.member",
  "sender": "@travis:t2l.io",
  "state_key": "@travis:t2l.io",
  "content": {
    "membership": "leave",
    "reason": "I'm in too many rooms and never talk here"
  }
}
```


## Potential issues

There is a chance that quality of communication may deteriorate as a result of adding this field. Arguments
in rooms may result in the leave reason having personal attacks against other room members or rude remarks.
Moderators would be expected to handle these situations for these cases, including redacting the state event
if needed.

This also opens up an avenue for spam by having a very large reason for leaving. Clients are encouraged to
trim/hide the reason at a reasonable length.
