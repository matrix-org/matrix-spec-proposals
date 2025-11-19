# MSC4058: Additive Events

New features in Matrix often need to introduce new event types to persist and
communicate data within a room. Some of these features can ultimately clutter
the room state/history with events that aren't providing critical function but
do slow down scrollback.

This proposal introduces a concept of "additive events", where users in a room
can attach additional (structured) metadata to an event without having to take
up an entire event ID themselves. This data is communicated ephemerally and is
subject to random data loss, making it unsuitable for anything which needs a
proper permanent record.

## Proposal

The `unsigned` portion of an event gains an optional `m.additive` object. The
`m.additive` object is transmitted over federation, and is keyed by sender. The
value is another object containing the additive information and a signature to
cover the sent object.

For example:

```jsonc
{
  "type": "m.room.message",
  "sender": "@alice:example.org",
  // other fields not shown

  "unsigned": {
    "m.additive": {
      "@bob:example.org": {
        "hello": true,
        "signatures": {
          "@bob:example.org": {
            // Only one of Bob's devices needs to sign this
            "ed25519:DEVICEID": "<unpadded base64 signature covering `hello`>"
          },
          "example.org": { // must be the same server as the m.additive key
            // Only one of the server's keys needs to sign this
            "ed25519:KEYVERSION": "<unpadded base64 signature covering `hello`>"
          }
        }
      }
    }
  }
}
```

**TODO**: We need a way to describe a schema, to avoid abusive metadata being
applied.

**Note**: With respect to [MSC4049](https://github.com/matrix-org/matrix-spec-proposals/pull/4049),
the keys of `m.additive` can be rooms or servers too.

To add information to an event, a server transmits an EDU.

**TODO**: Describe EDU, and APIs so clients can generate it.

## Potential issues

**TODO**: Detail.

Spam/Abuse: Without a schema, users can add whatever they want.

Unredactable: The added metadata can't be redacted/removed.

Overwrite semantics: The MSC doesn't describe how to replace your added detail.

## Alternatives

**TODO**: Detail.

## Security considerations

**TODO**: Detail.

## Unstable prefix

As of writing, it is not intended that implementation begin. Therefore, an
unstable prefix is deliberately not declared.

## Dependencies

No direct dependencies.
