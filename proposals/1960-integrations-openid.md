# MSC1960: OpenID Connect information exchange for widgets

With the various integrations API proposals, widgets are left with no options to verify the
requesting user's ID if they need it. Widgets like the sticker picker must know who is making
the request and as such need a way to get accurate information about who is contacting them.

This proposal introduces a way for widgets (room and account) to do so over the `fromWidget`
API proposed by [MSC1236](https://github.com/matrix-org/matrix-doc/issues/1236).


## Proposal

Room and account widgets may request new OpenID Connect credentials from the user so they can log in/register with
the backing integration manager or other application. This is largely based on the prior art available
[here (element-web#7153)](https://github.com/vector-im/element-web/issues/7153). The rationale for such an
API is so that widgets can load things like a user's sticker packs or other information without having
to rely on secret strings. For example, a room could be used to let a user create custom sticker packs
via a common widget - it would be nice if that widget could auth the user without asking them to enter
their username and password into an iframe.

Widgets can request OpenID Connect credentials from the user by sending a `fromWidget` action of `get_openid`
to initiate the token exchange process. The client responds with an acknowledgement of
`{"state":"request"}` (or `{"state":"blocked"}` if the client/user doesn't think the widget is safe).
The client then prompts the user if the widget should be allowed to get details about the user,
optionally providing a way for the user to always accept/deny the widget. If the user agrees, the
client sends a `toWidget` action of `openid_credentials` with `data` holding the raw OpenID Connect credentials
object returned from the homeserver, and a `success: true` parameter, similar to the following:
```
{
    "api": "toWidget",
    "requestId": "AABBCC",
    "action": "openid_credentials",
    "widgetId": "DDEEFF",
    "data": {
        "success": true,
        "access_token": "SecretTokenHere",
        "token_type": "Bearer",
        "matrix_server_name": "example.com",
        "expires_in": 3600
    }
}
```

For clarity, the `data` consists of properties as returned by `/_matrix/client/r0/user/:userId/openid/request_token`
plus the `success` parameter.

If the user denies the widget, just `success: false` is returned in the `data` property.

To lessen the number of requests, a client can also respond to the original `get_openid` request with a
`state` of `"allowed"`, `success: true`, and the OpenID Connect credentials object (just like in the `data` for
`openid_credentials`).

The widget should not request OpenID Connect credentials until after it has exchanged capabilities with the client,
however this is not required to wait for the capabiltiies exchange.

The widget acknowledges the `openid_credentials` request with an empty response object.

A successful sequence diagram for this flow is as follows:

```
+-------+                                    +---------+                                +---------+
| User  |                                    | Client  |                                | Widget  |
+-------+                                    +---------+                                +---------+
    |                                             |                                          |
    |                                             |                 Capabilities negotiation |
    |                                             |<-----------------------------------------|
    |                                             |                                          |
    |                                             | Capabilities negotiation                 |
    |                                             |----------------------------------------->|
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
the client trusts. Widgets are now not able to rely on this behaviour with this proposal, although clients
may wish to still support it until adoption is complete. Widgets may wish to look into cookies and other
storage techniques to avoid continously requesting credentials, regardless of how they got those credentials.

An implementation of this proposal is [here](https://github.com/matrix-org/matrix-react-sdk/pull/2781).

The widget is left responsible for dealing with the OpenID object it receives, likely handing it off to
the integration manager it is backed by to exchange it for a long-lived Bearer token.

## Security considerations

The user is explicitly kept in the loop to avoid automatic and silent harvesting of private information.
Clients must ask the user for permission to send OpenID Connect information to a widget, but may optionally allow
the user to always allow/deny the widget access. Clients are encouraged to notify the user when future
requests are automatically handled due to the user's prior selection (eg: an unobtrusive popup saying
"hey, your sticker picker asked for your information. [Block future requests]").
