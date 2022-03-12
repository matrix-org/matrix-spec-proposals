# MSCXXXX: Removing Profile Information

In the Client-Server API specification, there is currently no clear way to remove the profile information, or to know
when it has been removed.

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
DELETE /_matrix/client/v1/profile/{userId}/avatar_url
DELETE /_matrix/client/v1/profile/{userId}/displayname
```

To identify the change, the `m.room.member` and `m.presence` events sent following the call to one of these two
endpoints MUST include the changed key with a `null` value. Subsequent `m.room.member` events SHOULD omit the deleted
key altogether.

To reflect those changes, omitting the `avatar_url` field in the body of the request to `PUT […]/avatar_url` or
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

The `m.room.member` event omits the changed key in `content`. This means that all the keys that are not unset should be
present every time a part of the profile is changed. This is limiting for custom keys as they might be omitted by
clients or servers that don't recognize them.

Another alternative, that is currently the behavior in some clients, is that the profile information cannot be unset
once it has been set.

## Security considerations

None that I can think of.

## Unstable prefix

When implementing this proposal, clients and servers should use the `org.matrix.mscXXXX` unstable prefix;

```http
DELETE /_matrix/client/unstable/org.matrix.mscXXXX/profile/{userId}/avatar_url
DELETE /_matrix/client/unstable/org.matrix.mscXXXX/profile/{userId}/displayname
```
