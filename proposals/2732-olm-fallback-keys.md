# MSC2732: Olm fallback keys

Olm uses a set of one-time keys when initializing a session between two
devices: Alice uploads one-time keys to her homeserver, and Bob claims one of
them to perform a Diffie-Hellman to generate a shared key.  As implied by the
name, a one-time key is only to be used once.  However, if all of Alice's
one-time keys are claimed, Bob will not be able to create a session with Alice.

This can be addressed by Alice uploading a fallback key that is used in place
of a one-time key when no one-time keys are available.

## Proposal

A new request parameter, `fallback_keys`, is added to the body of the
`/keys/upload` client-server API, which is in the same format as the
`one_time_keys` parameter with the exception that there must be at most one key
per key algorithm.  If the user had previously uploaded a fallback key for a
given algorithm, it is replaced -- the server will only keep one fallback key
per algorithm for each user.

When uploading fallback keys for algorithms whose key format is a signed JSON
object, client should include a property named `fallback` with a value of
`true`.

Example:

`POST /keys/upload`

```json
{
  "fallback_keys": {
    "signed_curve25519:AAAAAA": {
      "key": "base64+public+key",
      "fallback": true,
      "signatures": {
        "@alice:example.org": {
          "ed25519:DEVICEID": "base64+signature"
        }
      }
    }
  }
}
```

When Bob calls `/keys/claim` to claim one of Alice's one-time keys, but Alice
has no one-time keys left, the homeserver will return the fallback key instead,
if Alice had previously uploaded one.  Unlike with one-time keys, fallback keys
are not deleted when they are returned by `/keys/claim`.  However, the server
marks that they have been used.

A new response parameter, `device_unused_fallback_key_types`, is added to
`/sync`.  This is an array listing the key algorithms for which the server has
an unused fallback key for the user.  If the client wants the server to have a
fallback key for a given key algorithm, but that algorithm is not listed in
`device_unused_fallback_key_types`, the client will upload a new key as above.

The `device_unused_fallback_key_types` parameter must be present if the server
supports fallback keys.  Clients can thus treat this field as an indication
that the server supports fallback keys, and so only upload fallback keys to
servers that support them.

Example:

`GET /sync`

Response:

```json
{
  // other fields...
  "device_unused_fallback_key_types": ["signed_curve25519"]
}
```

## Security considerations

Using a fallback key rather than a one-time key has security implications.  An
attacker can replay a message that was originally sent with a fallback key, and
the receiving client will accept it as a new message if the fallback key is
still active.  Also, an attacker that compromises a client may be able to
retrieve the private part of the fallback key to decrypt past messages if the
client has still retained the private part of the fallback key.

For this reason, clients should not store the private part of the fallback key
indefinitely.  For example, client should only store at most two fallback keys:
the current fallback key (that it has not yet received any messages for) and
the previous fallback key, and should remove the previous fallback key once it
is reasonably certain that it has received all the messages that use it (for
example, one hour after receiving the first message that used it).

For addressing replay attacks, clients can also keep track of inbound sessions
to detect replays.

## Unstable prefix

The `fallback_key` request parameter and the `device_unused_fallback_key_types`
response parameter will be prefixed by `org.matrix.msc2732.`.
