---
layout: post
title: End-to-End Encryption implementation guide
categories: guides
---

Implementing End-to-End Encryption in Matrix clients
====================================================

This guide is intended for authors of Matrix clients who wish to add
support for end-to-end encryption. It is highly recommended that readers
be familiar with the Matrix protocol and the use of access tokens before
proceeding.

.. contents::

The libolm library
------------------

End-to-end encryption in Matrix is based on the Olm and Megolm
cryptographic ratchets. The recommended starting point for any client
authors is with the `libolm <http://matrix.org/git/olm>`__ library,
which contains implementations of all of the cryptographic primitives
required. The library itself is written in C/C++, but is architected in
a way which makes it easy to write wrappers for higher-level languages.

Devices
-------

We have a particular meaning for “device”. As a user, I might have
several devices (a desktop client, some web browsers, an Android device,
an iPhone, etc). When I first use a client, it should register itself as
a new device. If I log out and log in again as a different user, the
client must register as a new device. Critically, the client must create
a new set of keys (see below) for each “device”.

The longevity of devices will depend on the client. In the web client,
we create a new device every single time you log in. In a mobile client,
it might be acceptable to reuse the device if a login session expires,
**provided** the user is the same. **Never** share keys between
different users.

Devices are identified by their ``device_id`` (which is unique within
the scope of a given user). By default, the ``/login`` and ``/register``
endpoints will auto-generate a ``device_id`` and return it in the
response; a client is also free to generate its own ``device_id`` or, as
above, reuse a device, in which case the client should pass the
``device_id`` in the request body.

The lifetime of devices and ``access_token``\ s are closely related. In
the simple case where a new device is created each time you log in,
there is a one-to-one mapping between a ``device_id`` and an
``access_token``. If a client reuses a ``device_id`` when logging
in, there will be several ``access_token``\ s associated with a
given ``device_id`` - but still, we would expect only one of these to be
active at once (though we do not currently enforce that in Synapse).

Keys used in End-to-End encryption
----------------------------------

There are a number of keys involved in encrypted communication: a
summary of them follows.

Ed25519 fingerprint key pair
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ed25519 is a public-key cryptographic system for signing messages. In
Matrix, each device has an Ed25519 key pair which serves to identify
that device. The private part of the key pair should never leave the
device, but the public part is published to the Matrix network.

Curve25519 identity key pair
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Curve25519 is a public-key cryptographic system which can be used to
establish a shared secret. In Matrix, each device has a long-lived
Curve25519 identity key which is used to establish Olm sessions with
that device. Again, the private key should never leave the device, but
the public part is signed with the Ed25519 fingerprint key and published
to the network.

Theoretically we should rotate the Curve25519 identity key from time to
time, but we haven't implemented this yet.

Curve25519 one-time keys
~~~~~~~~~~~~~~~~~~~~~~~~

As well as the identity key, each device creates a number of Curve25519
key pairs which are also used to establish Olm sessions, but can only be
used once. Once again, the private part remains on the device.

At startup, Alice creates a number of one-time key pairs, and publishes
them to her homeserver. If Bob wants to establish an Olm session with
Alice, he needs to claim one of Alice’s one-time keys, and creates a new
one of his own. Those two keys, along with Alice’s and Bob’s identity
keys, are used in establishing an Olm session between Alice and Bob.

Megolm encryption keys
~~~~~~~~~~~~~~~~~~~~~~

The Megolm key is used to encrypt group messages (in fact it is used to
derive an AES-256 key, and an HMAC-SHA-256 key). It is initialised with
random data. Each time a message is sent, a hash calculation is done on
the Megolm key to derive the key for the next message. It is therefore
possible to share the current state of the Megolm key with a user,
allowing them to decrypt future messages but not past messages.

Ed25519 Megolm signing key pair
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a sender creates a Megolm session, he also creates another Ed25519
signing key pair. This is used to sign messages sent via that Megolm
session, to authenticate the sender. Once again, the private part of the
key remains on the device. The public part is shared with other devices
in the room alongside the encryption key.

Creating and registering device keys
------------------------------------

This process only happens once, when a device first starts.

It must create the Ed25519 fingerprint key pair and the Curve25519
identity key pair. This is done by calling ``olm_create_account`` in
libolm. The (base64-encoded) keys are retrieved by calling
``olm_account_identity_keys``. The account should be stored for future
use.

