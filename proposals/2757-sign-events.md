# MSC2757: Sign Events

Currently the homeserver is trusted to not modify events in cleartext rooms. To resolve this you can
turn on end-to-end encryption in a given room. That, however, adds a lot of overhead and is pointless
for big, public rooms. As such, it would be nice to be able to sign your own events you send, so that
the recipient can ensure that the homeserver did not tamper with the message itself.

## Proposal

The general idea is to sign the `content` of each event you send out with your own ed25519 key and a
new `message_signing` key. Signing with your own ed25519 key is not enough, as that makes the signature
unverifyable after you log out of your own device. Only using a `message_signing` key is not enough,
as signing with your own device key is a nice mitigation for a client that does not support cross-signing yet

### The `message_signing` key

The `message_signing` key would be an ed25519 key similar to the cross-sigining `user_signing` and
`self-signing` keys: It is signed by your own master key, uploaded and distributed via the same
endpoints.

As `usage` it is expected to have `message_signing` listed.

#### POST `/_matrix/client/r0/keys/signatures/upload`

A new key, `message_signing_key`, is introduced, which uploads the message singing key, signed by the
master key. As usual, when a user uploads or changes a message singing key, the user ID of that person
should appear in the `changed` field of the `/sync` reply of other users. An example payload could
look as following:

```json
{
  "master_key": {
    "user_id": "@alice:example.com",
    "usage": ["master"],
    "keys": {
      "ed25519:base64+master+public+key": "base64+master+public+key",
    }
  },
  "self_signing_key": {
    "user_id": "@alice:example.com",
    "usage": ["self_signing"],
    "keys": {
      "ed25519:base64+self+signing+public+key": "base64+self+signing+public+key",
    },
    "signatures": {
      "@alice:example.com": {
        "ed25519:base64+master+public+key": "signature+of+self+signing+key"
      }
    }
  },
  "user_signing_key": {
    "user_id": "@alice:example.com",
    "usage": ["user_signing"],
    "keys": {
      "ed25519:base64+user+signing+public+key": "base64+user+signing+public+key",
    },
    "signatures": {
      "@alice:example.com": {
        "ed25519:base64+master+public+key": "signature+of+user+signing+key"
      }
    }
  },
  "message_signing_key": {
    "user_id": "@alice:example.com",
    "usage": ["message_signing"],
    "keys": {
      "ed25519:base64+message+signing+public+key": "base64+message+signing+key"
    },
    "signatures": {
      "@alice:example.com": {
        "ed25519:base64+master+public+key": "signature+of+message+signing+key"
      }
    }
  }
}
```

#### POST `/_matrix/client/r0/keys/query`

Similar to `user_signing` keys etc. a new dict, `message_signing_keys` is introduced.

#### Visibility

Similarly to the master key, everyone should be able to see a persons message signing key, if they
share a room with them. This is required to be abe to verify signatures of messages.

#### Storage in SSSS

The private key can be stored base64-encoded in SSSS under the key `m.message_signing`
(`m.cross_signing.message_signin`? Calling these keys "cross-signing" was prolly not too descriptive...).

### Signing messages

To sign a message you strip the `signatures` and `unsigned` dicts off of the `content` (if present),
encode it with canonical json and prepend the event type. Then you sign it with the message_signing
and device ed25519 key.

For example, a message of type `m.room.message` with the following content:
```json
{
  "msgtype": "m.text",
  "body": "foxies!",
  "unsigned": {
    "super secret": "wha!"
  }
}
```

Would yield the following string needing to be signed: `m.room.message{"body":"foxies!","msgtype":"m.text"}`

Prepending the event type is done to rule out attack vectors where the server could modify the type of
an event.

After that, the generated signatures are added in a signatures dict to the content, similar as done
elsewhere:

```json
{
  "msgtype": "m.text",
  "body": "foxies!",
  "unsigned": {
    "super secret": "wha!"
  },
  "signatures": {
    "@alice:example.com": {
      "ed25519:base64+message+signing+key": "signature+of+message+signing+key",
      "ed25519:device+id": "signature+of+device+id"
    }
  }
}
```

This new content is then used to send messages via `/_matrix/client/r0/rooms/{roomId}/send/{eventType}/{txnId}`.

### Signing messages in encrypted rooms

To add additional verification and authenticity it is a good idea to also sign messages in encrypted
rooms. The encrypted content should be signed.

For example, you want to send an encrypted `m.room.message` with the content

```json
{
  "msgtype": "m.text",
  "body": "foxies!",
}
```

You first encrypt the message as usual, so that it becomes an event of type `m.room.encrypted` with content

```json
{
  "algorithm": "m.megolm.v1.aes-sha2",
  "ciphertext": "beep",
  "device_id": "HCJDXEANPN",
  "sender_key": "boop",
  "session_id": "blubb"
}
```

Then, you have to sign the following string: `m.room.encrypted{"algorithm":"m.megolm.v1.aes-sha2","ciphertext":"beep","device_id":"HCJDXEANPN","sender_key":"boop","session_id":"blubb"}`

Then, the content finally becomes

```json
{
  "algorithm": "m.megolm.v1.aes-sha2",
  "ciphertext": "beep",
  "device_id": "HCJDXEANPN",
  "sender_key": "boop",
  "session_id": "blubb",
  "signatures": {
    "@alice:example.com": {
      "ed25519:base64+message+signing+key": "signature+of+message+signing+key",
      "ed25519:HCJDXEANPN": "signature+of+device+HCJDXEANPN"
    }
  }
}
```

This content is then sent, as usual, as `m.room.encrypted`.

### Verifying message signatures

If signatures are present and bad, a client MUST at least display a warning, or completely hide that
message.

If signatures are present and good, clients MAY indicate that in the UI somehow, e.g. by a green
checkmark.

## Potential issues

The introduction of a new message_signing key will force users to enter their recovery passphrase
to enable this feature, as the master key is typically not cached. Additionally, the message_signing
key should be cached on devices, so that the user doesn't have to enter their recovery key every time
they want to send a message.

## Alternatives

Instead of introducing a new message_signing key, the self_signing key could be re-used for that
purpose, as the visibility of those should be the same. The two keys, however, have different
purposes. Additionally, the message_signing key should be cached, making it potentially more vulnerable
to being stolen. As such, it is a good idea to keep the two separate, to be able to revoke them
independently.

## Security considerations

The message_signing key should be cached by clients, but it shouldn't be stolen by a third party.
Thus, clients will have to think about themselves how to resolve this issue, e.g. by using a securly
encrypted store provided by their platform.

Additionally, you lose deniability if you sign all your messages.
