# MSC3391: Deleting account data

## Proposal

### Endpoints

Account data and room data currently have the following endpoints;

```
GET /_matrix/client/v3/user/{userId}/account_data/{type}

PUT /_matrix/client/v3/user/{userId}/account_data/{type}

GET /_matrix/client/v3/user/{userId}/rooms/{roomId}/account_data/{type}

PUT /_matrix/client/v3/user/{userId}/rooms/{roomId}/account_data/{type}
```

This proposal aims to add the following two endpoints (with no body);

```
DELETE /_matrix/client/v3/user/{userId}/account_data/{type}

DELETE /_matrix/client/v3/user/{userId}/rooms/{roomId}/account_data/{type}
```

These, respectively, removes account-wide account data, and room-scoped account data.

### Sync

Account Data changes are announced through sync, this proposal also aims to add the following to sync;

```json5

{
  // ...
  "account_data": {
    "events": [
      {
        // ...
      }
    ],
    "removed_events": ["m.direct", "m.push_rules"] // <- NEW
  },
  // ...
  "rooms": {
    "join": {

      "!this-is-a-room:example.com": {
        // ...
        "account_data": {
          "events": [
            {
              // ...
            }
          ],
          "removed_events": ["m.tag", "m.fully_read"] // <- NEW
        }
        // ...
      },

    }
  },
  // ...
}

```

Providing an optional `removed_events` key per every `account_data` object, containing an array
which references the deleted account-data types.

These are the tags that were removed since `since` and `next_batch`, if `since` is specified and
valid.

If between `since` and `next_batch` the account data has been deleted and re-created, this field
shouldn't exist, and data should be just put in `account_data.events` as if it's a normal
change/creation.

If, for some reason, an event type exists in both `account_data.events` and
`account_data.removed_events`, the reference in `.removed_events` must be ignored.

Requests to `/sync` without a `since` token must not include `.removed_events`. Consequently,
anything present in `events` represents a full state of account data, and anything missing (from a
previous `since`-less sync) must be removed from the client's cache.

#### Backwards Compatibility Note

When a server announces it supports any version that does not include this MSC (via `/versions`), it
**must** include an empty (`{}`) `events` entry for deleted account data (per sync), together with
the entry in `removed_events`.

This is done for backwards compatibility reasons, as clients may or may not understand the
`removed_events` key when communicating with this server.

*This author believes that any matrix client will act responsibly when encountering a server
supporting only matrix versions it does not understand, and fail-fast if this is the case.*

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

And `org.matrix.msc3391.removed_events` for `account_data` sync.
