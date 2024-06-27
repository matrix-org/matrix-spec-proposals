# MSC4039: Access the Content repository with the Widget API

[MSC2762](https://github.com/matrix-org/matrix-spec-proposals/pull/2762) specifies a Widget API that
is able to receive events from and write events to the room that is loaded in the client. But beside
the room events, homeservers also manage media content for the users. While widgets can already
download media, given they acquired the URL of the homeserver, they can't upload new media into the
room. This would be useful to post images or attachments, but also to upload larger files that can't
be stored in a room event, like a whiteboard that can easily grow larger than 64kb.

This proposal aims to bring the functionality of uploading media to the content repository into the
widget specification. It should provide the same features that the
[“Upload Content” endpoint](https://spec.matrix.org/v1.7/client-server-api/#post_matrixmediav3upload)
of the Client-Server API provides. 

## Proposal

The widget API is extended with a new url parameter that can be requested and that will tell the
widget the URL of the homeserver API the user is currently using:

* `matrix_base_url`: The URL of the homeserver API.

The widget API is extended with two new interfaces to upload files into the content repository. The
user must manually approve the following capability before the actions can be used:

- `m.upload_file`: Let the widget upload files.

### Get configuration

To trigger the action to get the configuration, widgets will use a new `fromWidget` request with the
action `get_media_config` which takes the following shape:

```json
{
  "api": "fromWidget",
  "widgetId": "20200827_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "get_media_config",
  "data": {}
}
```

If the widget did not get approved for the capability required to send the event, the client MUST
send an error response (as required currently by the capabilities system for widgets).

If the event is successfully sent by the client, the client sends the following response:

```json
{
  "api": "fromWidget",
  "widgetId": "20200827_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "get_media_config",
  "data": {},
  "response": {
    "m.upload.size": 1000,
  }
}
```

The `response` is a mirrored representation of the original `/_matrix/media/v3/config` API.

### Upload file

To trigger the action to upload a file, widgets will use a new `fromWidget` request with the action
`upload_file` which takes the following shape:

```json
{
  "api": "fromWidget",
  "widgetId": "20200827_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "upload_file",
  "data": {
    "file": "some-content"
  }
}
```

`data.file` is a `XMLHttpRequestBodyInit` that is supported as a data type in the `postMessage` API.

If the widget did not get approved for the capability required to send the event, the client MUST
send an error response (as required currently by the capabilities system for widgets).

The client SHOULD NOT modify the data of the request.

If the event is successfully sent by the client, the client sends the following response:

```json
{
  "api": "fromWidget",
  "widgetId": "20200827_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "upload_file",
  "data": {
    "file": "some-content"
  },
  "response": {
    "content_uri": "mxc://..."
  }
}
```

## Potential issues

[MSC3916](https://github.com/matrix-org/matrix-spec-proposals/pull/3916) plans to add authentication
for media access. This would require the Widget API to receive an additional extension to be able to
access stored media. It is assumed that a successor of the current widget api
(like https://github.com/matrix-org/matrix-spec-proposals/pull/3008) will replace this need in the
future.

[MSC2246](https://github.com/matrix-org/matrix-spec-proposals/pull/2246) splits the interface of the
media upload into a “create the mxc-id” and a “upload the file for the mxc-id” stage. It is assumed
that the new API can be transparently implemented in the client so the widget could still use the old
API definition.

## Alternatives

It would be preferable if the widget would not need to pass the actual data to the client over the
Widget API, but if it could acquire an authenticated upload URL that it can use to upload the file
directly to the homeserver without the need of an authentication token. 
[MSC2246](https://github.com/matrix-org/matrix-spec-proposals/pull/2246) goes into this direction,
however, it still requires that the upload is authenticated.

## Security considerations

The same considerations as in [MSC2762](https://github.com/matrix-org/matrix-spec-proposals/pull/2762)
apply. This feature will allow the widget to be able to upload data into the media repository. This
could potentially be used to upload malicious content. However, the access will only be possible
when the user accepts the capability and grant access if the widget is trusted by the user.

## Unstable prefix

While this MSC is not present in the spec, clients and widgets should:

- Use `org.matrix.msc4039.` in place of `m.` in all new identifiers of this MSC.
- Use `org.matrix.msc4039.matrix_base_url` in place of `matrix_base_url` for the url parameter.
- Use `org.matrix.msc4039.get_media_config` in place of `get_media_config` for the action type in the
  `fromWidget` requests.
- Use `org.matrix.msc4039.upload_file` in place of `upload_file` for the action type in the
  `fromWidget` requests.
- Only call/support the `action`s if an API version of `org.matrix.msc4039` is advertised.
