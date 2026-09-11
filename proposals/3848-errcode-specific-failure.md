# MSC3848: Introduce errcodes for specific event sending failures.

When performing an action on the C-S API, sometimes requests will fail with
a generic `M_FORBIDDEN` error with implementations providing a more meaningful
context in the `error` field. While some client implementations have taken it
upon themselves to scan these error fields for probable causes, this isn't a
particularly safe or spec-complaint way to react to errors.

Some examples of failures which require more standardized error information
include already-joined errors when a user tries to invite another user to a room,
or being unable to send an event into a room due to lacking the required power level.

For this reason, this proposal suggests including new `errcode` definitions
which provide more specific information about the failure.

## Proposal

New `errcode` would be introduced into the error body of a response
(https://spec.matrix.org/v1.3/client-server-api/#standard-error-response). 

`M_ALREADY_JOINED` would be fired when a membership action fails when the authenticated user
is already joined to the room.

This would cover endpoints:
  - [POST /_matrix/client/v3/rooms/{roomId}/invite](https://spec.matrix.org/v1.3/client-server-api/#post_matrixclientv3roomsroomidinvite)
  - [POST /_matrix/client/v3/rooms/knock/{roomIdOrAlias}](https://spec.matrix.org/v1.3/client-server-api/#post_matrixclientv3knockroomidoralias)
  - [PUT  /_matrix/client/v3/rooms/{roomId}/state/{eventType}/{stateKey}](https://spec.matrix.org/v1.3/client-server-api/#put_matrixclientv3roomsroomidstateeventtypestatekey)

Note that it would not cover endpoints where trying to join a room when the
user is already joined would no-op, like `POST /_matrix/client/v3/join/{roomIdOrAlias}`.

`M_INSUFFICIENT_POWER` would be when the authenticated user does not have the required power level to
perform an action in the room.

`M_NOT_JOINED` would be when the authenticated user is not joined to a room, but attempts to perform
an action in it.

Both errcodes would cover endpoints:
  - [POST /_matrix/client/v3/rooms/{roomId}/invite](https://spec.matrix.org/v1.3/client-server-api/#post_matrixclientv3roomsroomidinvite)
  - [POST /_matrix/client/v3/rooms/knock/{roomIdOrAlias}](https://spec.matrix.org/v1.3/client-server-api/#post_matrixclientv3knockroomidoralias)
  - [POST /_matrix/client/v3/rooms/{roomId}/unban](https://spec.matrix.org/v1.3/client-server-api/#post_matrixclientv3roomsroomidban)
  - [POST /_matrix/client/v3/rooms/{roomId}/ban](https://spec.matrix.org/v1.3/client-server-api/#post_matrixclientv3roomsroomidban)
  - [POST /_matrix/client/v3/rooms/{roomId}/kick](https://spec.matrix.org/v1.3/client-server-api/#post_matrixclientv3roomsroomidkick)
  - [PUT /_matrix/client/v3/rooms/{roomId}/state/{eventType}/{stateKey}](https://spec.matrix.org/v1.3/client-server-api/#put_matrixclientv3roomsroomidstateeventtypestatekey)
  - [PUT /_matrix/client/v3/rooms/{roomId}/send/{eventType}/{txnId}](https://spec.matrix.org/v1.3/client-server-api/#put_matrixclientv3roomsroomidsendeventtypetxnid)


## Potential issues

Changing long-established error codes in Matrix will be fraught with risk, as many
clients will need updating to support the new error types. Failure to do so might lead
to unexpected behaviours or confusing error messages. For this reason, the unstable implementation
will continue to provide the old errcode in the body of the error while providing the
new proposed errcode under its own field. This gives clients a chance to adapt to the
new errcode / ensure their behaviours with unexpected errcodes are acceptable.

## Alternatives

We could introduce a second field to the error body for more specific errors, but this would likely make
error handling in clients much more complicated. There is precedence already in the spec for specific
error codes for specific failures, so there is little need to subclass.

## Security considerations

None.

## Unstable prefix

While this MSC is not considered stable for implementation, implementations should use `org.matrix.msc3848.unstable.errcode`
as a prefix to the fields on the error body. `M_FORBIDDEN` will still be emitted as a `errcode` while the
MSC is unstable, and will be replaced when the spec stabilizes.

The errcodes will be have the prefix `M_` replaced with `ORG.MATRIX.MSC3848.`.

## Dependencies

None.
