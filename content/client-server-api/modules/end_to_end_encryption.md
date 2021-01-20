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
32-byte Ed25519 public key, encoded using [unpadded Base64](). Example:

    "SogYyrkTldLz0BXP+GYWs0qaYacUI0RleEqNT8J3riQ"

The name `curve25519` corresponds to the
[Curve25519](https://cr.yp.to/ecdh.html) ECDH algorithm. The key is a
32-byte Curve25519 public key, encoded using [unpadded Base64]().
Example:

    "JGLn/yafz74HB2AbPLYJWIVGnKAtqECOBf11yyXac2Y"

The name `signed_curve25519` also corresponds to the Curve25519
algorithm, but a key using this algorithm is represented by an object
with the following properties:

`KeyObject`

<table>
<thead>
<tr class="header">
<th>Parameter</th>
<th>Type</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><p>key</p></td>
<td><p>string</p></td>
<td><p><strong>Required.</strong> The unpadded Base64-encoded 32-byte Curve25519 public key.</p></td>
</tr>
<tr class="even">
<td><p>signatures</p></td>
<td><p>Signatures</p></td>
<td><p><strong>Required.</strong> Signatures of the key object.</p>
<p>The signature is calculated using the process described at <a href="../appendices.html#signing-json">Signing JSON</a>.</p></td>
</tr>
</tbody>
</table>

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
as a signed JSON object, using the `/keys/upload`\_ API. The JSON object
must include the public part of the device's Ed25519 key, and must be
signed by that key, as described in [Signing
JSON](../appendices.html#signing-json).

One-time keys are also uploaded to the homeserver using the
`/keys/upload`\_ API.

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
obtained by calling `/keys/query`\_, passing Bob's user ID in the
`device_keys` parameter.

From time to time, Bob may add new devices, and Alice will need to know
this so that she can include his new devices for later encrypted
messages. A naive solution to this would be to call `/keys/query`\_
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
2.  It then makes a request to `/keys/query`\_, passing Bob's user ID in
    the `device_keys` parameter. When the request completes, it stores
    the resulting list of devices in persistent storage, and clears the
    'outdated' flag.
3.  During its normal processing of responses to \_, Alice's client
    inspects the `changed` property of the `device_lists`\_ field. If it
    is tracking the device lists of any of the listed users, then it
    marks the device lists for those users outdated, and initiates
    another request to `/keys/query`\_ for them.
4.  Periodically, Alice's client stores the `next_batch` field of the
    result from \_ in persistent storage. If Alice later restarts her
    client, it can obtain a list of the users who have updated their
    device list while it was offline by calling `/keys/changes`\_,
    passing the recorded `next_batch` field as the `from` parameter. If
    the client is tracking the device list of any of the users listed in
    the response, it marks them as outdated. It combines this list with
    those already flagged as outdated, and initiates a `/keys/query`\_
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

Extensions to `m.room.message` msgtypes
&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;

This module adds `file` and `thumbnail_file` properties, of type
`EncryptedFile`, to `m.room.message` msgtypes that reference files, such
as [m.file]() and [m.image](), replacing the `url` and `thumbnail_url`
properties.

`EncryptedFile`

<table>
<thead>
<tr class="header">
<th>Parameter</th>
<th>Type</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>url</td>
<td>string</td>
<td><strong>Required.</strong> The URL to the file.</td>
</tr>
<tr class="even">
<td>key</td>
<td>JWK</td>
<td><strong>Required.</strong> A <a href="https://tools.ietf.org/html/rfc7517#appendix-A.3">JSON Web Key</a> object.</td>
</tr>
<tr class="odd">
<td><p>iv</p></td>
<td><p>string</p></td>
<td><p><strong>Required.</strong> The 128-bit unique counter block used by AES-CTR, encoded as unpadded base64.</p></td>
</tr>
<tr class="even">
<td><p>hashes</p></td>
<td><p>{string: string}</p></td>
<td><p><strong>Required.</strong> A map from an algorithm name to a hash of the ciphertext, encoded as unpadded base64. Clients should support the SHA-256 hash, which uses the key <code>sha256</code>.</p></td>
</tr>
<tr class="odd">
<td><p>v</p></td>
<td><p>string</p></td>
<td><p><strong>Required.</strong> Version of the encrypted attachments protocol. Must be <code>v2</code>.</p></td>
</tr>
</tbody>
</table>

`JWK`

<table>
<thead>
<tr class="header">
<th>Parameter</th>
<th>Type</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>kty</td>
<td>string</td>
<td><strong>Required.</strong> Key type. Must be <code>oct</code>.</td>
</tr>
<tr class="even">
<td><p>key_ops</p></td>
<td><p>[string]</p></td>
<td><p><strong>Required.</strong> Key operations. Must at least contain <code>encrypt</code> and <code>decrypt</code>.</p></td>
</tr>
<tr class="odd">
<td>alg</td>
<td>string</td>
<td><strong>Required.</strong> Algorithm. Must be <code>A256CTR</code>.</td>
</tr>
<tr class="even">
<td>k</td>
<td>string</td>
<td><strong>Required.</strong> The key, encoded as urlsafe unpadded base64.</td>
</tr>
<tr class="odd">
<td><p>ext</p></td>
<td><p>boolean</p></td>
<td><p><strong>Required.</strong> Extractable. Must be <code>true</code>. This is a <a href="https://w3c.github.io/webcrypto/#iana-section-jwk">W3C extension</a>.</p></td>
</tr>
</tbody>
</table>

Example:

##### Claiming one-time keys

A client wanting to set up a session with another device can claim a
one-time key for that device. This is done by making a request to the
`/keys/claim`\_ API.

A homeserver should rate-limit the number of one-time keys that a given
user or remote server can claim. A homeserver should discard the public
part of a one time key once it has given that key to another user.

#### Device verification

Before Alice sends Bob encrypted data, or trusts data received from him,
she may want to verify that she is actually communicating with him,
rather than a man-in-the-middle. This verification process requires an
out-of-band channel: there is no way to do it within Matrix without
trusting the administrators of the homeservers.

In Matrix, verification works by Alice meeting Bob in person, or
contacting him via some other trusted medium, and use [SAS
Verification](#SAS Verification) to interactively verify Bob's devices.
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
supported by the specification. The methods all use a common framework
for negotiating the key verification.

To use this framework, Alice's client would send
`m.key.verification.request` events to Bob's devices. All of the
`to_device` messages sent to Bob MUST have the same `transaction_id` to
indicate they are part of the same request. This allows Bob to reject
the request on one device, and have it apply to all of his devices.
Similarly, it allows Bob to process the verification on one device
without having to involve all of his devices.

When Bob's device receives an `m.key.verification.request`, it should
prompt Bob to verify keys with Alice using one of the supported methods
in the request. If Bob's device does not understand any of the methods,
it should not cancel the request as one of his other devices may support
the request. Instead, Bob's device should tell Bob that an unsupported
method was used for starting key verification. The prompt for Bob to
accept/reject Alice's request (or the unsupported method prompt) should
be automatically dismissed 10 minutes after the `timestamp` field or 2
minutes after Bob's client receives the message, whichever comes first,
if Bob does not interact with the prompt. The prompt should additionally
be hidden if an appropriate `m.key.verification.cancel` message is
received.

If Bob rejects the request, Bob's client must send an
`m.key.verification.cancel` message to Alice's device. Upon receipt,
Alice's device should tell her that Bob does not want to verify her
device and send `m.key.verification.cancel` messages to all of Bob's
devices to notify them that the request was rejected.

If Bob accepts the request, Bob's device starts the key verification
process by sending an `m.key.verification.start` message to Alice's
device. Upon receipt of this message, Alice's device should send an
`m.key.verification.cancel` message to all of Bob's other devices to
indicate the process has been started. The start message must use the
same `transaction_id` from the original key verification request if it
is in response to the request. The start message can be sent
independently of any request.

Individual verification methods may add additional steps, events, and
properties to the verification messages. Event types for methods defined
in this specification must be under the `m.key.verification` namespace
and any other event types must be namespaced according to the Java
package naming convention.

Any of Alice's or Bob's devices can cancel the key verification request
or process at any time with an `m.key.verification.cancel` message to
all applicable devices.

This framework yields the following handshake, assuming both Alice and
Bob each have 2 devices, Bob's first device accepts the key verification
request, and Alice's second device initiates the request. Note how
Alice's first device is not involved in the request or verification
process.

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
            |                 |          m.key.verification.start |               |
            |                 |<----------------------------------|               |
            |                 |                                   |               |
            |                 | m.key.verification.cancel         |               |
            |                 |-------------------------------------------------->|
            |                 |                                   |               |
```

After the handshake, the verification process begins.

{{m\_key\_verification\_request\_event}}

{{m\_key\_verification\_start\_event}}

{{m\_key\_verification\_cancel\_event}}

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

The verification process takes place over [to-device]() messages in two
phases:

1.  Key agreement phase (based on [ZRTP key
    agreement](https://tools.ietf.org/html/rfc6189#section-4.4.1)).
2.  Key verification phase (based on HMAC).

The process between Alice and Bob verifying each other would be:

1.  Alice and Bob establish a secure out-of-band connection, such as
    meeting in-person or a video call. "Secure" here means that either
    party cannot be impersonated, not explicit secrecy.
2.  Alice and Bob communicate which devices they'd like to verify with
    each other.
3.  Alice selects Bob's device from the device list and begins
    verification.
4.  Alice's client ensures it has a copy of Bob's device key.
5.  Alice's device sends Bob's device an `m.key.verification.start`
    message.
6.  Bob's device receives the message and selects a key agreement
    protocol, hash algorithm, message authentication code, and SAS
    method supported by Alice's device.
7.  Bob's device ensures it has a copy of Alice's device key.
8.  Bob's device creates an ephemeral Curve25519 key pair
    (*K*<sub>*B*</sub><sup>*p**r**i**v**a**t**e*</sup>, *K*<sub>*B*</sub><sup>*p**u**b**l**i**c*</sup>),
    and calculates the hash (using the chosen algorithm) of the public
    key *K*<sub>*B*</sub><sup>*p**u**b**l**i**c*</sup>.
9.  Bob's device replies to Alice's device with an
    `m.key.verification.accept` message.
10. Alice's device receives Bob's message and stores the commitment hash
    for later use.
11. Alice's device creates an ephemeral Curve25519 key pair
    (*K*<sub>*A*</sub><sup>*p**r**i**v**a**t**e*</sup>, *K*<sub>*A*</sub><sup>*p**u**b**l**i**c*</sup>)
    and replies to Bob's device with an `m.key.verification.key`,
    sending only the public key
    *K*<sub>*A*</sub><sup>*p**u**b**l**i**c*</sup>.
12. Bob's device receives Alice's message and replies with its own
    `m.key.verification.key` message containing its public key
    *K*<sub>*B*</sub><sup>*p**u**b**l**i**c*</sup>.
13. Alice's device receives Bob's message and verifies the commitment
    hash from earlier matches the hash of the key Bob's device just sent
    and the content of Alice's `m.key.verification.start` message.
14. Both Alice and Bob's devices perform an Elliptic-curve
    Diffie-Hellman
    (*E**C**D**H*(*K*<sub>*A*</sub><sup>*p**r**i**v**a**t**e*</sup>, *K*<sub>*B*</sub><sup>*p**u**b**l**i**c*</sup>)),
    using the result as the shared secret.
15. Both Alice and Bob's devices display a SAS to their users, which is
    derived from the shared key using one of the methods in this
    section. If multiple SAS methods are available, clients should allow
    the users to select a method.
16. Alice and Bob compare the strings shown by their devices, and tell
    their devices if they match or not.
17. Assuming they match, Alice and Bob's devices calculate the HMAC of
    their own device keys and a comma-separated sorted list of the key
    IDs that they wish the other user to verify, using SHA-256 as the
    hash function. HMAC is defined in [RFC
    2104](https://tools.ietf.org/html/rfc2104). The key for the HMAC is
    different for each item and is calculated by generating 32 bytes
    (256 bits) using [the key verification HKDF](#sas-hkdf).
18. Alice's device sends Bob's device an `m.key.verification.mac`
    message containing the MAC of Alice's device keys and the MAC of her
    key IDs to be verified. Bob's device does the same for Bob's device
    keys and key IDs concurrently with Alice.
19. When the other device receives the `m.key.verification.mac` message,
    the device calculates the HMAC of its copies of the other device's
    keys given in the message, as well as the HMAC of the
    comma-separated, sorted, list of key IDs in the message. The device
    compares these with the HMAC values given in the message, and if
    everything matches then the device keys are verified.

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

{{m\_key\_verification\_start\_m\_sas\_v1\_event}}

{{m\_key\_verification\_accept\_event}}

{{m\_key\_verification\_key\_event}}

{{m\_key\_verification\_mac\_event}}

###### HKDF calculation

In all of the SAS methods, HKDF is as defined in [RFC
5869](https://tools.ietf.org/html/rfc5869) and uses the previously
agreed-upon hash function for the hash function. The shared secret is
supplied as the input keying material. No salt is used. When the
`key_agreement_protocol` is `curve25519-hkdf-sha256`, the info parameter
is the concatenation of:

> -   The string `MATRIX_KEY_VERIFICATION_SAS|`.
> -   The Matrix ID of the user who sent the `m.key.verification.start`
>     message, followed by `|`.
> -   The Device ID of the device which sent the
>     `m.key.verification.start` message, followed by `|`.
> -   The public key from the `m.key.verification.key` message sent by
>     the device which sent the `m.key.verification.start` message,
>     followed by `|`.
> -   The Matrix ID of the user who sent the `m.key.verification.accept`
>     message, followed by `|`.
> -   The Device ID of the device which sent the
>     `m.key.verification.accept` message, followed by `|`.
> -   The public key from the `m.key.verification.key` message sent by
>     the device which sent the `m.key.verification.accept` message,
>     followed by `|`.
> -   The `transaction_id` being used.

When the `key_agreement_protocol` is the deprecated method `curve25519`,
the info parameter is the concatenation of:

> -   The string `MATRIX_KEY_VERIFICATION_SAS`.
> -   The Matrix ID of the user who sent the `m.key.verification.start`
>     message.
> -   The Device ID of the device which sent the
>     `m.key.verification.start` message.
> -   The Matrix ID of the user who sent the `m.key.verification.accept`
>     message.
> -   The Device ID of the device which sent the
>     `m.key.verification.accept` message.
> -   The `transaction_id` being used.

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

> -   The string `MATRIX_KEY_VERIFICATION_MAC`.
> -   The Matrix ID of the user whose key is being MAC-ed.
> -   The Device ID of the device sending the MAC.
> -   The Matrix ID of the other user.
> -   The Device ID of the device receiving the MAC.
> -   The `transaction_id` being used.
> -   The Key ID of the key being MAC-ed, or the string `KEY_IDS` if the
>     item being MAC-ed is the list of key IDs.

###### SAS method: `decimal`

Generate 5 bytes using [HKDF](#sas-hkdf) then take sequences of 13 bits
to convert to decimal numbers (resulting in 3 numbers between 0 and 8191
inclusive each). Add 1000 to each calculated number.

The bitwise operations to get the numbers given the 5 bytes
*B*<sub>0</sub>, *B*<sub>1</sub>, *B*<sub>2</sub>, *B*<sub>3</sub>, *B*<sub>4</sub>
would be:

-   First: (*B*<sub>0</sub> ≪ 5|*B*<sub>1</sub> ≫ 3) + 1000
-   Second:
    ((*B*<sub>1</sub>&0*x*7) ≪ 10|*B*<sub>2</sub> ≪ 2|*B*<sub>3</sub> ≫ 6) + 1000
-   Third: ((*B*<sub>3</sub>&0*x*3*F*) ≪ 7|*B*<sub>4</sub> ≫ 1) + 1000

The digits are displayed to the user either with an appropriate
separator, such as dashes, or with the numbers on individual lines.

###### SAS method: `emoji`

Generate 6 bytes using [HKDF](#sas-hkdf) then split the first 42 bits
into 7 groups of 6 bits, similar to how one would base64 encode
something. Convert each group of 6 bits to a number and use the
following table to get the corresponding emoji:

{{sas\_emoji\_table}}

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
/\_matrix/client/r0/keys/device\_signing/upload](). When Alice uploads
new cross-signing keys, her user ID will appear in the `changed`
property of the `device_lists` field of the `/sync` of response of all
users who share an encrypted room with her. When Bob sees Alice's user
ID in his `/sync`, he will call [POST /\_matrix/client/r0/keys/query]()
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

{{cross\_signing\_cs\_http\_api}}

#### Sharing keys between devices

If Bob has an encrypted conversation with Alice on his computer, and
then logs in through his phone for the first time, he may want to have
access to the previously exchanged messages. To address this issue,
several methods are provided to allow users to transfer keys from one
device to another.

##### Key requests

When a device is missing keys to decrypt messages, it can request the
keys by sending [m.room\_key\_request]() to-device messages to other
devices with `action` set to `request`.

If a device wishes to share the keys with that device, it can forward
the keys to the first device by sending an encrypted
[m.forwarded\_room\_key]() to-device message. The first device should
then send an [m.room\_key\_request]() to-device message with `action`
set to `request_cancellation` to the other devices that it had
originally sent the key request to; a device that receives a
`request_cancellation` should disregard any previously-received
`request` message with the same `request_id` and `requesting_device_id`.

If a device does not wish to share keys with that device, it can
indicate this by sending an [m.room\_key.withheld]() to-device message,
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
/\_matrix/client/r0/room\_keys/version]() and define how the keys are to
be encrypted through the backup's `auth_data`; other clients can
discover the backup by calling [GET
/\_matrix/client/r0/room\_keys/version](). Keys are encrypted according
to the backup's `auth_data` and added to the backup by calling [PUT
/\_matrix/client/r0/room\_keys/keys]() or one of its variants, and can
be retrieved by calling [GET /\_matrix/client/r0/room\_keys/keys]() or
one of its variants. Keys can only be written to the most recently
created version of the backup. Backups can also be deleted using [DELETE
/\_matrix/client/r0/room\_keys/version/{version}](), or individual keys
can be deleted using [DELETE /\_matrix/client/r0/room\_keys/keys]() or
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

###### Backup algorithm: `m.megolm_backup.v1.curve25519-aes-sha2`

When a backup is created with the `algorithm` set to
`m.megolm_backup.v1.curve25519-aes-sha2`, the `auth_data` should have
the following format:

`AuthData`

<table>
<thead>
<tr class="header">
<th>Parameter</th>
<th>Type</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><p>public_key</p></td>
<td><p>string</p></td>
<td><p><strong>Required.</strong> The curve25519 public key used to encrypt the backups, encoded in unpadded base64.</p></td>
</tr>
<tr class="even">
<td><p>signatures</p></td>
<td><p>Signatures</p></td>
<td><p>Optional. Signatures of the <code>auth_data</code>, as Signed JSON</p></td>
</tr>
</tbody>
</table>

The `session_data` field in the backups is constructed as follows:

1.  Encode the session key to be backed up as a JSON object with the
    properties:

    <table>
    <thead>
    <tr class="header">
    <th>Parameter</th>
    <th>Type</th>
    <th>Description</th>
    </tr>
    </thead>
    <tbody>
    <tr class="odd">
    <td><p>algorithm</p></td>
    <td><p>string</p></td>
    <td><p><strong>Required.</strong> The end-to-end message encryption algorithm that the key is for. Must be <code>m.megolm.v1.aes-sha2</code>.</p></td>
    </tr>
    <tr class="even">
    <td><p>forwarding_curve25519_key_chain</p></td>
    <td><p>[string]</p></td>
    <td><p><strong>Required.</strong> Chain of Curve25519 keys through which this session was forwarded, via <a href="">m.forwarded_room_key</a> events.</p></td>
    </tr>
    <tr class="odd">
    <td><p>sender_key</p></td>
    <td><p>string</p></td>
    <td><p><strong>Required.</strong> Unpadded base64-encoded device curve25519 key.</p></td>
    </tr>
    <tr class="even">
    <td><p>sender_claimed_keys</p></td>
    <td><p>{string: string}</p></td>
    <td><p><strong>Required.</strong> A map from algorithm name (<code>ed25519</code>) to the identity key for the sending device.</p></td>
    </tr>
    <tr class="odd">
    <td><p>session_key</p></td>
    <td><p>string</p></td>
    <td><p><strong>Required.</strong> Unpadded base64-encoded session key in <a href="https://gitlab.matrix.org/matrix-org/olm/blob/master/docs/megolm.md#session-sharing-format">session-sharing format</a>.</p></td>
    </tr>
    </tbody>
    </table>

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

{{key\_backup\_cs\_http\_api}}

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

    <table>
    <thead>
    <tr class="header">
    <th>Size (bytes)</th>
    <th>Description</th>
    </tr>
    </thead>
    <tbody>
    <tr class="odd">
    <td>1</td>
    <td>Export format version, which must be <code>0x01</code>.</td>
    </tr>
    <tr class="even">
    <td>16</td>
    <td>The salt S.</td>
    </tr>
    <tr class="odd">
    <td>16</td>
    <td>The initialization vector IV.</td>
    </tr>
    <tr class="even">
    <td>4</td>
    <td>The number of rounds N, as a big-endian unsigned 32-bit integer.</td>
    </tr>
    <tr class="odd">
    <td>variable</td>
    <td>The encrypted JSON object.</td>
    </tr>
    <tr class="even">
    <td><p>32</p></td>
    <td><p>The HMAC-SHA-256 of all the above string concatenated together, using K' as the key.</p></td>
    </tr>
    </tbody>
    </table>

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

<table>
<thead>
<tr class="header">
<th>Parameter</th>
<th>Type</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><p>algorithm</p></td>
<td><p>string</p></td>
<td><p>Required. The encryption algorithm that the session uses. Must be <code>m.megolm.v1.aes-sha2</code>.</p></td>
</tr>
<tr class="even">
<td><p>forwarding_curve25519_key_chain</p></td>
<td><p>[string]</p></td>
<td><p>Required. Chain of Curve25519 keys through which this session was forwarded, via <a href="">m.forwarded_room_key</a> events.</p></td>
</tr>
<tr class="odd">
<td><p>room_id</p></td>
<td><p>string</p></td>
<td><p>Required. The room where the session is used.</p></td>
</tr>
<tr class="even">
<td><p>sender_key</p></td>
<td><p>string</p></td>
<td><p>Required. The Curve25519 key of the device which initiated the session originally.</p></td>
</tr>
<tr class="odd">
<td><p>sender_claimed_keys</p></td>
<td><p>{string: string}</p></td>
<td><p>Required. The Ed25519 key of the device which initiated the session originally.</p></td>
</tr>
<tr class="even">
<td>session_id</td>
<td>string</td>
<td>Required. The ID of the session.</td>
</tr>
<tr class="odd">
<td>session_key</td>
<td>string</td>
<td>Required. The key for the session.</td>
</tr>
</tbody>
</table>

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
under the `keys` property match the keys returned by `/keys/query`\_ for
the given user, and must also verify the signature of the payload.
Without this check, a client cannot be sure that the sender device owns
the private part of the ed25519 key it claims to have in the Olm
payload. This is crucial when the ed25519 key corresponds to a verified
device.

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

To establish a new session, the client sends an [m.dummy](#m-dummy)
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

{{m\_room\_encryption\_event}}

{{m\_room\_encrypted\_event}}

{{m\_room\_key\_event}}

{{m\_room\_key\_request\_event}}

{{m\_forwarded\_room\_key\_event}}

{{m\_dummy\_event}}

##### Key management API

{{keys\_cs\_http\_api}}

##### Extensions to /sync

This module adds an optional `device_lists` property to the \_ response,
as specified below. The server need only populate this property for an
incremental `/sync` (i.e., one where the `since` parameter was
specified). The client is expected to use `/keys/query`\_ or
`/keys/changes`\_ for the equivalent functionality after an initial
sync, as documented in [Tracking the device list for a
user](#tracking-the-device-list-for-a-user).

It also adds a `one_time_keys_count` property. Note the spelling
difference with the `one_time_key_counts` property in the
`/keys/upload`\_ response.

<table>
<thead>
<tr class="header">
<th>Parameter</th>
<th>Type</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><p>device_lists</p></td>
<td><p>DeviceLists</p></td>
<td><p>Optional. Information on e2e device updates. Note: only present on an incremental sync.</p></td>
</tr>
<tr class="even">
<td><p>device_one_time_keys_count</p></td>
<td><p>{string: integer}</p></td>
<td><p>Optional. For each key algorithm, the number of unclaimed one-time keys currently held on the server for this device.</p></td>
</tr>
</tbody>
</table>

`DeviceLists`

<table>
<thead>
<tr class="header">
<th>Parameter</th>
<th>Type</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><p>changed</p></td>
<td><p>[string]</p></td>
<td><p>List of users who have updated their device identity or cross-signing keys, or who now share an encrypted room with the client since the previous sync response.</p></td>
</tr>
<tr class="even">
<td><p>left</p></td>
<td><p>[string]</p></td>
<td><p>List of users with whom we do not share any encrypted rooms anymore since the previous sync response.</p></td>
</tr>
</tbody>
</table>

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

{{m\_room\_key\_withheld\_event}}
