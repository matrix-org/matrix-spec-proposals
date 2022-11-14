# MSC1960: OpenID Connect information exchange for widgets

Widgets are currently left with no options to verify the user's ID, making it hard for
personalized and authenticated widgets to exist. The spec says the `$matrix_user_id`
template variable cannot be relied upon due to how easy it is to faslify, which is true.

This MSC aims to solve the problem with verifiably accurate OpenID Connect credentials.

As of writing, the best resource to learn more about the widgets spec is the following
spec PR: https://github.com/matrix-org/matrix-doc/pull/2764

## Proposal

Typically widgets which need to accurately verify the user's identity will also have a
backend service of some kind. This backend service likely already uses the integration
manager authentication APIs introduced by [MSC1961](https://github.com/matrix-org/matrix-doc/pull/1961).

Through using the same concepts from MSC1961, the widget can verify the user's identity
by requesting a fresh OpenID Connect credential object to pass along to its backend, like
the integration manager which might be running it.

The protocol sequence defined here is based upon the previous discussion in the Element Web
issue tracker: https://github.com/vector-im/element-web/issues/7153

It is proposed that after the capabilities negotiation, the widget can ask the client for
an OpenID Connect credential object so it can pass it along to its backend for validation.
The request SHOULD result in the user being prompted to confirm that the widget can have
their information. Because of this user interaction, it's not always possible for the user
to complete the approval within the 10 second suggested timeout by the widget spec. As
such, the initial request by the widget can have one of three states:

1. The client indicates that the user is being prompted (to be followed up on).
2. The client sends over credentials for the widget to verify.
3. The client indicates the request was blocked/denied.

The initial request from the widget looks as follows:

```json
{
    "api": "fromWidget",
    "action": "get_openid",
    "requestId": "AAABBB",
    "widgetId": "CCCDDD",
    "data": {}
}
```

Which then receives a response which has a `state` field alongside potentially the credentials
to be verified. Matching the order of possible responses above, here are examples:

```json
{
    "api": "fromWidget",
    "action": "get_openid",
    "requestId": "AAABBB",
    "widgetId": "CCCDDD",
    "data": {},
    "response": {
        "state": "request"
    }
}
```

```json
{
    "api": "fromWidget",
    "action": "get_openid",
    "requestId": "AAABBB",
    "widgetId": "CCCDDD",
    "data": {},
    "response": {
        "state": "allowed",
        "access_token": "s3cr3t",
        "token_type": "Bearer",
        "matrix_server_name": "example.org",
        "expires_in": 3600
    }
}
```

```json
{
    "api": "fromWidget",
    "action": "get_openid",
    "requestId": "AAABBB",
    "widgetId": "CCCDDD",
    "data": {},
    "response": {
        "state": "blocked"
    }
}
```

The credential information is directly copied from the `/_matrix/client/r0/user/:userId/openid/request_token`
response.

In the case of `state: "request"`, the user is being asked to approve the widget's attempt to
verify their identity. To ensure that future requests are quicker, clients are encouraged to
include a "remember this widget" option to make use of the immediate `state: "allowed"` or
`state: "blocked"` responses above.

There is no timeout associated with the user making their selection. Once a user does make
a selection (allow or deny the request), the client sends a `toWidget` request to indicate the
result, using a very similar structure to the above immediate responses:

```json
{
    "api": "toWidget",
    "action": "openid_credentials",
    "requestId": "EEEFFF",
    "widgetId": "CCCDDD",
    "data": {
        "state": "allowed",
        "original_request_id": "AAABBB",
        "access_token": "s3cr3t",
        "token_type": "Bearer",
        "matrix_server_name": "example.org",
        "expires_in": 3600
    }
}
```

```json
{
    "api": "toWidget",
    "action": "openid_credentials",
    "requestId": "EEEFFF",
    "widgetId": "CCCDDD",
    "data": {
        "state": "blocked",
        "original_request_id": "AAABBB"
    }
}
```

`original_request_id` is the `requestId` of the `get_openid` request which started the prompt,
for the widget's reference.

The widget acknowledges receipt of the credentials with an empty `response` object.

A typical sequence diagram for this flow is as follows:

```
+-------+                                    +---------+                                +---------+
| User  |                                    | Client  |                                | Widget  |
+-------+                                    +---------+                                +---------+
    |                                             |                                          |
    |                                             |                 Capabilities negotiation |
    |                                             |----------------------------------------->|
    |                                             |                                          |
    |                                             | Capabilities negotiation                 |
    |                                             |<-----------------------------------------|
    |                                             |                                          |
    |                                             |            fromWidget get_openid request |
    |                                             |<-----------------------------------------|
    |                                             |                                          |
    |                                             | ack with state "request"                 |
    |                                             |----------------------------------------->|
    |                                             |                                          |
    |      Ask if the widget can have information |                                          |
    |<--------------------------------------------|                                          |
    |                                             |                                          |
    | Approve                                     |                                          |
    |-------------------------------------------->|                                          |
    |                                             |                                          |
    |                                             | toWidget openid_credentials request      |
    |                                             |----------------------------------------->|
    |                                             |                                          |
    |                                             |     acknowledge request (empty response) |
    |                                             |<-----------------------------------------|
```

Prior to this proposal, widgets could use an undocumented `scalar_token` parameter if the client chose to
send it to the widget. Clients typically chose to send it if the widget's URL matched a whitelist for URLs
the client trusts. With the widget specification as written, widgets cannot rely on this behaviour.

Widgets may wish to look into cookies and other storage techniques to avoid continuously requesting
credentials. Widgets should also look into [MSC1961](https://github.com/matrix-org/matrix-doc/pull/1961)
for information on how to properly verify the OpenID Connect credentials it will be receiving. The
widget is ultimately responsible for how it deals with the credentials, though the author recommends
handing it off to an integration manager's `/register` endpoint to acquire a single token string
instead.

An implementation of this proposal's early draft is here: https://github.com/matrix-org/matrix-react-sdk/pull/2781

## Security considerations

The user is explicitly kept in the loop to avoid automatic and silent harvesting of private information.
Clients must ask the user for permission to send OpenID Connect information to a widget, but may optionally allow
the user to always allow/deny the widget access. Clients are encouraged to notify the user when future
requests are automatically handled due to the user's prior selection (eg: an unobtrusive popup saying
"hey, your sticker picker asked for your information. [Block future requests]").
