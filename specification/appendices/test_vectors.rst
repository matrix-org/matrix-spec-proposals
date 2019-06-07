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
        "room_id": "!x:domain",
        "sender": "@a:domain",
        "origin": "domain",
        "origin_server_ts": 1000000,
        "signatures": {},
        "hashes": {},
        "type": "X",
        "content": {},
        "prev_events": [],
        "auth_events": [],
        "depth": 3,
        "unsigned": {
            "age_ts": 1000000
        }
    }

The event signing algorithm should emit the following signed event:

.. code:: json

    {
        "auth_events": [],
        "content": {},
        "depth": 3,
        "hashes": {
            "sha256": "5jM4wQpv6lnBo7CLIghJuHdW+s2CMBJPUOGOC89ncos"
        },
        "origin": "domain",
        "origin_server_ts": 1000000,
        "prev_events": [],
        "room_id": "!x:domain",
        "sender": "@a:domain",
        "signatures": {
            "domain": {
                "ed25519:1": "KxwGjPSDEtvnFgU00fwFz+l6d2pJM6XBIaMEn81SXPTRl16AqLAYqfIReFGZlHi5KLjAWbOoMszkwsQma+lYAg"
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
            "body": "Here is the message content"
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
            "body": "Here is the message content"
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
