WebSockets API
==============

Introduction
------------
This document is a proposal for a WebSockets-based client-server API. It is not
intended to replace the REST API, but rather to complement it and provide an
alternative interface for certain operations.

The primary goal is to offer a more efficient interface than the REST API: by
using a bidirectional protocol such as WebSockets we can avoid the overheads
involved in long-polling (SSL negotiation, HTTP headers, etc). In doing so we
will reduce the latency between server and client by allowing the server to
send events as soon as they arrive, rather than having to wait for a poll from
the client.

Note: This proposal got continued in a google document you can find here:
https://docs.google.com/document/d/104ClehFBgqLQbf4s-AKX2ijr8sOAxcizfcRs_atsB0g

Handshake
---------
1. Instead of calling ``/sync``, the client makes a websocket request to
   ``/_matrix/client/rN/stream``, passing the query parameters ``access_token``
   and ``since``, and optionally ``filter`` - all of which have the same
   meaning as for ``/sync``.

   * The client sets the ``Sec-WebSocket-Protocol`` to ``m.json``. (Servers may
     offer alternative encodings; at present only the JSON encoding is
     specified but in future we will specify alternative encodings.)

#. The server returns the websocket handshake; the socket is then connected.

If the server does not return a valid websocket handshake, this indicates that
the server or an intermediate proxy does not support WebSockets. In this case,
the client should fall back to polling the ``/sync`` REST endpoint.

Example
~~~~~~~

Client request:

.. code:: http

    GET /_matrix/client/v2_alpha/stream?access_token=123456&since=s72594_4483_1934 HTTP/1.1
    Host: matrix.org
    Upgrade: websocket
    Connection: Upgrade
    Sec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==
    Sec-WebSocket-Protocol: m.json
    Sec-WebSocket-Version: 13
    Origin: https://matrix.org

Server response:

.. code:: http

    HTTP/1.1 101 Switching Protocols
    Upgrade: websocket
    Connection: Upgrade
    Sec-WebSocket-Accept: HSmrc0sMlYUkAGmm5OPpG2HaGWk=
    Sec-WebSocket-Protocol: m.json


Update Notifications
--------------------
Once the socket is connected, the server begins streaming updates over the
websocket. The server sends Update notifications about new messages or state
changes. To make it easy for clients to parse, Update notifications have the
same structure as the response to ``/sync``: an object with the following
members:

============= ========== ===================================================
Key           Type       Description
============= ========== ===================================================
next_batch    string     The batch token to supply in the ``since`` param of
                         the next /sync request. This is not required for
                         streaming of events over the WebSocket, but is
                         provided so that clients can reconnect if the
                         socket is disconnected.
presence      Presence   The updates to the presence status of other users.
rooms         Rooms      Updates to rooms.
============= ========== ===================================================

Example
~~~~~~~
Message from the server:

.. code:: json

    {
        "next_batch": "s72595_4483_1934",
        "presence": {
            "events": []
        },
        "rooms": {
            "join": {},
            "invite": {},
            "leave": {}
        }
    }


Client-initiated operations
---------------------------

The client can perform certain operations by sending a websocket message to
the server. Such a "Request" message should be a JSON-encoded object with
the following members:

============= ========== ===================================================
Key           Type       Description
============= ========== ===================================================
id            string     A unique identifier for this request
method        string     Specifies the name of the operation to be
                         performed; see below for available operations
param         object     The parameters for the requested operation.
============= ========== ===================================================

The server responds to a client Request with a Response message. This is a
JSON-encoded object with the following members:

============= ========== ===================================================
Key           Type       Description
============= ========== ===================================================
id            string     The same as the value in the corresponding Request
                         object. The presence of the ``id`` field
                         distinguishes a Response message from an Update 
                         notification.
result        object     On success, the results of the request.
error         object     On error, an object giving the resons for the
                         error. This has the same structure as the "standard
                         error response" for the Matrix API: an object with
                         the fields ``errcode`` and ``error``.
============= ========== ===================================================

Request methods
~~~~~~~~~~~~~~~
It is not intended that all operations which are available via the REST API
will be available via the WebSockets API, but a few simple, common operations
will be exposed. The initial operations will be as follows.

