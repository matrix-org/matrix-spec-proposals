# MSC4102: Clarifying precedence in threaded and unthreaded read receipts in EDUs

*This MSC assumes some knowledge around threaded receipts. Please read
[MSC3771: Read receipts for threads](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/3771-read-receipts-for-threads.md)
as for brevity some concepts won't be re-explained.*

This proposal clarifies previously undefined behaviour around how read receipts are expressed over
the CSAPI and SSAPI. This clarification reliably provides clients with sufficient information to
determine read receipts, without placing additional burdens on client implementations.

## Background

[MSC3771: Read receipts for threads](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/3771-read-receipts-for-threads.md)
defined an API shape for threaded read receipts over the `/sync` API. They look like this:
```js
{
  "content": {
    "$thread_reply": {
      "m.read": {
        "@rikj:jki.re": {
          "ts": 1436451550453,
          "thread_id": "$thread_root" // or "main" or absent
        }
      }
    }
  },
  "room_id": "!jEsUZKDJdhlrceRyVU:example.org",
  "type": "m.receipt"
}
```

This is problematic because it expresses receipt uniqueness based on the 3-uple (event ID, receipt type, user ID).
In reality, uniqueness is based on the 4-uple of (event ID, receipt type, user ID, **thread ID**). This makes it
impossible to express certain receipt aggregations, such as:
```
      Receipts Table
room | user | event | thread
-----+------+-------+--------
!foo | @bob | $abc  | NULL         // unthreaded receipt
!foo | @bob | $abc  | "some_id"    // threaded receipt
```
It is impossible to express these two receipts in a single `m.receipt` EDU, as the presence of `thread_id: "some_id"`
by definition removes the absence of a thread ID, turning the receipt from an unthreaded receipt into a threaded receipt.

[MSC3771: Read receipts for threads](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/3771-read-receipts-for-threads.md)
does not provide rules around how to combine these receipts. This has led to undefined server behaviour. In practice,
both Synapse and the Sliding Sync Proxy will combine them in a "last write wins" manner. If the unthreaded receipt is
sent after the threaded receipt, then `/sync` will always return the unthreaded receipt and vice versa. This is not a
hypothetical problem: Element-Web will send both threaded and unthreaded receipts for the same event if the event in
question is the most recent event in the room, which is fairly common.

This becomes a major problem when the threaded receipt "wins" and is returned _instead of_ the unthreaded receipt.
Some clients, such as Element X, do not handle threads and will ignore receipts with a non-main `thread_id`, assuming that
clients will also be sending unthreaded receipts. When the threaded receipt "wins" however, these clients will simply
not see the receipt, despite the sender sending it.

## Proposal

When a server is combining receipts into an EDU, if there are multiple receipts for the same (user, event, receipt type), always
choose the receipt which is unthreaded (has no `thread_id`) when aggregating into an EDU.

This change will apply to all `m.receipt` EDUs, which includes both CSAPI and Federation endpoints.

For example, given these two EDUs:
```js
// EDU 1
{
    "content": {
        "$1435641916114394fHBLK:matrix.org": {
            "m.read": {
                "@erikj:jki.re": {
                    "ts": 1550000000000
                }
            }
        }
    },
    "type": "m.receipt"
}

// EDU 2
{
    "content": {
        "$1435641916114394fHBLK:matrix.org": {
            "m.read": {
                "@erikj:jki.re": {
                    "ts": 1559999999999,
                    "thread_id": "foo"
                }
            },
            "m.read.private": {
                "@self:example.org": {
                    "ts": 1660000000000,
                    "thread_id": "bar"
                }
            }
        }
    },
    "type": "m.receipt"
}
```
The unthreaded receipt wins and the combined EDU should become:
```js
// Combined EDU
{
    "content": {
        "$1435641916114394fHBLK:matrix.org": {
            "m.read": {
                "@erikj:jki.re": {
                    "ts": 1550000000000
                }
            },
            "m.read.private": {
                "@self:example.org": {
                    "ts": 1660000000000,
                    "thread_id": "bar"
                }
            }
        }
    },
    "type": "m.receipt"
}
```
Note:
 - the data from the unthreaded receipt (the `ts`) is used.
 - the threaded receipt for type `m.read.private` is kept, as the 3-uple (user, event, receipt type) must match
   for the precedence rules to kick in.

## Potential issues

Some data is lost when aggregating EDUs, as the fact that a threaded receipt was sent will be lost. This is not a
problem in practice because an unthreaded receipt always takes precedence over a threaded receipt due to it
being a superset of the same data.

Thread-unaware clients need to inspect `thread_id: "main"` receipts to accurately get read receipts from thread-aware
clients, as that is how thread-aware clients send receipts for unthreaded events. Despite this, the
`main` thread ID has no significance in this proposal, and should be treated as any other thread ID when determining
precedence. This is because an unthreaded receipt (no thread ID) is still a superset of the `main` thread, just like
any other thread.

## Alternatives

Servers could split `m.receipt` EDUs and send threaded receipts in one EDU and unthreaded EDUs in another. This
creates additional EDUs, increasing bandwidth usage, processing time and increases complexity as servers need to
handle cases where EDUs are sent incompletely to remote clients/servers.

Servers could instead always choose the threaded receipt instead of the unthreaded receipt. This would make it
harder to implement thread-unaware Matrix clients, as some receipt information is lost and can only be found by
introspecting the threaded receipts.

## Security considerations

None.

## Unstable prefix

No unstable prefix required as no new endpoints / JSON keys are added in this proposal.

## Dependencies

None.
