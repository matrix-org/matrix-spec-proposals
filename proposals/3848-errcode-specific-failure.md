# MSC3848: Introduce errcodes for specific membership change failures.

When performing an action on the C-S API, sometimes it will fail if the user is already joined to the room. In
these cases, homeservers will throw a `M_FORBIDDEN` stating that the action wasn't successful. However, it's difficult
to distinguish this kind of failure from insufficient permission errors (or other kinds of errors). This would be
useful, as the caller can then react to the error e.g. refresh it's membership cache if it tries to invite a user
that is already joined.

## Proposal

New `errcode` would be introduced into the error body of a response (https://spec.matrix.org/latest/client-server-api/#standard-error-response). 

`M_ALREADY_JOINED` would be fired when a membership action fails when the user is already joined to the room.
This would cover endpoints:
  - [POST /_matrix/client/v3/rooms/{roomId}/invite](https://spec.matrix.org/latest/client-server-api/#post_matrixclientv3roomsroomidinvite)
  - [POST /_matrix/client/v3/rooms/knock/{roomIdOrAlias}](https://spec.matrix.org/latest/client-server-api/#post_matrixclientv3knockroomidoralias)
  - [PUT  /_matrix/client/v3/rooms/{roomId}/state/{eventType}/{stateKey}](https://spec.matrix.org/latest/client-server-api/#put_matrixclientv3roomsroomidstateeventtypestatekey)
Note that it would not cover endpoints where trying to join a room when the user is already joined would no-op, like `POST /_matrix/client/v3/join/{roomIdOrAlias}`.

`M_INSUFFICENT_POWER` would be when your user does not have the specific required power level to
perform an action in the room.
  - [POST /_matrix/client/v3/rooms/{roomId}/invite](https://spec.matrix.org/latest/client-server-api/#post_matrixclientv3roomsroomidinvite)
  - [POST /_matrix/client/v3/rooms/knock/{roomIdOrAlias}](https://spec.matrix.org/latest/client-server-api/#post_matrixclientv3knockroomidoralias)
  - [POST /_matrix/client/v3/rooms/{roomId}/unban](https://spec.matrix.org/latest/client-server-api/#post_matrixclientv3roomsroomidban)
  - [POST /_matrix/client/v3/rooms/{roomId}/ban](https://spec.matrix.org/latest/client-server-api/#post_matrixclientv3roomsroomidban)
  - [POST /_matrix/client/v3/rooms/{roomId}/kick](https://spec.matrix.org/latest/client-server-api/#post_matrixclientv3roomsroomidkick)
  - [PUT  /_matrix/client/v3/rooms/{roomId}/state/{eventType}/{stateKey}](https://spec.matrix.org/latest/client-server-api/#put_matrixclientv3roomsroomidstateeventtypestatekey)


## Potential issues

Changing long-established error codes in Matrix will be fraught with risk, as many clients will need updating
to support the new error types. Failure to do so might lead to unexpected behaviours or confusing error messages.
However, the alternative is keeping the non-specific error codes and having the 

## Alternatives

We could introduce a second field to the error body for more specific errors, but this would likely make
error handling in clients much more complicated.

## Security considerations

None.

## Unstable prefix

While this MSC is not considered stable for implementation, implementations should use `org.matrix.unstable.errcode`
as a prefix to the fields on the error body. `M_FORBIDDEN` will still be emitted as a `errcode` while the
MSC is unstable, and will be replaced when the spec stabilizes.

## Dependencies

None.