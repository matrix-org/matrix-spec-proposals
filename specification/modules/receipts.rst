Receipts
--------

.. _module:receipts:

Receipts are used to publish which events in a room the user or their devices
have interacted with. For example, which events the user has read. For
efficiency this is done as "up to" markers, i.e. marking a particular event
as, say, ``read`` indicates the user has read all events *up to* that event.

Client-Server API
~~~~~~~~~~~~~~~~~

Clients will receive receipts in the following format::

     {
        "type": "m.receipt",
        "room_id": <room_id>,
        "content": {
            <event_id>: {
                <receipt_type>: {
                    <user_id>: { "ts": <ts>, ... },
                    ...
                }
            },
            ...
        }
    }

For example::

    {
        "type": "m.receipt",
        "room_id": "!KpjVgQyZpzBwvMBsnT:matrix.org",
        "content": {
            "$1435641916114394fHBLK:matrix.org": {
                "read": {
                    "@erikj:jki.re": { "ts": 1436451550453 },
                    ...
                }
            },
            ...
        }
    }

For efficiency, receipts are batched into one event per room. In the initialSync
and v2 sync APIs the receipts are listed in a separate top level ``receipts``
key. Each ``user_id``, ``receipt_type`` pair must be associated with only a
single ``event_id``. New receipts that come down the event streams are deltas.
Deltas update existing mappings, clobbering based on ``user_id``,
``receipt_type`` pairs.


A client can update the markers for its user by issuing a request::

    POST /_matrix/client/v2_alpha/rooms/<room_id>/receipt/read/<event_id>

Where the contents of the ``POST`` will be included in the content sent to
other users. The server will automatically set the ``ts`` field.


Server-Server API
~~~~~~~~~~~~~~~~~

Receipts are sent across federation as EDUs with type ``m.receipt``. The
format of the EDUs are::

    {
        <room_id>: {
            <receipt_type>: {
                <user_id>: { <content> }
            },
            ...
        },
        ...
    }

These are always sent as deltas to previously sent receipts.

