# MSC2247: Require users to have visibility on an event when submitting reports

The [report API](https://matrix.org/docs/spec/client_server/r0.5.0#post-matrix-client-r0-rooms-roomid-report-eventid)
currently does not require users to be joined to the room in order to report that an
event is inappropriate. This offers anyone the ability to report that any event is
inappropriate without being joined to the room. There is limited use for users to call report on
rooms they cannot presently see, so this endpoint should require users to be joined. 

Furthermore this proposal addresses the case where the user may not have visibility
on an event. In that case, similar logic applies as described below.

## Proposal

The `/rooms/{roomId}/report/{eventId}` endpoint should check to see if the authenticated user
is joined to the room in the current state of the room. If the user is not joined to the room OR
the room does not exist, the server should respond with:

```json
{
    "errcode": "M_FORBIDDEN",
    "error": "The room does not exist, or you are not joined to the room."
}
```

where the contents of `error` can be left to the implementation. It is key to note that this response
MUST be sent regardless if the room exists or not as this endpoint could be used as a way to brute
force room IDs in order to find a room.

If the user is joined to the room, but the event doesn't exist OR the user doesn't have permission to see
the event then the response should be:

```json
{
    "errcode": "M_FORBIDDEN",
    "error": "The event does not exist, or you do not have permission to see it."
}
```

Care should be taken to note that some homeservers may not have backfilled an event, while it may exist.
Implementations MAY fetch the event from another server when handling this request, although this
is not required.


## Tradeoffs

## Potential issues

## Security considerations

## Conclusion
