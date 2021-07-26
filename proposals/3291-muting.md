# MSC3291: Muting in VoIP calls

During VoIP calls, it is common for a user to mute their microphone/camera.
Ideally, the other side should be able to see that the opponent's camera is
muted, so that it could reflect this in the UI (e.g. show the user's avatar
instead of their camera feed). We would also want the changes in the mutes state
to be quick.

Using pure WebRTC there are two ways to do muting and both have their issues:

+ Disabling the corresponding track
+ Setting the corresponding track as `recvonly`/`inactive`

The Alternatives section describes the issues with using these alone.

## Proposal

This MSC proposes that clients disable muted tracks (as is almost instantaneous)
and extends the `SDPStreamMetadata` object (see
[MSC3077](https://github.com/matrix-org/matrix-doc/pull/3077)) to allow
indicating the mute state to the other side using the following fields:

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
    }
}
```

## Potential issues

When the user mutes their camera, the client will meaningless which will waste
bandwidth.

## Alternatives

### Only disabling the corresponding track

This is the solution that some clients (e.g. Element) use at the moment. While
this is almost instantaneous, it doesn't allow the other side to know the
opponent's mute state. This leads to the opponent showing a black screen for a
muted video track and not doing anything for a muted audio track which is bad
for UX.

### Setting the corresponding track as `recvonly`/`inactive`

While this would be beneficial for low bandwidth connections, it takes time. The
delay might be acceptable for video but isn't for audio (with which your would
assume an instantaneous mute state change). This is also problematic since there
could be a confusion with holding (as defined in
[MSC2746](https://github.com/matrix-org/matrix-doc/pull/2746)).

### Using a separate event for muting

While this might feel clearer initially, it doesn't have much real benefit. The
mute state is in fact a meta information about the stream and using
`sdp_stream_metadata` is also more flexible for cases where the user joins a
call already muted. It is also more flexible in general and would be useful if
we ever decided to do what is described in the next section.

### A combination of disabling tracks, `sdp_stream_metadata` and SDP

An option would be using the current method in combination with setting the
corresponding track as `recvonly`/`inactive`. Along with this clients would need
to set the mute state in `sdp_stream_metadata` to avoid conflicts with holding.
While this solution might be the most flexible solution as it would allow
clients to choose between bandwidth and a mute state change delay for each
track, it would be harder to implement and feels generally disjointed.

## Security considerations

None that I can think of.

## Unstable prefix

|Release                             |Development                                           |
|------------------------------------|------------------------------------------------------|
|`m.call.sdp_stream_metadata_changed`|`org.matrix.msc3291.call.sdp_stream_metadata_changed` |
