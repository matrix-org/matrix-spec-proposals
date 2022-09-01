# MSC3720: Account status endpoint

Matrix clients sometimes need a way to display additional information about a
user. For example, when interacting with a Matrix user, it might be useful for
clients to show whether this user's account has been deactivated, or even exists
at all.

Currently clients are forced to resort to hacks to try to derive this
information. Some, for example, check whether a user has a profile (display
name, avatar) set when trying to send an invite, which means that if a user
doesn't have any profile information (which is valid under the Matrix
specification), the inviter might be warned that the user might not exist.

## Proposal

Two new endpoints are added to the specification, one to the client-server API
and one to the server-server API.

### `POST /_matrix/client/v1/account_status`

This endpoint requires authentication via an access token.

The body of this endpoint includes a `user_ids` field which is an array listing
all of the users account(s) to look up the status of:

```json
{
    "user_ids": [
        "@user1:example.com",
        "@user2:example.com",
        "@user3:example.com",
        "@user4:otherexample.com"
    ]
}
```

If no error arises, the endpoint responds with a body using the following
format:

```json
{
    "account_statuses": {
        "@user1:example.com": {
            "exists": true,
            "deactivated": false
        },
        "@user2:example.com": {
            "exists": false
        },
    },
    "failures": [
        "@user3:example.com",
        "@user4:otherexample.com"
    ]
}
```

The `account_statuses` object in the response lists all statuses that could
successfully be retrieved. Each key in this object maps to one of the user IDs
listed in the request. For each account:

* `exists` is a boolean that indicates whether an account exists with this user
  ID.
* `deactivated` is a boolean that indicates whether the account has been
  deactivated. Omitted if `exists` is `false`.

The `failures` object in the response lists all user IDs for which no status
could be retrieved for any reason (e.g. federation issues, missing federation
endpoint, missing user in the remote server's response, etc).

The combination of the lists of user IDs from `user_statuses` and `failures`
must match the full list of user IDs provided in the request.

If one or more account(s) is not local to the homeserver this request is
performed on, the homeserver must attempt to retrieve account status using the
federation endpoint described below.

Below is how this endpoint behaves in case of errors:

* If no `user_ids` field is provided, the endpoint responds with a 400 status
  code and a `M_MISSING_PARAM` error code.
* If one or more of the user ID(s) provided cannot be parsed as a valid Matrix
  user ID, the endpoint responds with a 400 status code and a `M_INVALID_PARAM`
  error code.

If the `user_ids` field is an empty list, the server responds with a `200 OK`
status and an empty body (`{}`).

### `POST /_matrix/federation/v1/account_status`

This endpoint behaves in an identical way to the client-side endpoint described
above, with the additional following error case:

* If one or more of the user ID(s) provided does not match an account that
  belongs to the homeserver receiving the request, the endpoint responds with a
  400 status code and a `M_INVALID_PARAM` error code.

### `m.account_status` capability

Some server administrators might not want to disclose too much information about
their users. To support this use case, homeservers must expose a
`m.account_status` capability to tell clients whether they support retrieving
account status via the client-side endpoint described above.

## Alternatives

A previous version of this proposal used `GET` requests instead of `POST`.
However, while `GET` is semantically more correct here, the methods have been
changed to `POST` so user IDs don't leak into reverse proxy logs.

## Security considerations

### Allowing servers to refuse to share account statuses

Should a server administrator not want to disclose information about their users
through the federation endpoint described above, they should use a reverse proxy
or similar tool to prevent access to the endpoint. On top of this, homeserver
implementations may implement measures to respond with a 403 status code and a
`M_FORBIDDEN` error code in this case.

### Overwriting the statuses of another server's account

When processing the response from a request to the federation endpoint described
in this proposal, homeservers implementations must verify that every account the
remote homeserver has provided a status for belongs to the remote homeserver.
For any account for which this isn't the case, the status provided by the remote
homeserver must be ignored. This is to prevent mischievous homeservers from
trying to overwrite the status of accounts that don't belong to them.

## Unstable prefixes

Until this proposal is stabilised in a new version of the Matrix specification,
implementations should use the following paths for the endpoints described in
this document:

| Stable path                             | Unstable path                                                    |
|-----------------------------------------|------------------------------------------------------------------|
| `/_matrix/client/v1/account_status`     | `/_matrix/client/unstable/org.matrix.msc3720/account_status`     |
| `/_matrix/federation/v1/account_status` | `/_matrix/federation/unstable/org.matrix.msc3720/account_status` |

Additionally, implementations should use the unstable identifier
`org.matrix.msc3720.account_status` instead of `m.account_status` for the
client-side capability.
