# MSC4059: Mutable event content

[Edits](https://spec.matrix.org/v1.8/client-server-api/#event-replacements) are
used to "replace" an event's contents, and are structured as events themselves.
This can, in some circumstances, cause excessive event traffic which slows down
scrollback.

This proposal introduces a complimentary feature to edits which allows events to
be partially changed in-place. By editing events in-place, there is no edit
history for clients to use - this can make the feature unhelpful in many cases.

## Proposal

In a future room version...

**TODO**: Detail.

Events must self-declare as mutable by *not* providing a content hash over
federation. Events *with* a content hash are considered immutable because the
hash is covered by both the reference hash (event ID) and signatures.

Mutable events can only change change details which don't affect their reference
hash. For example, the `membership` field of `m.room.member` *cannot* be mutated
because it is part of the redaction algorithm, which then feeds into both the
event's signatures and reference hash. Fields like `displayname` would be
mutable, however.

A mutation is signed by the sender to help ensure it's not forged by a server.
**TODO**: Involve cross-signing in here?

Mutations are advertised over federation using EDUs (**TODO**: EDU definition),
indicating to other servers that they need to either re-fetch or apply the
contained change to their copy of the event. Only mutations sent by the original
event sender are permitted/legal - all others are ignored.

For example, if given an "original event" as follows:

```jsonc
{
  "type": "m.room.member",
  "state_key": "@alice:example.org",
  "sender": "@alice:example.org",
  "content": {
    "membership": "join",
    "displayname": "Alice",
    "avatar_url": "mxc://example.org/abc123"
  },
  "origin_server_ts": 1234567890,
  "signatures": {
    "example.org": {
      "ed25519:abcd": "<unpadded base64 PDU signature>"
    }
  },
  "auth_events": [/* ... */],
  "prev_events": [/* ... */]
  // note lack of `hashes`, indicating mutability
}
```

A mutation EDU might be sent out as such:

```jsonc
{
  "event_id": "$event",
  "mutation": {
    "displayname": "Alice LastNameHere", // we're changing `content.displayname`
    // note lack of `avatar_url` - we're "removing" it
  },
  "signatures": {
    "@alice:example.org": {
      // TODO: Which device(s) sign this?
      "ed25519:DEVICEID": "<unpadded base64 signature for `mutation`>"
    }
  }
}
```

The server then applies that over top of the redactable fields in `content`,
including the sender's signatures for clients to verify (if they want to):

```jsonc
{
  "type": "m.room.member",
  "state_key": "@alice:example.org",
  "sender": "@alice:example.org",
  "content": {
    "membership": "join",
    "displayname": "Alice LastNameHere",
    "signatures": {
      "@alice:example.org": {
        "ed25519:DEVICEID": "<unpadded base64 signature for `mutation`>"
      }
    }
  },
  "origin_server_ts": 1234567890,
  "signatures": {
    "example.org": {
      "ed25519:abcd": "<unpadded base64 PDU signature>"
    }
  },
  "auth_events": [/* ... */],
  "prev_events": [/* ... */]
  // note lack of `hashes`, indicating mutability
}
```

## Potential issues

**TODO**: Detail.

It's unclear as a server or client if you have the "latest" copy of an event.
This makes the feature useful only when loss is tolerable. A server can always
try to ask the origin for the latest copy of mutable events, but that server
might not be online anymore. Other participating servers might not have the
latest copy either.

## Alternatives

**TODO**: Detail.

Just send edits, or regular state updates!?

## Security considerations

**TODO**: Detail.

## Unstable prefix

As of writing, it is not intended that implementation begin. Therefore, an
unstable prefix is deliberately not declared.

## Dependencies

No direct dependencies.
