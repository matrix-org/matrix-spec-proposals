# MSC3288: Add room type to `/_matrix/identity/v2/store-invite` API

Currently when inviting via 3pid, the Identity Server receives some information about the room,
like for example the room name and avatar as well as the inviter name.
This allows the identity server to generate a rich email to the invitee.

Now that the matrix spec supports spaces, it would be nice to also provide this information to the identity server
so that the email invite could be customized for spaces.  The current implementation would say wrongly that 
you are invited to a room when the room is actually a space.

The goal of this proposal is to make 3pid invites space aware.


## Proposal

Homeservers should also send the `room_type` to the identity server when performing a third party invite (__Invitation storage__).


__Proposed change:__

Add a new `room_type` field in json body of [`POST /_matrix/identity/v2/store-invite`](https://matrix.org/docs/spec/identity_service/r0.3.0#post-matrix-identity-v2-store-invite):

| Parameter | Type | Description |
|--|--|--|
| room_type  | string  | The room type for the room to which the user is invited. This should be retrieved from the value of `type` in the `m.room.create` event's `content`. Do not include parameter if `type` is not present in `m.room.create`.

````
POST /_matrix/identity/v2/store-invite HTTP/1.1
Content-Type: application/json

{
  "medium": "email",
  "address": "foo@example.com",
  "room_id": "!something:example.org",
  "sender": "@bob:example.com",
  "room_alias": "#somewhere:example.org",
  "room_avatar_url": "mxc://example.org/s0meM3dia",
  "room_join_rules": "public",
  "room_name": "The Bob Project",
  "room_type": "m.space",
  "sender_display_name": "Bob Smith",
  "sender_avatar_url": "mxc://example.org/an0th3rM3dia"
}
````

The identity server could then use room type to customize the email depending on the room type.

__Email Generation__

The link in the generated email should also pass over the `room_type` to clients ( like it is doing for 
`inviter_name`, `room_name`, `room_avatar`)

## Potential issues

None.


## Security considerations

None.

## Unstable prefix

The following mapping will be used for identifiers in this MSC during development:


Proposed final identifier       | Purpose | Development identifier
------------------------------- | ------- | ----
`room_type` | POST body | `org.matrix.msc3288.room_type`
