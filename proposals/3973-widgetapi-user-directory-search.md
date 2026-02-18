# MSC3973: Search users in the user directory with the Widget API

[MSC2762](https://github.com/matrix-org/matrix-spec-proposals/pull/2762) specifies a Widget API that
is able to receive events from and write events to the room that is loaded in the client. This includes
the support to invite users into a room by creating membership events. However, in order for this to
work properly, the widgets needs to be able to discover users from the user directory of the server.
That allows them to show the user a custom UI which might be useful in different applications such
as a meeting planner.

This proposal aims to bring the functionality of searching in the user directory into the widget
specification. It should provide the same features that the
[“User Directory search” endpoint](https://spec.matrix.org/v1.6/client-server-api/#post_matrixclientv3user_directorysearch)
of the Client-Server API provides. It should further provide the same results as the invite dialog of
the hosting client (e.g. Element) so the same search terms lead to the same results in all components.

## Proposal

The widget API is extended with a new interface to search users in the user directory. The user must
manually approve the following capability before the action can be used:

- `m.user_directory_search`: Let the widget access the user directory.

To trigger the action, widgets will use a new `fromWidget` request with the action
`user_directory_search` which takes the following shape:

```json
{
  "api": "fromWidget",
  "widgetId": "20200827_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "user_directory_search",
  "data": {
    "search_term": "foo",
    "limit": 10
  }
}
```

Under `data`, all keys are a mirrored representation of the original `/_matrix/client/v3/user_directory/search`
API. The `limit` field is optional and defaults to whatever the homeserver implementation uses.

If the widget did not get approved for the capability required to send the event, the client MUST
send an error response (as required currently by the capabilities system for widgets).

The client SHOULD NOT modify the data of the request.

If the event is successfully sent by the client, the client sends the following response:

```json
{
  "api": "fromWidget",
  "widgetId": "20200827_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "user_directory_search",
  "data": {
    "search_term": "foo",
    "limit": 10
  },
  "response": {
    "limited": false,
    "results": [
      {
        "avatar_url": "mxc://bar.com/foo",
        "display_name": "Foo",
        "user_id": "@foo:bar.com"
      }
    ]
  }
}
```

The `limited` and `results` fields of the `response` are required and are a mirrored representation
of the original `/_matrix/client/v3/user_directory/search` API.

## Security considerations

The same considerations as in [MSC2762](https://github.com/matrix-org/matrix-spec-proposals/pull/2762)
apply. This feature will allow the widget to be able to receive information about who is present on
the homeserver / in the user directory. This information could be used by the widget to send it to
a third-party server to store or misuse it. However, the access will only be possible when the user
accepts the capability and grant access if the widget is trusted by the user.

## Unstable prefix

While this MSC is not present in the spec, clients and widgets should:

- Use `org.matrix.msc3973.` in place of `m.` in all new identifiers of this MSC.
- Use `org.matrix.msc3973.user_directory_search` in place of `user_directory_search` for the action type in the
  `fromWidget` requests.
- Only call/support the `action`s if an API version of `org.matrix.msc3973` is advertised.
