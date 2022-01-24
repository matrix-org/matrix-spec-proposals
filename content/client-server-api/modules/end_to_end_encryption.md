---
type: module
---

### End-to-End Encryption

Matrix optionally supports end-to-end encryption, allowing rooms to be
created whose conversation contents are not decryptable or interceptable
on any of the participating homeservers.

#### Key Distribution

Encryption and Authentication in Matrix is based around public-key
cryptography. The Matrix protocol provides a basic mechanism for
exchange of public keys, though an out-of-band channel is required to
exchange fingerprints between users to build a web of trust.

##### Overview

1) Bob publishes the public keys and supported algorithms for his
device. This may include long-term identity keys, and/or one-time
keys.

```
      +----------+  +--------------+
      | Bob's HS |  | Bob's Device |
      +----------+  +--------------+
            |              |
            |<=============|
              /keys/upload
```

2) Alice requests Bob's public identity keys and supported algorithms.

```
      +----------------+  +------------+  +----------+
      | Alice's Device |  | Alice's HS |  | Bob's HS |
      +----------------+  +------------+  +----------+
             |                  |               |
             |=================>|==============>|
               /keys/query        <federation>
```

3) Alice selects an algorithm and claims any one-time keys needed.

```
      +----------------+  +------------+  +----------+
      | Alice's Device |  | Alice's HS |  | Bob's HS |
      +----------------+  +------------+  +----------+
             |                  |               |
             |=================>|==============>|
               /keys/claim         <federation>
```

##### Key algorithms

