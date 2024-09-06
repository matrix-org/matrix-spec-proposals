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
that the server is permanently offline and should suspend further discovery attempts for a period
of time specified by the homeserver's implementation.

This will avoid unnecessary DNS lookups and requests to servers that no longer wish to federate.

### Server-Server API Changes

When a homeserver receives a `410 Gone` response from the `/.well-known/matrix/server` endpoint,
it should consider the server offline and halt discovery.

The period until discovery is re-attempted can be determined by the homeserver's implementation,
such as using exponential backoff, waiting a period of days, or until the next restart.

### Implementation Details

- The suspension period should be configurable to allow administrators to fine-tune the behaviour
  based on their specific needs and network conditions.
- Homeservers should resume discovery attempts after the suspension period has elapsed, or when new
  PDUs or EDUs are received from the server as this should signal that the server is online.

## Potential Issues

If the suspension period is too long, it may delay the detection of a server that has come back
online. Conversely, too short and it may lead to unnecessary requests.

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
