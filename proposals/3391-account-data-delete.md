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

This proposal aims to add the following two endpoints;

```
DELETE /_matrix/client/r0/user/{userId}/account_data/{type}

DELETE /_matrix/client/r0/user/{userId}/rooms/{roomId}/account_data/{type}
```

With no body.

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

Which are the tags that were removed since `since` and `next_batch`, if `since` is specified and valid.


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