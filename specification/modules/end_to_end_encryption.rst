.. Copyright 2016 OpenMarket Ltd
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
whose conversation contents is not decryptable or interceptable on any of the
participating homeservers.

.. WARNING::
  End-to-end crypto is still being designed and prototyped. The following is
  subject to change as the design evolves.

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


Key Algorithms
~~~~~~~~~~~~~~

The name ``ed25519`` corresponds to the `Ed25519`_ signature algorithm. The key
is a Base64-encoded 32-byte Ed25519 public key.

The name ``curve25519`` corresponds to the `Curve25519`_ ECDH algorithm. The
key is a Base64-encoded 32-byte Curve25519 public key.

The name ``signed_curve25519`` also corresponds to the Curve25519 algorithm,
but keys using this algorithm are objects with the properties ``key`` (giving
the Base64-encoded 32-byte Curve25519 public key), and ``signatures`` (giving a
signature for the key object, as described in `Signing JSON`_).

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

For Olm version 1 (see |m.olm.v1.curve25519-aes-sha2|_), each device requires a single
Curve25519 identity key, and a number of Curve25519 one-time keys.

Uploading Keys
~~~~~~~~~~~~~~

A device uploads the public parts of identity keys to their homeserver as a
signed JSON object, using the |/keys/upload|_ API.
The JSON object must include the public part of the device's Ed25519 key, and
must be signed by that key, as described in `Signing JSON`_.

One-time keys are also uploaded to the homeserver.

Devices must store the private part of each key they upload. They can
discard the private part of a one-time key when they receive a message using
that key. However it's possible that a one-time key given out by a homeserver
will never be used, so the device that generates the key will never know that
it can discard the key. Therefore a device could end up trying to store too
many private keys. A device that is trying to store too many private keys may
discard keys starting with the oldest.

Downloading Keys
~~~~~~~~~~~~~~~~

Keys are downloaded as a collection of signed JSON objects, using the
|/keys/query|_ API.

Claiming One-Time Keys
~~~~~~~~~~~~~~~~~~~~~~

A client wanting to set up a session with another device can claim a one-time
key for that device. This is done by making a request to the |/keys/claim|_
API.

A homeserver should rate-limit the number of one-time keys that a given user or
remote server can claim. A homeserver should discard the public part of a one
time key once it has given that key to another user.


Messaging Algorithms
--------------------

Messaging Algorithm Names
~~~~~~~~~~~~~~~~~~~~~~~~~

Messaging algorithm names use the extensible naming scheme used throughout this
specification. Algorithm names that start with ``m.`` are reserved for
algorithms defined by this specification. Implementations wanting to experiment
with new algorithms are encouraged to pick algorithm names that start with
their domain to reduce the risk of collisions.

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
* Curve25519 for the DH ratchet.
* HMAC-SHA-256 for the hash ratchet.
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
            "body": "<base_64>"
    } } } }

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
is no matching session, the client should show this as an invalid message.

The plaintext payload is of the form:

.. code:: json

   {
     "type": "<type of the plaintext event>",
     "content": "<content for the plaintext event>",
     "room_id": "<the room_id>",
   }

The type and content of the plaintext message event are given in the payload.

We include the room ID in the payload, because otherwise the homeserver would
be able to change the room a message was sent in.

.. TODO: claimed_keys

Clients must confirm that the ``sender_key`` belongs to the user that sent the
message. TODO: how?

``m.megolm.v1.aes-sha2``
~~~~~~~~~~~~~~~~~~~~~~~~

The name ``m.megolm.v1.aes-sha2`` corresponds to version 1 of the Megolm
ratchet, as defined by the `Megolm specification`_. This uses:

* HMAC-SHA-256 for the hash ratchet.
* HKDF-SHA-256, AES-256 in CBC mode, and 8 byte truncated HMAC-SHA-256 for authenticated encryption.
* Ed25519 for message authenticity.


Events
------

{{m_room_encryption_event}}

{{m_room_encrypted_event}}

{{m_room_key_event}}

{{m_new_device_event}}

Key management API
------------------

{{keys_cs_http_api}}


.. References

.. _ed25519: http://ed25519.cr.yp.to/
.. _curve25519: https://cr.yp.to/ecdh.html
.. _`Olm specification`: http://matrix.org/docs/spec/olm.html
.. _`Megolm specification`: http://matrix.org/docs/spec/megolm.html

.. TODO-spec:
   move json-signing algorithm out of the s2s spec
.. _`Signing JSON`: ../server_server/unstable.html#signing-json

.. |m.olm.v1.curve25519-aes-sha2| replace:: ``m.olm.v1.curve25519-aes-sha2``

.. |/keys/upload| replace:: ``/keys/upload``
.. _/keys/upload: #post-matrix-client-%CLIENT_MAJOR_VERSION%-keys-upload

.. |/keys/query| replace:: ``/keys/query``
.. _/keys/query: #post-matrix-client-%CLIENT_MAJOR_VERSION%-keys-query

.. |/keys/claim| replace:: ``/keys/claim``
.. _/keys/claim: #post-matrix-client-%CLIENT_MAJOR_VERSION%-keys-claim
