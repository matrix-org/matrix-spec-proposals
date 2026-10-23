# MSC3759: Leave event metadata for deactivated users

When a user is deactivated on Matrix, some homeservers choose to remove that user from all the rooms
they are joined to. This isn't strictly part of the Matrix spec, but nonetheless major implementations
like Synapse do so. However to other users in the room, it is not clear whether an account is deactivated
or just leaving the room, and this causes some significant problems.

Bridges are usually designed to interpret leave event from a user as a specific instruction to leave
a remote room. For instance, a user leaving a room bridged to WhatsApp is usually interpreted as the
user wanting to leave the remote side. However when the user **deactivates** their account, services
aren't able to distinguish the intent of the leave as an automated account cleanup actions, rather than
a request to leave all remote bridged rooms. This lack of clarity leads to users finding themselves
completely parted from all their remote contacts, which is certainly not great.

Therefore, this proposal suggests that leave events sent on behalf of a deactivation should include
some metadata to state the source of the leave.

## Proposal

Any `m.room.member` event, sent to a room with a `membership` of `leave` on behalf of a deactivation
should include a new boolean field.

`"m.deactivated": true`

which would be part of the membership content.

```json5
{
  "content": {
    // N.B this assumes that displayname and avatar_url are removed for privacy reasons during a
    // deactivation
    "membership": "leave",
    "m.deactivated": true,
  },
  "event_id": "$143273582443PhrSn:example.org",
  "origin_server_ts": 1432735824653,
  "room_id": "!jEsUZKDJdhlrceRyVU:example.org",
  "sender": "@example:example.org",
  "state_key": "@alice:example.org",
  "type": "m.room.member",
  "unsigned": {
    "age": 1234
  }
}
```

Services and clients that see this key can assume that the user is no longer using Matrix and can therefore
start cleaning up any connected metadata/cached information about the user.

This key MUST only be treated as valid if the `sender` and the `state_key` match. If the event is instead
a kick, the key MUST be ignored.

## Potential issues

Adding a metadata key to leave events means that all users who shared a room with this user would be able
to tell that the user requested a deactivation, rather than just leaving a room. While this does give
away more information about the user, it would also allow any connected service as well as clients to remove
any information. This means that by virtue of including this key, more services can perform erase of a user
from their datastores.

It should be noted, like anything else in a Matrix event, that the key could be sent manually by a user
to "fake their own death". Services MUST not trust this key for actions where identifying the
deactivated status of a user is critical, but where it may only inconvience the user (such as deleting some
bridge configuration) it is satisfactory enough.

## Alternatives

[MSC3720](https://github.com/matrix-org/matrix-spec-proposals/pull/3720) would help in solving this problem,
as services could lookup the status of a user when a leave event comes in and determine the deactivated
status. However this comes with two notable drawbacks:

1. The service would have to poll this endpoint upon *every* leave, which would likely cause more load
   on the homeserver and the service requesting the information. This could be made event worse if the
   endpoint was ratelimited.
2. If there was any chance of a race between the leave event being sent and the response of this endpoint
   confirming, then there could be a chance of data-loss for bridged users. 


## Security considerations

None at this time.

## Unstable prefix

`org.matrix.msc3759.deactivated` should be used instead of `m.deactivated` while this proposal is in review.

## Dependencies

None.