It should then publish these keys to the homeserver. To do this, it
should construct a JSON object as follows:

.. code:: json

  {
    "algorithms": ["m.olm.v1.curve25519-aes-sha2", "m.megolm.v1.aes-sha2"],
    "device_id": "<device_id>",
    "keys": {
      "curve25519:<device_id>": "<curve25519_key>",
      "ed25519:<device_id>": "<ed25519_key>"
    },
    "user_id: <user_id>"
  }

The object should be formatted as `Canonical
JSON <http://matrix.org/docs/spec/server_server/unstable.html#canonical-json>`__,
then signed with ``olm_account_sign``; the signature should be added to
the JSON as ``signatures.<user_id>.ed25519:<device_id>``.

The signed JSON is then uploaded via
``POST /_matrix/client/unstable/keys/upload``.

Creating and registering one-time keys
--------------------------------------

At first start, and at regular intervals
thereafter\ [#]_, the client should check how
many one-time keys the homeserver has stored for it, and, if necessary,
generate and upload some more.

.. [#] Every 10 minutes is suggested.

The number of one-time keys currently stored is returned by
``POST /_matrix/client/unstable/keys/upload``. (Post an empty JSON object
``{}`` if you don’t want to upload the device keys.)

The maximum number of active keys supported by libolm is returned by
``olm_account_max_number_of_one_time_keys``. The client should try to
maintain about half this number on the homeserver.

To generate new one-time keys:

* Call ``olm_account_generate_one_time_keys`` to generate new keys.

* Call ``olm_account_one_time_keys`` to retrieve the unpublished keys. This
  returns a JSON-formatted object with the single property ``curve25519``,
  which is itself an object mapping key id to base64-encoded Curve25519
  key. For example:

  .. code:: json

    {
      "curve25519": {
        "AAAAAA": "wo76WcYtb0Vk/pBOdmduiGJ0wIEjW4IBMbbQn7aSnTo",
        "AAAAAB": "LRvjo46L1X2vx69sS9QNFD29HWulxrmW11Up5AfAjgU"
      }
    }

* Each key should be signed with the account key. To do this:

  * Construct a JSON object as follows:

    .. code:: json

       {
         "key": "<curve25519_key>"
       }

  * Call ``olm_account_sign`` to calculate the signature.

  * Add the signature should be added to the JSON as
    ``signatures.<user_id>.ed25519:<device_id>``.

  * The complete key object should now look like:

    .. code:: json

       {
         "key": "wo76WcYtb0Vk/pBOdmduiGJ0wIEjW4IBMbbQn7aSnTo",
         "signatures": {
           "@alice:example.com": {
             "ed25519:JLAFKJWSCS": "dSO80A01XiigH3uBiDVx/EjzaoycHcjq9lfQX0uWsqxl2giMIiSPR8a4d291W1ihKJL/a+myXS367WT6NAIcBA"
           }
         }
       }


* Aggregate all the signed one-time keys into a single JSON object as follows:

  .. code:: json

    {
      "one_time_keys": {
        "signed_curve25519:<key_id>": {
          "key": "<curve25519_key>",
          "signatures": {
            "<user_id>": {
              "ed25519:<device_id>": "<signature>"
            }
          }
        },
        "signed_curve25519:<key_id>": {
          ...
        },
        ...
      }
    }

* Upload the object via ``POST /_matrix/client/unstable/keys/upload``.

* Call ``olm_account_mark_keys_as_published`` to tell the olm library not to
  return the same keys from a future call to ``olm_account_one_time_keys``.

Configuring a room to use encryption
------------------------------------

To enable encryption in a room, a client should send a state event of
type ``m.room.encryption``, and content ``{ "algorithm":
"m.megolm.v1.aes-sha2" }``.

.. |m.room.encryption| replace:: ``m.room.encryption``
.. _`m.room.encryption`:

Handling an ``m.room.encryption`` state event
---------------------------------------------

When a client receives an ``m.room.encryption`` event as above, it
should set a flag to indicate that messages sent in the room should be
encrypted.

This flag should **not** be cleared if a later ``m.room.encryption``
event changes the configuration. This is to avoid a situation where a
MITM can simply ask participants to disable encryption. In short: once
encryption is enabled in a room, it can never be disabled.

The event should contain an ``algorithm`` property which defines which
encryption algorithm should be used for encryption. Currently only
``m.megolm.v1-aes-sha2`` is permitted here.

The event may also include other settings for how messages sent in the room
should be encrypted (for example, ``rotation_period_ms`` to define how often
the session should be replaced).

Handling an ``m.room.encrypted`` event
--------------------------------------

Encrypted events have a type of ``m.room.encrypted``. They have a
content property ``algorithm`` which gives the encryption algorithm in
use, as well as other properties specific to the algorithm [#]_.

.. [#] Note that a redacted event will have an empty content, and hence the
   content will have no ``algorithm`` property. Thus a client should check
   whether an event is redacted before checking for the ``algorithm`` property.

The encrypted payload is a JSON object with the properties ``type``
(giving the decrypted event type), and ``content`` (giving the decrypted
content). Depending on the algorithm in use, the payload may contain
additional keys.

There are currently two defined algorithms:

``m.olm.v1.curve25519-aes-sha2``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Encrypted events using this algorithm should have a ``sender_key`` and a
``ciphertext`` property.

The ``sender_key`` property of the event content gives the Curve25519
identity key of the sender. Clients should maintain a list of known Olm
sessions for each device they speak to; it is recommended to index them
by Curve25519 identity key.

Olm messages are encrypted separately for each recipient device.
``ciphertext`` is an object mapping from the Curve25519 identity key for
the recipient device. The receiving client should, of course, look for
its own identity key in this object. (If it isn't listed, the message
wasn't sent for it, and the client can't decrypt it; it should show an
error instead, or similar).

This should result in an object with the properties ``type`` and
``body``. Messages of type '0' are 'prekey' messages which are used to
establish a new Olm session between two devices; type '1' are normal
messages which are used once a message has been received on the session.

When a message (of either type) is received, a client should first
attempt to decrypt it with each of the known sessions for that sender.
There are two steps to this:

-  If (and only if) ``type==0``, the client should call
   ``olm_matches_inbound_session`` with the session and ``body``. This
   returns a flag indicating whether the message was encrypted using
   that session.

-  The client calls ``olm_decrypt``, with the session, ``type``, and
   ``body``. If this is successful, it returns the plaintext of the
   event.

If the client was unable to decrypt the message using any known sessions
(or if there are no known sessions yet), **and** the message had type 0,
**and** ``olm_matches_inbound_session`` wasn't true for any existing
sessions, then the client can try establishing a new session. This is
done as follows:

-  Call ``olm_create_inbound_session_from`` using the olm account, and
   the ``sender_key`` and ``body`` of the message.

-  If the session was established successfully:

   -  call ``olm_remove_one_time_keys`` to ensure that the same
      one-time-key cannot be reused.

   -  Call ``olm_decrypt`` with the new session

   -  Store the session for future use

At the end of this, the client will hopefully have successfully
decrypted the payload.

As well as the ``type`` and ``content`` properties, the payload should
contain a number of other properties. Each of these should be checked as
follows [#]_.

``sender``
  The user ID of the sender. The client should check that this matches the
  ``sender`` in the event.

``recipient``
  The user ID of the recipient. The client should check that this matches the
  local user ID.

``keys``
  an object with a property ``ed25519``, The client should check that the
  value of this property matches the sender's fingerprint key when `marking
  the event as verified`_\ .

``recipient_keys``
  an object with a property ``ed25519``. The client should check that the
  value of this property matches its own fingerprint key.

.. [#] These tests prevent an attacker publishing someone else's curve25519
   keys as their own and subsequently claiming to have sent messages which they
   didn't.

``m.megolm.v1.aes-sha2``
~~~~~~~~~~~~~~~~~~~~~~~~

Encrypted events using this algorithm should have ``sender_key``,
``session_id`` and ``ciphertext`` content properties. If the
``room_id``, ``sender_key`` and ``session_id`` correspond to a known
Megolm session (see `below`__), the ciphertext can be
decrypted by passing the ciphertext into ``olm_group_decrypt``.

__ `m.room_key`_

In order to avoid replay attacks a client should remember the megolm
``message_index`` returned by ``olm_group_decrypt`` of each event they decrypt
for each session. If the client decrypts an event with the same
``message_index`` as one that it has already received using that session then
it should treat the message as invalid. However, care must be taken when an
event is decrypted multiple times that it is not flagged as a replay attack.
For example, this may happen when the client decrypts an event, the event gets
purged from the client's cache, and then the client backfills and re-decrypts
the event. One way to handle this case is to ensure that the record of
``message_index``\ es is appropriately purged when the client's cache of events
is purged. Another way is to remember the event's ``event_id`` and
``origin_server_ts`` along with its ``message_index``. When the client decrypts
an event with a ``message_index`` matching that of a previously-decrypted
event, it can then compare the ``event_id`` and ``origin_server_ts`` that it
remembered for that ``message_index``, and if those fields match, then the
message should be decrypted as normal.

The client should check that the sender's fingerprint key matches the
``keys.ed25519`` property of the event which established the Megolm session
when `marking the event as verified`_.

.. _`m.room_key`:

Handling an ``m.room_key`` event
--------------------------------

These events contain key data to allow decryption of other messages.
They are sent to specific devices, so they appear in the ``to_device``
section of the response to ``GET /_matrix/client/r0/sync``. They will
also be encrypted, so will need decrypting as above before they can be
seen. (These events are generated by other clients - see `starting a megolm
session`_).

The event content will contain an 'algorithm' property, indicating the
encryption algorithm the key data is to be used for. Currently, this
will always be ``m.megolm.v1.aes-sha2``.

Room key events for Megolm will also have ``room_id``, ``session_id``, and
``session_key`` keys. They are used to establish a Megolm session.  The
``room_id`` identifies which room the session will be used in. The ``room_id``,
together with the ``sender_key`` of the ``room_key`` event before it was
decrypted, and the ``session_id``, uniquely identify a Megolm session. If they
do not represent a known session, the client should start a new inbound Megolm
session by calling ``olm_init_inbound_group_session`` with the ``session_key``.

The client should remember the value of the keys property of the payload
of the encrypted ``m.room_key`` event and store it with the inbound
session. This is used as above when marking the event as verified.

.. _`download the device list`:

Downloading the device list for users in the room
-------------------------------------------------

Before an encrypted message can be sent, it is necessary to retrieve the
list of devices for each user in the room. This can be done proactively,
or deferred until the first message is sent. The information is also
required to allow users to `verify or block devices`__.

__ `blocking`_

The client should build a JSON query object as follows:

.. code:: json

  {
    "device_keys": {
      "<user_id>": {},
      [...]
    }
  }

Each member in the room should be included in the query. This is then
sent via ``POST /_matrix/client/unstable/keys/query.``

The result includes, for each listed user id, a map from device ID to an
object containing information on the device, as follows:

.. code:: json

  {
    "algorithms": [...],
    "device_id": "<device_id>",
    "keys": {
      "curve25519:<device_id>": "<curve25519_key>",
      "ed25519:<device_id>": "<ed25519_key>"
    },
    "signatures": {
      "<userId>": {
        "ed25519:<device_id>": "<signature>"
      },
    },
    "unsigned": {
      "device_display_name": "<display name>"
    },
    "user_id: <user_id>"
  }

The client should first check the signature on this object. To do this,
it should remove the ``signatures`` and ``unsigned`` properties, format
the remainder as Canonical JSON, and pass the result into
``olm_ed25519_verify``, using the Ed25519 key for the ``key`` parameter,
and the corresponding signature for the ``signature`` parameter. If the
signature check fails, no further processing should be done on the
device.

The client must also check that the ``user_id`` and ``device_id`` fields in the
object match those in the top-level map [#]_.

The client should check if the ``user_id``/``device_id`` correspond to a device
it had seen previously. If it did, the client **must** check that the Ed25519
key hasn't changed. Again, if it has changed, no further processing should be
done on the device.

Otherwise the client stores the information about this device.

.. [#] This prevents a malicious or compromised homeserver replacing the keys
       for the device with those of another.

Sending an encrypted event
--------------------------

When sending a message in a room `configured to use encryption`__, a client
first checks to see if it has an active outbound Megolm session. If not, it
first `creates one as per below`__. If an outbound session exists, it should
check if it is time to `rotate`__ it, and create a new one if so.

__ `Configuring a room to use encryption`_
__ `Starting a Megolm session`_
__ `Rotating Megolm sessions`_

The client then builds an encryption payload as follows:

.. code:: json

  {
    "type": "<event type>",
    "content": "<event content>",
    "room_id": "<id of destination room>"
  }

and calls ``olm_group_encrypt`` to encrypt the payload. This is then packaged
into event content as follows:

.. code:: json

  {
    "algorithm": "m.megolm.v1.aes-sha2",
    "sender_key": "<our curve25519 device key>",
    "ciphertext": "<encrypted payload>",
    "session_id": "<outbound group session id>",
    "device_id": "<our device ID>"
  }

Finally, the encrypted event is sent to the room with ``POST
/_matrix/client/r0/rooms/<room_id>/send/m.room.encrypted/<txn_id>``.

Starting a Megolm session
~~~~~~~~~~~~~~~~~~~~~~~~~

When a message is first sent in an encrypted room, the client should
start a new outbound Megolm session. This should **not** be done
proactively, to avoid proliferation of unnecessary Megolm sessions.

To create the session, the client should call
``olm_init_outbound_group_session``, and store the details of the
outbound session for future use.

The client should then call ``olm_outbound_group_session_id`` to get the
unique ID of the new session, and ``olm_outbound_group_session_key`` to
retrieve the current ratchet key and index. It should store these
details as an inbound session, just as it would when `receiving them via
an m.room_key event`__.

__ `m.room_key`_

The client must then share the keys for this session with each device in the
room. It must therefore `download the device list`_ if it hasn't already done
so, and for each device in the room which has not been `blocked`__, the client
should:

__ `blocking`_

* Build a content object as follows:

  .. code:: json

    {
      "algorithm": "m.megolm.v1.aes-sha2",
      "room_id": "<id of destination room>",
      "session_id": "<session id>",
      "session_key": "<session_key>"
    }

-  Encrypt the content as an ``m.room_key`` event using Olm, as below.

Once all of the key-sharing event contents have been assembled, the
events should be sent to the corresponding devices via
``PUT /_matrix/client/unstable/sendToDevice/m.room.encrypted/<txnId>``.

Rotating Megolm sessions
~~~~~~~~~~~~~~~~~~~~~~~~

Megolm sessions may not be reused indefinitely.

The number of messages which can be sent before a session should be rotated is
given by the ``rotation_period_msgs`` property of the |m.room.encryption|_
event, or ``100`` if that property isn't present.

Similarly, the maximum age of a megolm session is given, in milliseconds, by
the ``rotation_period_ms`` property of the ``m.room.encryption``
event. ``604800000`` (a week) is the recommended default here.

Once either the message limit or time limit have been reached, the client
should start a new session before sending any more messages.


Encrypting an event with Olm
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Olm is not used for encrypting room events, as it requires a separate
copy of the ciphertext for each device, and because the receiving device
can only decrypt received messages once. However, it is used for
encrypting key-sharing events for Megolm.

When encrypting an event using Olm, the client should:

-  Build an encryption payload as follows:

   .. code:: json

     {
       "type": "<event type>",
       "content": "<event content>",
       "sender": "<our user ID>",
       "sender_device": "<our device ID>",
       "keys": {
         "ed25519": "<our ed25519 fingerprint key>"
       },
       "recipient": "<recipient user ID>",
       "recipient_keys": {
         "ed25519": "<recipient's ed25519 fingerprint key>"
       },
     }

-  Check if it has an existing Olm session; if it does not, `start a new
   one`__. If it has several (as may happen due to
   races when establishing sessions), it should use the one with the
   first session_id when sorted by their ASCII codepoints (ie, 'A'
   would be before 'Z', which would be before 'a').

   __ `Starting an Olm session`_

-  Encrypt the payload by calling ``olm_encrypt``.

-  Package the payload into event content as follows:

   .. code:: json

     {
       "algorithm": "m.olm.v1.curve25519-aes-sha2",
       "sender_key": "<our curve25519 identity key>",
       "ciphertext": "<encrypted payload>"
     }

Starting an Olm session
~~~~~~~~~~~~~~~~~~~~~~~

To start a new Olm session with another device, a client must first
claim one of the other device's one-time keys. To do this, it should
create a query object as follows:

.. code:: json

  {
    "<user id>": {
      "<device_id>": "signed_curve25519",
      ...
    },
    ...
  }

and send this via ``POST /_matrix/client/unstable/keys/claim``. Claims
for multiple devices should be aggregated into a single request.

This will return a result as follows:

.. code:: json

  {
    "one_time_keys": {
      "<user id>": {
        "<device_id>": {
          "signed_curve25519:<key_id>": {
            "key": "<curve25519_key>",
            "signatures": {
              "<user_id>": {
                "ed25519:<device_id>": "<signature>"
              }
            }
          },
        },
        ...
      },
      ...
    }
  }

The client should first check the signatures on the signed key objects. As with
checking the signatures on the device keys, it should remove the ``signatures``
and (if present) ``unsigned`` properties, format the remainder as Canonical
JSON, and pass the result into ``olm_ed25519_verify``, using the Ed25519 device
key for the ``key`` parameter.

Provided the key object passes verification, the client should then pass the
key, along with the Curve25519 Identity key for the remote device, into
``olm_create_outbound_session``.

Handling membership changes
---------------------------

The client should monitor rooms which are configured to use encryption for
membership changes.

When a member leaves a room, the client should invalidate any active outbound
Megolm session, to ensure that a new session is used next time the user sends a
message.

When a new member joins a room, the client should first `download the device
list`_ for the new member, if it doesn't already have it.

After giving the user an opportunity to `block`__ any suspicious devices, the
client should share the keys for the outbound Megolm session with all the new
member's devices. This is done in the same way as `creating a new session`__,
except that there is no need to start a new Megolm session: due to the design
of the Megolm ratchet, the new user will only be able to decrypt messages
starting from the current state. The recommended method is to maintain a list
of members who are waiting for the session keys, and share them when the user
next sends a message.

__ `blocking`_
__ `Starting a Megolm session`_

Sending New Device announcements
--------------------------------

When a user logs in on a new device, it is necessary to make sure that
other devices in any rooms with encryption enabled are aware of the new
device. This is done as follows.

Once the initial call to the ``/sync`` API completes, the client should
iterate through each room where encryption is enabled. For each user
(including the client's own user), it should build a content object as
follows:

.. code:: json

  {
    "device_id": "<our device ID>",
    "rooms": ["<shared room id 1>", "<room id 2>", ... ]
  }

Once all of these have been constructed, they should be sent to all of the
relevant user's devices (using the wildcard ``*`` in place of the
``device_id``) via ``PUT
/_matrix/client/unstable/sendToDevice/m.new_device/<txnId>.``

Handling an ``m.new_device`` event
----------------------------------

As with ``m.room_key`` events, these will appear in the ``to_device``
section of the ``/sync`` response.

The client should `download the device list`_ of the sender, to get the details
of the new device.

The event content will contain a ``rooms`` property, as well as the
``device_id`` of the new device. For each room in the list, the client
should check if encryption is enabled, and if the sender of the event is
a member of that room. If so, the client should share the keys for the
outbound Megolm session with the new device, in the same way as
`handling a new user in the room`__.

__ `Handling membership changes`_

.. _`blocking`:

Blocking / Verifying devices
----------------------------

It should be possible for a user to mark each device belonging to
another user as 'Blocked' or 'Verified'.

When a user chooses to block a device, this means that no further
encrypted messages should be shared with that device. In short, it
should be excluded when sharing room keys when `starting a new Megolm
session <#_p5d1esx6gkrc>`__. Any active outbound Megolm sessions whose
keys have been shared with the device should also be invalidated so that
no further messages are sent over them.

Verifying a device involves ensuring that the device belongs to the
claimed user. Currently this must be done by showing the user the
Ed25519 fingerprint key for the device, and prompting the user to verify
out-of-band that it matches the key shown on the other user's device.

.. _`marking the event as verified`:

Marking events as 'verified'
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once a device has been verified, it is possible to verify that events
have been sent from a particular device. See the section on `Handling an
m.room.encrypted event`_ for notes on how to do this
for each algorithm. Events sent from a verified device can be decorated
in the UI to show that they have been sent from a verified device.
