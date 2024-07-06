# MSC4163: Make ACLs apply to EDUs

[Access Control Lists](https://spec.matrix.org/v1.11/client-server-api/#server-access-control-lists-acls-for-rooms)
(also known as ACLs) are used to prevent other servers from participating in a room at a federation level,
covering many federation API endpoints, including
[`/send`](https://spec.matrix.org/v1.11/server-server-api/#put_matrixfederationv1sendtxnid). However, while ACLs
are applied on a per-PDU basis on this endpoint, they are not applied to EDUs at all. Considering that some EDUs
are specific to certain rooms (e.g. read recipts & typing indicators), it makes sense to apply ACLs to them as well.


## Proposal

As EDUs aren't always local to a specific room, ACLs are applied differently depending on the EDU type.

For
[typing notifications (`m.typing`)](https://spec.matrix.org/v1.11/server-server-api/#typing-notifications),
the `room_id` field inside `content` should be checked, with the typing notification rejected if the `user_id`
inside the `content` field is from a server which is forbidden by the room's ACL.

For [read recipts (`m.recipt`)](https://spec.matrix.org/v1.11/server-server-api/#receipts), each `m.read`
recipt for each `room_id` inside `content`, the read recipt should be rejected if the server of the `user_id`
is forbidden by the room's ACL.

## Potential issues

None considered.

## Alternatives

Leave things as-is, which wouldn't be that big of a deal when you consider that this would only apply
to typing notifcations and read recipts currently, which don't allow for very significant disruption inside
a room. However, as ACLs are meant to prevent certain servers from participating in a room at all, it makes
sense to apply ACLs to EDUs which are local to certain rooms, as they are a form of participation.

## Security considerations

None considered.

## Unstable prefix

None required, as no new fields or endpoints were added.

## Dependencies

None.
