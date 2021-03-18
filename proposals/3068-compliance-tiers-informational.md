# MSC3068: Compliance profiles

This MSC seeks to standardise the terminology on compliant a Matrix client or
a server is.

## Proposal

Unfortunately, not all clients and not all servers implement the specification
as exactly written, and noncompliant or unspecified events that are accepted
are very common. This informational MSC describes several compliance tiers,
based on the implementation of required and optional features, and features not
specified in the official Matrix protocol specification ("extensions"):

* Strictly compliant: All required and optional parts of the spec is fully
implemented, with no additional checks or no extensions.
* Petty compliant: All required parts are implemented, with some required
checks missing and possibly with extensions.
* Compliant: All required parts are implemented with no additional checks,
possibly with some extensions. Optional features may or may not be implemented.
* Undercompliant: Some required parts of spec are missing in the implementation,
but not to the point to prevent coherent resolution or authentication.
* Overcompliant: All required parts are implemented, with some additional
checks, possibly to the point of rejecting any unspecified events from the
other party.
* Overly overcompliant: All required and optional parts are implemented, and
with so many additional checks that a counterparty deviating in any manner
cannot communicate in any manner.
* Non-compliant: Anything else.

These tiers apply to clients and servers equally.

## Interoperation considerations

* Petty compliant and undercompliant servers are a security risk. Therefore
having undercompliant or petty compliant servers with open registration
is discouraged.
* Overcompliant or overly overcompliant clients will fail to communicate
with most of the current Matrix ecosystem.
* Overly overcompliant parties will fail to communicate with undercompliant or
petty compliant parties, and may fail to communicate with strictly compliant
parties.
