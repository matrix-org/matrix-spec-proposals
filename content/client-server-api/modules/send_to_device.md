---
type: module
---

### Send-to-Device messaging

This module provides a means by which clients can exchange signalling
messages without them being stored permanently as part of a shared
communication history. A message is delivered exactly once to each
client device.

The primary motivation for this API is exchanging data that is
meaningless or undesirable to persist in the room DAG - for example,
one-time authentication tokens or key data. It is not intended for
conversational data, which should be sent using the normal [`/rooms/<room_id>/send`](/client-server-api/#put_matrixclientv3roomsroomidsendeventtypetxnid) API for
consistency throughout Matrix.

#### Client behaviour

To send a message to other devices, a client should call
[`/sendToDevice`](/client-server-api/#put_matrixclientv3sendtodeviceeventtypetxnid). Only one message can be sent to each device per
transaction, and they must all have the same event type. The device ID
in the request body can be set to `*` to request that the message be
sent to all known devices.

If there are send-to-device messages waiting for a client, they will be
returned by [`/sync`](/client-server-api/#get_matrixclientv3sync), as detailed in [Extensions to /sync](/client-server-api/#extensions-to-sync). Clients should
inspect the `type` of each returned event, and ignore any they do not
understand.

#### Server behaviour

Servers should store pending messages for local users until they are
successfully delivered to the destination device. When a client calls
[`/sync`](/client-server-api/#get_matrixclientv3sync)
with an access token which corresponds to a device with pending
messages, the server should list the pending messages, in order of
arrival, in the response body.

When the client calls `/sync` again with the `next_batch` token from the
first response, the server should infer that any send-to-device messages
in that response have been delivered successfully, and delete them from
the store.

If there is a large queue of send-to-device messages, the server should
limit the number sent in each `/sync` response. 100 messages is
recommended as a reasonable limit.

If the client sends messages to users on remote domains, those messages
should be sent on to the remote servers via
[federation](/server-server-api#send-to-device-messaging).

#### Protocol definitions

{{% http-api spec="client-server" api="to_device" %}}

##### Extensions to /sync

This module adds the following properties to the [`/sync`](/client-server-api/#get_matrixclientv3sync) response:

| Parameter | Type      | Description                                                                 |
|-----------|-----------|-----------------------------------------------------------------------------|
| to_device | ToDevice  | Optional. Information on the send-to-device messages for the client device. |

`ToDevice`

| Parameter | Type      | Description                      |
|-----------|-----------|----------------------------------|
| events    | [Event]   | List of send-to-device messages. |

`Event`

| Parameter  | Type         | Description                                                                                     |
|------------|--------------|-------------------------------------------------------------------------------------------------|
| content    | EventContent | The content of this event. The fields in this object will vary depending on the type of event.  |
| sender     | string       | The Matrix user ID of the user who sent this event.                                             |
| type       | string       | The type of event.                                                                              |

Example response:

```json
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
```
