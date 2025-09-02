# MSC4089: Delivery Receipts

A common feature among messaging clients is "delivery receipts". Similar to [read receipts](https://spec.matrix.org/v1.9/client-server-api/#receipts),
delivery receipts denote when a client has received *and* decrypted a given message. They do not
denote whether a user has "seen" that message, such as in a push notification.

In a Digital Markets Act (DMA) world, the need for a protocol to support popular messaging features
rises. This proposal introduces a concept of delivery receipts to Matrix, aiming to be compatible
with potential bridges and protocol converters which need such a feature to operate.

## Proposal

The specification already has a general concept of [receipts](https://spec.matrix.org/v1.9/client-server-api/#receipts),
which is currently in use only by read (or "seen") receipts. We extend this module with a new `m.delivery`
receipt to track individual events being received by the client.

Delivery receipts are sent by all of a user's clients to report back to the event's sender that an
event was decrypted successfully. They are not "up to" markers - they are for singular events. Other
users in the room do *not* see delivery receipts for events they didn't send.

If an event is not encrypted, a delivery receipt is sent when the client receives the event. If an
event is encrypted but could not be decrypted, no delivery receipt is sent.

**TODO**: We may want to consider an explicit "failed delivery" receipt.

`m.delivery` is part of `m.receipt` as follows:

```jsonc
{
  "type": "m.receipt",
  "content": {
    "$eventid": {
      "m.read": {
        // per spec
      },
      "m.read.private": {
        // per spec
      },
      "m.delivery": {
        "@user:example.org": {
          "ts": 1661384801651, // same as m.read[.private]
        }
      }
    }
  }
}
```

Typically, a client would send a delivery receipt with
[`POST /_matrix/client/v3/rooms/:roomId/receipt/:type/:eventId`](https://spec.matrix.org/v1.9/client-server-api/#post_matrixclientv3roomsroomidreceiptreceipttypeeventid), like so:

```text
POST /_matrix/client/v3/rooms/!room:example.org/receipt/m.delivery/$event
Content-Type: application/json
{}
```

The server then implies `ts` and sends the resulting EDU to the target event's origin server. The
delivery receipt must only be routed to the target event sender.

Receiving a `m.read[.private]` receipt without a delivery receipt does *not* imply
delivery, but rather that a client either does not support delivery receipts or was not
able to decrypt the message.

Clients are welcome to implement additional requirements before sending a delivery receipt. For example,
a user setting to disable delivery receipts in public rooms specifically, or all rooms the user is in.
Defaults may be applied which prevent delivery receipts from being sent. It is recommended that delivery
receipts be sent by default for encrypted private rooms (where join rules are not public).

Delivery receipts should not be sent for events prior to a user's join.

If a server receives a duplicate request to send a delivery receipt, it should 200 OK it. This is to
ensure that if a client fails to receive a response it doesn't retry forever.

## Potential issues

If a user sends an event in Matrix HQ, they could potentially receive 50 thousand delivery receipts
multiplied by the number of devices each of those users has. The mobile device could potentially exceed
data limits just receiving these receipts. Servers should bundle delivery receipts to deliver them to
the client rather than sending each one individually.

**TODO**: Maybe we also limit size or require a client to opt-in with a filter param of some sort?

This is not an issue with read receipts as those receipts generally trickle in slowly as users open
the room.

## Alternatives

**TODO**: Spec out what persistent delivery receipts look like.

## Security considerations

Privacy considerations have been made to ensure information is not needlessly disclosed to the rest
of the room. It's not great that someone could send a message to see which devices are online, and it'd
be even worse if a bot could scrape receipt data to determine someone's schedule without ever sending
an event. Delivery receipts *should* be used only in private settings, and clients *should* choose
default options for users which protect their privacy. For example, not sending delivery receipts in
public rooms.

## Unstable prefix

Before FCP, clients use [`/versions`](https://spec.matrix.org/v1.9/client-server-api/#get_matrixclientversions)
to see if the server supports `org.matrix.msc4089` as an unstable feature. If the server *does* support
the feature, clients can use `org.matrix.msc4089.delivery` in place of `m.delivery` throughout this MSC.

After FCP, but before being released in the spec, clients can look for the same `/versions` feature
flag and try to send `m.delivery` receipts to the server. If the server responds with an error, the
client can fall back to `org.matrix.msc4089.delivery`.

After being released in the spec, clients can use that specification version in the `/versions` response
to determine if the server supports `m.delivery` receipts. If the server does, the client can send
delivery receipts as such. If not, the previous advice still applies regarding unstable identifiers.

## Dependencies

There are no dependencies.
