# MSC4006: Answered Elsewhere for VoIP

Usually, it is self-evident when a VoIP call in Matrix has been answered by a different client:
the answer event from a different party ID is present in the room. However, bridges can complicate
this. If one client is SIP bridge, for example, the SIP server will just send a CANCEL on any call
forks that are not answered, adding a cause of 200 with text, "Call completed elsewhere"
(https://www.rfc-editor.org/rfc/rfc3326). This cause code will currently be ignored by the bridge as
there is no equivalent to translate it to, so the call will show as a missed call.

## Proposal

Add another value for the `reason` field in an `m.call.hangup` event of `answered_elsewhere`.

```
{
  "type": "m.call.hangup",
  "content": {
    "call_id": "1234567",
    "party_id": "AAAAAAA",
    "version": "1",
    "reason": "answered_elsewhere"
  },
}
```

## Potential issues

This would make the VoIP spec marginally more complex for all clients, when a large majority of users
are probably unlikely to interact with such a bridge, let alone complete a call elsewhere. However,
if clients choose to ignore this reason code, the failure mode will simply be that the call shows as
a missed call (as it does currently).

## Alternatives

This could potentially be done without extra spec if the bridge were to create a fake answer event.
However, in SIP, the bridge would get no further information about the call, so wouldn't know when it
ended, meaning that it would have to send a fake hangup straight afterwards, so the call would appear
as zero duration.

A previous version of this proposal suggested, `completed_elsewhere` to match SIP (and not imply that
the call was necessarily answered). However, there is prior art in the js-sdk implementing `answered_elsewhere`.


## Security considerations

None forseen.

## Unstable prefix

Until merged, the reason code shall be, `org.matrix.msc4006.completed_elsewhere`.

