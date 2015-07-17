End-to-End Encryption
=====================

.. TODO-doc
  - Why is this needed.
  - Overview of process
  - Implementation

Matrix optionally supports end-to-end encryption, allowing rooms to be created
whose conversation contents is not decryptable or interceptable on any of the
participating homeservers.

End-to-end crypto is still being designed and prototyped - notes on the design
may be found at https://lwn.net/Articles/634144/


Overview
========

.. code::

    1) Bob publishes the public keys and supported algorithms for his device.

                                          +----------+  +--------------+
                                          | Bob's HS |  | Bob's Device |
                                          +----------+  +--------------+
                                                |              |
                                                |<=============|
                                                  /keys/upload

    2) Alice requests Bob's public key and supported algorithms.

      +----------------+  +------------+  +----------+
      | Alice's Device |  | Alice's HS |  | Bob's HS |
      +----------------+  +------------+  +----------+
             |                  |               |
             |=================>|==============>|
               /keys/query        <federation>

    3) Alice selects an algorithm claims any one-time keys needed.

      +----------------+  +------------+  +----------+
      | Alice's Device |  | Alice's HS |  | Bob's HS |
      +----------------+  +------------+  +----------+
             |                  |               |
             |=================>|==============>|
               /keys/claim         <federation>

    4) Alice sends an encrypted message to Bob.

      +----------------+  +------------+  +----------+  +--------------+
      | Alice's Device |  | Alice's HS |  | Bob's HS |  | Bob's Device |
      +----------------+  +------------+  +----------+  +--------------+
             |                  |               |              |
             |----------------->|-------------->|------------->|
               /send/             <federation>     <events>


Client Behaviour
----------------

Uploading Keys
~~~~~~~~~~~~~~

Keys are uploaded as a signed JSON object. The JSON object must include an
ed25519 key and must be signed by that key. A device may only have one ed25519
signing key. This key is used as the fingerprint for a device by other clients.

The JSON object is signed using the process given by `Signing JSON`_.


.. code:: http

    POST /_matrix/client/v2_alpha/keys/upload/<device_id> HTTP/1.1
    Content-Type: application/json

    {
      "device_keys": {
        "user_id": "<user_id>",
        "device_id": "<device_id>",
        "valid_after_ts": 1234567890123,
        "valid_until_ts": 2345678901234,
        "algorithms": [
          "<algorithm-name>",
        ],
        "keys": {
          "<algorithm>:<device_id>": "<key_base64>",
        },
        "signatures:" {
          "<user_id>" {
            "<algorithm>:<device_id>": "<signature_base64>"
      } } },
      "one_time_keys": {
        "<algorithm>:<key_id>": "<key_base64>"
    } }

.. code:: http

    200 OK
    Content-Type: application/json

    {
      "one_time_key_counts": {
        "<algorithm>": 50
      }
    }


Downloading Keys
~~~~~~~~~~~~~~~~

Keys are downloaded as a collection of signed JSON objects. There
will be a JSON object per device per user. If one of the user's
devices doesn't support end-to-end encryption then their
homeserver must synthesise a JSON object without any device keys
for that device.

The JSON must be signed by both the homeserver of
the user querying the keys and by the homeserver of the device
being queried. This provides an audit trail if either homeserver
lies about the keys a user owns.

.. code:: http

    POST /keys/query HTTP/1.1
    Content-Type: application/json

    {
      "device_keys": {
        "<user_id>": ["<device_id>"]
    } }


.. code:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

    {
      "device_keys": {
        "<user_id>": {
          "<device_id>": {
            "user_id": "<user_id>",
            "device_id": "<device_id>",
            "valid_after_ts": 1234567890123,
            "valid_until_ts": 2345678901234,
            "algorithms": [
              "<algorithm_name>",
            ],
            "keys": {
              "<algorithm>:<device_id>": "<key_base64>",
            },
            "signatures:" {
              "<user_id>": {
                "<algorithm>:<device_id>": "<signature_base64>"
              },
              "<local_server_name>": {
                "<algorithm>:<key_id>": "<signature_base64>"
              },
              "<remote_server_name>": {
                "<algorithm>:<key_id>": "<signature_base64>"
    } } } } } }


Claiming One Time Keys
~~~~~~~~~~~~~~~~~~~~~~

Some algorithms require one-time keys to improve their secrecy and deniability.
These keys are used once during session establishment, and are then thrown
away. In order for these keys to be useful for improving deniability they
must not be signed using the ed25519 key for a device.

A device must generate a number of these keys and publish them onto their
homeserver. A device must periodically check how many one-time keys their
homeserver still has. If the number has become too small then the device must
generate new one-time keys and upload them to the homeserver.

Devices must store the private part of each one-time key they upload. They can
discard the private part of the one-time key when they receive a message using
that key. However it's possible that a one-time key given out by a homeserver
will never be used, so the device that generates the key will never know that
it can discard the key. Therefore a device could end up trying to store too
many private keys. A device that is trying to store too many private keys may
discard keys starting with the oldest.

A homeserver should ratelimit the number of one-time keys that a given user or
remote server can claim. A homeserver should discard the public part of a one
time key once it has given that key to another user.


.. code:: http

    POST /keys/claim HTTP/1.1
    Content-Type: application/json

    {
      "one_time_keys": {
        "<user_id>": {
          "<device_id>": "<algorithm>"
    } } }

.. code:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

    {
      "one_time_keys": {
        "<user_id>": {
          "<device_id>": {
            "<algorithm>:<key_id>": "<key_base64>"
    } } } }


Sending a Message
~~~~~~~~~~~~~~~~~

Encrypted messages are sent in the form.

.. code:: json

    {
        "type": "m.room.encrypted"
        "content": {
            "algorithm": "<algorithm_name>"
        }
    } }


.. code:: json

    {
        "type": "m.room.message"
        "content": {
            "algorithm": "m.olm.v1.curve25519-aes-sha2",
            "sender_key": <sender_curve25519_key>,
            "ciphertexts": {
                "<device_curve25519_key>: {
                    "type": 0,
                    "body": "<base_64>"
    }   }   }   }


The plaintext payload is of the form:

.. code:: json

   TODO: SPEC the JSON plaintext format
