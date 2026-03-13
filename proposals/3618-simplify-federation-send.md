# MSC3618: Simplify federation `/send` response

## Overview

Currently we specify that the federation `/send` endpoint returns a body of
`pdus: { string: PDU Processing Result}`. In theory a homeserver can return
information here on an event-by-event basis as to whether there was a problem
processing events in the transaction or not.

However, this does not really make much difference in practice — soft-fails
are silent and rejected events may be too – and server implementations do not
"cherry-pick" which events in a transaction to retry later. Since the presence
of a `txnId` in the request implies that we should consider a transaction to be
idempotent for a given `txnId`, we should therefore either accept that the
entire transaction was accepted successfully by the remote side or we should
retry the entire transaction.

The worst case is that the homeserver is not able to process the transaction at
all for some reason, i.e. due to the database being down or similar, in which
case the server really should just return a HTTP 500 status code and this
signals to the sender to retry later.

## Proposal

This MSC proposes that we remove the `pdus` section from the response body, so
that we return only one of two conditions:

* A HTTP 200 with a `{}` body to signal that the transaction was accepted;
* A HTTP 500 to signal that there was a problem with the transaction and to retry
  sending later.

## Benefits

A significant benefit is that the receiving homeserver no longer needs to block the
the `/send` request in order to wait for the events to be processed for their `PDU Processing
Result`s.

Given that it is possible for a transaction to contain events from multiple rooms, or
EDUs for unrelated purposes, it is bad that a single busy room can lengthen the amount of
time to return the `/send` response to the caller. This means that new events for other
rooms may be held back unnecessarily by processing events for a single busy room, as
per the spec:

> The sending server must wait and retry for a 200 OK response before sending a
> transaction with a different txnId to the receiving server.

With this proposal, the receiving server no longer needs to wait for `PDU Processing Result`s
as this MSC does away with them. Receiving servers that do not want to durably persist transactions
before processing them can continue to perform all work in-memory by continuing to block the `/send`
request until all processing is completed, as may be done today. Additionally, a receiving
server that is receiving too many transactions from a remote homeserver may wish to block for
an arbitrary period of time for rate-limiting purposes, but this is an implementation specific
detail and not strictly required.

Another benefit is that sending homeservers no longer need to parse the response body at
all and can instead just determine whether the transaction was accepted successfully by
observing the HTTP status code.

## Potential issues

Synapse appears to use the `"pdus"` key for logging (see [here](https://github.com/matrix-org/synapse/blob/b38bdae3a2e5b7cfe862580368b996b8d7dfa50f/synapse/federation/sender/transaction_manager.py#L160)).
Conduit does the same and treats the response as an empty list if it is not present. Dendrite
ignores the response body altogether.
