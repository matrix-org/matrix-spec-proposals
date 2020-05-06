.. Copyright 2016 OpenMarket Ltd
.. Copyright 2019 The Matrix.org Foundation C.I.C.
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..     http://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.

End-to-End Encryption
=====================

.. _module:e2e:

Matrix optionally supports end-to-end encryption, allowing rooms to be created
whose conversation contents are not decryptable or interceptable on any of the
participating homeservers.

Key Distribution
----------------
Encryption and Authentication in Matrix is based around public-key
cryptography. The Matrix protocol provides a basic mechanism for exchange of
public keys, though an out-of-band channel is required to exchange fingerprints
between users to build a web of trust.

Overview
~~~~~~~~

.. code::

    1) Bob publishes the public keys and supported algorithms for his
       device. This may include long-term identity keys, and/or one-time
       keys.

                                          +----------+  +--------------+
                                          | Bob's HS |  | Bob's Device |
                                          +----------+  +--------------+
                                                |              |
                                                |<=============|
                                                  /keys/upload

    2) Alice requests Bob's public identity keys and supported algorithms.

      +----------------+  +------------+  +----------+
      | Alice's Device |  | Alice's HS |  | Bob's HS |
      +----------------+  +------------+  +----------+
             |                  |               |
             |=================>|==============>|
               /keys/query        <federation>

    3) Alice selects an algorithm and claims any one-time keys needed.

      +----------------+  +------------+  +----------+
      | Alice's Device |  | Alice's HS |  | Bob's HS |
      +----------------+  +------------+  +----------+
             |                  |               |
             |=================>|==============>|
               /keys/claim         <federation>


Key algorithms
~~~~~~~~~~~~~~

The name ``ed25519`` corresponds to the `Ed25519`_ signature algorithm. The key
is a 32-byte Ed25519 public key, encoded using `unpadded Base64`_. Example:

.. code:: json

   "SogYyrkTldLz0BXP+GYWs0qaYacUI0RleEqNT8J3riQ"

The name ``curve25519`` corresponds to the `Curve25519`_ ECDH algorithm. The
key is a 32-byte Curve25519 public key, encoded using `unpadded
Base64`_. Example:

.. code:: json

  "JGLn/yafz74HB2AbPLYJWIVGnKAtqECOBf11yyXac2Y"

The name ``signed_curve25519`` also corresponds to the Curve25519 algorithm,
but keys using this algorithm are objects with the properties ``key`` (giving
the Base64-encoded 32-byte Curve25519 public key), and ``signatures`` (giving a
signature for the key object, as described in `Signing JSON`_). Example:

.. code:: json

  {
    "key":"06UzBknVHFMwgi7AVloY7ylC+xhOhEX4PkNge14Grl8",
    "signatures": {
      "@user:example.com": {
        "ed25519:EGURVBUNJP": "YbJva03ihSj5mPk+CHMJKUKlCXCPFXjXOK6VqBnN9nA2evksQcTGn6hwQfrgRHIDDXO2le49x7jnWJHMJrJoBQ"
      }
    }
  }

Device keys
~~~~~~~~~~~

Each device should have one Ed25519 signing key. This key should be generated
on the device from a cryptographically secure source, and the private part of
the key should never be exported from the device. This key is used as the
fingerprint for a device by other clients.

A device will generally need to generate a number of additional keys. Details
of these will vary depending on the messaging algorithm in use.

Algorithms generally require device identity keys as well as signing keys. Some
algorithms also require one-time keys to improve their secrecy and deniability.
These keys are used once during session establishment, and are then thrown
away.

For Olm version 1, each device requires a single Curve25519 identity key, and a
number of signed Curve25519 one-time keys.

Uploading keys
~~~~~~~~~~~~~~

A device uploads the public parts of identity keys to their homeserver as a
signed JSON object, using the |/keys/upload|_ API.
The JSON object must include the public part of the device's Ed25519 key, and
must be signed by that key, as described in `Signing JSON`_.

One-time keys are also uploaded to the homeserver using the |/keys/upload|_
API.

Devices must store the private part of each key they upload. They can
discard the private part of a one-time key when they receive a message using
that key. However it's possible that a one-time key given out by a homeserver
will never be used, so the device that generates the key will never know that
it can discard the key. Therefore a device could end up trying to store too
many private keys. A device that is trying to store too many private keys may
discard keys starting with the oldest.

Tracking the device list for a user
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before Alice can send an encrypted message to Bob, she needs a list of each of
his devices and the associated identity keys, so that she can establish an
encryption session with each device. This list can be obtained by calling
|/keys/query|_, passing Bob's user ID in the ``device_keys`` parameter.

From time to time, Bob may add new devices, and Alice will need to know this so
that she can include his new devices for later encrypted messages. A naive
solution to this would be to call |/keys/query|_ before sending each message -
however, the number of users and devices may be large and this would be
inefficient.

It is therefore expected that each client will maintain a list of devices for a
number of users (in practice, typically each user with whom we share an
encrypted room). Furthermore, it is likely that this list will need to be
persisted between invocations of the client application (to preserve device
verification data and to alert Alice if Bob suddenly gets a new
device).

Alice's client can maintain a list of Bob's devices via the following
process:

#. It first sets a flag to record that it is now tracking Bob's device list,
   and a separate flag to indicate that its list of Bob's devices is
   outdated. Both flags should be in storage which persists over client
   restarts.

#. It then makes a request to |/keys/query|_, passing Bob's user ID in the
   ``device_keys`` parameter. When the request completes, it stores the
   resulting list of devices in persistent storage, and clears the 'outdated'
   flag.

