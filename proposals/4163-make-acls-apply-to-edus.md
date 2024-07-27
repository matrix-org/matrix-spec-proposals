# MSC4163: Make ACLs apply to EDUs

[Access Control Lists](https://spec.matrix.org/v1.11/client-server-api/#server-access-control-lists-acls-for-rooms)
(also known as ACLs) are used to prevent other servers from participating in a room at a federation level,
covering many federation API endpoints, including
[`/send`](https://spec.matrix.org/v1.11/server-server-api/#put_matrixfederationv1sendtxnid). However, while ACLs
are applied on a per-PDU basis on this endpoint, they are not applied to EDUs at all. Considering that some EDUs
are specific to certain rooms (e.g. read receipts & typing indicators), it makes sense to apply ACLs to them as well.


## Proposal

All EDUs which are local to a specific room MUST have ACLs applied to them. This means that for the EDUs currently
in the spec, ACLs would only apply to receipts and typing notifications. Examples of how ACLs should be enforced 
at the point of receiving a transaction for those two types of EDUs are as follows:
  - For
[typing notifications (`m.typing`)](https://spec.matrix.org/v1.11/server-server-api/#typing-notifications),
the `room_id` field inside `content` should be checked, with the typing notification ignored if the `origin`
of the request is a server which is forbidden by the room's ACL. Ignoring the typing notification means that the EDU
MUST be dropped upon receipt.
  - For [read receipts (`m.receipt`)](https://spec.matrix.org/v1.11/server-server-api/#receipts), all receipts
inside a `room_id` inside `content` should be ignored if the `origin` of the request is forbidden by the
room's ACL.

## Potential issues

None considered.

## Alternatives

Leave things as-is, which wouldn't be that big of a deal when you consider that this would only apply
to typing notifications and read receipts currently, which don't allow for very significant disruption inside
a room. However, as ACLs are meant to prevent certain servers from participating in a room at all, it makes
sense to apply ACLs to EDUs which are local to certain rooms, as they are a form of participation.

## Security considerations

None considered.

## Unstable prefix

None required, as no new fields or endpoints are added.

## Dependencies

None.
