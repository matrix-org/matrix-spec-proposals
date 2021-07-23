# MSC3291: Muting in VoIP calls

During VoIP calls, it is common for a user to mute their microphone/camera.
Ideally, the other side should be able to see that the opponent's camera is
muted, so that it could reflect this in the UI (e.g. show the user's avatar
instead of their camera feed). We would also want the changes in the mutes state
to be quick.

Using pure WebRTC there are two ways to do muting and both have their issues:

+ Disabling the corresponding track - there will be no way to know the track is
  muted from the opponent's perspective. On the other hand, this is almost
  instantaneous.
+ Setting the corresponding track as `recvonly`/`inactive` - this is problematic
  since it leads to re-negotiation which takes time. This could also conflict
  with holding (as defined in
  [MSC2746](https://github.com/matrix-org/matrix-doc/pull/2746)).

## Proposal

This MSC proposes a solution to this by extending the `SDPStreamMetadata` (see
[MSC3077](https://github.com/matrix-org/matrix-doc/pull/3077)) by the following
fields:

+ `audio_muted` - a boolean indicating the current audio mute state
+ `video_muted` - a boolean indicating the current video mute state

This MSC also adds a new call event `m.call.sdp_stream_metadata_changed`, which
has the common VoIP fields as specified in
[MSC2746](https://github.com/matrix-org/matrix-doc/pull/2746) (`version`,
`call_id`, `party_id`) and a `sdp_stream_metadata` object which is the same
thing as `sdp_stream_metadata`  in `m.call.negotiate`, `m.call.invite` and
`m.call.answer`. The client sends this event the when `sdp_stream_metadata` has
changed but no negotiation is required (e.g. the user mutes their
camera/microphone).

If a client sends an event with some of the fields missing the previous state
should be assumed. If there is no previous state all tracks should be assumed as
*not* muted. If a track is missing from a stream that track should be considered
muted.

### Example

```JSON
{
    "type": "m.call.sdp_stream_metadata_changed",
    "room_id": "!roomId",
    "content": {
        "call_id": "1414213562373095",
        "party_id": "1732050807568877",
        "sdp_stream_metadata": {
            "2311546231": {
                "purpose": "m.usermedia",
                "audio_muted:": false,
                "video_muted": true,
            }
        },
        "version": "1",
    },
}
```

## Potential issues

When the user mutes their camera, the client will meaningless which will waste
bandwidth.


## Security considerations

None that I can think of.

## Unstable prefix

|Release                             |Development                                           |
|------------------------------------|------------------------------------------------------|
|`m.call.sdp_stream_metadata_changed`|`org.matrix.msc3291.call.sdp_stream_metadata_changed` |
