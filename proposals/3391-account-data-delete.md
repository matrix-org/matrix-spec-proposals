# MSC3391: Deleting account data

Currently, in Matrix, there is no semantic way to "remove" or "delete" account data. There is only a
method to create and update it, them being effectively the same operation, but no method to "remove"
it.

This violates the CRUD principle, and disallows "cleaning up" account data, or de-reference certain
keys used for certain actions, as then they will stay around forever.

## Proposal

This proposal aims to:
- Define "`{}`" account data content as effectively "deleted", alongside out-of-band deletion semantics.
- Allow `DELETE` HTTP methods on account data endpoints to perform the deletion.

The first, defining `{}` as "deleted", is to codify this defacto "nullification" into the spec as
expected behavior for deletion. This paves the way for better client interpretation of that data,
and would allow backwards compatibility when clients do `PUT` `{}` as account data. (More on this in
the dedicated section)

### Endpoints

Account data and room data currently have the following endpoints:

Global Account Data,
[`GET`](https://spec.matrix.org/v1.4/client-server-api/#get_matrixclientv3useruseridaccount_datatype)
and
[`PUT`](https://spec.matrix.org/v1.4/client-server-api/#put_matrixclientv3useruseridaccount_datatype):
```
GET /_matrix/client/v3/user/{userId}/account_data/{type}

PUT /_matrix/client/v3/user/{userId}/account_data/{type}
```

And Room-specific Account Data,
[`GET`](https://spec.matrix.org/v1.4/client-server-api/#get_matrixclientv3useruseridroomsroomidaccount_datatype)
and
[`PUT`](https://spec.matrix.org/v1.4/client-server-api/#put_matrixclientv3useruseridroomsroomidaccount_datatype):
```
GET /_matrix/client/v3/user/{userId}/rooms/{roomId}/account_data/{type}

PUT /_matrix/client/v3/user/{userId}/rooms/{roomId}/account_data/{type}
```

This proposal aims to add the following two endpoints (with no request body):
```
DELETE /_matrix/client/v3/user/{userId}/account_data/{type}

DELETE /_matrix/client/v3/user/{userId}/rooms/{roomId}/account_data/{type}
```

These, respectively, remove account-wide account data, and room-scoped account data.

#### Deleted account data responses

Furthermore, when a client deletes account data, it must expect `/account_data/` to return a 404 on
the next request.

#### Backwards Compatibility

For backwards compatibility reasons, if a client `PUT`s `{}` for account data, that must be seen
equivalent as `DELETE`-ing that account data.

### Sync

Account Data changes are announced through sync, this proposal also aims to change this response slightly after account data deletion.

In `account_data.events` and `rooms.join.{room_id}.account_data.events`, a client must interpret
`{}` for an event content as it being deleted.

This must happen only on syncs with a `since` token.

## Security considerations

No considerable security problems, other than the fact that a user can potentially delete important data.

## Unstable prefix

When implementing this proposal, servers should use the `org.matrix.msc3391` unstable prefix:

```
DELETE /_matrix/client/unstable/org.matrix.msc3391/user/{userId}/account_data/{type}

DELETE /_matrix/client/unstable/org.matrix.msc3391/user/{userId}/rooms/{roomId}/account_data/{type}
```

The `unstable_features` key for this MSC is `org.matrix.msc3391`.
