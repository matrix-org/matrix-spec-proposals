# MSC2390 - Incidental elimination of Ephemeral Data Units

The Ephemeral Data Unit is a class of Matrix Event without an `event_id`. EDU's
are specified in contrast to Persistent Data Units (PDU) which are addressed
by an `event_id`. EDU's are intended to provide a basis to implement features
which may require some order of magnitude more resources than would be tolerable
for a PDU.

### Problems

Currently there are only three feature applications of an EDU:
read-receipts, typing and presence. In contrast, there are scores of features
applied through the PDU mechanism; with several developments actively in
motion. Regardless of the etiology for this stagnation, we contend that EDU's
are an unfavorable mechanism. Nevertheless, many things are known about why EDU's
are not favorable: they provide an unreliable mechanism for features that
inevitably require reliability; thus increases implementation complexity. EDU's
are also an insecure mechanism. Their payloads are not signed by their origins.
They are a clear vector for attack and on at least on one occasion, the subject
of a CVE against Synapse.

### Solution

This MSC specifies the following:

1. No further use of this mechanism should be specified.

2. When current use of EDU's are eliminated this construct should be stricken
from the specification.
