# MSC3754: Removing Profile Information

In the Client-Server API specification, there is currently no clear way to remove the profile information.

## Proposal

On top of the current profile endpoints:

```http
GET /_matrix/client/v3/profile/{userId}/avatar_url
GET /_matrix/client/v3/profile/{userId}/displayname
PUT /_matrix/client/v3/profile/{userId}/avatar_url
PUT /_matrix/client/v3/profile/{userId}/displayname
```

This proposal adds two new endpoints for deleting the data:

```http
DELETE /_matrix/client/v3/profile/{userId}/avatar_url
DELETE /_matrix/client/v3/profile/{userId}/displayname
```

To identify the change, the `m.room.member` and `m.presence` events sent following the call to one of these two
endpoints MUST remove the corresponding key.

To pair with the new endpoints, omitting the `avatar_url` field in the body of the request to `PUT […]/avatar_url` or
the `displayname` field in the body of the request to `PUT […]/displayname` is now deprecated. They can be marked as
required in a future MSC.

## Potential issues

Marking the fields in the body of the `PUT` endpoints requests as required would break compatibility for existing
clients so they are only deprecated for now. This means that the servers must accept two different ways of removing
profile data for the time being.

## Alternatives

Even if it is not documented, it is currently possible to remove profile account data. The general consensus is to send
`{ avatar_url: "" }` for `avatar_url` or `{}` for `displayname`. This means that a clarification in the spec would
either be inconsistent between the `PUT` endpoints or it whould require a change in the current implementations.

[MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133) introduces a way to add and delete custom
profile fields, and its `DELETE` endpoint would effectively replace this MSC.

Another alternative, that is currently the behavior in some clients, is that the profile information cannot be unset
once it has been set.

## Security considerations

None that I can think of.

## Unstable prefix

When implementing this proposal, clients and servers should use the `org.matrix.msc3754` unstable prefix;

```http
DELETE /_matrix/client/unstable/org.matrix.msc3754/profile/{userId}/avatar_url
DELETE /_matrix/client/unstable/org.matrix.msc3754/profile/{userId}/displayname
```
