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

End to end encryption is being worked on and will be coming soon.

You can read about what's underway at http://matrix.org/speculator/spec/drafts%2Fe2e/client_server/unstable.html#end-to-end-encryption.

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

Downloading Identity Keys
~~~~~~~~~~~~~~~~~~~~~~~~~

Identity keys are downloaded as a collection of signed JSON objects, using the
|/keys/query|_ API.

Claiming one-time keys
~~~~~~~~~~~~~~~~~~~~~~

A client wanting to set up a session with another device can claim a one-time
key for that device. This is done by making a request to the |/keys/claim|_
API.

A homeserver should rate-limit the number of one-time keys that a given user or
remote server can claim. A homeserver should discard the public part of a one
time key once it has given that key to another user.

Protocol definitions
--------------------

{{keys_cs_http_api}}


.. anchor for link from /sync api spec
.. |device_lists_sync| replace:: End-to-end encryption
.. _device_lists_sync:

Extensions to /sync
~~~~~~~~~~~~~~~~~~~

This module adds the following properties to the |/sync|_ response:

.. todo: generate this from a swagger definition?

.. device_lists: { changed: ["@user:server", ... ]},

============ =========== =====================================================
Parameter    Type        Description
============ =========== =====================================================
device_lists DeviceLists Optional. Information on e2e device updates.
============ =========== =====================================================

``DeviceLists``

========= ========= =============================================
Parameter Type      Description
========= ========= =============================================
changed   [string]  List of users who have updated their device identity keys
                    since the previous sync response.
========= ========= =============================================


Example response:

.. code:: json

  {
    "next_batch": "s72595_4483_1934",
    "rooms": {"leave": {}, "join": {}, "invite": {}},
    "device_lists": {
      "changed": [
         "@alice:example.com",
      ],
    },
  }

.. References

.. _ed25519: http://ed25519.cr.yp.to/
.. _curve25519: https://cr.yp.to/ecdh.html

.. _`Signing JSON`: ../appendices.html#signing-json

.. |m.olm.v1.curve25519-aes-sha2| replace:: ``m.olm.v1.curve25519-aes-sha2``

.. |/keys/upload| replace:: ``/keys/upload``
.. _/keys/upload: #post-matrix-client-%CLIENT_MAJOR_VERSION%-keys-upload

.. |/keys/query| replace:: ``/keys/query``
.. _/keys/query: #post-matrix-client-%CLIENT_MAJOR_VERSION%-keys-query

.. |/keys/claim| replace:: ``/keys/claim``
.. _/keys/claim: #post-matrix-client-%CLIENT_MAJOR_VERSION%-keys-claim
