.. Copyright 2015 OpenMarket Ltd
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

Appendices
==========

Security Threat Model
----------------------

Denial of Service
~~~~~~~~~~~~~~~~~

The attacker could attempt to prevent delivery of messages to or from the
victim in order to:

* Disrupt service or marketing campaign of a commercial competitor.
* Censor a discussion or censor a participant in a discussion.
* Perform general vandalism.

Threat: Resource Exhaustion
+++++++++++++++++++++++++++

An attacker could cause the victims server to exhaust a particular resource
(e.g. open TCP connections, CPU, memory, disk storage)

Threat: Unrecoverable Consistency Violations
++++++++++++++++++++++++++++++++++++++++++++

An attacker could send messages which created an unrecoverable "split-brain"
state in the cluster such that the victim's servers could no longer derive a
consistent view of the chatroom state.

Threat: Bad History
+++++++++++++++++++

An attacker could convince the victim to accept invalid messages which the
victim would then include in their view of the chatroom history. Other servers
in the chatroom would reject the invalid messages and potentially reject the
victims messages as well since they depended on the invalid messages.

.. TODO-spec
  Track trustworthiness of HS or users based on if they try to pretend they
  haven't seen recent events, and fake a splitbrain... --M

Threat: Block Network Traffic
+++++++++++++++++++++++++++++

An attacker could try to firewall traffic between the victim's server and some
or all of the other servers in the chatroom.

Threat: High Volume of Messages
+++++++++++++++++++++++++++++++

An attacker could send large volumes of messages to a chatroom with the victim
making the chatroom unusable.

Threat: Banning users without necessary authorisation
+++++++++++++++++++++++++++++++++++++++++++++++++++++

An attacker could attempt to ban a user from a chatroom with the necessary
authorisation.

Spoofing
~~~~~~~~

An attacker could try to send a message claiming to be from the victim without
the victim having sent the message in order to:

* Impersonate the victim while performing illicit activity.
* Obtain privileges of the victim.

Threat: Altering Message Contents
+++++++++++++++++++++++++++++++++

An attacker could try to alter the contents of an existing message from the
victim.

Threat: Fake Message "origin" Field
+++++++++++++++++++++++++++++++++++

An attacker could try to send a new message purporting to be from the victim
with a phony "origin" field.

Spamming
~~~~~~~~

The attacker could try to send a high volume of solicited or unsolicited
messages to the victim in order to:

* Find victims for scams.
* Market unwanted products.

Threat: Unsolicited Messages
++++++++++++++++++++++++++++

An attacker could try to send messages to victims who do not wish to receive
them.

Threat: Abusive Messages
++++++++++++++++++++++++

An attacker could send abusive or threatening messages to the victim

Spying
~~~~~~

The attacker could try to access message contents or metadata for messages sent
by the victim or to the victim that were not intended to reach the attacker in
order to:

* Gain sensitive personal or commercial information.
* Impersonate the victim using credentials contained in the messages.
  (e.g. password reset messages)
* Discover who the victim was talking to and when.

Threat: Disclosure during Transmission
++++++++++++++++++++++++++++++++++++++

An attacker could try to expose the message contents or metadata during
transmission between the servers.

Threat: Disclosure to Servers Outside Chatroom
++++++++++++++++++++++++++++++++++++++++++++++

An attacker could try to convince servers within a chatroom to send messages to
a server it controls that was not authorised to be within the chatroom.

Threat: Disclosure to Servers Within Chatroom
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An attacker could take control of a server within a chatroom to expose message
contents or metadata for messages in that room.


Cryptographic Test Vectors
--------------------------

To assist in the development of compatible implementations, the following test
values may be useful for verifying the cryptographic event signing code.

Signing Key
~~~~~~~~~~~

The following test vectors all use the 32-byte value given by the following
Base64-encoded string as the seed for generating the ``ed25519`` signing key:

.. code::

    SIGNING_KEY_SEED = decode_base64(
        "YJDBA9Xnr2sVqXD9Vj7XVUnmFZcZrlw8Md7kMW+3XA1"
    )

In each case, the server name and key ID are as follows:

.. code::

    SERVER_NAME = "domain"

    KEY_ID = "ed25519:1"

JSON Signing
~~~~~~~~~~~~

Given an empty JSON object:

.. code:: json

    {}

The JSON signing algorithm should emit the following signed data:

.. code:: json

    {
        "signatures": {
            "domain": {
                "ed25519:1": "K8280/U9SSy9IVtjBuVeLr+HpOB4BQFWbg+UZaADMtTdGYI7Geitb76LTrr5QV/7Xg4ahLwYGYZzuHGZKM5ZAQ"
            }
        }
    }

Given the following JSON object with data values in it:

.. code:: json

    {
        "one": 1,
        "two": "Two"
    }

The JSON signing algorithm should emit the following signed JSON:

.. code:: json

    {
        "one": 1,
        "signatures": {
            "domain": {
                "ed25519:1": "KqmLSbO39/Bzb0QIYE82zqLwsA+PDzYIpIRA2sRQ4sL53+sN6/fpNSoqE7BP7vBZhG6kYdD13EIMJpvhJI+6Bw"
            }
        },
        "two": "Two"
    }

Event Signing
~~~~~~~~~~~~~

Given the following minimally-sized event:

.. code:: json

    {
        "event_id": "$0:domain",
        "origin": "domain",
        "origin_server_ts": 1000000,
        "signatures": {},
        "type": "X",
        "unsigned": {
            "age_ts": 1000000
        }
    }

The event signing algorithm should emit the following signed event:

.. code:: json

    {
        "event_id": "$0:domain",
        "hashes": {
            "sha256": "6tJjLpXtggfke8UxFhAKg82QVkJzvKOVOOSjUDK4ZSI"
        },
        "origin": "domain",
        "origin_server_ts": 1000000,
        "signatures": {
            "domain": {
                "ed25519:1": "2Wptgo4CwmLo/Y8B8qinxApKaCkBG2fjTWB7AbP5Uy+aIbygsSdLOFzvdDjww8zUVKCmI02eP9xtyJxc/cLiBA"
            }
        },
        "type": "X",
        "unsigned": {
            "age_ts": 1000000
        }
    }

Given the following event containing redactable content:

.. code:: json

    {
        "content": {
            "body": "Here is the message content",
        },
        "event_id": "$0:domain",
        "origin": "domain",
        "origin_server_ts": 1000000,
        "type": "m.room.message",
        "room_id": "!r:domain",
        "sender": "@u:domain",
        "signatures": {},
        "unsigned": {
            "age_ts": 1000000
        }
    }

The event signing algorithm should emit the following signed event:

.. code:: json

    {
        "content": {
            "body": "Here is the message content",
        },
        "event_id": "$0:domain",
        "hashes": {
            "sha256": "onLKD1bGljeBWQhWZ1kaP9SorVmRQNdN5aM2JYU2n/g"
        },
        "origin": "domain",
        "origin_server_ts": 1000000,
        "type": "m.room.message",
        "room_id": "!r:domain",
        "sender": "@u:domain",
        "signatures": {
            "domain": {
                "ed25519:1": "Wm+VzmOUOz08Ds+0NTWb1d4CZrVsJSikkeRxh6aCcUwu6pNC78FunoD7KNWzqFn241eYHYMGCA5McEiVPdhzBA"
            }
        },
        "unsigned": {
            "age_ts": 1000000
        }
    }
