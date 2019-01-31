# Proposal to do SRV lookups after .well-known to discover homeservers

Currently there is a logistical error proposed by [MSC1708](https://github.com/matrix-org/matrix-doc/pull/1708)
which results in some homeservers unable to migrate to the new functionality
proposed by [MSC1711](https://github.com/matrix-org/matrix-doc/pull/1711). This
can happen if the delegated homeserver cannot obtain a valid TLS certificate for
the top level domain, and an SRV record is used for backwards compatibility reasons.

## Proposal

We change the order of operations to perform a .well-known lookup before falling
back to resolving the SRV record. This allows for domains to delegate to other
hostnames and maintains backwards compatibility with older homeservers.

## Tradeoffs

More HTTP hits will be made due to the .well-known lookup being first. This is
somewhat mitigated by servers caching the responses appropriately, and using
connection pools where possible.
