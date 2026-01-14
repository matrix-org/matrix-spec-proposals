# MSC4398: Remove the depth field from PDUs

The depth field is useless ever since room v3 (possibly
v2?) and seems to only cause problems, especially on
Synapse servers due to Synapse using the depth field for
timeline ordering.

## Proposal

Remove the depth field from PDUs.

This change would result in a PDU now looking like this:

```json
{
  "auth_events": [
    "$urlsafe_base64_encoded_eventid",
    "$a-different-event-id"
  ],
  "content": {
    "key": "value"
  },
  "hashes": {
    "sha256": "thishashcoversallfieldsincasethisisredacted"
  },
  "origin_server_ts": 1404838188000,
  "prev_events": [
    "$urlsafe_base64_encoded_eventid",
    "$a-different-event-id"
  ],
  "room_id": "!Nhcu5BS-UMnFX7hBVfVSoXiD7OgH6iRT-xyIuqDnpYQ",
  "sender": "@alice:example.com",
  "signatures": {
    "example.com": {
      "ed25519:key_version": "these86bytesofbase64signaturecoveressentialfieldsincludinghashessocancheckredactedpdus"
    }
  },
  "type": "m.room.message",
  "unsigned": {
    "age": 4612
  }
}
```

## Potential issues

Synapse would need to change how it handles timeline ordering.
Other than that, none.

## Alternatives

None?

## Security considerations

None.

## Unstable prefix

The room version for this MSC is `com.nhjkl.msc4398.opt1`, and it is
based on room version `12`.

## Dependencies

None.