``ping``
^^^^^^^^
This is a no-op which clients may use to keep their connection alive.

The request ``params`` and the response ``result`` should be empty.

``send``
^^^^^^^^
Send a message event to a room. The parameters are as follows:

============= ========== ===================================================
Parameter     Type       Description
============= ========== ===================================================
room_id       string     **Required.** The room to send the event to
event_type    string     **Required.** The type of event to send.
content       object     **Required.** The content of the event.
============= ========== ===================================================

The result is as follows:

============= ========== ===================================================
Key           Type       Description
============= ========== ===================================================
event_id      string     A unique identifier for the event.
============= ========== ===================================================

The ``id`` from the Request message is used as the transaction ID by the
server.

``state``
^^^^^^^^^
Update the state on a room.

============= ========== ===================================================
Parameter     Type       Description
============= ========== ===================================================
room_id       string     **Required.** The room to set the state in
event_type    string     **Required.** The type of event to send.
state_key     string     **Required.** The state_key for the state to send.
content       object     **Required.** The content of the event.
============= ========== ===================================================

The result is as follows:

============= ========== ===================================================
Key           Type       Description
============= ========== ===================================================
event_id      string     A unique identifier for the event.
============= ========== ===================================================


Example
~~~~~~~
Client request:

.. code:: json

    {
        "id": "12345",
        "method": "send",
        "params": {
            "room_id": "!d41d8cd:matrix.org",
            "event_type": "m.room.message",
            "content": {
                "msgtype": "m.text",
                "body": "hello"
            }
        }
    }

Server response:

.. code:: json

    {
        "id": "12345",
        "result": {
            "event_id": "$66697273743031:matrix.org"
        }
    }

Alternative server response, in case of error:

.. code:: json

    {
        "id": "12345",
        "error": {
           "errcode": "M_MISSING_PARAM",
           "error": "Missing parameter: event_type"
        }
    }


Rationale
---------
Alternatives to WebSockets include HTTP/2, CoAP, and simply rolling our own
protocol over raw TCP sockets. However, the need to implement browser-based
clients essentially reduces our choice to WebSockets. HTTP/2 streams will
probably provide an interesting alternative in the future, but current browsers
do not appear to give javascript applications low-level access to the protocol.

Concerning the continued use of the JSON encoding: we prefer to focus on the
transition to WebSockets initially. Replacing JSON with a compact
representation such as CBOR, MessagePack, or even just compressed JSON will be
a likely extension for the future. The support for negotiation of subprotocols
within WebSockets should make this a simple transition once time permits.

The number of methods available for client requests is deliberately limited, as
each method requires code to be written to map it onto the equivalent REST
implementation. Some REST methods - for instance, user registration and login -
would be pointless to expose via WebSockets. It is likely, however, that we
will increate the number of methods available via the WebSockets API as it
becomes clear which would be most useful.

Open questions
--------------

Throttling
~~~~~~~~~~
At least in v2 sync, clients are inherently self-throttling - if they do not
poll quickly enough, events will be dropped from the next result. This proposal
raises the possibility that events will be produced more quickly than they can
be sent to the client; backlogs will build up on the server and/or in the
intermediate network, which will not only lead to high latency on events being
delivered, but will lead to responses to client requests also being delayed.

We may need to implement some sort of throttling mechanism by which the server
can start to drop events. The difficulty is in knowing when to start dropping
events. A few ideas:

* Use websocket pings to measure the RTT; if it starts to increase, start
  dropping events. But this requires knowledge of the base RTT, and a useful
  model of what constitutes an excessive increase.

* Have the client acknowledge each batch of events, and use a window to ensure
  the number of outstanding batches is limited. This is annoying as it requires
  the client to have to acknowledge batches - and it's not clear what the right
  window size is: we want a big window for long fat networks (think of mobile
  clients), but a small one for one with lower latency.

* Start dropping events if the server's TCP buffer starts filling up. This has
  the advantage of delegating the congestion-detection to TCP (which already
  has a number of algorithms to deal with it, to greater or lesser
  effectiveness), but relies on homeservers being hosted on OSes which use
  sensible TCP congestion-avoidance algorithms, and more critically, an ability
  to read the fill level of the TCP send buffer.
