# MSC3077: Support for multi-stream VoIP

This MSC proposes a method for differentiating WebRTC streams from each other.

[MSC2746](https://github.com/matrix-org/matrix-doc/pull/2746) has improved VoIP
immeasurably. Yet, there is still no clear way to handle things such as
screen-sharing.

Simple VoIP calls only ever feature one stream, though often clients will want
to send multiple - usermedia, screensharing and possibly more. In a situation
with more streams, it can be very helpful to provide the other side with
metadata about the content of the streams.

## Proposal

This MSC proposes adding an `sdp_stream_metadata` field to the events containing
a session description i.e.:

+ [`m.call.invite`](https://spec.matrix.org/v1.7/client-server-api/#mcallinvite)
+ [`m.call.answer`](https://spec.matrix.org/v1.7/client-server-api/#mcallanswer)
+ [`m.call.negotiate`](https://spec.matrix.org/v1.7/client-server-api/#mcallnegotiate)

The `sdp_stream_metadata` field is an object in which each key is one stream
`id` in the session description. The values are objects with the
following fields:

+ `purpose` - a string indicating the purpose of the stream. For compatibility
  between client the following values are defined:
  + `m.usermedia` - stream that contains the webcam and/or microphone tracks
  + `m.screenshare` - stream with the screen-sharing tracks

### Example

```JSON
{
    "type": "m.call.invite",
    "room_id": "!roomId",
    "content": {
        "call_id": "1414213562373095",
        "invitee": "@bob:matrix.org",
        "party_id": "1732050807568877",
        "lifetime": "60000",
        "capabilities": {
            "m.call.transferee": true,
        },
        "offer": {
            "sdp": "...",
            "type": "offer",
        },
        "sdp_stream_metadata": {
            "271828182845": {
                "purpose": "m.screenshare",
            },
            "314159265358": {
                "purpose": "m.usermedia",
            },
        },
        "version": "1",
    },
}
```

### Edge cases

+ If an incoming stream is not described in `sdp_stream_metadata` and
  `sdp_stream_metadata` is present, the stream should be ignored.
+ If a stream has a `purpose` of an unknown type (i.e. not `m.usermedia` or
  `m.screenshare`), it should be ignored.

### Backwards compatibility

During the initial invite and answer exchange clients find out if the field
`sdp_stream_metadata` is missing. If it is not present in the event sent by the
opponent, the client should ignore any new incoming streams (i.e. it should use
the first one) and it shouldn't send more than one stream (i.e. clients cannot send a video feed and a screenshare at the same time, as is the case in current clients).

## Alternatives

Setting the stream `id`s to custom values had been considered. Though this is
possible on some platforms, it is not in browsers. That is because the `id`
property of `MediaStream` is _read-only_ as the [MDN Documentation
states](https://developer.mozilla.org/en-US/docs/Web/API/MediaStream/id).
Similar is true for SDP attributes.

This proposal is also more practical for cases where more complex metadata is
needed. For conferencing, a `user_id` field could be added to
the objects in `sdp_stream_metadata`; for differentiating between the front and rear camera of a
phone, a `camera_type` field could be added.

Previously, it has been thought that the `purpose` field has to be unique (or
another unique field has to be added), though this could only ever be important
if we wanted to replace a stream with another one in-place. It was deemed as a
rather uncommon thing for which there doesn't seem to be any use-case, so
uniqueness is not required.

## Unstable prefix

During development, the following fields should be used:

|Release                     |Development                                    |
|----------------------------|-----------------------------------------------|
|`sdp_stream_metadata`       |`org.matrix.msc3077.sdp_stream_metadata`       |
|`m.call.sdp_stream_metadata`|`org.matrix.msc3077.call.sdp_stream_metadata`  |

## Potential issues

None that I can think of.

## Security considerations

None that I can think of.
