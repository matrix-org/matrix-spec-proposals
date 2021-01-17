# MSC2970: Remove pusher path requirement

Recently synapse [removed the ability to set arbitrary pusher paths](https://github.com/matrix-org/synapse/pull/8865),
in order to follow the spec. During the time that synapse has allowed any pusher paths, it has shown
itself to be very useful, to the point where this fix for synapse to follow the spec has become a
real hindrance in some areas.

With the need of push notifications without FCM or apples push system getting greater and greater, an
elegant approach is to self-host push for your own devices and completely remove the need of any gateway.
This has been experimented with before, in projects such as [matrix-gotify](https://gitlab.com/Sorunome/matrix-gotify).
These setups, however, typically have a URL specific to a device. The requirement of pushing to
`/_matrix/push/v1/notify` makes this requirement impossible.

Additionally p2p push could push directly to an ipv6 address of a phone, if it is known. Depending on
implementation a custom path is not possible here, either.

In general, having a path requirement for the pushers basically forces app developers to implement
and host matrix-specific gateways, instead of just being able to push general json blobs directly to
your phone. The removal of a pusher path requirement would *greatly* increase flexibility here.

## Proposal

The requirement for pushers with a kind `http` to have the path `/_matrix/push/v1/notify` is removed.
The homeserver is expected to just push notifications in the specified format to the URL as given,
including host, path and query part. The requirement that pusher URLs MUST be https remains.

### Versioning

In the future a new, incompatible, push format may be introduced. As a client typically dictates what
format of push it wants, the new format could be indicated by setting the pusher kind to e.g. `httpv2`.
The client is then also expected to use a pusher URL which is capable of that new format. That way,
client, server and wherever the pusher URL points to all know what payload to expect.

## Potential issues

None

## Alternatives

Instead of allowing the pusher path to be anything, it could be introduced that the pusher path may
be prefixed with custom path fragments, but must still end in `/_matrix/push/v1/notify`. This approach
tries to solve future versioning of different payloads by setting the version within the path. However,
it would make matrix harder to integrate into existing push systems without the need for a gateway,
as a push server might not expect paths to be suffixed. The versioning via introducing a new pusher
kind seems appropriate either way, if the payload significantly changes. As such, it seems that allowing
any pusher paths is the less restrictive approach.

## Security considerations

None
