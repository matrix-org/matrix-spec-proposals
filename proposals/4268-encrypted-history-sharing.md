# MSC4268: Sharing room keys for past messages

In Matrix, rooms can be configured via the
[`m.room.history_visibility`](https://spec.matrix.org/v1.14/client-server-api/#room-history-visibility)
state event such that previously-sent messages can be visible to users that
join the room. However, this is ineffective in encrypted rooms, where new
joiners will lack the keys necessary to decrypt historical messages.

This proposal defines a mechanism by which existing room members can share the
decryption keys with new members, for example when inviting them, thus giving
the new members access to historical messages.

A previous proposal,
[MSC3061](https://github.com/matrix-org/matrix-spec-proposals/pull/3061) aimed
to solve a similar problem; however, the mechanism used did not scale well. In
addition, the implementation in `matrix-js-sdk` was subject to a [security
vulnerability](https://matrix.org/blog/2024/10/security-disclosure-matrix-js-sdk-and-matrix-react-sdk/)
which this proposal addresses.

## Proposal

### Room key bundle format

When Alice is about to invite Bob to a room, she first assembles a "room key
bundle" containing all of the room keys for megolm sessions that she believes
future members of the room should have access to. Specifically, those are the
megolm sessions associated with that room which were marked with
`shared_history`: see [below](#shared_history-property-in-mroom_key-events).

The keys are assembled into a JSON object with the following structure:

```json5
{
  "room_keys": [
    {
      "algorithm": "m.megolm.v1.aes-sha2",
      "room_id": "!Cuyf34gef24t:localhost",
      "sender_claimed_keys": { "ed25519": "aj40p+aw64yPIdsxoog8jhPu9i7l7NcFRecuOQblE3Y" },
      "sender_key": "RF3s+E7RkTQTGF2d8Deol0FkQvgII2aJDf3/Jp5mxVU",
      "session_id": "X3lUlvLELLYxeTx4yOVu6UDpasGEVO0Jbu+QFnm0cKQ",
      "session_key": "AgAAAADxKHa9uFxcXzwYoNueL5Xqi69IkD4sni8Llf..."
    },
    // ... etc
  ],
  "withheld": [
    {
      "algorithm": "m.megolm.v1.aes-sha2",
      "code": "m.history_not_shared",
      "reason": "History not shared",
      "room_id": "!Cuyf34gef24t:localhost",
      "sender_key": "RF3s+E7RkTQTGF2d8Deol0FkQvgII2aJDf3/Jp5mxVU",
      "session_id": "X3lUlvLELLYxeTx4yOVu6UDpasGEVO0Jbu+QFnm0cKQ"
    }
  ]
}
```

The properties in the object are defined as:

  * `room_keys`: an array of objects each with the following fields from [`ExportedSessionData`](https://spec.matrix.org/v1.14/client-server-api/#definition-exportedsessiondata):

     * `algorithm`
     * `room_id`
     * `sender_claimed_keys`
     * `sender_key`
     * `session_id`
     * `session_key`

   `forwarding_curve_key_chain` is omitted since it is useless in this case.
   The `shared_history` flag defined below is omitted (it is `true` by
   implication).

 * `withheld`: an array of objects with the same format as the content of an
   [`m.room_key.withheld`](https://spec.matrix.org/v1.14/client-server-api/#mroom_keywithheld)
   message, usually with code `m.history_not_shared` (see
   [below](#new-withheld-code)) to indicate that the recipient isn't allowed to
   receive the key.

A single session MUST NOT appear in both the `room_keys` and `withheld` sections.

The JSON object is then encrypted using the same algorithm as [encrypted
attachments](https://spec.matrix.org/v1.14/client-server-api/#sending-encrypted-attachments)
(i.e., with AES256-CTR), and uploaded with [`POST
/_matrix/media/v3/upload`](https://spec.matrix.org/v1.14/client-server-api/#post_matrixmediav3upload).

The details of this key bundle are then shared with Bob, as below.

### `m.room_key_bundle` to-device message

Having uploaded the encrypted key bundle, Alice must share the details with each of Bob's devices.

She first ensures she has an up-to-date list of his devices (performing a
[`/keys/query`](https://spec.matrix.org/v1.14/client-server-api/#post_matrixclientv3keysquery)
request if necessary. She then sends a to-device message to each of his devices
**which are correctly signed by his cross-signing keys**.

A new to-device message type is defined, `m.room_key_bundle`, which MUST be
encrypted using
[Olm](https://spec.matrix.org/v1.14/client-server-api/#molmv1curve25519-aes-sha2).

The plaintext content of such a message should be:

```
{
  "type": "m.room_key_bundle",
  "content": {
    "room_id": "!Cuyf34gef24t:localhost",
    "file": {
      "v": "v2",
      "url": "mxc://example.org/FHyPlCeYUSFFxlgbQYZmoEoe",
      "key": {
          "alg": "A256CTR",
          "ext": true,
          "k": "aWF6-32KGYaC3A_FEUCk1Bt0JA37zP0wrStgmdCaW-0",
          "key_ops": ["encrypt","decrypt"],
          "kty": "oct"
      },
      "iv": "w+sE15fzSc0AAAAAAAAAAA",
      "hashes": {
        "sha256": "fdSLu/YkRx3Wyh3KQabP3rd6+SFiKg5lsJZQHtkSAYA"
      }
    }
  },
  "sender": "@alice:example.com",
  "recipient": "@bob:example.org",
  "recipient_keys": { "ed25519": "<bob_ed25519_key>" }
  "keys": { "ed25519": "<alice_ed25519_key>" },
  "sender_device_keys": { ... }
}
```

The properties within the `content` are defined as:

 * `room_id`: the room to which the keys in the key bundle relate. (This is
   required so that Bob can download the key bundle at the right time.)

 * `file`: `EncryptedFile` from the [encrypted attachment
   format](https://spec.matrix.org/v1.13/client-server-api/#extensions-to-mroommessage-msgtypes).

`sender`, `recipient`, `recipient_keys` and `keys` are the normal fields
required by Olm-encrypted messages.

`sender_device_keys` are the sender's device keys, as defined by
[MSC4147](https://github.com/matrix-org/matrix-spec-proposals/pull/4147), which
are **required** for `m.room_key_bundle` messages. The sender MUST include
them, and recipients SHOULD ignore `m.room_key_bundle` messages which omit
them.


### `shared_history` property in `m.room_key` messages

Suppose Alice and Bob are participating in an encrypted room, and Bob now
wishes to invite Charlie to join the chat. If the [history
visibility](https://spec.matrix.org/v1.14/client-server-api/#room-history-visibility)
settings allow, Bob can share the message decryption keys for previously sent
messages with Charlie. However, it is dangerous for Bob to take the server's
word for the history visibility setting: a malicious server admin collaborating
with Charlie could tell Bob that the history visibility was open when in fact
it was restricted. In addition, the history visibility in a given room may have
been changed over time and it can be difficult for clients to estalish which
setting was in force for a particular Megolm session.

To counter this, we add a `shared_history` property to
[`m.room_key`](https://spec.matrix.org/v1.14/client-server-api/#mroom_key)
messages, indicating that the creator of that Megolm session understands and
agrees that the session keys may be shared with newly-invited users in
future. For example:

```json
{
  "type": "m.room_key",
  "content": {
    "algorithm": "m.megolm.v1.aes-sha2",
    "room_id": "!room_id",
    "session_id": "session_id",
    "session_key": "session_key",
    "shared_history": true
  }
}
```

In other words: when Alice wants to send a message in the room she shares with
Bob, she first checks the `history_visibility`. If it is `shared` or
`world_readable`, then when she sends the Megolm keys to Bob, she sets
`shared_history` to `true`.

Clients SHOULD show a visual indication to users that their encrypted messages
may be shared with future room members in this way.

If the history visibility changes in a way that would affect the
`shared_history` flag (i.e., it changes from `joined` or `invited` to `shared`
or `world_readable`, or vice versa), then clients MUST rotate their outbound
megolm session before sending more messages.

In addition, a `shared_history` property is added to the [`BackedUpSessionData`
type](https://spec.matrix.org/v1.14/client-server-api/#definition-backedupsessiondata)
in key backups (that is, the plaintext object that gets encrypted into the
`session_data` field) and the [`ExportedSessionData`
type](https://spec.matrix.org/v1.14/client-server-api/#definition-exportedsessiondata). In
both cases, the new property is set to `true` if the session was shared with us
with `shared_history: true`, and `false` otherwise.

For example:

```json
{
  "algorithm": "m.megolm.v1.aes-sha2",
  "forwarding_curve25519_key_chain": [
    "hPQNcabIABgGnx3/ACv/jmMmiQHoeFfuLB17tzWp6Hw"
  ],
  "sender_claimed_keys": {
    "ed25519": "aj40p+aw64yPIdsxoog8jhPu9i7l7NcFRecuOQblE3Y"
  },
  "sender_key": "RF3s+E7RkTQTGF2d8Deol0FkQvgII2aJDf3/Jp5mxVU",
  "session_key": "AgAAAADxKHa9uFxcXzwYoNueL5Xqi69IkD4sni8Llf...",
  "shared_history": true
}
```

In all cases, an absent or non-boolean `shared_history` property is treated the same as
`shared_history: false`.

### New "withheld" code

The spec currently
[defines](https://spec.matrix.org/v1.14/client-server-api/#mroom_keywithheld) a
number of "withheld" codes which are used to indicate that a client is
deliberately *not* sharing a megolm session key with another. Normally these
codes are used in `m.room_key.withheld` to-device events; as the text above
specifies, we will now also use them in the `withheld` section of the room key bundle.

This MSC proposes the addition of a new withheld code, `m.history_not_shared`,
which is used specifically to indicate that the megolm session in question does not
have the `shared_history` flag set (which means that the creator of that
session believed that the room history visibility did not allow new members to
access history).

* Aside: the spec currently contains a definition for a `withheld` code
  `m.unauthorised`. However, its semantics are unclear: the spec defines it as
  meaning "the user/device is not allowed to have the key", but is unclear
  about why this might happen. (Arguably, `m.blacklisted` and `m.unverified`
  are also cases of "the user/device is not allowed to have the key".)

  In practice, modern Element clients (including Element Web and the classic
  mobile clients, since the port to the Rust crypto stack), do not send this
  withheld code at all. Further, the example given in the spec, "the
  user/device was not in the room when the original message was sent", is
  somewhat similar to this usecase.

  It is therefore somewhat tempting to repurpose `m.unauthorised` to suit this
  usecase. However, `m.unauthorised` has been used for other purposes in the
  past (for example, [Element Android
  Classic](https://github.com/element-hq/element-android/blob/v1.6.5/matrix-sdk-android/src/kotlinCrypto/java/org/matrix/android/sdk/internal/crypto/IncomingKeyRequestManager.kt#L276)
  used to use it as a general-purpose refusal to respond to key requests from
  other users), and we have little insight as to how `m.unauthorised` might be
  used in non-Element clients.

  In short, a new code is likely to cause less confusion than repurposing
  `m.unauthorised`,

### Actions as a receiving client

When Bob's client receives an `m.room_key_bundle` event from Alice, there are two possibilities:

 * If Bob has recently accepted an invite to the room from Alice, the client
   should immediately download the key bundle and start processing it. Note,
   however, that this process must be resilient to Bob's client being restarted
   before the download/import completes.

   TODO: what does "recently" mean?

 * Otherwise, Bob's client should store the details of the key bundle but not
   download it immediately.  If he later accepts an invite to the room from
   Alice, his client downloads and processes the bundle at that point.

   Delaying the download in this way avoids a potential DoS vector in which an
   attacker can cause the victim to download a lot of useless data.

Once Bob has downloaded the key bundle, the sessions are imported as they would
be when importing a key export; however:

  * Only keys for the relevant room should be imported.

  * Bob's client should remember who sent the keys (Alice, in this case), and
    MUST show that information to the user, since he has only that user's word
    for the authenticity of those sessions.

TODO: tell the sender we have finished with the bundle, so they can delete it?

## Potential issues

## Alternatives

## Security considerations

* The proposed mechanism allows clients to share the decryption keys for
  significant amounts of encrypted content. Sharing historical keys in this way
  represents a significantly greater security risk than sharing keys for future
  messages on an ad-hoc basis, as when sending `m.room_key` messages.

  It is therefore **crucial** that the inviting client take careful measures to
  ensure that the recipient devices genuinely belong to the intended
  recipient, rather than having been injected by an intruder.

  For example, the recipient must cross-sign his devices, and the sender must
  ensure that the devices are correctly signed. Further, the sender should keep
  records of cross-signing keys seen for each user, and if a change is
  observed, consider this a red flag suggesting that the account may be
  compromised and confirm with the user.

* Recipients must be mindful that there is no authoritative evidence of the
  sender of messages decrypted using a room key bundle: a malicious (or buggy)
  inviter working in cahoots with a homeserver administrator could make it
  appear as though events sent by one user were in fact sent by another.

  Ultimately, the recipient of a key bundle is taking the world of the sender
  of that key bundle as to the actual owner of each megolm session. This is an
  inevitable consequence of the deniability property of encrypted messaging.

  Recipient clients should make this constraint obvious to the user, for
  example by showing the affected messages with a label "Alice shared this message".

* Recipients should be mindful of the potential of denial-of-service (DoS) and
  cache-poisoning attacks from malicious senders.

  In particular, a malicious sender could try to prompt a recipient to download
  significant amounts of data from the media store by sending
  `m.room_key_bundle` messages pointing to large media files.

  Further, a malicious sender might attempt to make the recipient believe that
  a megolm session belonged to Alice, whereas it actually belonged to
  Charlie. Even if the recipient later receives a key bundle from an honest
  user, they may now have difficulty deciding which user was correct.

  Both problems can be mitigated by only accepting key bundles when accepting
  an invite from that user.

## Unstable prefix

Until this MSC is accepted, the following identifiers should be used:

 * `io.element.msc4268.room_key_bundle` instead of `m.room_key_bundle` for the
   to-device message containing details of the key bundle.

 * `org.matrix.msc3061.shared_history` instead of `shared_history` for the
   property in `BackedUpSessionData` and `ExportedSessionData` indicating that
   the key can be shared with new members.

 * `io.element.msc4268.history_not_shared` instead of `m.history_not_shared` as
   the withheld code for sessions which are not marked as `shared_history`.

## Dependencies

This MSC depends on [MSC4147](https://github.com/matrix-org/matrix-spec-proposals/pull/4147), which has recently been accepted into the spec.
