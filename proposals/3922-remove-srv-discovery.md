# MSC3922: Removing SRV records from homeserver discovery

Currently when [resolving server names](https://spec.matrix.org/v1.4/server-server-api/#resolving-server-names),
homeservers (or any implementation trying to locate a server, such as integration managers or widgets
using [OpenID Connect validation](https://spec.matrix.org/v1.4/server-server-api/#openid)) must support
an ability to resolve SRV DNS records. Aside from this being difficult in the case of widgets (for example),
SRV records typically cause deployment issues due to them not working "as expected" by server administrators.

In addition to SRV records not "properly" supporting CNAMEs, TLS certificates are difficult to configure
correctly and often lead to issues with the wrong certificate being presented. These sorts of issues
come up often enough that [Synapse's documentation](https://matrix-org.github.io/synapse/v1.70/delegate.html#srv-dns-record-delegation)
doesn't even explain how to use SRV records, instead referencing the specification itself and citing that
.well-known is often what administrators are looking for. The documentation additionally calls it
"SRV delegation", further indicating that the use of SRV records is complex (it's not true delegation,
unlike what is possible with .well-known).

This proposal removes all reference of SRV records from the homeserver discovery specification, and
a plan to handle the rollout of such an invasive change.

## Proposal

In short, the [current rules](https://spec.matrix.org/v1.4/server-server-api/#resolving-server-names)
which reference SRV records are deleted. This leads to the following discovery mechanism:

*Note*: Some details, such as caching and certificate presentation, are excluded. They are unchanged.

1. If the hostname is an IP literal, then that IP address should be used. If a port number is given then
   it should be used, otherwise using port 8448. The `Host` header in the request is set to the server name
   (which is the IP address), with port number if explicitly given.
2. If the hostname is *not* an IP literal, but does have an explicit port, resolve the name using A or
   AAAA records to an IP and use that with the explicit port. The `Host` header in the request is set to
   the server name, with port number.
3. If the hostname is *not* an IP literal, a regular HTTPS request is made to the .well-known endpoint
   on that domain. The hostname presented by this endpoint is called the "delegated hostname" and repeats
   discovery steps 1 & 2 above. It does not repeat step 3 (this step) as that could cause infinite loops
   or needless delays in discovery.
4. Server discovery fails and the server is presumed offline or invalid if it has not been resolved to
   a usable IP and port by this step.

Clearly this would cause disruption in the larger ecosystem as some servers might still be using SRV
records to identify themselves. Readers of this proposal are encouraged to proactively change over to
.well-known to identify if there are legitimate reasons for keeping SRV records, even if this proposal
is still in a draft/unapproved state. 

In order to not cause massive breaking changes in the ecosystem, this proposal first deprecates SRV
discovery for a minimum of 1 calendar year from the time of the spec release itself. Afterwards, at the
discretion of the Spec Core Team (SCT), SRV discovery can be removed without notice.

Homeserver authors (Synapse, Dendrite, Conduit, etc) are encouraged to use the deprecation period to
help their users transition to .well-known discovery, and if reading this proposal before it is accepted
then to help identify any legitimate reason to keep SRV discovery in the specification (for example, a
user of theirs is completely unable to switch to .well-known - the case would be discussed to determine
if it's a reasonable blocker for this proposal). 

The Matrix.org Foundation would also be engaged in helping users move over to .well-known through the
normal channels (blog posts, changelog on Synapse, social media, etc). 

## Potential issues

As identified, this change could impact legitimate usage of SRV records for discovery - this proposal
exists to give readers, homeserver authors, etc time to identify these cases before the proposal is put
up for final comment period (thus proposing it for acceptance). If legitimate cases of SRV records are
found, this proposal may be declined or rejected (per normal process).

## Alternatives

This may be a good time to design new discovery mechanisms, however that would have an even larger
impact on the ecosystem. Additionally, .well-known appears to be the (current) industry standard
for this mechanism.

## Security considerations

Removing SRV discovery could mean a higher rate of homeservers being delegated to third party providers
or being targets of takeover attempts, however given Synapse (the most populous homeserver implementation)
already strongly recommends .well-known over SRV, this issue is considered trivial in nature.

## Unstable prefix

No unstable prefix is possible for this proposal. Instead, a migration period is explicitly proposed
as an alternative.

## Dependencies

None relevant.