#. During its normal processing of responses to |/sync|_, Alice's client
   inspects the ``changed`` property of the |device_lists|_ field. If it is
   tracking the device lists of any of the listed users, then it marks the
   device lists for those users outdated, and initiates another request to
   |/keys/query|_ for them.

#. Periodically, Alice's client stores the ``next_batch`` field of the result
   from |/sync|_ in persistent storage. If Alice later restarts her client, it
   can obtain a list of the users who have updated their device list while it
   was offline by calling |/keys/changes|_, passing the recorded ``next_batch``
   field as the ``from`` parameter. If the client is tracking the device list
   of any of the users listed in the response, it marks them as outdated. It
   combines this list with those already flagged as outdated, and initiates a
   |/keys/query|_ request for all of them.

.. Warning::

   Bob may update one of his devices while Alice has a request to
   ``/keys/query`` in flight. Alice's client may therefore see Bob's user ID in
   the ``device_lists`` field of the ``/sync`` response while the first request
   is in flight, and initiate a second request to ``/keys/query``. This may
   lead to either of two related problems.

   The first problem is that, when the first request completes, the client will
   clear the 'outdated' flag for Bob's devices. If the second request fails, or
   the client is shut down before it completes, this could lead to Alice using
   an outdated list of Bob's devices.

   The second possibility is that, under certain conditions, the second request
   may complete *before* the first one. When the first request completes, the
   client could overwrite the later results from the second request with those
   from the first request.

   Clients MUST guard against these situations. For example, a client could
   ensure that only one request to ``/keys/query`` is in flight at a time for
   each user, by queuing additional requests until the first completes.
   Alternatively, the client could make a new request immediately, but ensure
   that the first request's results are ignored (possibly by cancelling the
   request).

.. Note::

  When Bob and Alice share a room, with Bob tracking Alice's devices, she may leave
  the room and then add a new device. Bob will not be notified of this change,
  as he doesn't share a room anymore with Alice. When they start sharing a
  room again, Bob has an out-of-date list of Alice's devices. In order to address
  this issue, Bob's homeserver will add Alice's user ID to the ``changed`` property of
  the ``device_lists`` field, thus Bob will update his list of Alice's devices as part
  of his normal processing. Note that Bob can also be notified when he stops sharing
  any room with Alice by inspecting the ``left`` property of the ``device_lists``
  field, and as a result should remove her from its list of tracked users.

.. |device_lists| replace:: ``device_lists``
.. _`device_lists`: `device_lists_sync`_


Sending encrypted attachments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When encryption is enabled in a room, files should be uploaded encrypted on
the homeserver.

In order to achieve this, a client should generate a single-use 256-bit AES
key, and encrypt the file using AES-CTR. The counter should be 64-bit long,
starting at 0 and prefixed by a random 64-bit Initialization Vector (IV), which
together form a 128-bit unique counter block.

.. Warning::
  An IV must never be used multiple times with the same key. This implies that
  if there are multiple files to encrypt in the same message, typically an
  image and its thumbnail, the files must not share both the same key and IV.

Then, the encrypted file can be uploaded to the homeserver.
The key and the IV must be included in the room event along with the resulting
``mxc://`` in order to allow recipients to decrypt the file. As the event
containing those will be Megolm encrypted, the server will never have access to
the decrypted file.

A hash of the ciphertext must also be included, in order to prevent the homeserver from
changing the file content.

A client should send the data as an encrypted ``m.room.message`` event, using
either ``m.file`` as the msgtype, or the appropriate msgtype for the file
type. The key is sent using the `JSON Web Key`_ format, with a `W3C
extension`_.

.. anchor for link from m.message api spec
.. |encrypted_files| replace:: End-to-end encryption
.. _encrypted_files:

Extensions to ``m.message`` msgtypes
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

This module adds ``file`` and ``thumbnail_file`` properties, of type
``EncryptedFile``, to ``m.message`` msgtypes that reference files, such as
`m.file`_ and `m.image`_, replacing the ``url`` and ``thumbnail_url``
properties.

.. todo: generate this from a swagger definition?

``EncryptedFile``

========= ================ =====================================================
Parameter Type             Description
========= ================ =====================================================
url       string           **Required.** The URL to the file.
key       JWK              **Required.** A `JSON Web Key`_ object.
iv        string           **Required.** The Initialisation Vector used by
                           AES-CTR, encoded as unpadded base64.
hashes    {string: string} **Required.** A map from an algorithm name to a hash
                           of the ciphertext, encoded as unpadded base64. Clients
                           should support the SHA-256 hash, which uses the key
                           ``sha256``.
v         string           **Required.** Version of the encrypted attachments
                           protocol. Must be ``v2``.
========= ================ =====================================================

``JWK``

========= ========= ============================================================
Parameter Type      Description
========= ========= ============================================================
kty       string    **Required.** Key type. Must be ``oct``.
key_ops   [string]  **Required.** Key operations. Must at least contain
                    ``encrypt`` and ``decrypt``.
alg       string    **Required.** Algorithm. Must be ``A256CTR``.
k         string    **Required.** The key, encoded as urlsafe unpadded base64.
ext       boolean   **Required.** Extractable. Must be ``true``. This is a
                    `W3C extension`_.
========= ========= ============================================================

Example:

