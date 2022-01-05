---
type: module
---

### Direct Messaging

All communication over Matrix happens within a room. It is sometimes
desirable to offer users the concept of speaking directly to one
particular person. This module defines a way of marking certain rooms as
'direct chats' with a given person. This does not restrict the chat to
being between exactly two people since this would preclude the presence
of automated 'bot' users or even a 'personal assistant' who is able to
answer direct messages on behalf of the user in their absence.

A room may not necessarily be considered 'direct' by all members of the
room, but a signalling mechanism exists to propagate the information of
whether a chat is 'direct' to an invitee.

#### Events

{{% event event="m.direct" %}}

#### Client behaviour

To start a direct chat with another user, the inviting user's client
should set the `is_direct` flag to [`/createRoom`](/client-server-api/#post_matrixclientv3createroom). The client should do this
whenever the flow the user has followed is one where their intention is
to speak directly with another person, as opposed to bringing that
person in to a shared room. For example, clicking on 'Start Chat' beside
a person's profile picture would imply the `is_direct` flag should be
set.

The invitee's client may use the `is_direct` flag in the
[m.room.member](#mroommember) event to automatically mark the room as a direct chat
but this is not required: it may for example, prompt the user, or ignore
the flag altogether.

Both the inviting client and the invitee's client should record the fact
that the room is a direct chat by storing an `m.direct` event in the
account data using [`/user/<user_id>/account_data/<type>`](/client-server-api/#put_matrixclientv3useruseridaccount_datatype).

#### Server behaviour

When the `is_direct` flag is given to [`/createRoom`](/client-server-api/#post_matrixclientv3createroom), the home server must set the
`is_direct` flag in the invite member event for any users invited in the
[`/createRoom`](/client-server-api/#post_matrixclientv3createroom) call.
