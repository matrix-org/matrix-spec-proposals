# MSC3391: Deleting account data

## Proposal

### Endpoints

Account data and room data currently have the following endpoints;

```
GET /_matrix/client/r0/user/{userId}/account_data/{type}

PUT /_matrix/client/r0/user/{userId}/account_data/{type}

GET /_matrix/client/r0/user/{userId}/rooms/{roomId}/account_data/{type}

PUT /_matrix/client/r0/user/{userId}/rooms/{roomId}/account_data/{type}
```

This proposal aims to add the following two endpoints (with no body);

```
DELETE /_matrix/client/r0/user/{userId}/account_data/{type}

DELETE /_matrix/client/r0/user/{userId}/rooms/{roomId}/account_data/{type}
```

These, respectively, removes account-wide account data, and room-scoped account data.

### Sync

Account Data changes are announced through sync, this proposal also aims to add the following to sync;

```json5

{
  // ...
  "account_data_removed": ["m.direct", "m.push_rules"], // <- NEW
  // ...
  "rooms": {
    "join": {
      "!this-is-a-room:example.com": {
        // ...
        "account_data_removed": ["m.tag", "m.fully_read"], // <- NEW
        // ...
      }
    }
  },
  // ...
}

```

Providing an optional `account_data_removed` key, containing an array which references the deleted account-data types.

Which are the tags that were removed since `since` and `next_batch`, if `since` is specified and valid.

If between `since` and `next_batch` the account data has been deleted and re-created, this field shouldn't exist,
and data should be just put in `account_data` as if it's a normal change/creation.

If, for some reason, an event type exists in both `account_data_removed` and `account_data`, the reference in
`account_data_removed` must be ignored.

Full-state syncs must not include `account_data_removed`, but consequently clients must see anything
in `account_data` as replacing what existed previously.

## Potential issues

Desync is possible, and so if there's a situation where the client has a different view on account
data than the server, it should query the account data wherever possible.

## Security considerations

No considerable security problems, other than the fact that a user can potentially delete important data.

Though, for the purposes of this proposal, that is seen as a proper feature of CRUD :)

## Unstable prefix

When implementing this proposal, servers should use the `org.matrix.msc3391` unstable prefix;

```
DELETE /_matrix/client/unstable/org.matrix.msc3391/user/{userId}/account_data/{type}

DELETE /_matrix/client/unstable/org.matrix.msc3391/user/{userId}/rooms/{roomId}/account_data/{type}
```

And `org.matrix.msc3391.account_data_removed` for sync.

**Note:** As this operation would be largely "unknown" to clients,
cache invalidation problems could occur as clients could aggressively cache account data.