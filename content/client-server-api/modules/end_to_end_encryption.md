---
type: module
weight: 100
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

One-time keys are also uploaded to the homeserver using the
[`/keys/upload`](/client-server-api/#post_matrixclientv3keysupload) API.

Devices must store the private part of each key they upload. They can
discard the private part of a one-time key when they receive a message
using that key. However it's possible that a one-time key given out by a
homeserver will never be used, so the device that generates the key will
never know that it can discard the key. Therefore a device could end up
trying to store too many private keys. A device that is trying to store
too many private keys may discard keys starting with the oldest.

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

##### Claiming one-time keys

A client wanting to set up a session with another device can claim a
one-time key for that device. This is done by making a request to the
[`/keys/claim`](/client-server-api/#post_matrixclientv3keysclaim) API.

A homeserver should rate-limit the number of one-time keys that a given
user or remote server can claim. A homeserver should discard the public
part of a one time key once it has given that key to another user.

##### Cross-signing

Verification is essential in ensuring that events can only be seen by
the intended recipients. The [events spec](/events/#device-verification)
defines how Alice and Bob can verify their devices interactively.

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
/\_matrix/client/r0/keys/device\_signing/upload](/client-server-api/#post_matrixclientv3keysdevice_signingupload). When Alice uploads
new cross-signing keys, her user ID will appear in the `changed`
property of the `device_lists` field of the `/sync` of response of all
users who share an encrypted room with her. When Bob sees Alice's user
ID in his `/sync`, he will call [POST /\_matrix/client/r0/keys/query](/client-server-api/#post_matrixclientv3keysquery)
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
/\_matrix/client/r0/room\_keys/version](#post_matrixclientv3room_keysversion) and define how the keys are to
be encrypted through the backup's `auth_data`; other clients can
discover the backup by calling [GET
/\_matrix/client/r0/room\_keys/version](#get_matrixclientv3room_keysversion). Keys are encrypted according
to the backup's `auth_data` and added to the backup by calling [PUT
/\_matrix/client/r0/room\_keys/keys](#put_matrixclientv3room_keyskeys) or one of its variants, and can
be retrieved by calling [GET /\_matrix/client/r0/room\_keys/keys](#get_matrixclientv3room_keyskeys) or
one of its variants. Keys can only be written to the most recently
created version of the backup. Backups can also be deleted using [DELETE
/\_matrix/client/r0/room\_keys/version/{version}](#delete_matrixclientv3room_keysversionversion), or individual keys
can be deleted using [DELETE /\_matrix/client/r0/room\_keys/keys](#delete_matrixclientv3room_keyskeys) or
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

#### Protocol definitions

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

| Parameter                  | Type               | Description                                                                                                            |
|----------------------------|--------------------|------------------------------------------------------------------------------------------------------------------------|
| device_lists               | DeviceLists        | Optional. Information on e2e device updates. Note: only present on an incremental sync.                                |
| device_one_time_keys_count | {string: integer}  | Optional. For each key algorithm, the number of unclaimed one-time keys currently held on the server for this device.  |

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
