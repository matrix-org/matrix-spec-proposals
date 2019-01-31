# Proposal to do SRV lookups after .well-known to discover homeservers

Currently there is a logistical error proposed by [MSC1708](https://github.com/matrix-org/matrix-doc/pull/1708)
which results in some homeservers unable to migrate to the new functionality
proposed by [MSC1711](https://github.com/matrix-org/matrix-doc/pull/1711). This
can happen if the delegated homeserver cannot obtain a valid TLS certificate for
the domain, and an SRV record is used for backwards compatibility reasons.

Specifically, in order to be compatible with requests from both Synapse 0.34 and 1.0,
servers can have both a SRV and a .well-known file, with Synapse presenting a certificate
corresponding to the target of the .well-known. Synapse 0.34 is then happy because it
will follow the SRV (and won't care about the incorrect certificate); Synapse 1.0 is
happy because it will follow the .well-known (and will see the correct cert).

## Proposal

We change the order of operations to perform a .well-known lookup before falling
back to resolving the SRV record. This allows for domains to delegate to other
hostnames and maintains backwards compatibility with older homeservers.

## Tradeoffs

More HTTP hits will be made due to the .well-known lookup being first. This is
somewhat mitigated by servers caching the responses appropriately, and using
connection pools where possible.
