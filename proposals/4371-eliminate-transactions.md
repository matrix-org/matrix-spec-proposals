# MSC4371: On the elimination of federation transactions

Server Specification [v1.16 § 4](https://spec.matrix.org/v1.16/server-server-api/#transactions)
(including all prior versions) defines an envelope structure accompanying a protocol for common message
transport between servers referred to as "transactions." These structures collect messages queued by
an origin for a destination, then transmitted, acknowledged by the destination, and then this process
is repeated with new messages queued by the origin in the interim.

Transactions have existed since the early protocol (circa 2014) when HTTP/1.1 was the common standard
of transport. In HTTP/1 requests are processed sequentially within each connection. Multiple
connections may be used for concurrent processing but a federation server will already be
communicating to many destinations; minimizing connections between hosts is essential. Pipelining may
also be used to hide latency but without explicit support by HTTP/1 there are many complications;
protocol designers instead lean toward other solutions. From this environment federation transactions
arose.

Ironically transactions succumb to the same shortcomings as HTTP/1 itself. The Matrix protocol
specifies that only one transaction can be in flight at a time. The round-trip time for successful
acknowledgement must be paid before new information even begins to transmit. This introduces a
head-of-line-blocking effect, often paralyzing communication for any number of reasons such as
implementation errors, denial-of-service exploitation, or common processing where latent network
requests are often required to resolve a message to acceptance. During these events messages will
continue to queue on an origin. Eventually this queue exceeds the limits for a single transaction thus
requiring multiple rounds of transactions. These queuing events have been known to take days to
resolve.

Many messages bundled in these tranches often have no dependency on each other. For example, the
primary context division in Matrix is the Room: rooms have no specified interdependency: "transacting"
messages from different rooms at the same time serves no purpose. It is purely a hazard. Worse, the
primary unit of messaging for a room, the PDU, contains its own sequencing and reliability mechanism
allowing it to exist fully independent of any transaction—as it virtually always does in every other
context where PDU's are found. Sequencing PDU's in separate transactions is simply not necessary;
purely a hazard.

The specification states: "A Transaction is meaningful only to the pair of homeservers that exchanged
it; they are not globally-meaningful." This limited use and isolation eases our task to reduce or
eliminate transactions entirely.

### Proposal

We specify `PUT /_matrix/federation/v2/send/{ EventId | EduId }` where events are sent
indiscriminately. An `EduId` is an arbitrary string which MUST NOT be prefixed by `$`.

##### Unstable Prefix

 `PUT /_matrix/federation/unstable/net.zemos.send/{ EventId | EduId }`

### Discussion

When used over modern HTTP/2 only a single connection is required to conduct an arbitrary number of
concurrent transmissions. HTTP/1 systems can very safely utilize pipelining considering the
idempotency of named PUT requests.


### Alternatives

A possible alternative would be to keep the transaction structure while amending the protocol
semantics for requisite conccurency in the modern age. Nevertheless the transaction structure has some
defects for optimal network software. For example, network software benefits from transmitting the
same message to multiple destinations without recrafting specific versions for each destination.

### Potential Issues

Some EDU's can exist naturally outside of transactions such as read-receipts which target a specific
`event_id`, can be replayed, and can be received in any order. Nevertheless a wider analysis of
transmitting EDU's indescriminately will have to be considered and some additional sequencing will
likely be necessary in their payloads.

### Security Considerations
