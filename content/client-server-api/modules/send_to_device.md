---
type: module
weight: 80
---

### Send-to-Device messaging<span id="module:to_device"></span>

This module provides a means by which clients can exchange signalling
messages without them being stored permanently as part of a shared
communication history. A message is delivered exactly once to each
client device.

The primary motivation for this API is exchanging data that is
meaningless or undesirable to persist in the room DAG - for example,
one-time authentication tokens or key data. It is not intended for
conversational data, which should be sent using the normal \_ API for
consistency throughout Matrix.

#### Client behaviour

To send a message to other devices, a client should call
`/sendToDevice`\_. Only one message can be sent to each device per
transaction, and they must all have the same event type. The device ID
in the request body can be set to `*` to request that the message be
sent to all known devices.

If there are send-to-device messages waiting for a client, they will be
returned by \_, as detailed in Extensions to /sync\_. Clients should
inspect the `type` of each returned event, and ignore any they do not
understand.

#### Server behaviour

Servers should store pending messages for local users until they are
successfully delivered to the destination device. When a client calls \_
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
[federation](../server_server/%SERVER_RELEASE_LABEL%.html#send-to-device-messaging).

#### Protocol definitions

{{to\_device\_cs\_http\_api}}

##### Extensions to /sync

This module adds the following properties to the \_ response:

<table>
<thead>
<tr class="header">
<th>Parameter</th>
<th>Type</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><p>to_device</p></td>
<td><p>ToDevice</p></td>
<td><p>Optional. Information on the send-to-device messages for the client device.</p></td>
</tr>
</tbody>
</table>

`ToDevice`

<table>
<thead>
<tr class="header">
<th>Parameter</th>
<th>Type</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>events</td>
<td>[Event]</td>
<td>List of send-to-device messages.</td>
</tr>
</tbody>
</table>

`Event`

<table>
<thead>
<tr class="header">
<th>Parameter</th>
<th>Type</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><p>content</p></td>
<td><p>EventContent</p></td>
<td><p>The content of this event. The fields in this object will vary depending on the type of event.</p></td>
</tr>
<tr class="even">
<td><p>sender</p></td>
<td><p>string</p></td>
<td><p>The Matrix user ID of the user who sent this event.</p></td>
</tr>
<tr class="odd">
<td>type</td>
<td>string</td>
<td>The type of event.</td>
</tr>
</tbody>
</table>

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
