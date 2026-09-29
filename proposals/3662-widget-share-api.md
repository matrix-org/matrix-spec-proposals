# MSC3662: Allow Widgets to share user MxIds to the client

[Widgets](https://github.com/matrix-org/matrix-doc/pull/2764) offer the ability to expand
the functionality of clients by calling widget APIs to invoke actions on the client.

This proposal aims to allow widgets to share the details of users to the client with the
intention that the client can then open a dialogue to create a new room or invite a user.
This is useful for bridge situations where the bridge would like to offer a widget for
searching for users across the remote network, which can then invoke invites or room creation
on the remote side.

For navigating to rooms/events, this is somewhat covered by [MSC2931](https://github.com/matrix-org/matrix-doc/pull/2931/files). While that
MSC covers navigating to matrix.to, it does not convey the intended action.

## Proposal

To send the information to the client, widgets would use a new `fromWidget` request with
action `mxid_share` which takes the following shape:

```json5
{
  "api": "fromWidget",
  "widgetId": "20200827_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "mxid_share",
  "data": {
    "users": [
      {
        "user_id": "@alice:example.com",
        "display_name": "Alice",
        "avatar_url": "mxc://foo/bar"
      }
    ],
    "action_hint": "invite", // One of invite, create_room
  }
}
```

The `users` field must contain a set valid Matrix users. The `display_name` and `avatar_url` fields
are optional decoration, which may be used if the requested user does not exist yet (as can be the case with bridges).
The client SHOULD attempt to do it's own lookup of the `user_id`'s profile first and only fall back to the included
profile if the lookup fails.

If any of the provided `user_id` values are invalid, or if the `users` array is empty then the client MUST ignore
the request.

The `action_hint` field is optional, and describes to the client the intention of the user.

- When the `action_hint` is `invite`, the client should prefer to show an invite interface prepopulated with
the user's details.
- When the `action_hint` is `create_room`, the client should create a DM with the included users.
- Otherwise, it is left up to the implementation to decide how to handle the shared information.


Since the API proposed here doesn't *mutate* the client in any way, this proposal require a capability to
be negotiated. Information passed from the widget to the client should NEVER be used without the client
consenting to the action (e.g. never autocreate a DM room with a user without prompting)

## Potential issues

TODO: Issues?

## Alternatives

TODO: Alternatives?

## Security considerations

This proposal allows the widget to choose displaynames and avatars for users it provides
to the client, which could be used maliciously to hide the identity of a user in the interface.
It's imperative that the client first tries to determine if a profile already exists, and failing that
the userID of the shared user(s) should be presented so the user of the client can make their
own assessment. 


## Unstable prefix

While this MSC is not in a released version of the specification, clients should use 
`uk.half-shot.mscXXXX.mxid_share` as the `action` type.

