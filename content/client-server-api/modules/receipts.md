---
type: module
---

### Receipts

This module adds in support for receipts. These receipts are a form of
acknowledgement of an event. This module defines a single
acknowledgement: `m.read` which indicates that the user has read up to a
given event.

Sending a receipt for each event can result in sending large amounts of
traffic to a homeserver. To prevent this from becoming a problem,
receipts are implemented using "up to" markers. This marker indicates
that the acknowledgement applies to all events "up to and including" the
event specified. For example, marking an event as "read" would indicate
that the user had read all events *up to* the referenced event. See the
[Receiving notifications](#receiving-notifications) section for more
information on how read receipts affect notification counts.

#### Events

Each `user_id`, `receipt_type` pair must be associated with only a
single `event_id`.

{{% event event="m.receipt" %}}

#### Client behaviour

In `/sync`, receipts are listed under the `ephemeral` array of events
for a given room. New receipts that come down the event streams are
deltas which update existing mappings. Clients should replace older
receipt acknowledgements based on `user_id` and `receipt_type` pairs.
For example:

    Client receives m.receipt:
      user = @alice:example.com
      receipt_type = m.read
      event_id = $aaa:example.com

    Client receives another m.receipt:
      user = @alice:example.com
      receipt_type = m.read
      event_id = $bbb:example.com

    The client should replace the older acknowledgement for $aaa:example.com with
    this one for $bbb:example.com

Clients should send read receipts when there is some certainty that the
event in question has been **displayed** to the user. Simply receiving
an event does not provide enough certainty that the user has seen the
event. The user SHOULD need to *take some action* such as viewing the
room that the event was sent to or dismissing a notification in order
for the event to count as "read". Clients SHOULD NOT send read receipts
for events sent by their own user.

A client can update the markers for its user by interacting with the
following HTTP APIs.

{{% http-api spec="client-server" api="receipts" %}}

#### Server behaviour

For efficiency, receipts SHOULD be batched into one event per room
before delivering them to clients.

Receipts are sent across federation as EDUs with type `m.receipt`. The
format of the EDUs are:

```
{
    <room_id>: {
        <receipt_type>: {
            <user_id>: { <content> }
        },
        ...
    },
    ...
}
```

These are always sent as deltas to previously sent receipts. Currently
only a single `<receipt_type>` should be used: `m.read`.

#### Security considerations

As receipts are sent outside the context of the event graph, there are
no integrity checks performed on the contents of `m.receipt` events.
