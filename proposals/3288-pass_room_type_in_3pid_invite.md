# MSC3288: Make email invites space aware

Currently when inviting via 3pid, the Identity Server is getting some information about the room,
like for example the room name and avatar as well as the inviter name.
This allows the identity server to generate a rich email to the invitee.

Now that the matrix spec supports spaces, it would be nice to also provide this information to the identity server
so that the email invite could be customized for spaces, current implementation would say wrongly that 
you are invited to a room when the room is actually a space.

The goal of this proposal is to make 3pid invites space aware.


## Proposal

Home servers should also send the `room_type` to the identity server when performing a third party invite (__Invitation storage__).


__Proposed change:__

Add a new `room_type` field in json body of `POST /_matrix/identity/v2/store-invite`

| Parameter | Type | Description |
|--|--|--|
| room_type  | string  | The room type for the room to which the user is invited. This should be retrieved from the value of `type` in `m.room.create` event.

````
POST /_matrix/identity/v2/store-invite HTTP/1.1
Content-Type: application/json

{
  "medium": "email",
  "address": "foo@example.com",
  "room_id": "!something:example.org",
  "sender": "@bob:example.com",
  "room_alias": "#somewhere:exmaple.org",
  "room_avatar_url": "mxc://example.org/s0meM3dia",
  "room_join_rules": "public",
  "room_name": "The Bob Project",
  "room_type": "m.space",
  "sender_display_name": "Bob Smith",
  "sender_avatar_url": "mxc://example.org/an0th3rM3dia"
}
````

The identity server could then use room type to customize the email depending on the room type.


## Potential issues

None.


## Security considerations

None.

## Unstable prefix

The following mapping will be used for identifiers in this MSC during development:


Proposed final identifier       | Purpose | Development identifier
------------------------------- | ------- | ----
`room_type` | event type | `org.matrix.msc3288.room_type`