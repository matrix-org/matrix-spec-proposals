# MSC4045: Deprecating the use of IP addresses in server names

A server in Matrix must be named according to the [existing grammar](https://spec.matrix.org/v1.7/appendices/#server-name),
which includes support for bare IPv4 and IPv6 addresses. These bare IP addresses are then further
handled by the [server discovery](https://spec.matrix.org/v1.7/server-server-api/#server-discovery)
algorithm when trying to make contact with the target server. However, a challenge arises due to
the specification's [requirement to use TLS](https://spec.matrix.org/v1.7/server-server-api/#tls):
getting a valid or useful certificate from a known Certificate Authority is effectively impossible.

If a server *does* somehow get a certificate for an IP address, the operator of that server can *never*
lose that IP address if they plan to continue communicating with the rest of the federated network.
Worse, the operator can intentionally recycle the IP address as a [DoS vector](https://github.com/matrix-org/matrix-spec/issues/386).

Further, [server ACLs](https://spec.matrix.org/v1.7/client-server-api/#server-access-control-lists-acls-for-rooms)
already have a capability to ban bare IP address server names in rooms, and the vast majority of
known public rooms using server ACLs already do so (largely thanks to tools like [Mjolnir](https://github.com/matrix-org/mjolnir)
which non-optionally set the `allow_ip_literals` flag to `false`).

This proposal deprecates the use of bare IP addresses, and entirely bans them from a future room
version, preventing/discouraging further IP-only server names from appearing in the public federation.

## Proposal

In a future room version, the [grammar](https://spec.matrix.org/v1.7/appendices/#server-name) for
a server name is adjusted to be:

```
server_name = hostname [ ":" port ]
port        = 1*5DIGIT
hostname    = 1*255dns-char
dns-char    = DIGIT / ALPHA / "-" / "."
```

The special considerations for IPv4 and IPv6 addresses are removed.

Additionally, steps 1 and 3a of the [server name resolution algorithm](https://spec.matrix.org/v1.7/server-server-api/#resolving-server-names)
are *deprecated*. Deprecation in this context is to discourage continued use, and to queue the
affected steps for eventual removal from the specification under the [deprecation policy](https://spec.matrix.org/v1.7/#deprecation-policy).

## Potential issues

Users on servers with affected by this MSC will be stuck and unable to join new/upgraded rooms.
[MSC4044](https://github.com/matrix-org/matrix-spec-proposals/pull/4044) goes into detail regarding
the anticipated solution for such users.

Local development environments and private federations are not affected by these changes, as they
are able to implement them anyways without affecting the overall usage of the protocol. Development
environments already typically disable the TLS requirement, for example, and can simply use `localhost`
with port numbers to differentiate servers. Developers can additionally update their hosts file to
get away from `localhost` if desirable.

## Alternatives

No sufficient alternatives known.

## Security considerations

Per the introduction, a Denial of Service vector is (eventually) mitigated by the effects of this MSC.

## Unstable prefix

This MSC can be implemented in a room version identified as `org.matrix.msc4045`. A future MSC will
be required to incorporate this MSC into a stable room version.

## Dependencies

This MSC inherits the account portability concerns of [MSC4044](https://github.com/matrix-org/matrix-spec-proposals/pull/4044),
but is not blocked by MSC4044 being accepted. Similarly, the deprecation approach for the discovery algorithm
is copied in a non-blocking way from [MSC4040](https://github.com/matrix-org/matrix-spec-proposals/pull/4040).

As of writing, this MSC is required by the Spec Core Team's documents/proposals within the MIMI working
group at the IETF.
