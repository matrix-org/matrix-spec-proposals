# MSC3068: Compliance profiles (INFORMATIONAL)

Unfortunately, not all clients and not all servers implement the specification
as exactly written, and noncompliant or unspecified events that are accepted
are very common. This informational MSC describes several compliance tiers:

* Strictly compliant: All required and optional parts of the spec is fully
implemented, with no additional checks or no extensions.
* Petty compliant: All required parts are implemented, with some required
checks missing and possibly with extensions.
* Compliant: All required parts are implemented with no additional checks,
possibly with some extensions.
* Undercompliant: Some required parts of spec are missing in the implementation,
but not to the point to prevent coherent resolution or authentication.
* Overcompliant: All required parts are implemented, with some additional
checks, possibly to the point of rejecting any unspecified events from the
other party.
* Overly overcompliant: All required and optional parts are implemented, and with
so many additional checks that a counterparty deviating in any manner cannot
communicate in any manner.
* Non-compliant: Anything else.

These tiers apply to clients and servers equally.
