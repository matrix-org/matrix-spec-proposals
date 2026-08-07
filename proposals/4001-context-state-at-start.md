# MSC4001: Return start of room state at context

The endpoint `GET /_matrix/client/v3/rooms/{roomId}/context/{eventId}` 
describes that the `state` field in the 200 response returns the state of the 
room at the **last** event returned. This is the case for all six spec versions 
released so far:

- [v1.1](https://spec.matrix.org/v1.1/client-server-api/#get_matrixclientv3roomsroomidcontexteventid)
- [v1.2](https://spec.matrix.org/v1.2/client-server-api/#get_matrixclientv3roomsroomidcontexteventid)
- [v1.3](https://spec.matrix.org/v1.3/client-server-api/#get_matrixclientv3roomsroomidcontexteventid)
- [v1.4](https://spec.matrix.org/v1.4/client-server-api/#get_matrixclientv3roomsroomidcontexteventid)
- [v1.5](https://spec.matrix.org/v1.5/client-server-api/#get_matrixclientv3roomsroomidcontexteventid)
- [v1.6](https://spec.matrix.org/v1.6/client-server-api/#get_matrixclientv3roomsroomidcontexteventid)

Earlier in these specs, the following rationale is described:

> [...] consider a returned timeline [M0, S1, M2], where M0 and M2 are both 
> messages sent by the same user, and S1 is a state event where that user 
> changes their displayname. If the state list represents the room state at the 
> end of the timeline, the client must take a copy of the state dictionary, and 
> rewind S1, in order to correctly calculate the display name for M0.


## Proposal

For the same reason that this behaviour was altered for the 
`GET /_matrix/client/v3/sync` endpoint, the endpoint 
`GET /_matrix/client/v3/rooms/{roomId}/context/{eventId}` should use the 
`state` field in its 200 response to return the room state at the **first** 
event returned.


## Potential issues

It was unclear whether this specification detail was overlooked. If that was 
the case, then implementations like Synapse might already support this MSC de 
facto.

If there was more confusion over this detail, then some developers might need 
to go back to alter their software to remain spec-compliant for older versions.


## Alternatives

Instead of accepting this as a proposal, it can instead be accepted as a 
clarification. This does rely on major implementations not following the spec 
de jure, as it might take time to re-implement the clarification.
