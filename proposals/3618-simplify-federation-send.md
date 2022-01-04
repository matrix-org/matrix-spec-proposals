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

A significant benefit is that homeserver implementations no longer need to block
the `/send` request in order to wait for the events to be processed for their error
results. This can potentially remove head-of-line blocking from `/send` altogether
if homeservers can durably queue the incoming events before returning.

Another benefit is that homeservers no longer need to parse the response body at
all and can instead just determine whether the transaction was accepted successfully
by the HTTP status code.

## Potential issues

Synapse appears to use the `"pdus"` key for logging (see [here](https://github.com/matrix-org/synapse/blob/b38bdae3a2e5b7cfe862580368b996b8d7dfa50f/synapse/federation/sender/transaction_manager.py#L160)). Dendrite, however, ignores the response body altogether.
