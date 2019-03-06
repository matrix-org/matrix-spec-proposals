# MSC 1915 - Add unbind 3PID APIs

Note that this is a simplified version of MSC1194.


## Motivation

Currently we do not have a reasonable route for a user to unbind/remove a 3PID
from their account, particularly when deactivating their account. Users have an
expectation to be able to do this, and thus we should have an API to provide it.

This is meant as a simple extension to the current APIs, and so this explicitly
does not try and solve any existing usability concerns.


## New APIs

### Client-Server API

Add `POST /_matrix/client/r0/account/3pid/delete` API, which expects a JSON body
with `medium`, `address` and `id_server` fields (as per existing APIs).

The `id_server` parameter is optional and if missing the server will attempt to
unbind from a suitable identity server (e.g. its default identity server or the
server used when originally binding the 3pid).

The 200 response is a JSON object with an `id_server_unbind_result` field whose
value is either `success` or `no-support`, where the latter indicates that the
identity server (IS) does not support unbinding 3PIDs directly.

Example:

```
POST /_matrix/client/r0/account/3pid/delete HTTP/1.1

{
    "medium": "email",
    "address": "foobar@example.com",
    "id_server": "https://matrix.org
}

HTTP/1.1 200 OK
{
    "id_server_unbind_result": "success"
}
```


### Identity Server API

Add `POST /_matrix/identity/api/v1/unbind` with `mxid` and `threepid` fields.
The `mxid` is the user's `user_id` and `threepid` is a dict with the usual
`medium` and `address` fields.

If the server returns a 400, 404 or 501 HTTP error code then the homeserver
should assume that the identity server doesn't support the `/unbind` API, unless
it returns a specific matrix error response (i.e. the body is a JSON object with
`error` and `errcode` fields).

The identity server should accept any request to unbind a 3PID for a `user_id` from
the homeserver controlling that user ID.

Example:

```
POST /_matrix/identity/api/v1/unbind HTTP/1.1

{
    "mxid": "@foobar:example.com",
    "threepid": {
        "medium": "email",
        "address": "foobar@example.com"
    }
}

HTTP/1.1 200 OK

{}
```

# Trade-offs

A homeserver can unbind any 3PID associated with one of its users, and
specifically does not require a re-validation of control of the 3PID. This means
that users have to trust that their homeserver will not arbitrarily remove valid
3PIDs, however users must already trust their homeserver to a large extent. The
flip side is that this provides a mechanism for homeservers and users to remove
3PIDs directed at their user IDs that they no longer (or never did) have control
over.

Removing a 3PID does not require user interactive auth (UIA), which opens a
potential attack whereby a logged in device can remove all associated 3PIDs and
then log out all devices. If the user has forgotten their password they would no
longer be able to reset their password via a 3PID (e.g. email), resulting in
losing access to their account. However, given that clients and servers have
implemented these APIs in the wild this is considered a sufficient edge case
that adding UIA is unlikely to be worthwhile.
