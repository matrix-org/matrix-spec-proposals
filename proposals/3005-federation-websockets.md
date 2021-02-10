# MSC3005: Federation over WebSockets

Currently, Matrix Federation works via
[transactions](https://matrix.org/docs/spec/server_server/r0.1.4#put-matrix-federation-v1-send-txnid),
encapsulating queued PDUs and EDUs and sending them through individual HTTP requests.

This system can be slow or otherwise resource-intensive in a number of ways, through how each
transaction request is largely the same (except content and maybe `txn` ), and how each goes through
the entire HTTP request chain for every single transaction, which can hamper Time-To-Deliver over federation.

## Proposal

The proposal thus is to then introduce a new optionally-implementable WebSocket endpoint,
`/federation/v2/stream` , which is then upgradable to a WebSocket connection.

Servers over federation can implement this endpoint, if servers encounter 404 when querying this
endpoint, it should be assumed the server does not implement WebSocket streaming, and instead
`/federation/v1/send/{txn}` -based federation event-sending must be used.

A connecting server must include `X-Matrix-Origin-Server` in their request to the stream endpoint.

### 2 different frame options.

*This section outlines 2 different framing options I had in mind, please comment with thoughts.*

*Anything included in square brackets is a proposal, not fully thought-out*

#### Leading-type-byte frame

In the WebSocket stream, a frame must be interpreted in the following fashion;

[The leading byte denotes what type and format the data following it will be.]

*or*

#### Leading-type-word frame

[The leading null-terminated string denotes what type and format the data following it will be.]

#### Bytes/Words and their Meanings

*The first option, `01` and such, are in hexadecimal for the first byte of the frame.*

`FF` *or* `ctrl` denotes a "control event", the data following it will contain information about the
stream connection itself, such as time synchronization, event sequencing, or other (to be defined)
control events. It's payload definition is described [down below](#control-events).

`01` *or* `pdu` denotes a PDU being sent over the stream, the receiving server should perceive the
origin server time to be offset by its own internal clock. The PDU must be replied to with an
acknowledgement or an error, using "ID of the PDU" semantics similar to `/v1/send` . It's payload is
the full PDU object.

`02` *or* `edu` denotes a EDU being sent over the stream, this (with parity to `/v1/send` ) is not
acknowledged. It's payload is the full EDU object.

`10` *or* `pack` acknowledges a PDU, it's payload is the "ID of a PDU" in string form.

*or*

It's payload is defined as follows;

``` json
{
  "id": "<PDU ID>"
}
```

`11` *or* `perr` returns an error for a PDU, it's payload is defined as follows;

``` json
[
  "<PDU ID>",
  "<Error in string format>"
]
```

### "object"

This proposal does not lock down the payload formatting down to JSON, it does make it a default.

The recommendation is to use `?format=cbor` or the like to define it's payload object format, in the
future.

### Control Events

Control events are defined as follows;

``` json
{
  "op": 0, // specific control opcode
  "data": null // arbitrary data for the opcode
}
```

| Opcode | Description               | Content                 | Comment                                                                      |
| ------ | ------------------------- | ----------------------- | ---------------------------------------------------------------------------- |
| 0      | Heartbeat                 | TS of origin server     | Can be sent by either server                                                 |
| 1      | Heartbeat response        | TS of responding server |                                                                              |
| 2      | Graceful shutdown request |                         | Useful for terminating the connection correctly and cleanly by either server |

*The current proposal is unidirectional, it is possible to make this bidirectional.*

## Potential issues

Not all servers could implement this, so support must never be primarily assumed, a server must be
able to fall back to `v1/send`.

A long-standing WS connection can tie up a lot of resources, so connection pruning (or timeout after
inactivity) should be considered.

In the form of a multi-process matrix server, architectural design should be considered (example; in
he case of synapse, the websockets should be established from federation senders *(in how the
proposal is currently unidirectional, see comment above)*, not from the main homeserver process).

## Alternatives

**WebTransport**: A [new draft standard](https://w3c.github.io/webtransport/) in progress,
abstracting network interfaces, making it easier for user-facing applications to build APIs on top
of networking APIs.

WebTransport is currently way too young of a spec, this proposal focuses on making a standard
WebSocket stream format.

**Direct TCP/TLS**: Using direct TCP/TLS connections for Federation.

All matrix server implementations today are mainly HTTP+JSON based, WebSockets allow upgrading from
HTTP, and most reverse proxies recognize this, so it's more accessable and easier to implement. Most
frameworks aren't exactly kind to receiving and handling arbitrary TCP, and so the implementation
overhead for a TCP/TLS-based solution would be higher than a WebSocket-based solution.

**Do Nothing**: Do Nothing, keep the current HTTP-`/send` mechanic.

While a viable option, and keeping as a reliable always-existing fallback, this is not fast, as
WebSockets would be able to overcome time and processing between receiving a payload for a PDU/EDU,
due to how directly it's IO could be delivered to application code that handles it, which can
decrease latency.

## Security considerations

None that aren't already applicable to `v1/send`.

## Unstable prefix

For experimental implementations of this spec, `/federation/unstable/nl.jboi.msc3005/stream` should
be used. This endpoint can be queried with the same mechanics as the proposed
`/federation/v2/stream` defined in [here](#proposal).
