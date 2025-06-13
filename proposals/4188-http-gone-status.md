# MSC4188: Handling 410 Gone Status in Matrix Server Discovery

*This proposal aims to improve the efficiency of Matrix server discovery by introducing a mechanism
for homeservers to handle the `410 Gone` HTTP status code. This will help reduce unnecessary
requests to servers that are intentionally no longer available, optimising network resources and
improving overall performance.*

## Proposal

Currently, when a Matrix homeserver attempts to discover another server, as a first step it checks
that server's `/.well-known/matrix/server` endpoint for possible delegation. Any status other than
`200 OK` is currently considered an error and should result in continuing the discovery process,
checking for SRV records and/or trying the default port.

This proposal suggests that homeservers should interpret a `410 Gone` status code as an indication
that the server intends to be permanently offline and should suspend further discovery attempts for
an extended period of time specified by the homeserver's implementation.

The intent of returning `410 Gone` is to signal "this server is permanently gone and does not wish
to federate", however implementations should treat this as a temporary suspension rather than a
permanent block, as domain ownership can change over time and server operators may change their mind.

This will avoid unnecessary DNS lookups and requests to servers that no longer wish to federate.

### Server-Server API Changes

When a homeserver receives a `410 Gone` response from the `/.well-known/matrix/server` endpoint,
it should consider the server offline and halt discovery attempts for an extended period.

The period until discovery is re-attempted can be determined by the homeserver's implementation,
such as using exponential backoff, waiting a period of weeks or months, or until the next restart.

This MSC recommends homeservers *should* wait a minimum of 24 hours and *should* wait no longer
than 90 days, balancing the need to respect the server's intent to be offline whilst allowing for
potential future changes in server operation or domain ownership.

Homeservers *should* resume normal discovery attempts immediately if they receive new PDUs or EDUs
from the server, as receiving new activity signals the server is online and the `410 Gone` status
may no longer be accurate.

### Implementation Details

- The suspension period should be configurable to allow administrators to fine-tune the behaviour
  based on their specific needs and network conditions.
- Homeservers should resume discovery attempts after the suspension period has elapsed, or when new
  PDUs or EDUs are received from the server, as receiving new activity signals the server is online.
- Implementations may choose to use exponential backoff, starting with shorter periods and gradually
  increasing to the maximum configured duration.

## Potential Issues

If the suspension period is too long, it may delay the detection of a server that has come back
online under new management. Conversely, too short and it may lead to unnecessary requests to
servers that genuinely wish to permanently cease federation.

The recommended maximum of 90 days attempts to balance these concerns whilst significantly reducing
unnecessary requests compared to current behaviour.

## Alternatives

- **Permanent Suspension**: Instead of a configurable suspension period, homeservers could
  permanently stop discovery attempts for servers that return a `410 Gone` status. However,
  this approach may lead to issues if the server comes back online.
- **No Change**: Homeservers could continue to handle the `410 Gone` status as they currently do,
  without any special treatment. This would not address the inefficiencies (and unwanted requests)
  caused by repeated discovery attempts.

## Unstable Prefix

No unstable prefix has been proposed as the `410 Gone` status currently causes servers to continue
discovery as normal.

## Dependencies

This MSC does not have any dependencies on other MSCs.