The name `ed25519` corresponds to the
[Ed25519](http://ed25519.cr.yp.to/) signature algorithm. The key is a
32-byte Ed25519 public key, encoded using [unpadded Base64](/appendices/#unpadded-base64). Example:

    "SogYyrkTldLz0BXP+GYWs0qaYacUI0RleEqNT8J3riQ"

The name `curve25519` corresponds to the
[Curve25519](https://cr.yp.to/ecdh.html) ECDH algorithm. The key is a
32-byte Curve25519 public key, encoded using [unpadded Base64](/appendices/#unpadded-base64).
Example:

    "JGLn/yafz74HB2AbPLYJWIVGnKAtqECOBf11yyXac2Y"

The name `signed_curve25519` also corresponds to the Curve25519
algorithm, but a key using this algorithm is represented by an object
with the following properties:

`KeyObject`

| Parameter  | Type       | Description                                                                                                                                       |
|------------|------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| key        | string     | **Required.** The unpadded Base64-encoded 32-byte Curve25519 public key.                                                                          |
| signatures | Signatures | **Required.** Signatures of the key object. The signature is calculated using the process described at [Signing JSON](/appendices/#signing-json). |

Example:

```json
{
  "key":"06UzBknVHFMwgi7AVloY7ylC+xhOhEX4PkNge14Grl8",
  "signatures": {
    "@user:example.com": {
      "ed25519:EGURVBUNJP": "YbJva03ihSj5mPk+CHMJKUKlCXCPFXjXOK6VqBnN9nA2evksQcTGn6hwQfrgRHIDDXO2le49x7jnWJHMJrJoBQ"
    }
  }
}
```

##### Device keys

Each device should have one Ed25519 signing key. This key should be
generated on the device from a cryptographically secure source, and the
private part of the key should never be exported from the device. This
key is used as the fingerprint for a device by other clients.

A device will generally need to generate a number of additional keys.
Details of these will vary depending on the messaging algorithm in use.

Algorithms generally require device identity keys as well as signing
keys. Some algorithms also require one-time keys to improve their
secrecy and deniability. These keys are used once during session
establishment, and are then thrown away.

For Olm version 1, each device requires a single Curve25519 identity
key, and a number of signed Curve25519 one-time keys.

##### Uploading keys

A device uploads the public parts of identity keys to their homeserver
as a signed JSON object, using the [`/keys/upload`](/client-server-api/#post_matrixclientv3keysupload) API. The JSON object
must include the public part of the device's Ed25519 key, and must be
signed by that key, as described in [Signing
JSON](/appendices/#signing-json).

One-time and fallback keys are also uploaded to the homeserver using the
[`/keys/upload`](/client-server-api/#post_matrixclientv3keysupload) API.

{{% added-in v="1.2" %}} Fallback keys are similar to one-time keys, but
are not consumed once used. They are only used when the device has run out
of one-time keys, and can be replaced by a new fallback key.

Devices must store the private part of each key they upload. They can
discard the private part of a one-time key when they receive a message
using that key. However it's possible that a one-time key given out by a
homeserver will never be used, so the device that generates the key will
never know that it can discard the key. Therefore a device could end up
trying to store too many private keys. A device that is trying to store
too many private keys may discard keys starting with the oldest.

{{% boxes/warning %}}
Fallback keys are used to prevent one-time key exhaustion when devices
are offline/unable to upload additional keys, though sessions started using
fallback keys could be vulnerable to replay attacks.
{{% /boxes/warning %}}

{{% boxes/warning %}}
Clients should not store the private half of fallback keys indefinitely
to avoid situations where attackers can decrypt past messages sent using
that fallback key.

Instead, clients should keep the private keys for at most 2 fallback keys:
the current, unused, fallback key and the key immediately preceding it.
Once the client is reasonably certain it has received all messages that
used the old fallback key, such as after an hour since the first message,
it should remove that fallback key.
{{% /boxes/warning %}}

##### Tracking the device list for a user

Before Alice can send an encrypted message to Bob, she needs a list of
each of his devices and the associated identity keys, so that she can
establish an encryption session with each device. This list can be
obtained by calling [`/keys/query`](/client-server-api/#post_matrixclientv3keysquery), passing Bob's user ID in the
`device_keys` parameter.

From time to time, Bob may add new devices, and Alice will need to know
this so that she can include his new devices for later encrypted
messages. A naive solution to this would be to call [`/keys/query`](/client-server-api/#post_matrixclientv3keysquery)
before sending each message -however, the number of users and devices
may be large and this would be inefficient.

It is therefore expected that each client will maintain a list of
devices for a number of users (in practice, typically each user with
whom we share an encrypted room). Furthermore, it is likely that this
list will need to be persisted between invocations of the client
application (to preserve device verification data and to alert Alice if
Bob suddenly gets a new device).

Alice's client can maintain a list of Bob's devices via the following
process:

1.  It first sets a flag to record that it is now tracking Bob's device
    list, and a separate flag to indicate that its list of Bob's devices
    is outdated. Both flags should be in storage which persists over
    client restarts.
2.  It then makes a request to [`/keys/query`](/client-server-api/#post_matrixclientv3keysquery), passing Bob's user ID in
    the `device_keys` parameter. When the request completes, it stores
    the resulting list of devices in persistent storage, and clears the
    'outdated' flag.
3.  During its normal processing of responses to [`/sync`](/client-server-api/#get_matrixclientv3sync), Alice's client
    inspects the `changed` property of the [`device_lists`](/client-server-api/#extensions-to-sync-1) field. If it
    is tracking the device lists of any of the listed users, then it
    marks the device lists for those users outdated, and initiates
    another request to [`/keys/query`](/client-server-api/#post_matrixclientv3keysquery) for them.
4.  Periodically, Alice's client stores the `next_batch` field of the
    result from [`/sync`](/client-server-api/#get_matrixclientv3sync) in persistent storage. If Alice later restarts her
    client, it can obtain a list of the users who have updated their
    device list while it was offline by calling [`/keys/changes`](/client-server-api/#get_matrixclientv3keyschanges),
    passing the recorded `next_batch` field as the `from` parameter. If
    the client is tracking the device list of any of the users listed in
    the response, it marks them as outdated. It combines this list with
    those already flagged as outdated, and initiates a [`/keys/query`](/client-server-api/#post_matrixclientv3keysquery)
    request for all of them.

{{% boxes/warning %}}
Bob may update one of his devices while Alice has a request to
`/keys/query` in flight. Alice's client may therefore see Bob's user ID
in the `device_lists` field of the `/sync` response while the first
request is in flight, and initiate a second request to `/keys/query`.
This may lead to either of two related problems.

The first problem is that, when the first request completes, the client
will clear the 'outdated' flag for Bob's devices. If the second request
fails, or the client is shut down before it completes, this could lead
to Alice using an outdated list of Bob's devices.

The second possibility is that, under certain conditions, the second
request may complete *before* the first one. When the first request
completes, the client could overwrite the later results from the second
request with those from the first request.

Clients MUST guard against these situations. For example, a client could
ensure that only one request to `/keys/query` is in flight at a time for
each user, by queuing additional requests until the first completes.
Alternatively, the client could make a new request immediately, but
ensure that the first request's results are ignored (possibly by
cancelling the request).
{{% /boxes/warning %}}

{{% boxes/note %}}
When Bob and Alice share a room, with Bob tracking Alice's devices, she
may leave the room and then add a new device. Bob will not be notified
of this change, as he doesn't share a room anymore with Alice. When they
start sharing a room again, Bob has an out-of-date list of Alice's
devices. In order to address this issue, Bob's homeserver will add
Alice's user ID to the `changed` property of the `device_lists` field,
thus Bob will update his list of Alice's devices as part of his normal
processing. Note that Bob can also be notified when he stops sharing any
room with Alice by inspecting the `left` property of the `device_lists`
field, and as a result should remove her from its list of tracked users.
{{% /boxes/note %}}

##### Sending encrypted attachments

When encryption is enabled in a room, files should be uploaded encrypted
on the homeserver.

In order to achieve this, a client should generate a single-use 256-bit
AES key, and encrypt the file using AES-CTR. The counter should be
64-bit long, starting at 0 and prefixed by a random 64-bit
Initialization Vector (IV), which together form a 128-bit unique counter
block.

{{% boxes/warning %}}
An IV must never be used multiple times with the same key. This implies
that if there are multiple files to encrypt in the same message,
typically an image and its thumbnail, the files must not share both the
same key and IV.
{{% /boxes/warning %}}

Then, the encrypted file can be uploaded to the homeserver. The key and
the IV must be included in the room event along with the resulting
`mxc://` in order to allow recipients to decrypt the file. As the event
containing those will be Megolm encrypted, the server will never have
access to the decrypted file.

A hash of the ciphertext must also be included, in order to prevent the
homeserver from changing the file content.

A client should send the data as an encrypted `m.room.message` event,
using either `m.file` as the msgtype, or the appropriate msgtype for the
file type. The key is sent using the [JSON Web
Key](https://tools.ietf.org/html/rfc7517#appendix-A.3) format, with a
[W3C extension](https://w3c.github.io/webcrypto/#iana-section-jwk).

###### Extensions to `m.room.message` msgtypes

This module adds `file` and `thumbnail_file` properties, of type
`EncryptedFile`, to `m.room.message` msgtypes that reference files, such
as [m.file](#mfile) and [m.image](#mimage), replacing the `url` and `thumbnail_url`
properties.

`EncryptedFile`

| Parameter | Type             | Description                                                                                    |
|-----------|------------------|------------------------------------------------------------------------------------------------|
| url       | string           | **Required.** The URL to the file.                                                             |
| key       | JWK              | **Required.** A [JSON Web Key](https://tools.ietf.org/html/rfc7517#appendix-A.3) object.       |
| iv        | string           | **Required.** The 128-bit unique counter block used by AES-CTR, encoded as unpadded base64.    |
| hashes    | {string: string} | **Required.** A map from an algorithm name to a hash of the ciphertext, encoded as unpadded base64. Clients should support the SHA-256 hash, which uses the key `sha256`. |
| v         | string           | **Required.** Version of the encrypted attachments protocol. Must be `v2`.                     |

`JWK`

| Parameter | Type     | Description                                                                                                              |
| --------- |----------|--------------------------------------------------------------------------------------------------------------------------|
| kty       | string   | **Required.** Key type. Must be `oct`.                                                                                   |
| key_ops   | [string] | **Required.** Key operations. Must at least contain `encrypt` and `decrypt`.                                             |
| alg       | string   | **Required.** Algorithm. Must be `A256CTR`.                                                                              |
| k         | string   | **Required.** The key, encoded as urlsafe unpadded base64.                                                               |
| ext       | boolean  | **Required.** Extractable. Must be `true`. This is a [W3C extension](https://w3c.github.io/webcrypto/#iana-section-jwk). |

Example:

```json
{
  "content": {
    "body": "something-important.jpg",
    "file": {
      "url": "mxc://example.org/FHyPlCeYUSFFxlgbQYZmoEoe",
      "v": "v2",
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
    },
    "info": {
      "mimetype": "image/jpeg",
      "h": 1536,
      "size": 422018,
      "thumbnail_file": {
        "hashes": {
          "sha256": "/NogKqW5bz/m8xHgFiH5haFGjCNVmUIPLzfvOhHdrxY"
        },
        "iv": "U+k7PfwLr6UAAAAAAAAAAA",
        "key": {
          "alg": "A256CTR",
          "ext": true,
          "k": "RMyd6zhlbifsACM1DXkCbioZ2u0SywGljTH8JmGcylg",
          "key_ops": ["encrypt", "decrypt"],
          "kty": "oct"
        },
        "url": "mxc://example.org/pmVJxyxGlmxHposwVSlOaEOv",
        "v": "v2"
      },
      "thumbnail_info": {
        "h": 768,
        "mimetype": "image/jpeg",
        "size": 211009,
        "w": 432
      },
      "w": 864
    },
    "msgtype": "m.image"
  },
  "event_id": "$143273582443PhrSn:example.org",
  "origin_server_ts": 1432735824653,
  "room_id": "!jEsUZKDJdhlrceRyVU:example.org",
  "sender": "@example:example.org",
  "type": "m.room.message",
  "unsigned": {
      "age": 1234
  }
}
```

##### Claiming one-time keys

A client wanting to set up a session with another device can claim a
one-time key for that device. This is done by making a request to the
[`/keys/claim`](/client-server-api/#post_matrixclientv3keysclaim) API.

A homeserver should rate-limit the number of one-time keys that a given
user or remote server can claim. A homeserver should discard the public
part of a one time key once it has given that key to another user.

{{% added-in v="1.2" %}} If the device has run out of one-time keys which
can be claimed, the homeserver will return the fallback key (if one was
uploaded). Fallback keys are not deleted once used and should be replaced
by the device when they are able to upload more one-time keys.

#### Device verification

Before Alice sends Bob encrypted data, or trusts data received from him,
she may want to verify that she is actually communicating with him,
rather than a man-in-the-middle. This verification process requires an
out-of-band channel: there is no way to do it within Matrix without
trusting the administrators of the homeservers.

In Matrix, verification works by Alice meeting Bob in person, or
contacting him via some other trusted medium, and using one of the
verification methods defined below to interactively verify Bob's devices.
Alice and Bob may also read aloud their unpadded base64 encoded Ed25519
public key, as returned by `/keys/query`.

Device verification may reach one of several conclusions. For example:

-   Alice may "accept" the device. This means that she is satisfied that
    the device belongs to Bob. She can then encrypt sensitive material
    for that device, and knows that messages received were sent from
    that device.
-   Alice may "reject" the device. She will do this if she knows or
    suspects that Bob does not control that device (or equivalently,
    does not trust Bob). She will not send sensitive material to that
    device, and cannot trust messages apparently received from it.
-   Alice may choose to skip the device verification process. She is not
    able to verify that the device actually belongs to Bob, but has no
    reason to suspect otherwise. The encryption protocol continues to
    protect against passive eavesdroppers.

{{% boxes/note %}}
Once the signing key has been verified, it is then up to the encryption
protocol to verify that a given message was sent from a device holding
that Ed25519 private key, or to encrypt a message so that it may only be
decrypted by such a device. For the Olm protocol, this is documented at
<https://matrix.org/docs/olm_signing.html>.
{{% /boxes/note %}}

##### Key verification framework

Verifying keys manually by reading out the Ed25519 key is not very
user-friendly, and can lead to errors. In order to help mitigate errors,
and to make the process easier for users, some verification methods are
supported by the specification and use messages exchanged by the user's devices
to assist in the verification. The methods all use a common framework
for negotiating the key verification.

Verification messages can be sent either in a room shared by the two parties,
which should be a [direct messaging](#direct-messaging) room between the two
parties, or by using [to-device](#send-to-device-messaging) messages sent
directly between the two devices involved.  In both cases, the messages
exchanged are similar, with minor differences as detailed below. Verifying
between two different users should be performed using in-room messages, whereas
verifying two devices belonging to the same user should be performed using
to-device messages.

A key verification session is identified by an ID that is established by the
first message sent in that session. For verifications using in-room messages,
the ID is the event ID of the initial message, and for verifications using
to-device messages, the first message contains a `transaction_id` field that is
shared by the other messages of that session.

In general, verification operates as follows:

- Alice requests a key verification with Bob by sending an
  `m.key.verification.request` event. This event indicates the verification
  methods that Alice's client supports. (Note that "Alice" and "Bob" may in
  fact be the same user, in the case where a user is verifying their own
  devices.)
- Bob's client prompts Bob to accept the key verification. When Bob accepts
  the verification, Bob's client sends an `m.key.verification.ready` event.
  This event indicates the verification methods, corresponding to the
  verification methods supported by Alice's client, that Bob's client supports.
- Alice's or Bob's devices allow their users to select one of the verification
  methods supported by both devices to use for verification. When Alice or Bob
  selects a verification method, their device begins the verification by
  sending an `m.key.verification.start` event, indicating the selected
  verification method. Note that if there is only one verification method in
  common between the devices then the receiver's device (Bob) can auto-select
  it.
- Alice and Bob complete the verification as defined by the selected
  verification method. This could involve their clients exchanging messages,
  Alice and Bob exchanging information out-of-band, and/or Alice and Bob
  interacting with their devices.
- Alice's and Bob's clients send `m.key.verification.done` events to indicate
  that the verification was successful.

Verifications can be cancelled by either device at any time by sending an
`m.key.verification.cancel` event with a `code` field that indicates the reason
it was cancelled.

When using to-device messages, Alice may not know which of Bob's devices to
verify, or may not want to choose a specific device. In this case, Alice will
send `m.key.verification.request` events to all of Bob's devices. All of these
events will use the same transaction ID. When Bob accepts or declines the
verification on one of his devices (sending either an
`m.key.verification.ready` or `m.key.verification.cancel` event), Alice will
send an `m.key.verification.cancel` event to Bob's other devices with a `code`
of `m.accepted` in the case where Bob accepted the verification, or `m.user` in
the case where Bob rejected the verification. This yields the following
handshake when using to-device messages, assuming both Alice and Bob each have
2 devices, Bob's first device accepts the key verification request, and Alice's
second device initiates the request. Note how Alice's first device is not
involved in the request or verification process. Also note that, although in
this example, Bob's device sends the `m.key.verification.start`, Alice's device
could also send that message. As well, the order of the
`m.key.verification.done` messages could be reversed.

```
    +---------------+ +---------------+                    +-------------+ +-------------+
    | AliceDevice1  | | AliceDevice2  |                    | BobDevice1  | | BobDevice2  |
    +---------------+ +---------------+                    +-------------+ +-------------+
            |                 |                                   |               |
            |                 | m.key.verification.request        |               |
            |                 |---------------------------------->|               |
            |                 |                                   |               |
            |                 | m.key.verification.request        |               |
            |                 |-------------------------------------------------->|
            |                 |                                   |               |
            |                 |          m.key.verification.ready |               |
            |                 |<----------------------------------|               |
            |                 |                                   |               |
            |                 | m.key.verification.cancel         |               |
            |                 |-------------------------------------------------->|
            |                 |                                   |               |
            |                 |          m.key.verification.start |               |
            |                 |<----------------------------------|               |
            |                 |                                   |               |
            .
            .                       (verification messages)
            .
            |                 |                                   |               |
            |                 |           m.key.verification.done |               |
            |                 |<----------------------------------|               |
            |                 |                                   |               |
            |                 | m.key.verification.done           |               |
            |                 |---------------------------------->|               |
            |                 |                                   |               |
```

When using in-room messages and the room has encryption enabled, clients should
ensure that encryption does not hinder the verification. For example, if the
verification messages are encrypted, clients must ensure that all the
recipient's unverified devices receive the keys necessary to decrypt the
messages, even if they would normally not be given the keys to decrypt messages
in the room. Alternatively, verification messages may be sent unencrypted,
though this is not encouraged.

Upon receipt of Alice's `m.key.verification.request` message, if Bob's device
does not understand any of the methods, it should not cancel the request as one
of his other devices may support the request. Instead, Bob's device should tell
Bob that no supported method was found, and allow him to manually reject the
request.

The prompt for Bob to accept/reject Alice's request (or the unsupported method
prompt) should be automatically dismissed 10 minutes after the `timestamp` (in
the case of to-device messages) or `origin_ts` (in the case of in-room
messages) field or 2 minutes after Bob's client receives the message, whichever
comes first, if Bob does not interact with the prompt. The prompt should
additionally be hidden if an appropriate `m.key.verification.cancel` message is
received.

If Bob rejects the request, Bob's client must send an
`m.key.verification.cancel` event with `code` set to `m.user`. Upon receipt,
Alice's device should tell her that Bob does not want to verify her device and,
if the request was sent as a to-device message, send
`m.key.verification.cancel` messages to all of Bob's devices to notify them
that the request was rejected.

If Alice's and Bob's clients both send an `m.key.verification.start` message,
and both specify the same verification method, then the
`m.key.verification.start` message sent by the user whose ID is the
lexicographically largest user ID should be ignored, and the situation should
be treated the same as if only the user with the lexicographically smallest
user ID had sent the `m.key.verification.start` message.  In the case where the
user IDs are the same (that is, when a user is verifying their own device),
then the device IDs should be compared instead.  If the two
`m.key.verification.start` messages do not specify the same verification
method, then the verification should be cancelled with a `code` of
`m.unexpected_message`.

An `m.key.verification.start` message can also be sent independently of any
request, specifying the verification method to use. This behaviour is
deprecated, and new clients should not begin verifications in this way.
However, clients should handle such verifications started by other clients.

Individual verification methods may add additional steps, events, and
properties to the verification messages. Event types for methods defined
in this specification must be under the `m.key.verification` namespace
and any other event types must be namespaced according to the Java
package naming convention.

{{% event event="m.key.verification.request" %}}

{{% event event="m.key.verification.ready" %}}

{{% event event="m.key.verification.start" %}}

{{% event event="m.key.verification.done" %}}

{{% event event="m.key.verification.cancel" %}}

##### Short Authentication String (SAS) verification

SAS verification is a user-friendly key verification process built off
the common framework outlined above. SAS verification is intended to be
a highly interactive process for users, and as such exposes verification
methods which are easier for users to use.

The verification process is heavily inspired by Phil Zimmermann's ZRTP
key agreement handshake. A key part of key agreement in ZRTP is the hash
commitment: the party that begins the Diffie-Hellman key sharing sends a
hash of their part of the Diffie-Hellman exchange, and does not send
their part of the Diffie-Hellman exchange until they have received the
other party's part. Thus an attacker essentially only has one attempt to
attack the Diffie-Hellman exchange, and hence we can verify fewer bits
while still achieving a high degree of security: if we verify n bits,
then an attacker has a 1 in 2<sup>n</sup> chance of success. For
example, if we verify 40 bits, then an attacker has a 1 in
1,099,511,627,776 chance (or less than 1 in 10<sup>12</sup> chance) of
success. A failed attack would result in a mismatched Short
Authentication String, alerting users to the attack.

To advertise support for this method, clients use the name `m.sas.v1` in the
`methods` fields of the `m.key.verification.request` and
`m.key.verification.ready` events.

The verification process takes place in two phases:

1.  Key agreement phase (based on [ZRTP key
    agreement](https://tools.ietf.org/html/rfc6189#section-4.4.1)).
2.  Key verification phase (based on HMAC).

The process between Alice and Bob verifying each other would be:

1.  Alice and Bob establish a secure out-of-band connection, such as
    meeting in-person or a video call. "Secure" here means that either
    party cannot be impersonated, not explicit secrecy.
2.  Alice and Bob begin a key verification using the key verification
    framework as described above.
3.  Alice's device sends Bob's device an `m.key.verification.start`
    message. Alice's device ensures it has a copy of Bob's device key.
4.  Bob's device receives the message and selects a key agreement
    protocol, hash algorithm, message authentication code, and SAS
    method supported by Alice's device.
5.  Bob's device ensures it has a copy of Alice's device key.
6.  Bob's device creates an ephemeral Curve25519 key pair
    (*K<sub>B</sub><sup>private</sup>*, *K<sub>B</sub><sup>public</sup>*),
    and calculates the hash (using the chosen algorithm) of the public
    key *K<sub>B</sub><sup>public</sup>*.
7.  Bob's device replies to Alice's device with an
    `m.key.verification.accept` message.
8.  Alice's device receives Bob's message and stores the commitment hash
    for later use.
9.  Alice's device creates an ephemeral Curve25519 key pair
    (*K<sub>A</sub><sup>private</sup>*, *K<sub>A</sub><sup>public</sup>*)
    and replies to Bob's device with an `m.key.verification.key`,
    sending only the public key
    *K<sub>A</sub><sup>public</sup>*.
10. Bob's device receives Alice's message and replies with its own
    `m.key.verification.key` message containing its public key
    *K<sub>B</sub><sup>public</sup>*.
11. Alice's device receives Bob's message and verifies the commitment
    hash from earlier matches the hash of the key Bob's device just sent
    and the content of Alice's `m.key.verification.start` message.
12. Both Alice and Bob's devices perform an Elliptic-curve
    Diffie-Hellman
    (*ECDH(K<sub>A</sub><sup>private</sup>*, *K<sub>B</sub><sup>public</sup>*)),
    using the result as the shared secret.
13. Both Alice and Bob's devices display a SAS to their users, which is
    derived from the shared key using one of the methods in this
    section. If multiple SAS methods are available, clients should allow
    the users to select a method.
14. Alice and Bob compare the strings shown by their devices, and tell
    their devices if they match or not.
15. Assuming they match, Alice and Bob's devices calculate the HMAC of
    their own device keys and a comma-separated sorted list of the key
    IDs that they wish the other user to verify, using SHA-256 as the
    hash function. HMAC is defined in [RFC
    2104](https://tools.ietf.org/html/rfc2104). The key for the HMAC is
    different for each item and is calculated by generating 32 bytes
    (256 bits) using [the key verification HKDF](#hkdf-calculation).
16. Alice's device sends Bob's device an `m.key.verification.mac`
    message containing the MAC of Alice's device keys and the MAC of her
    key IDs to be verified. Bob's device does the same for Bob's device
    keys and key IDs concurrently with Alice.
17. When the other device receives the `m.key.verification.mac` message,
    the device calculates the HMAC of its copies of the other device's
    keys given in the message, as well as the HMAC of the
    comma-separated, sorted, list of key IDs in the message. The device
    compares these with the HMAC values given in the message, and if
    everything matches then the device keys are verified.
18. Alice and Bob's devices send `m.key.verification.done` messages to complete
    the verification.

The wire protocol looks like the following between Alice and Bob's
devices:

```
    +-------------+                    +-----------+
    | AliceDevice |                    | BobDevice |
    +-------------+                    +-----------+
          |                                 |
          | m.key.verification.start        |
          |-------------------------------->|
          |                                 |
          |       m.key.verification.accept |
          |<--------------------------------|
          |                                 |
          | m.key.verification.key          |
          |-------------------------------->|
          |                                 |
          |          m.key.verification.key |
          |<--------------------------------|
          |                                 |
          | m.key.verification.mac          |
          |-------------------------------->|
          |                                 |
          |          m.key.verification.mac |
          |<--------------------------------|
          |                                 |
```

###### Error and exception handling

At any point the interactive verification can go wrong. The following
describes what to do when an error happens:

-   Alice or Bob can cancel the verification at any time. An
    `m.key.verification.cancel` message must be sent to signify the
    cancellation.
-   The verification can time out. Clients should time out a
    verification that does not complete within 10 minutes. Additionally,
    clients should expire a `transaction_id` which goes unused for 10
    minutes after having last sent/received it. The client should inform
    the user that the verification timed out, and send an appropriate
    `m.key.verification.cancel` message to the other device.
-   When the same device attempts to initiate multiple verification
    attempts, the recipient should cancel all attempts with that device.
-   When a device receives an unknown `transaction_id`, it should send
    an appropriate `m.key.verification.cancel` message to the other
    device indicating as such. This does not apply for inbound
    `m.key.verification.start` or `m.key.verification.cancel` messages.
-   If the two devices do not share a common key share, hash, HMAC, or
    SAS method then the device should notify the other device with an
    appropriate `m.key.verification.cancel` message.
-   If the user claims the Short Authentication Strings do not match,
    the device should send an appropriate `m.key.verification.cancel`
    message to the other device.
-   If the device receives a message out of sequence or that it was not
    expecting, it should notify the other device with an appropriate
    `m.key.verification.cancel` message.

###### Verification messages specific to SAS

Building off the common framework, the following events are involved in
SAS verification.

The `m.key.verification.cancel` event is unchanged, however the
following error codes are used in addition to those already specified:

-   `m.unknown_method`: The devices are unable to agree on the key
    agreement, hash, MAC, or SAS method.
-   `m.mismatched_commitment`: The hash commitment did not match.
-   `m.mismatched_sas`: The SAS did not match.

{{% event event="m.key.verification.start$m.sas.v1" %}}

{{% event event="m.key.verification.accept" %}}

{{% event event="m.key.verification.key" %}}

{{% event event="m.key.verification.mac" %}}

###### HKDF calculation

In all of the SAS methods, HKDF is as defined in [RFC
5869](https://tools.ietf.org/html/rfc5869) and uses the previously
agreed-upon hash function for the hash function. The shared secret is
supplied as the input keying material. No salt is used. When the
`key_agreement_protocol` is `curve25519-hkdf-sha256`, the info parameter
is the concatenation of:

-   The string `MATRIX_KEY_VERIFICATION_SAS|`.
-   The Matrix ID of the user who sent the `m.key.verification.start`
    message, followed by `|`.
-   The Device ID of the device which sent the
    `m.key.verification.start` message, followed by `|`.
-   The public key from the `m.key.verification.key` message sent by
    the device which sent the `m.key.verification.start` message,
    followed by `|`.
-   The Matrix ID of the user who sent the `m.key.verification.accept`
    message, followed by `|`.
-   The Device ID of the device which sent the
    `m.key.verification.accept` message, followed by `|`.
-   The public key from the `m.key.verification.key` message sent by
    the device which sent the `m.key.verification.accept` message,
    followed by `|`.
-   The `transaction_id` being used.

When the `key_agreement_protocol` is the deprecated method `curve25519`,
the info parameter is the concatenation of:

-   The string `MATRIX_KEY_VERIFICATION_SAS`.
-   The Matrix ID of the user who sent the `m.key.verification.start`
    message.
-   The Device ID of the device which sent the
    `m.key.verification.start` message.
-   The Matrix ID of the user who sent the `m.key.verification.accept`
    message.
-   The Device ID of the device which sent the
    `m.key.verification.accept` message.
-   The `transaction_id` being used.

New implementations are discouraged from implementing the `curve25519`
method.

{{% boxes/rationale %}}
HKDF is used over the plain shared secret as it results in a harder
attack as well as more uniform data to work with.
{{% /boxes/rationale %}}

For verification of each party's device keys, HKDF is as defined in RFC
5869 and uses SHA-256 as the hash function. The shared secret is
supplied as the input keying material. No salt is used, and in the info
parameter is the concatenation of:

-   The string `MATRIX_KEY_VERIFICATION_MAC`.
-   The Matrix ID of the user whose key is being MAC-ed.
-   The Device ID of the device sending the MAC.
-   The Matrix ID of the other user.
-   The Device ID of the device receiving the MAC.
-   The `transaction_id` being used.
-   The Key ID of the key being MAC-ed, or the string `KEY_IDS` if the
    item being MAC-ed is the list of key IDs.

###### SAS method: `decimal`

Generate 5 bytes using [HKDF](#hkdf-calculation) then take sequences of 13 bits
to convert to decimal numbers (resulting in 3 numbers between 0 and 8191
inclusive each). Add 1000 to each calculated number.

The bitwise operations to get the numbers given the 5 bytes
*B<sub>0</sub>*, *B<sub>1</sub>*, *B<sub>2</sub>*, *B<sub>3</sub>*, *B<sub>4</sub>*
would be:

-   First: (*B<sub>0</sub>* ≪ 5|*B<sub>1</sub>* ≫ 3) + 1000
-   Second:
    ((*B<sub>1</sub>*&0x7) ≪ 10|*B<sub>2</sub>* ≪ 2|*B<sub>3</sub>* ≫ 6) + 1000
-   Third: ((*B<sub>3</sub>*&0x3F) ≪ 7|*B<sub>4</sub>* ≫ 1) + 1000

The digits are displayed to the user either with an appropriate
separator, such as dashes, or with the numbers on individual lines.

###### SAS method: `emoji`

Generate 6 bytes using [HKDF](#hkdf-calculation) then split the first 42 bits
into 7 groups of 6 bits, similar to how one would base64 encode
something. Convert each group of 6 bits to a number and use the
following table to get the corresponding emoji:

{{% sas-emojis %}}

{{% boxes/note %}}
This table is available as JSON at
<https://github.com/matrix-org/matrix-doc/blob/master/data-definitions/sas-emoji.json>
{{% /boxes/note %}}

{{% boxes/rationale %}}
The emoji above were chosen to:

-   Be recognisable without colour.
-   Be recognisable at a small size.
-   Be recognisable by most cultures.
-   Be distinguishable from each other.
-   Easily described by a few words.
-   Avoid symbols with negative connotations.
-   Be likely similar across multiple platforms.
{{% /boxes/rationale %}}

Clients SHOULD show the emoji with the descriptions from the table, or
appropriate translation of those descriptions. Client authors SHOULD
collaborate to create a common set of translations for all languages.

{{% boxes/note %}}
Known translations for the emoji are available from
<https://github.com/matrix-org/matrix-doc/blob/master/data-definitions/>
and can be translated online:
<https://translate.riot.im/projects/matrix-doc/sas-emoji-v1>
{{% /boxes/note %}}

##### Cross-signing

Rather than requiring Alice to verify each of Bob's devices with each of
her own devices and vice versa, the cross-signing feature allows users
to sign their device keys such that Alice and Bob only need to verify
once. With cross-signing, each user has a set of cross-signing keys that
are used to sign their own device keys and other users' keys, and can be
used to trust device keys that were not verified directly.

Each user has three ed25519 key pairs for cross-signing:

-   a master key (MSK) that serves as the user's identity in
    cross-signing and signs their other cross-signing keys;
-   a user-signing key (USK) -- only visible to the user that it belongs
    to --that signs other users' master keys; and
-   a self-signing key (SSK) that signs the user's own device keys.

The master key may also be used to sign other items such as the backup
key. The master key may also be signed by the user's own device keys to
aid in migrating from device verifications: if Alice's device had
previously verified Bob's device and Bob's device has signed his master
key, then Alice's device can trust Bob's master key, and she can sign it
with her user-signing key.

Users upload their cross-signing keys to the server using [POST
/\_matrix/client/v3/keys/device\_signing/upload](/client-server-api/#post_matrixclientv3keysdevice_signingupload). When Alice uploads
new cross-signing keys, her user ID will appear in the `changed`
property of the `device_lists` field of the `/sync` of response of all
users who share an encrypted room with her. When Bob sees Alice's user
ID in his `/sync`, he will call [POST /\_matrix/client/v3/keys/query](/client-server-api/#post_matrixclientv3keysquery)
to retrieve Alice's device and cross-signing keys.

If Alice has a device and wishes to send an encrypted message to Bob,
she can trust Bob's device if:

-   Alice's device is using a master key that has signed her
    user-signing key,
-   Alice's user-signing key has signed Bob's master key,
-   Bob's master key has signed Bob's self-signing key, and
-   Bob's self-signing key has signed Bob's device key.

The following diagram illustrates how keys are signed:

```
    +------------------+                ..................   +----------------+
    | +--------------+ |   ..................            :   | +------------+ |
    | |              v v   v            :   :            v   v v            | |
    | |           +-----------+         :   :         +-----------+         | |
    | |           | Alice MSK |         :   :         |  Bob MSK  |         | |
    | |           +-----------+         :   :         +-----------+         | |
    | |             |       :           :   :           :       |           | |
    | |          +--+       :...        :   :        ...:       +--+        | |
    | |          v             v        :   :        v             v        | |
    | |    +-----------+ .............  :   :  ............. +-----------+  | |
    | |    | Alice SSK | : Alice USK :  :   :  :  Bob USK  : |  Bob SSK  |  | |
    | |    +-----------+ :...........:  :   :  :...........: +-----------+  | |
    | |      |  ...  |         :        :   :        :         |  ...  |    | |
    | |      V       V         :........:   :........:         V       V    | |
    | | +---------+   -+                                  +---------+   -+  | |
    | | | Devices | ...|                                  | Devices | ...|  | |
    | | +---------+   -+                                  +---------+   -+  | |
    | |      |  ...  |                                         |  ...  |    | |
    | +------+       |                                         |       +----+ |
    +----------------+                                         +--------------+
```

In the diagram, boxes represent keys and lines represent signatures with
the arrows pointing from the signing key to the key being signed. Dotted
boxes and lines represent keys and signatures that are only visible to
the user who created them.

The following diagram illustrates Alice's view, hiding the keys and
signatures that she cannot see:

```
    +------------------+                +----------------+   +----------------+
    | +--------------+ |                |                |   | +------------+ |
    | |              v v                |                v   v v            | |
    | |           +-----------+         |             +-----------+         | |
    | |           | Alice MSK |         |             |  Bob MSK  |         | |
    | |           +-----------+         |             +-----------+         | |
    | |             |       |           |                       |           | |
    | |          +--+       +--+        |                       +--+        | |
    | |          v             v        |                          v        | |
    | |    +-----------+ +-----------+  |                    +-----------+  | |
    | |    | Alice SSK | | Alice USK |  |                    |  Bob SSK  |  | |
    | |    +-----------+ +-----------+  |                    +-----------+  | |
    | |      |  ...  |         |        |                      |  ...  |    | |
    | |      V       V         +--------+                      V       V    | |
    | | +---------+   -+                                  +---------+   -+  | |
    | | | Devices | ...|                                  | Devices | ...|  | |
    | | +---------+   -+                                  +---------+   -+  | |
    | |      |  ...  |                                         |  ...  |    | |
    | +------+       |                                         |       +----+ |
    +----------------+                                         +--------------+
```

[Verification methods](#device-verification) can be used to verify a
user's master key by using the master public key, encoded using unpadded
base64, as the device ID, and treating it as a normal device. For
example, if Alice and Bob verify each other using SAS, Alice's
`m.key.verification.mac` message to Bob may include
`"ed25519:alices+master+public+key": "alices+master+public+key"` in the
`mac` property. Servers therefore must ensure that device IDs will not
collide with cross-signing public keys.

The cross-signing private keys can be stored on the server or shared with other
devices using the [Secrets](#secrets) module.  When doing so, the master,
user-signing, and self-signing keys are identified using the names
`m.cross_signing.master`, `m.cross_signing.user_signing`, and
`m.cross_signing.self_signing`, respectively, and the keys are base64-encoded
before being encrypted.

###### Key and signature security

A user's master key could allow an attacker to impersonate that user to
other users, or other users to that user. Thus clients must ensure that
the private part of the master key is treated securely. If clients do
not have a secure means of storing the master key (such as a secret
storage system provided by the operating system), then clients must not
store the private part.

If a user's client sees that any other user has changed their master
key, that client must notify the user about the change before allowing
communication between the users to continue.

A user's user-signing and self-signing keys are intended to be easily
replaceable if they are compromised by re-issuing a new key signed by
the user's master key and possibly by re-verifying devices or users.
However, doing so relies on the user being able to notice when their
keys have been compromised, and it involves extra work for the user, and
so although clients do not have to treat the private parts as
sensitively as the master key, clients should still make efforts to
store the private part securely, or not store it at all. Clients will
need to balance the security of the keys with the usability of signing
users and devices when performing key verification.

To avoid leaking of social graphs, servers will only allow users to see:

-   signatures made by the user's own master, self-signing or
    user-signing keys,
-   signatures made by the user's own devices about their own master
    key,
-   signatures made by other users' self-signing keys about their
    respective devices,
-   signatures made by other users' master keys about their respective
    self-signing key, or
-   signatures made by other users' devices about their respective
    master keys.

Users will not be able to see signatures made by other users'
user-signing keys.

{{% http-api spec="client-server" api="cross_signing" %}}

##### QR codes

{{% added-in v="1.1" %}}

Verifying by QR codes provides a quick way to verify when one of the parties
has a device capable of scanning a QR code. The QR code encodes both parties'
master signing keys as well as a random shared secret that is used to allow
bi-directional verification from a single scan.

To advertise the ability to show a QR code, clients use the names
`m.qr_code.show.v1` and `m.reciprocate.v1` in the `methods` fields of the
`m.key.verification.request` and `m.key.verification.ready` events. To
advertise the ability to scan a QR code, clients use the names
`m.qr_code.scan.v1` and `m.reciprocate.v1` in the `methods` fields of the
`m.key.verification.request` and `m.key.verification.ready` events.
Clients that support both showing and scanning QR codes would advertise
`m.qr_code.show.v1`, `m.qr_code.scan.v1`, and `m.reciprocate.v1` as
methods.

The process between Alice and Bob verifying each other would be:

1. Alice and Bob meet in person, and want to verify each other's keys.
2. Alice and Bob begin a key verification using the key verification
   framework as described above.
3. Alice's client displays a QR code that Bob is able to scan if Bob's client
   indicated the ability to scan, an option to scan Bob's QR code if her client
   is able to scan.  Bob's client prompts displays a QR code that Alice can
   scan if Alice's client indicated the ability to scan, and an option to scan
   Alice's QR code if his client is able to scan. The format for the QR code
   is described below. Other options, like starting SAS Emoji verification,
   can be presented alongside the QR code if the devices have appropriate
   support.
5. Alice scans Bob's QR code.
6. Alice's device ensures that the keys encoded in the QR code match the
   expected values for the keys. If not, Alice's device displays an error
   message indicating that the code is incorrect, and sends a
   `m.key.verification.cancel` message to Bob's device.

   Otherwise, at this point:
   - Alice's device has now verified Bob's key, and
   - Alice's device knows that Bob has the correct key for her.

   Thus for Bob to verify Alice's key, Alice needs to tell Bob that he has the
   right key.
7. Alice's device displays a message saying that the verification was
   successful because the QR code's keys will have matched the keys
   expected for Bob. Bob's device hasn't had a chance to verify Alice's
   keys yet so wouldn't show the same message. Bob will know that
   he has the right key for Alice because Alice's device will have shown
   this message, as otherwise the verification would be cancelled.
8. Alice's device sends an `m.key.verification.start` message with `method` set
   to `m.reciprocate.v1` to Bob (see below).  The message includes the shared
   secret from the QR code.  This signals to Bob's device that Alice has
   scanned Bob's QR code.

   This message is merely a signal for Bob's device to proceed to the next
   step, and is not used for verification purposes.
9. Upon receipt of the `m.key.verification.start` message, Bob's device ensures
   that the shared secret matches.

   If the shared secret does not match, it should display an error message
   indicating that an attack was attempted.  (This does not affect Alice's
   verification of Bob's keys.)

   If the shared secret does match, it asks Bob to confirm that Alice
   has scanned the QR code.
10. Bob sees Alice's device confirm that the key matches, and presses the button
    on his device to indicate that Alice's key is verified.

    Bob's verification of Alice's key hinges on Alice telling Bob the result of
    her scan.  Since the QR code includes what Bob thinks Alice's key is,
    Alice's device can check whether Bob has the right key for her.  Alice has
    no motivation to lie about the result, as getting Bob to trust an incorrect
    key would only affect communications between herself and Bob.  Thus Alice
    telling Bob that the code was scanned successfully is sufficient for Bob to
    trust Alice's key, under the assumption that this communication is done
    over a trusted medium (such as in-person).
11. Both devices send an `m.key.verification.done` message.

###### QR code format

The QR codes to be displayed and scanned using this format will encode binary
strings in the general form:

- the ASCII string `MATRIX`
- one byte indicating the QR code version (must be `0x02`)
- one byte indicating the QR code verification mode.  Should be one of the
  following values:
  - `0x00` verifying another user with cross-signing
  - `0x01` self-verifying in which the current device does trust the master key
  - `0x02` self-verifying in which the current device does not yet trust the
    master key
- the event ID or `transaction_id` of the associated verification
  request event, encoded as:
  - two bytes in network byte order (big-endian) indicating the length in
    bytes of the ID as a UTF-8 string
  - the ID as a UTF-8 string
- the first key, as 32 bytes.  The key to use depends on the mode field:
  - if `0x00` or `0x01`, then the current user's own master cross-signing public key
  - if `0x02`, then the current device's device key
- the second key, as 32 bytes.  The key to use depends on the mode field:
  - if `0x00`, then what the device thinks the other user's master
    cross-signing key is
  - if `0x01`, then what the device thinks the other device's device key is
  - if `0x02`, then what the device thinks the user's master cross-signing key
    is
- a random shared secret, as a byte string.  It is suggested to use a secret
  that is about 8 bytes long.  Note: as we do not share the length of the
  secret, and it is not a fixed size, clients will just use the remainder of
  binary string as the shared secret.

For example, if Alice displays a QR code encoding the following binary string:

```
      "MATRIX"    |ver|mode| len   | event ID
 4D 41 54 52 49 58  02  00   00 2D   21 41 42 43 44 ...
| user's cross-signing key    | other user's cross-signing key | shared secret
  00 01 02 03 04 05 06 07 ...   10 11 12 13 14 15 16 17 ...      20 21 22 23 24 25 26 27
```

this indicates that Alice is verifying another user (say Bob), in response to
the request from event "$ABCD...", her cross-signing key is
`0001020304050607...` (which is "AAECAwQFBg..." in base64), she thinks that
Bob's cross-signing key is `1011121314151617...` (which is "EBESExQVFh..." in
base64), and the shared secret is `2021222324252627` (which is "ICEiIyQlJic" in
base64).

###### Verification messages specific to QR codes

{{% event event="m.key.verification.start$m.reciprocate.v1" %}}

#### Sharing keys between devices

If Bob has an encrypted conversation with Alice on his computer, and
then logs in through his phone for the first time, he may want to have
access to the previously exchanged messages. To address this issue,
several methods are provided to allow users to transfer keys from one
device to another.

##### Key requests

When a device is missing keys to decrypt messages, it can request the
keys by sending [m.room\_key\_request](#mroom_key_request) to-device messages to other
devices with `action` set to `request`.

If a device wishes to share the keys with that device, it can forward
the keys to the first device by sending an encrypted
[m.forwarded\_room\_key](#mforwarded_room_key) to-device message. The first device should
then send an [m.room\_key\_request](#mroom_key_request) to-device message with `action`
set to `request_cancellation` to the other devices that it had
originally sent the key request to; a device that receives a
`request_cancellation` should disregard any previously-received
`request` message with the same `request_id` and `requesting_device_id`.

If a device does not wish to share keys with that device, it can
indicate this by sending an [m.room\_key.withheld](#mroom_key.withheld) to-device message,
as described in [Reporting that decryption keys are
withheld](#reporting-that-decryption-keys-are-withheld).

{{% boxes/note %}}
Key sharing can be a big attack vector, thus it must be done very
carefully. A reasonable strategy is for a user's client to only send
keys requested by the verified devices of the same user.
{{% /boxes/note %}}

##### Server-side key backups

Devices may upload encrypted copies of keys to the server. When a device
tries to read a message that it does not have keys for, it may request
the key from the server and decrypt it. Backups are per-user, and users
may replace backups with new backups.

In contrast with [Key requests](#key-requests), Server-side key backups
do not require another device to be online from which to request keys.
However, as the session keys are stored on the server encrypted, it
requires users to enter a decryption key to decrypt the session keys.

To create a backup, a client will call [POST
/\_matrix/client/v3/room\_keys/version](#post_matrixclientv3room_keysversion) and define how the keys are to
be encrypted through the backup's `auth_data`; other clients can
discover the backup by calling [GET
/\_matrix/client/v3/room\_keys/version](#get_matrixclientv3room_keysversion). Keys are encrypted according
to the backup's `auth_data` and added to the backup by calling [PUT
/\_matrix/client/v3/room\_keys/keys](#put_matrixclientv3room_keyskeys) or one of its variants, and can
be retrieved by calling [GET /\_matrix/client/v3/room\_keys/keys](#get_matrixclientv3room_keyskeys) or
one of its variants. Keys can only be written to the most recently
created version of the backup. Backups can also be deleted using [DELETE
/\_matrix/client/v3/room\_keys/version/{version}](#delete_matrixclientv3room_keysversionversion), or individual keys
can be deleted using [DELETE /\_matrix/client/v3/room\_keys/keys](#delete_matrixclientv3room_keyskeys) or
one of its variants.

Clients must only store keys in backups after they have ensured that the
`auth_data` is trusted, either by checking the signatures on it, or by
deriving the public key from a private key that it obtained from a
trusted source.

When a client uploads a key for a session that the server already has a
key for, the server will choose to either keep the existing key or
replace it with the new key based on the key metadata as follows:

-   if the keys have different values for `is_verified`, then it will
    keep the key that has `is_verified` set to `true`;
-   if they have the same values for `is_verified`, then it will keep
    the key with a lower `first_message_index`;
-   and finally, is `is_verified` and `first_message_index` are equal,
    then it will keep the key with a lower `forwarded_count`.

###### Recovery key

If the recovery key (the private half of the backup encryption key) is
presented to the user to save, it is presented as a string constructed
as follows:

1.  The 256-bit curve25519 private key is prepended by the bytes `0x8B`
    and `0x01`
2.  All the bytes in the string above, including the two header bytes,
    are XORed together to form a parity byte. This parity byte is
    appended to the byte string.
3.  The byte string is encoded using base58, using the same [mapping as
    is used for Bitcoin
    addresses](https://en.bitcoin.it/wiki/Base58Check_encoding#Base58_symbol_chart),
    that is, using the alphabet
    `123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz`.
4.  A space should be added after every 4th character.

When reading in a recovery key, clients must disregard whitespace, and
perform the reverse of steps 1 through 3.

The recovery key can also be stored on the server or shared with other devices
using the [Secrets](#secrets) module. When doing so, it is identified using the
name `m.megolm_backup.v1`, and the key is base64-encoded before being
encrypted.

###### Backup algorithm: `m.megolm_backup.v1.curve25519-aes-sha2`

When a backup is created with the `algorithm` set to
`m.megolm_backup.v1.curve25519-aes-sha2`, the `auth_data` should have
the following format:

`AuthData`

| Parameter  | Type       | Description                                                                                      |
| -----------| -----------|--------------------------------------------------------------------------------------------------|
| public_key | string     | **Required.** The curve25519 public key used to encrypt the backups, encoded in unpadded base64. |
| signatures | Signatures | Optional. Signatures of the ``auth_data``, as Signed JSON                                        |

The `session_data` field in the backups is constructed as follows:

1.  Encode the session key to be backed up as a JSON object with the
    properties:

| Parameter                       | Type              | Description                                                                                                                                                                 |
| --------------------------------|-------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| algorithm                       | string            | **Required.** The end-to-end message encryption algorithm that the key is for.  Must be `m.megolm.v1.aes-sha2`.                                                             |
| forwarding_curve25519_key_chain | [string]          | **Required.** Chain of Curve25519 keys through which this session was forwarded, via [m.forwarded_room_key](#mforwarded_room_key) events.                                   |
| sender_key                      | string            | **Required.** Unpadded base64-encoded device curve25519 key.                                                                                                                |
| sender_claimed_keys             | {string: string}  | **Required.** A map from algorithm name (`ed25519`) to the identity key for the sending device.                                                                             |
| session_key                     | string            | **Required.** Unpadded base64-encoded session key in [session-sharing format](https://gitlab.matrix.org/matrix-org/olm/blob/master/docs/megolm.md#session-sharing-format).  |

2.  Generate an ephemeral curve25519 key, and perform an ECDH with the
    ephemeral key and the backup's public key to generate a shared
    secret. The public half of the ephemeral key, encoded using unpadded
    base64, becomes the `ephemeral` property of the `session_data`.

3.  Using the shared secret, generate 80 bytes by performing an HKDF
    using SHA-256 as the hash, with a salt of 32 bytes of 0, and with
    the empty string as the info. The first 32 bytes are used as the AES
    key, the next 32 bytes are used as the MAC key, and the last 16
    bytes are used as the AES initialization vector.

4.  Stringify the JSON object, and encrypt it using AES-CBC-256 with
    PKCS\#7 padding. This encrypted data, encoded using unpadded base64,
    becomes the `ciphertext` property of the `session_data`.

5.  Pass the raw encrypted data (prior to base64 encoding) through
    HMAC-SHA-256 using the MAC key generated above. The first 8 bytes of
    the resulting MAC are base64-encoded, and become the `mac` property
    of the `session_data`.

{{% http-api spec="client-server" api="key_backup" %}}

##### Key exports

Keys can be manually exported from one device to an encrypted file,
copied to another device, and imported. The file is encrypted using a
user-supplied passphrase, and is created as follows:

1.  Encode the sessions as a JSON object, formatted as described in [Key
    export format](#key-export-format).

2.  Generate a 512-bit key from the user-entered passphrase by computing
    [PBKDF2](https://tools.ietf.org/html/rfc2898#section-5.2)(HMAC-SHA-512,
    passphrase, S, N, 512), where S is a 128-bit
    cryptographically-random salt and N is the number of rounds. N
    should be at least 100,000. The keys K and K' are set to the first
    and last 256 bits of this generated key, respectively. K is used as
    an AES-256 key, and K' is used as an HMAC-SHA-256 key.

3.  Serialize the JSON object as a UTF-8 string, and encrypt it using
    AES-CTR-256 with the key K generated above, and with a 128-bit
    cryptographically-random initialization vector, IV, that has bit 63
    set to zero. (Setting bit 63 to zero in IV is needed to work around
    differences in implementations of AES-CTR.)

4.  Concatenate the following data:

| Size (bytes)| Description                                                                             |
| ------------|-----------------------------------------------------------------------------------------|
| 1           | Export format version, which must be `0x01`.                                            |
| 16          | The salt S.                                                                             |
| 16          | The initialization vector IV.                                                           |
| 4           | The number of rounds N, as a big-endian unsigned 32-bit integer.                        |
| variable    | The encrypted JSON object.                                                              |
| 32          | The HMAC-SHA-256 of all the above string concatenated together, using K' as the key.    |

5.  Base64-encode the string above. Newlines may be added to avoid
    overly long lines.

6.  Prepend the resulting string with
    `-----BEGIN MEGOLM SESSION DATA-----`, with a trailing newline, and
    append `-----END MEGOLM SESSION DATA-----`, with a leading and
    trailing newline.

###### Key export format

The exported sessions are formatted as a JSON array of `SessionData`
objects described as follows:

`SessionData`

| Parameter                         | Type             | Description                                                                                                                           |
|-----------------------------------|------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| algorithm                         | string           | Required. The encryption algorithm that the session uses. Must be `m.megolm.v1.aes-sha2`.                                             |
| forwarding_curve25519_key_chain   | [string]         | Required. Chain of Curve25519 keys through which this session was forwarded, via [m.forwarded_room_key](#mforwarded_room_key) events. |
| room_id                           | string           | Required. The room where the session is used.                                                                                         |
| sender_key                        | string           | Required. The Curve25519 key of the device which initiated the session originally.                                                    |
| sender_claimed_keys               | {string: string} | Required. The Ed25519 key of the device which initiated the session originally.                                                       |
| session_id                        | string           | Required. The ID of the session.                                                                                                      |
| session_key                       | string           | Required. The key for the session.                                                                                                    |

This is similar to the format before encryption used for the session
keys in [Server-side key backups](#server-side-key-backups) but adds the
`room_id` and `session_id` fields.

Example:

```
[
    {
        "algorithm": "m.megolm.v1.aes-sha2",
        "forwarding_curve25519_key_chain": [
            "hPQNcabIABgGnx3/ACv/jmMmiQHoeFfuLB17tzWp6Hw"
        ],
        "room_id": "!Cuyf34gef24t:localhost",
        "sender_key": "RF3s+E7RkTQTGF2d8Deol0FkQvgII2aJDf3/Jp5mxVU",
        "sender_claimed_keys": {
            "ed25519": "<device ed25519 identity key>",
        },
        "session_id": "X3lUlvLELLYxeTx4yOVu6UDpasGEVO0Jbu+QFnm0cKQ",
        "session_key": "AgAAAADxKHa9uFxcXzwYoNueL5Xqi69IkD4sni8Llf..."
    },
    ...
]
```

#### Messaging Algorithms

##### Messaging Algorithm Names

Messaging algorithm names use the extensible naming scheme used
throughout this specification. Algorithm names that start with `m.` are
reserved for algorithms defined by this specification. Implementations
wanting to experiment with new algorithms must be uniquely globally
namespaced following Java's package naming conventions.

Algorithm names should be short and meaningful, and should list the
primitives used by the algorithm so that it is easier to see if the
algorithm is using a broken primitive.

A name of `m.olm.v1` is too short: it gives no information about the
primitives in use, and is difficult to extend for different primitives.
However a name of
`m.olm.v1.ecdh-curve25519-hdkfsha256.hmacsha256.hkdfsha256-aes256-cbc-hmac64sha256`
is too long despite giving a more precise description of the algorithm:
it adds to the data transfer overhead and sacrifices clarity for human
readers without adding any useful extra information.

##### `m.olm.v1.curve25519-aes-sha2`

The name `m.olm.v1.curve25519-aes-sha2` corresponds to version 1 of the
Olm ratchet, as defined by the [Olm
specification](http://matrix.org/docs/spec/olm.html). This uses:

-   Curve25519 for the initial key agreement.
-   HKDF-SHA-256 for ratchet key derivation.
-   Curve25519 for the root key ratchet.
-   HMAC-SHA-256 for the chain key ratchet.
-   HKDF-SHA-256, AES-256 in CBC mode, and 8 byte truncated HMAC-SHA-256
    for authenticated encryption.

Devices that support Olm must include "m.olm.v1.curve25519-aes-sha2" in
their list of supported messaging algorithms, must list a Curve25519
device key, and must publish Curve25519 one-time keys.

An event encrypted using Olm has the following format:

```json
{
  "type": "m.room.encrypted",
  "content": {
    "algorithm": "m.olm.v1.curve25519-aes-sha2",
    "sender_key": "<sender_curve25519_key>",
    "ciphertext": {
      "<device_curve25519_key>": {
        "type": 0,
        "body": "<encrypted_payload_base_64>"
      }
    }
  }
}
```

`ciphertext` is a mapping from device Curve25519 key to an encrypted
payload for that device. `body` is a Base64-encoded Olm message body.
`type` is an integer indicating the type of the message body: 0 for the
initial pre-key message, 1 for ordinary messages.

Olm sessions will generate messages with a type of 0 until they receive
a message. Once a session has decrypted a message it will produce
messages with a type of 1.

When a client receives a message with a type of 0 it must first check if
it already has a matching session. If it does then it will use that
session to try to decrypt the message. If there is no existing session
then the client must create a new session and use the new session to
decrypt the message. A client must not persist a session or remove
one-time keys used by a session until it has successfully decrypted a
message using that session.

Messages with type 1 can only be decrypted with an existing session. If
there is no matching session, the client must treat this as an invalid
message.

The plaintext payload is of the form:

```json
{
  "type": "<type of the plaintext event>",
  "content": "<content for the plaintext event>",
  "sender": "<sender_user_id>",
  "recipient": "<recipient_user_id>",
  "recipient_keys": {
    "ed25519": "<our_ed25519_key>"
  },
  "keys": {
    "ed25519": "<sender_ed25519_key>"
  }
}
```

The type and content of the plaintext message event are given in the
payload.

Other properties are included in order to prevent an attacker from
publishing someone else's curve25519 keys as their own and subsequently
claiming to have sent messages which they didn't. `sender` must
correspond to the user who sent the event, `recipient` to the local
user, and `recipient_keys` to the local ed25519 key.

Clients must confirm that the `sender_key` and the `ed25519` field value
under the `keys` property match the keys returned by [`/keys/query`](/client-server-api/#post_matrixclientv3keysquery) for
the given user, and must also verify the signature of the keys from the
`/keys/query` response. Without this check, a client cannot be sure that
the sender device owns the private part of the ed25519 key it claims to
have in the Olm payload. This is crucial when the ed25519 key corresponds
to a verified device.

If a client has multiple sessions established with another device, it
should use the session from which it last received and successfully
decrypted a message. For these purposes, a session that has not received
any messages should use its creation time as the time that it last
received a message. A client may expire old sessions by defining a
maximum number of olm sessions that it will maintain for each device,
and expiring sessions on a Least Recently Used basis. The maximum number
of olm sessions maintained per device should be at least 4.

###### Recovering from undecryptable messages

Occasionally messages may be undecryptable by clients due to a variety
of reasons. When this happens to an Olm-encrypted message, the client
should assume that the Olm session has become corrupted and create a new
one to replace it.

{{% boxes/note %}}
Megolm-encrypted messages generally do not have the same problem.
Usually the key for an undecryptable Megolm-encrypted message will come
later, allowing the client to decrypt it successfully. Olm does not have
a way to recover from the failure, making this session replacement
process required.
{{% /boxes/note %}}

To establish a new session, the client sends an [m.dummy](#mdummy)
to-device event to the other party to notify them of the new session
details.

Clients should rate-limit the number of sessions it creates per device
that it receives a message from. Clients should not create a new session
with another device if it has already created one for that given device
in the past 1 hour.

Clients should attempt to mitigate loss of the undecryptable messages.
For example, Megolm sessions that were sent using the old session would
have been lost. The client can attempt to retrieve the lost sessions
through `m.room_key_request` messages.

##### `m.megolm.v1.aes-sha2`

The name `m.megolm.v1.aes-sha2` corresponds to version 1 of the Megolm
ratchet, as defined by the [Megolm
specification](http://matrix.org/docs/spec/megolm.html). This uses:

-   HMAC-SHA-256 for the hash ratchet.
-   HKDF-SHA-256, AES-256 in CBC mode, and 8 byte truncated HMAC-SHA-256
    for authenticated encryption.
-   Ed25519 for message authenticity.

Devices that support Megolm must support Olm, and include
"m.megolm.v1.aes-sha2" in their list of supported messaging algorithms.

An event encrypted using Megolm has the following format:

```json
{
  "type": "m.room.encrypted",
  "content": {
    "algorithm": "m.megolm.v1.aes-sha2",
    "sender_key": "<sender_curve25519_key>",
    "device_id": "<sender_device_id>",
    "session_id": "<outbound_group_session_id>",
    "ciphertext": "<encrypted_payload_base_64>"
  }
}
```

The encrypted payload can contain any message event. The plaintext is of
the form:

```json
{
  "type": "<event_type>",
  "content": "<event_content>",
  "room_id": "<the room_id>"
}
```

We include the room ID in the payload, because otherwise the homeserver
would be able to change the room a message was sent in.

Clients must guard against replay attacks by keeping track of the
ratchet indices of Megolm sessions. They should reject messages with a
ratchet index that they have already decrypted. Care should be taken in
order to avoid false positives, as a client may decrypt the same event
twice as part of its normal processing.

As with Olm events, clients must confirm that the `sender_key` belongs
to the user who sent the message. The same reasoning applies, but the
sender ed25519 key has to be inferred from the `keys.ed25519` property
of the event which established the Megolm session.

In order to enable end-to-end encryption in a room, clients can send an
`m.room.encryption` state event specifying `m.megolm.v1.aes-sha2` as its
`algorithm` property.

When creating a Megolm session in a room, clients must share the
corresponding session key using Olm with the intended recipients, so
that they can decrypt future messages encrypted using this session. An
`m.room_key` event is used to do this. Clients must also handle
`m.room_key` events sent by other devices in order to decrypt their
messages.

#### Protocol definitions

##### Events

{{% event event="m.room.encryption" %}}

{{% event event="m.room.encrypted" %}}

{{% event event="m.room_key" %}}

{{% event event="m.room_key_request" %}}

{{% event event="m.forwarded_room_key" %}}

{{% event event="m.dummy" %}}

##### Key management API

{{% http-api spec="client-server" api="keys" %}}

##### Extensions to /sync

This module adds an optional `device_lists` property to the [`/sync`](/client-server-api/#get_matrixclientv3sync)  response,
as specified below. The server need only populate this property for an
incremental `/sync` (i.e., one where the `since` parameter was
specified). The client is expected to use [`/keys/query`](/client-server-api/#post_matrixclientv3keysquery) or
[`/keys/changes`](/client-server-api/#get_matrixclientv3keyschanges) for the equivalent functionality after an initial
sync, as documented in [Tracking the device list for a
user](#tracking-the-device-list-for-a-user).

It also adds a `one_time_keys_count` property. Note the spelling
difference with the `one_time_key_counts` property in the
[`/keys/upload`](/client-server-api/#post_matrixclientv3keysupload) response.


{{% added-in v="1.2" %}} Finally, a `device_unused_fallback_key_types` property
is added to list the key algorithms where the device has a fallback key that
*has not* been used in a [`/keys/claim`](/client-server-api/#post_matrixclientv3keysclaim)
response. When a previously uploaded fallback key's algorithm is missing
from this list, the device should upload a replacement key alongside any
necessary one-time keys to avoid the fallback key's further usage. This
property is required for inclusion, though previous versions of the
specification did not have it. In addition to `/versions`, this can be
a way to identify the server's support for fallback keys.


| Parameter                        | Type               | Description                                                                                                            |
|----------------------------------|--------------------|------------------------------------------------------------------------------------------------------------------------|
| device_lists                     | DeviceLists        | Optional. Information on e2e device updates. Note: only present on an incremental sync.                                |
| device_one_time_keys_count       | {string: integer}  | Optional. For each key algorithm, the number of unclaimed one-time keys currently held on the server for this device.  If an algorithm is unlisted, the count for that algorithm is assumed to be zero.  If this entire parameter is missing, the count for all algorithms is assumed to be zero.  |
| device_unused_fallback_key_types | [string]           | **Required.** The unused fallback key algorithms.                                                                      |

`DeviceLists`

| Parameter  | Type      | Description                                                                                                                                                      |
|------------|-----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| changed    | [string]  | List of users who have updated their device identity or cross-signing keys, or who now share an encrypted room with the client since the previous sync response. |
| left       | [string]  | List of users with whom we do not share any encrypted rooms anymore since the previous sync response.                                                            |

{{% boxes/note %}}
For optimal performance, Alice should be added to `changed` in Bob's
sync only when she updates her devices or cross-signing keys, or when
Alice and Bob now share a room but didn't share any room previously.
However, for the sake of simpler logic, a server may add Alice to
`changed` when Alice and Bob share a new room, even if they previously
already shared a room.
{{% /boxes/note %}}

Example response:

```json
{
  "next_batch": "s72595_4483_1934",
  "rooms": {"leave": {}, "join": {}, "invite": {}},
  "device_lists": {
    "changed": [
       "@alice:example.com",
    ],
    "left": [
       "@bob:example.com",
    ],
  },
  "device_one_time_keys_count": {
    "curve25519": 10,
    "signed_curve25519": 20
  }
}
```

#### Reporting that decryption keys are withheld

When sending an encrypted event to a room, a client can optionally
signal to other devices in that room that it is not sending them the
keys needed to decrypt the event. In this way, the receiving client can
indicate to the user why it cannot decrypt the event, rather than just
showing a generic error message.

In the same way, when one device requests keys from another using [Key
requests](#key-requests), the device from which the key is being
requested may want to tell the requester that it is purposely not
sharing the key.

If Alice withholds a megolm session from Bob for some messages in a
room, and then later on decides to allow Bob to decrypt later messages,
she can send Bob the megolm session, ratcheted up to the point at which
she allows Bob to decrypt the messages. If Bob logs into a new device
and uses key sharing to obtain the decryption keys, the new device will
be sent the megolm sessions that have been ratcheted up. Bob's old
device can include the reason that the session was initially not shared
by including a `withheld` property in the `m.forwarded_room_key` message
that is an object with the `code` and `reason` properties from the
`m.room_key.withheld` message.

{{% event event="m.room_key.withheld" %}}
