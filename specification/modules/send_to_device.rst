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

.. _module:to_device:
.. _`to-device`:

Send-to-Device messaging
========================

This module provides a means by which clients can exchange signalling messages
without them being stored permanently as part of a shared communication
history. A message is delivered exactly once to each client device.

The primary motivation for this API is exchanging data that is meaningless or
undesirable to persist in the room DAG - for example, one-time authentication
tokens or key data. It is not intended for conversational data, which should be
sent using the normal |/rooms/<room_id>/send|_ API for consistency throughout
Matrix.

Client behaviour
----------------
To send a message to other devices, a client should call |/sendToDevice|_.
Only one message can be sent to each device per transaction, and they must all
have the same event type. The device ID in the request body can be set to ``*``
to request that the message be sent to all known devices.

If there are send-to-device messages waiting for a client, they will be
returned by |/sync|_, as detailed in |Extensions|_. Clients should
inspect the ``type`` of each returned event, and ignore any they do not
understand.

.. |Extensions| replace:: Extensions to /sync
.. _Extensions: `send_to_device_sync`_

Server behaviour
----------------
Servers should store pending messages for local users until they are
successfully delivered to the destination device. When a client calls |/sync|_
with an access token which corresponds to a device with pending messages, the
server should list the pending messages, in order of arrival, in the response
body.

When the client calls ``/sync`` again with the ``next_batch`` token from the
first response, the server should infer that any send-to-device messages in
that response have been delivered successfully, and delete them from the store.

If there is a large queue of send-to-device messages, the server should
limit the number sent in each ``/sync`` response. 100 messages is recommended
as a reasonable limit.

If the client sends messages to users on remote domains, those messages should
be sent on to the remote servers via
`federation`_.

.. _`federation`: ../server_server/%SERVER_RELEASE_LABEL%.html#send-to-device-messaging

.. TODO-spec:

   * Is a server allowed to delete undelivered messages? After how long? What
     about if the device is deleted?

   * If the destination HS doesn't support the ``m.direct_to_device`` EDU, it
     will just get dumped. Should we indicate that to the client?


Protocol definitions
--------------------

{{to_device_cs_http_api}}

.. TODO-spec:

   * What should a server do if the user id or device id is unknown? Presumably
     it shouldn't reject the request outright, because some of the destinations
     may be valid. Should we add something to the response?

.. anchor for link from /sync api spec
.. |send_to_device_sync| replace:: Send-to-Device messaging
.. _send_to_device_sync:

Extensions to /sync
~~~~~~~~~~~~~~~~~~~

This module adds the following properties to the |/sync|_ response:

.. todo: generate this from a swagger definition?

========= ========= =======================================================
Parameter Type      Description
========= ========= =======================================================
to_device ToDevice  Optional. Information on the send-to-device messages
                    for the client device.
========= ========= =======================================================

``ToDevice``

========= ========= =============================================
Parameter Type      Description
========= ========= =============================================
events    [Event]   List of send-to-device messages.
========= ========= =============================================

``Event``

================ ============ ==================================================
Parameter        Type         Description
================ ============ ==================================================
content          EventContent The content of this event. The fields in this
                              object will vary depending on the type of event.
sender           string       The Matrix user ID of the user who sent this
                              event.
type             string       The type of event.
================ ============ ==================================================


Example response:

.. code:: json

  {
    "next_batch": "s72595_4483_1934",
    "rooms": {"leave": {}, "join": {}, "invite": {}},
    "to_device": {
      "events": [
        {
          "sender": "@alice:example.com",
          "type": "m.new_device",
          "content": {
            "device_id": "XYZABCDE",
            "rooms": ["!726s6s6q:example.com"]
          }
        }
      ]
    }
  }


.. |/sendToDevice| replace:: ``/sendToDevice``
.. _/sendToDevice: #put-matrix-client-%CLIENT_MAJOR_VERSION%-sendtodevice-eventtype-txnid