.. code :: json

  {
    "content": {
      "body": "something-important.jpg",
      "file": {
        "url": "mxc://example.org/FHyPlCeYUSFFxlgbQYZmoEoe",
        "mimetype": "image/jpeg",
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
          "mimetype": "image/jpeg",
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

Claiming one-time keys
~~~~~~~~~~~~~~~~~~~~~~

A client wanting to set up a session with another device can claim a one-time
key for that device. This is done by making a request to the |/keys/claim|_
API.

A homeserver should rate-limit the number of one-time keys that a given user or
remote server can claim. A homeserver should discard the public part of a one
time key once it has given that key to another user.

Device verification
-------------------

Before Alice sends Bob encrypted data, or trusts data received from him, she
may want to verify that she is actually communicating with him, rather than a
man-in-the-middle. This verification process requires an out-of-band channel:
there is no way to do it within Matrix without trusting the administrators of
the homeservers.

In Matrix, verification works by Alice meeting Bob in person, or contacting him
via some other trusted medium, and use `SAS Verification`_ to interactively
verify Bob's devices. Alice and Bob may also read aloud their unpadded base64
encoded Ed25519 public key, as returned by ``/keys/query``.

Device verification may reach one of several conclusions. For example:

* Alice may "accept" the device. This means that she is satisfied that the
  device belongs to Bob. She can then encrypt sensitive material for that
  device, and knows that messages received were sent from that device.

* Alice may "reject" the device. She will do this if she knows or suspects
  that Bob does not control that device (or equivalently, does not trust
  Bob). She will not send sensitive material to that device, and cannot trust
  messages apparently received from it.

* Alice may choose to skip the device verification process. She is not able
  to verify that the device actually belongs to Bob, but has no reason to
  suspect otherwise. The encryption protocol continues to protect against
  passive eavesdroppers.

.. NOTE::

   Once the signing key has been verified, it is then up to the encryption
   protocol to verify that a given message was sent from a device holding that
   Ed25519 private key, or to encrypt a message so that it may only be
   decrypted by such a device. For the Olm protocol, this is documented at
   https://matrix.org/docs/olm_signing.html.


Key verification framework
~~~~~~~~~~~~~~~~~~~~~~~~~~

Verifying keys manually by reading out the Ed25519 key is not very user friendly,
and can lead to errors. In order to help mitigate errors, and to make the process
easier for users, some verification methods are supported by the specification.
The methods all use a common framework for negotiating the key verification.

To use this framework, Alice's client would send ``m.key.verification.request``
events to Bob's devices. All of the ``to_device`` messages sent to Bob MUST have
the same ``transaction_id`` to indicate they are part of the same request. This
allows Bob to reject the request on one device, and have it apply to all of his
devices. Similarly, it allows Bob to process the verification on one device without
having to involve all of his devices.

When Bob's device receives a ``m.key.verification.request``, it should prompt Bob
to verify keys with Alice using one of the supported methods in the request. If
Bob's device does not understand any of the methods, it should not cancel the request
as one of his other devices may support the request. Instead, Bob's device should
tell Bob that an unsupported method was used for starting key verification. The
prompt for Bob to accept/reject Alice's request (or the unsupported method prompt)
should be automatically dismissed 10 minutes after the ``timestamp`` field or 2
minutes after Bob's client receives the message, whichever comes first, if Bob
does not interact with the prompt. The prompt should additionally be hidden if
an appropriate ``m.key.verification.cancel`` message is received.

If Bob rejects the request, Bob's client must send a ``m.key.verification.cancel``
message to Alice's device. Upon receipt, Alice's device should tell her that Bob
does not want to verify her device and send ``m.key.verification.cancel`` messages
to all of Bob's devices to notify them that the request was rejected.

If Bob accepts the request, Bob's device starts the key verification process by
sending a ``m.key.verification.start`` message to Alice's device. Upon receipt
of this message, Alice's device should send a ``m.key.verification.cancel`` message
to all of Bob's other devices to indicate the process has been started. The start
message must use the same ``transaction_id`` from the original key verification
request if it is in response to the request. The start message can be sent indepdently
of any request.

Individual verification methods may add additional steps, events, and properties to
the verification messages. Event types for methods defined in this specification must
be under the ``m.key.verification`` namespace and any other event types must be namespaced
according to the Java package naming convention.

Any of Alice's or Bob's devices can cancel the key verification request or process
at any time with a ``m.key.verification.cancel`` message to all applicable devices.

This framework yields the following handshake, assuming both Alice and Bob each have
2 devices, Bob's first device accepts the key verification request, and Alice's second
device initiates the request. Note how Alice's first device is not involved in the
request or verification process.

::

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


After the handshake, the verification process begins.

{{m_key_verification_request_event}}

{{m_key_verification_start_event}}

{{m_key_verification_cancel_event}}


.. _`SAS Verification`:

Short Authentication String (SAS) verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

SAS verification is a user-friendly key verification process built off the common
framework outlined above. SAS verification is intended to be a highly interactive
process for users, and as such exposes verfiication methods which are easier for
users to use.

The verification process is heavily inspired by Phil Zimmerman's ZRTP key agreement
handshake. A key part of key agreement in ZRTP is the hash commitment: the party that
begins the Diffie-Hellman key sharing sends a hash of their part of the Diffie-Hellman
exchange, and does not send their part of the Diffie-Hellman exchange until they have
received the other party's part. Thus an attacker essentially only has one attempt to
attack the Diffie-Hellman exchange, and hence we can verify fewer bits while still
achieving a high degree of security: if we verify n bits, then an attacker has a 1 in
2\ :sup:`n` chance of success.  For example, if we verify 40 bits, then an attacker has
a 1 in 1,099,511,627,776 chance (or less than 1 in 1012 chance) of success. A failed
attack would result in a mismatched Short Authentication String, alerting users to the
attack.

The verification process takes place over `to-device`_ messages in two phases:

1. Key agreement phase (based on `ZRTP key agreement <https://tools.ietf.org/html/rfc6189#section-4.4.1>`_).
#. Key verification phase (based on HMAC).

The process between Alice and Bob verifying each other would be:

.. |AlicePublicKey| replace:: :math:`K_{A}^{public}`
.. |AlicePrivateKey| replace:: :math:`K_{A}^{private}`
.. |AliceCurve25519| replace:: :math:`K_{A}^{private},K_{A}^{public}`
.. |BobPublicKey| replace:: :math:`K_{B}^{public}`
.. |BobPrivateKey| replace:: :math:`K_{B}^{private}`
.. |BobCurve25519| replace:: :math:`K_{B}^{private},K_{B}^{public}`
.. |BobAliceCurve25519| replace:: :math:`K_{B}^{private}K_{A}^{public}`
.. |AliceBobECDH| replace:: :math:`ECDH(K_{A}^{private},K_{B}^{public})`

1. Alice and Bob establish a secure out-of-band connection, such as meeting
   in-person or a video call. "Secure" here means that either party cannot be
   impersonated, not explicit secrecy.
#. Alice and Bob communicate which devices they'd like to verify with each other.
#. Alice selects Bob's device from the device list and begins verification.
#. Alice's client ensures it has a copy of Bob's device key.
#. Alice's device sends Bob's device a ``m.key.verification.start`` message.
#. Bob's device receives the message and selects a key agreement protocol, hash
   algorithm, message authentication code, and SAS method supported by Alice's
   device.
#. Bob's device ensures it has a copy of Alice's device key.
#. Bob's device creates an ephemeral Curve25519 key pair (|BobCurve25519|), and
   calculates the hash (using the chosen algorithm) of the public key |BobPublicKey|.
#. Bob's device replies to Alice's device with a ``m.key.verification.accept`` message.
#. Alice's device receives Bob's message and stores the commitment hash for later use.
#. Alice's device creates an ephemeral Curve25519 key pair (|AliceCurve25519|) and
   replies to Bob's device with a ``m.key.verification.key``, sending only the public
   key |AlicePublicKey|.
#. Bob's device receives Alice's message and replies with its own ``m.key.verification.key``
   message containing its public key |BobPublicKey|.
#. Alice's device receives Bob's message and verifies the commitment hash from earlier
   matches the hash of the key Bob's device just sent and the content of Alice's
   ``m.key.verification.start`` message.
#. Both Alice and Bob's devices perform an Elliptic-curve Diffie-Hellman (|AliceBobECDH|),
   using the result as the shared secret.
#. Both Alice and Bob's devices display a SAS to their users, which is derived
   from the shared key using one of the methods in this section. If multiple SAS
   methods are available, clients should allow the users to select a method.
#. Alice and Bob compare the strings shown by their devices, and tell their devices if
   they match or not.
#. Assuming they match, Alice and Bob's devices calculate the HMAC of their own device keys
   and a comma-separated sorted list of of the key IDs that they wish the other user
   to verify, using SHA-256 as the hash function. HMAC is defined in [RFC 2104](https://tools.ietf.org/html/rfc2104).
   The key for the HMAC is different for each item and is calculated by generating
   32 bytes (256 bits) using `the key verification HKDF <#SAS-HKDF>`_.
#. Alice's device sends Bob's device a ``m.key.verification.mac`` message containing the
   MAC of Alice's device keys and the MAC of her key IDs to be verified. Bob's device does
   the same for Bob's device keys and key IDs concurrently with Alice.
#. When the other device receives the ``m.key.verification.mac`` message, the device
   calculates the HMAC of its copies of the other device's keys given in the message,
   as well as the HMAC of the comma-seperated, sorted, list of key IDs in the message.
   The device compares these with the HMAC values given in the message, and if everything
   matches then the device keys are verified.

The wire protocol looks like the following between Alice and Bob's devices::

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

Error and exception handling
<<<<<<<<<<<<<<<<<<<<<<<<<<<<

At any point the interactive verfication can go wrong. The following describes what
to do when an error happens:

* Alice or Bob can cancel the verification at any time. A ``m.key.verification.cancel``
  message must be sent to signify the cancellation.
* The verification can time out. Clients should time out a verification that does not
  complete within 10 minutes. Additionally, clients should expire a ``transaction_id``
  which goes unused for 10 minutes after having last sent/received it. The client should
  inform the user that the verification timed out, and send an appropriate
  ``m.key.verification.cancel`` message to the other device.
* When the same device attempts to intiate multiple verification attempts, the receipient
  should cancel all attempts with that device.
* When a device receives an unknown ``transaction_id``, it should send an appropriate
  ``m.key.verfication.cancel`` message to the other device indicating as such. This
  does not apply for inbound ``m.key.verification.start`` or ``m.key.verification.cancel``
  messages.
* If the two devices do not share a common key share, hash, HMAC, or SAS method then
  the device should notify the other device with an appropriate ``m.key.verification.cancel``
  message.
* If the user claims the Short Authentication Strings do not match, the device should
  send an appropriate ``m.key.verification.cancel`` message to the other device.
* If the device receives a message out of sequence or that it was not expecting, it should
  notify the other device with an appropriate ``m.key.verification.cancel`` message.


Verification messages specific to SAS
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

Building off the common framework, the following events are involved in SAS verification.

The ``m.key.verification.cancel`` event is unchanged, however the following error codes
are used in addition to those already specified:

* ``m.unknown_method``: The devices are unable to agree on the key agreement, hash, MAC,
  or SAS method.
* ``m.mismatched_commitment``: The hash commitment did not match.
* ``m.mismatched_sas``: The SAS did not match.


{{m_key_verification_start_m_sas_v1_event}}

{{m_key_verification_accept_event}}

{{m_key_verification_key_event}}

{{m_key_verification_mac_event}}


.. _`SAS-HKDF`:

HKDF calculation
<<<<<<<<<<<<<<<<

In all of the SAS methods, HKDF is as defined in [RFC 5869](https://tools.ietf.org/html/rfc5869)
and uses the previously agreed-upon hash function for the hash function. The shared
secret is supplied as the input keying material. No salt is used, and the input
parameter is the concatenation of:

  * The string ``MATRIX_KEY_VERIFICATION_SAS``.
  * The Matrix ID of the user who sent the ``m.key.verification.start`` message.
  * The Device ID of the device which sent the ``m.key.verification.start`` message.
  * The Matrix ID of the user who sent the ``m.key.verification.accept`` message.
  * The Device ID of the device which sent the ``m.key.verification.accept`` message.
  * The ``transaction_id`` being used.

.. admonition:: Rationale

  HKDF is used over the plain shared secret as it results in a harder attack
  as well as more uniform data to work with.

For verification of each party's device keys, HKDF is as defined in RFC 5869 and
uses SHA-256 as the hash function. The shared secret is supplied as the input keying
material. No salt is used, and in the input parameter is the concatenation of:

  * The string ``MATRIX_KEY_VERIFICATION_MAC``.
  * The Matrix ID of the user whose key is being MAC-ed.
  * The Device ID of the device sending the MAC.
  * The Matrix ID of the other user.
  * The Device ID of the device receiving the MAC.
  * The ``transaction_id`` being used.
  * The Key ID of the key being MAC-ed, or the string ``KEY_IDS`` if the item
    being MAC-ed is the list of key IDs.

SAS method: ``decimal``
<<<<<<<<<<<<<<<<<<<<<<<

Generate 5 bytes using `HKDF <#SAS-HKDF>`_ then take sequences of 13 bits to
convert to decimal numbers (resulting in 3 numbers between 0 and 8191 inclusive
each). Add 1000 to each calculated number.

The bitwise operations to get the numbers given the 5 bytes
:math:`B_{0}, B_{1}, B_{2}, B_{3}, B_{4}` would be:

* First: :math:`(B_{0} \ll 5 | B_{1} \gg 3) + 1000`
* Second: :math:`((B_{1} \& 0x7) \ll 10 | B_{2} \ll 2 | B_{3} \gg 6) + 1000`
* Third: :math:`((B_{3} \& 0x3F) \ll 7 | B_{4} \gg 1) + 1000`

The digits are displayed to the user either with an appropriate separator,
such as dashes, or with the numbers on individual lines.

SAS method: ``emoji``
<<<<<<<<<<<<<<<<<<<<<

Generate 6 bytes using `HKDF <#SAS-HKDF>`_ then split the first 42 bits into
7 groups of 6 bits, similar to how one would base64 encode something. Convert
each group of 6 bits to a number and use the following table to get the corresponding
emoji:

{{sas_emoji_table}}

.. Note::
   This table is available as JSON at
   https://github.com/matrix-org/matrix-doc/blob/master/data-definitions/sas-emoji.json

.. admonition:: Rationale

   The emoji above were chosen to:

   * Be recognisable without colour.
   * Be recognisable at a small size.
   * Be recognisable by most cultures.
   * Be distinguishable from each other.
   * Easily described by a few words.
   * Avoid symbols with negative connotations.
   * Be likely similar across multiple platforms.

Clients SHOULD show the emoji with the descriptions from the table, or appropriate
translation of those descriptions. Client authors SHOULD collaborate to create a
common set of translations for all languages.


.. section name changed, so make sure that old links keep working
.. _key-sharing:

Sharing keys between devices
----------------------------

If Bob has an encrypted conversation with Alice on his computer, and then logs in
through his phone for the first time, he may want to have access to the previously
exchanged messages. To address this issue, several methods are provided to
allow users to transfer keys from one device to another.

Key requests
~~~~~~~~~~~~

When a device is missing keys to decrypt messages, it can request the keys by
sending `m.room_key_request`_ to-device messages to other devices with
``action`` set to ``request``. If a device wishes to share the keys with that
device, it can forward the keys to the first device by sending an encrypted
`m.forwarded_room_key`_ to-device message. The first device should then send an
`m.room_key_request`_ to-device message with ``action`` set to
``request_cancellation`` to the other devices that it had originally sent the key
request to; a device that receives a ``request_cancellation`` should disregard any
previously-received ``request`` message with the same ``request_id`` and
``requesting_device_id``.

.. NOTE::

  Key sharing can be a big attack vector, thus it must be done very carefully.
  A reasonable strategy is for a user's client to only send keys requested by the
  verified devices of the same user.

Server-side key backups
~~~~~~~~~~~~~~~~~~~~~~~

Devices may upload encrypted copies of keys to the server. When a device tries
to read a message that it does not have keys for, it may request the key from
the server and decrypt it. Backups are per-user, and users may replace backups
with new backups.

In contrast with `Key requests`_, Server-side key backups do not require another
device to be online from which to request keys. However, as the session keys are
stored on the server encrypted, it requires users to enter a decryption key to
decrypt the session keys.

To create a backup, a client will call `POST
/_matrix/client/r0/room_keys/version`_ and define how the keys are to be
encrypted through the backup's ``auth_data``; other clients can discover the
backup by calling `GET /_matrix/client/r0/room_keys/version/{version}`_,
setting ``{version}`` to the empty string.  Keys are encrypted according to the
backups ``auth_data`` and added to the backup by calling `PUT
/_matrix/client/r0/room_keys/keys`_ or one of its variants, and can be
retrieved by calling `GET /_matrix/client/r0/room_keys/keys`_ or one of its
variants.  Keys can only be written to the most recently created version of the
backup.  Backups can also be deleted using `DELETE
/_matrix/client/r0/room_keys/version/{version}`_, or individual keys can be
deleted using `DELETE /_matrix/client/r0/room_keys/keys`_ or one of its
variants.

Clients must only store keys in backups after they have ensured that the
``auth_data`` is trusted, either by checking the signatures on it, or by
deriving the public key from a private key that it obtained from a trusted
source.

When a client uploads a key for a session that the server already has a key
for, the server will choose to either keep the existing key or replace it with
the new key based on the key metadata as follows:

- if the keys have different values for ``is_verified``, then it will keep the
  key that has ``is_verified`` set to ``true``;
- if they have the same values for ``is_verified``, then it will keep the key
  with a lower ``first_message_index``;
- and finally, is ``is_verified`` and ``first_message_index`` are equal, then
  it will keep the key with a lower ``forwarded_count``.

Recovery key
<<<<<<<<<<<<

If the recovery key (the private half of the backup encryption key) is
presented to the user to save, it is presented as a string constructed as
follows:

1. The 256-bit curve25519 private key is prepended by the bytes ``0x8B`` and
   ``0x01``
2. All the bytes in the string above, including the two header bytes, are XORed
   together to form a parity byte. This parity byte is appended to the byte
   string.
3. The byte string is encoded using base58, using the same `mapping as is used
   for Bitcoin addresses <https://en.bitcoin.it/wiki/Base58Check_encoding#Base58_symbol_chart>`_.
4. A space should be added after every 4th character.

When reading in a recovery key, clients must disregard whitespace, and perform
the reverse of steps 1 through 3.

Backup algorithm: ``m.megolm_backup.v1.curve25519-aes-sha2``
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

When a backup is created with the ``algorithm`` set to
``m.megolm_backup.v1.curve25519-aes-sha2``, the ``auth_data`` should have the
following format:

``AuthData``

.. table::
   :widths: auto

   ========== =========== ======================================================
   Parameter  Type        Description
   ========== =========== ======================================================
   public_key string      Required. The curve25519 public key used to encrypt
                          the backups, encoded in unpadded base64.
   signatures Signatures  Optional. Signatures of the ``auth_data``, as Signed
                          JSON
   ========== =========== ======================================================

The ``session_data`` field in the backups is constructed as follows:

1. Encode the session key to be backed up as a JSON object with the properties:

   .. table::
      :widths: auto

      =============================== ======== =========================================
      Parameter                       Type     Description
      =============================== ======== =========================================
      algorithm                       string   Required. The end-to-end message
                                               encryption algorithm that the key is
                                               for.  Must be ``m.megolm.v1.aes-sha2``.
      forwarding_curve25519_key_chain [string] Required. Chain of Curve25519 keys
                                               through which this session was
                                               forwarded, via
                                               `m.forwarded_room_key`_ events.
      sender_key                      string   Required. Unpadded base64-encoded
                                               device curve25519 key.
      sender_claimed_keys             {string: Required. A map from algorithm name
                                      string}  (``ed25519``) to the identity key
                                               for the sending device.
      session_key                     string   Required. Unpadded base64-encoded
                                               session key in `session-sharing format
                                               <https://gitlab.matrix.org/matrix-org/olm/blob/master/docs/megolm.md#session-sharing-format>`_.
      =============================== ======== =========================================

2. Generate an ephemeral curve25519 key, and perform an ECDH with the ephemeral
   key and the backup's public key to generate a shared secret.  The public
   half of the ephemeral key, encoded using unpadded base64, becomes the ``ephemeral``
   property of the ``session_data``.
3. Using the shared secret, generate 80 bytes by performing an HKDF using
   SHA-256 as the hash, with a salt of 32 bytes of 0, and with the empty string
   as the info.  The first 32 bytes are used as the AES key, the next 32 bytes
   are used as the MAC key, and the last 16 bytes are used as the AES
   initialization vector.
4. Stringify the JSON object, and encrypt it using AES-CBC-256 with PKCS#7
   padding.  This encrypted data, encoded using unpadded base64, becomes the
   ``ciphertext`` property of the ``session_data``.
5. Pass the raw encrypted data (prior to base64 encoding) through HMAC-SHA-256
   using the MAC key generated above.  The first 8 bytes of the resulting MAC
   are base64-encoded, and become the ``mac`` property of the ``session_data``.

{{key_backup_cs_http_api}}

Key exports
~~~~~~~~~~~

Keys can be manually exported from one device to an encrypted file, copied to
another device, and imported. The file is encrypted using a user-supplied
passphrase, and is created as follows:

1. Encode the sessions as a JSON object, formatted as described in `Key export
   format`_.
2. Generate a 512-bit key from the user-entered passphrase by computing
   `PBKDF2`_\(HMAC-SHA-512, passphrase, S, N, 512), where S is a 128-bit
   cryptographically-random salt and N is the number of rounds.  N should be at
   least 100,000.  The keys K and K' are set to the first and last 256 bits of
   this generated key, respectively.  K is used as an AES-256 key, and K' is
   used as an HMAC-SHA-256 key.
3. Serialize the JSON object as a UTF-8 string, and encrypt it using
   AES-CTR-256 with the key K generated above, and with a 128-bit
   cryptographically-random initialization vector, IV, that has bit 63 set to
   zero. (Setting bit 63 to zero in IV is needed to work around differences in
   implementations of AES-CTR.)
4. Concatenate the following data:

   ============ ===============================================================
   Size (bytes) Description
   ============ ===============================================================
   1            Export format version, which must be ``0x01``.
   16           The salt S.
   16           The initialization vector IV.
   4            The number of rounds N, as a big-endian unsigned 32-bit integer.
   variable     The encrypted JSON object.
   32           The HMAC-SHA-256 of all the above string concatenated together,
                using K' as the key.
   ============ ===============================================================

5. Base64-encode the string above. Newlines may be added to avoid overly long
   lines.
6. Prepend the resulting string with ``-----BEGIN MEGOLM SESSION DATA-----``,
   with a trailing newline, and append ``-----END MEGOLM SESSION DATA-----``,
   with a leading and trailing newline.

Key export format
<<<<<<<<<<<<<<<<<

The exported sessions are formatted as a JSON array of ``SessionData`` objects
described as follows:

``SessionData``

.. table::
   :widths: auto

   =============================== =========== ====================================
   Parameter                       Type        Description
   =============================== =========== ====================================
   algorithm                       string      Required. The encryption algorithm
                                               that the session uses. Must be
                                               ``m.megolm.v1.aes-sha2``.
   forwarding_curve25519_key_chain [string]    Required. Chain of Curve25519 keys
                                               through which this session was
                                               forwarded, via
                                               `m.forwarded_room_key`_ events.
   room_id                         string      Required. The room where the
                                               session is used.
   sender_key                      string      Required. The Curve25519 key of the
                                               device which initiated the session
                                               originally.
   sender_claimed_keys             {string:    Required. The Ed25519 key of the
                                   string}     device which initiated the session
                                               originally.
   session_id                      string      Required. The ID of the session.
   session_key                     string      Required. The key for the session.
   =============================== =========== ====================================

This is similar to the format before encryption used for the session keys in
`Server-side key backups`_ but adds the ``room_id`` and ``session_id`` fields.

Example:

.. code:: json

    {
        "sessions": [
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
    }

Messaging Algorithms
--------------------

Messaging Algorithm Names
~~~~~~~~~~~~~~~~~~~~~~~~~

Messaging algorithm names use the extensible naming scheme used throughout this
specification. Algorithm names that start with ``m.`` are reserved for
algorithms defined by this specification. Implementations wanting to experiment
with new algorithms must be uniquely globally namespaced following Java's package
naming conventions.

Algorithm names should be short and meaningful, and should list the primitives
used by the algorithm so that it is easier to see if the algorithm is using a
broken primitive.

A name of ``m.olm.v1`` is too short: it gives no information about the primitives
in use, and is difficult to extend for different primitives. However a name of
``m.olm.v1.ecdh-curve25519-hdkfsha256.hmacsha256.hkdfsha256-aes256-cbc-hmac64sha256``
is too long despite giving a more precise description of the algorithm: it adds
to the data transfer overhead and sacrifices clarity for human readers without
adding any useful extra information.

``m.olm.v1.curve25519-aes-sha2``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The name ``m.olm.v1.curve25519-aes-sha2`` corresponds to version 1 of the Olm
ratchet, as defined by the `Olm specification`_. This uses:

* Curve25519 for the initial key agreement.
* HKDF-SHA-256 for ratchet key derivation.
* Curve25519 for the root key ratchet.
* HMAC-SHA-256 for the chain key ratchet.
* HKDF-SHA-256, AES-256 in CBC mode, and 8 byte truncated HMAC-SHA-256 for authenticated encryption.

Devices that support Olm must include "m.olm.v1.curve25519-aes-sha2" in their
list of supported messaging algorithms, must list a Curve25519 device key, and
must publish Curve25519 one-time keys.

An event encrypted using Olm has the following format:

.. code:: json

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

``ciphertext`` is a mapping from device Curve25519 key to an encrypted payload
for that device. ``body`` is a Base64-encoded Olm message body. ``type`` is an
integer indicating the type of the message body: 0 for the initial pre-key
message, 1 for ordinary messages.

Olm sessions will generate messages with a type of 0 until they receive a
message. Once a session has decrypted a message it will produce messages with
a type of 1.

When a client receives a message with a type of 0 it must first check if it
already has a matching session. If it does then it will use that session to
try to decrypt the message. If there is no existing session then the client
must create a new session and use the new session to decrypt the message. A
client must not persist a session or remove one-time keys used by a session
until it has successfully decrypted a message using that session.

Messages with type 1 can only be decrypted with an existing session. If there
is no matching session, the client must treat this as an invalid message.

The plaintext payload is of the form:

.. code:: json

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

The type and content of the plaintext message event are given in the payload.

Other properties are included in order to prevent an attacker from publishing
someone else's curve25519 keys as their own and subsequently claiming to have
sent messages which they didn't.
``sender`` must correspond to the user who sent the event, ``recipient`` to
the local user, and ``recipient_keys`` to the local ed25519 key.

Clients must confirm that the ``sender_key`` and the ``ed25519`` field value
under the ``keys`` property match the keys returned by |/keys/query|_ for
the given user, and must also verify the signature of the payload. Without
this check, a client cannot be sure that the sender device owns the private
part of the ed25519 key it claims to have in the Olm payload.
This is crucial when the ed25519 key corresponds to a verified device.

If a client has multiple sessions established with another device, it should
use the session from which it last received and successfully decrypted a
message. For these purposes, a session that has not received any messages
should use its creation time as the time that it last received a message.
A client may expire old sessions by defining a maximum number of olm sessions
that it will maintain for each device, and expiring sessions on a Least Recently
Used basis.  The maximum number of olm sessions maintained per device should
be at least 4.

Recovering from undecryptable messages
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

Occasionally messages may be undecryptable by clients due to a variety of reasons.
When this happens to an Olm-encrypted message, the client should assume that the Olm
session has become corrupted and create a new one to replace it.

.. Note::
   Megolm-encrypted messages generally do not have the same problem. Usually the key
   for an undecryptable Megolm-encrypted message will come later, allowing the client
   to decrypt it successfully. Olm does not have a way to recover from the failure,
   making this session replacement process required.

To establish a new session, the client sends a `m.dummy <#m-dummy>`_ to-device event
to the other party to notify them of the new session details.

Clients should rate-limit the number of sessions it creates per device that it receives
a message from. Clients should not create a new session with another device if it has
already created one for that given device in the past 1 hour.

Clients should attempt to mitigate loss of the undecryptable messages. For example,
Megolm sessions that were sent using the old session would have been lost. The client
can attempt to retrieve the lost sessions through ``m.room_key_request`` messages.


``m.megolm.v1.aes-sha2``
~~~~~~~~~~~~~~~~~~~~~~~~

The name ``m.megolm.v1.aes-sha2`` corresponds to version 1 of the Megolm
ratchet, as defined by the `Megolm specification`_. This uses:

* HMAC-SHA-256 for the hash ratchet.
* HKDF-SHA-256, AES-256 in CBC mode, and 8 byte truncated HMAC-SHA-256 for authenticated encryption.
* Ed25519 for message authenticity.

Devices that support Megolm must support Olm, and include "m.megolm.v1.aes-sha2" in
their list of supported messaging algorithms.

An event encrypted using Megolm has the following format:

.. code:: json

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

The encrypted payload can contain any message event. The plaintext is of the form:

.. code:: json

    {
      "type": "<event_type>",
      "content": "<event_content>",
      "room_id": "<the room_id>"
    }

We include the room ID in the payload, because otherwise the homeserver would
be able to change the room a message was sent in.

Clients must guard against replay attacks by keeping track of the ratchet indices
of Megolm sessions. They should reject messages with a ratchet index that they
have already decrypted. Care should be taken in order to avoid false positives, as a
client may decrypt the same event twice as part of its normal processing.

As with Olm events, clients must confirm that the ``sender_key`` belongs to the user
who sent the message. The same reasoning applies, but the sender ed25519 key has to be
inferred from the ``keys.ed25519`` property of the event which established the Megolm
session.

In order to enable end-to-end encryption in a room, clients can send a
``m.room.encryption`` state event specifying ``m.megolm.v1.aes-sha2`` as its
``algorithm`` property.

When creating a Megolm session in a room, clients must share the corresponding session
key using Olm with the intended recipients, so that they can decrypt future messages
encrypted using this session. A ``m.room_key`` event is used to do this. Clients
must also handle ``m.room_key`` events sent by other devices in order to decrypt their
messages.

Protocol definitions
--------------------

Events
~~~~~~

{{m_room_encryption_event}}

{{m_room_encrypted_event}}

{{m_room_key_event}}

{{m_room_key_request_event}}

{{m_forwarded_room_key_event}}

{{m_dummy_event}}

Key management API
~~~~~~~~~~~~~~~~~~

{{keys_cs_http_api}}


.. anchor for link from /sync api spec
.. |device_lists_sync| replace:: End-to-end encryption
.. _device_lists_sync:

Extensions to /sync
~~~~~~~~~~~~~~~~~~~

This module adds an optional ``device_lists`` property to the |/sync|_
response, as specified below. The server need only populate this property for
an incremental ``/sync`` (ie, one where the ``since`` parameter was
specified). The client is expected to use |/keys/query|_ or |/keys/changes|_
for the equivalent functionality after an initial sync, as documented in
`Tracking the device list for a user`_.

It also adds a ``one_time_keys_count`` property. Note the spelling difference
with the ``one_time_key_counts`` property in the |/keys/upload|_ response.

.. todo: generate this from a swagger definition?

.. device_lists: { changed: ["@user:server", ... ]},

============ =========== =====================================================
Parameter    Type        Description
============ =========== =====================================================
device_lists DeviceLists Optional. Information on e2e device updates. Note:
                         only present on an incremental sync.
|device_otk| {string:    Optional. For each key algorithm, the number of
             integer}    unclaimed one-time keys currently held on the server
                         for this device.
============ =========== =====================================================

``DeviceLists``

========= ========= =============================================
Parameter Type      Description
========= ========= =============================================
changed   [string]  List of users who have updated their device identity keys,
                    or who now share an encrypted room with the client since
                    the previous sync response.
left      [string]  List of users with whom we do not share any encrypted rooms
                    anymore since the previous sync response.
========= ========= =============================================

.. NOTE::

  For optimal performance, Alice should be added to ``changed`` in Bob's sync only
  when she adds a new device, or when Alice and Bob now share a room but didn't
  share any room previously. However, for the sake of simpler logic, a server
  may add Alice to ``changed`` when Alice and Bob share a new room, even if they
  previously already shared a room.

Example response:

.. code:: json

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

.. References

.. _ed25519: http://ed25519.cr.yp.to/
.. _curve25519: https://cr.yp.to/ecdh.html
.. _`Olm specification`: http://matrix.org/docs/spec/olm.html
.. _`Megolm specification`: http://matrix.org/docs/spec/megolm.html
.. _`JSON Web Key`: https://tools.ietf.org/html/rfc7517#appendix-A.3
.. _`W3C extension`: https://w3c.github.io/webcrypto/#iana-section-jwk
.. _`PBKDF2`: https://tools.ietf.org/html/rfc2898#section-5.2

.. _`Signing JSON`: ../appendices.html#signing-json

.. |m.olm.v1.curve25519-aes-sha2| replace:: ``m.olm.v1.curve25519-aes-sha2``
.. |device_otk| replace:: device_one_time_keys_count

.. |/keys/upload| replace:: ``/keys/upload``
.. _/keys/upload: #post-matrix-client-%CLIENT_MAJOR_VERSION%-keys-upload

.. |/keys/query| replace:: ``/keys/query``
.. _/keys/query: #post-matrix-client-%CLIENT_MAJOR_VERSION%-keys-query

.. |/keys/claim| replace:: ``/keys/claim``
.. _/keys/claim: #post-matrix-client-%CLIENT_MAJOR_VERSION%-keys-claim

.. |/keys/changes| replace:: ``/keys/changes``
.. _/keys/changes: #get-matrix-client-%CLIENT_MAJOR_VERSION%-keys-changes
