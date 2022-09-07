# MSC3886: Simple rendezvous capability

In MSCyyyy a proposal is made to allow a user to login on a new device using an existing device by means of scanning a
QR code.

In order to facilitate this the two devices need some bi-directional communication channel which they can use to exchange
information such as:

- the homserver being used
- the user ID
- facilitation of issuing a new access token
- device ID for end-to-end encryption
- device keys for end-to-end encryption

To enable MSCyyyy and support any future proposals this MSC proposes a simple HTTP based protocol that can be used to
establish a direct communication channel between two IP connected devices.

It will work with devices behind NAT. It doesn't require homeserver administrators to deploy a separate server.

## Proposal

### Protocol

`POST /`

`PUT /<channel id>`

`GET /<channel id>`

`DELETE /<channel id>`

### CORS

### Choice of server

Ultimately it will be up to the Matrix client implementation to decide which rendezvous server to use.

However, it is suggested that the following logic is used by the device/client to choose the rendezvous server in order
of preference:

1. If the client is already logged in: try and use current homeserver.
1. If the client is not logged in and it is known which homeserver the user wants to connect to: try and use that homeserver.
1. Otherwise use a default server.

## Potential issues

Because this is an entirely new set of functionality it should not cause issue with any existing Matrix functions or capabilities.

The proposed protocol requires the devices to have IP connectivity to the server which might not be the case in P2P scenarios.

## Alternatives

Try and do something with STUN or TURN or [COAP](http://coap.technology/).

## Security considerations

### Confidentiality of data

Whilst the data transmitted can be encrypted in transit via HTTP/TLS the rendezvous server does have visibility over the
data.

As such, for the purposes of authentication and end-to-end encryption the channel should be treated as untrusted and some
form of secure layer should be used on top of the channel.

### Denial of Service attack surface

Because the protocol allows for the creation of arbitrary channels and storage of arbitrary data, it is possible to use
it as a denial of service attack surface.

As such, the following standard mitigations such as the following may be deemed appropriate by homeserver implementations
and administrators:

- rate limiting of requests
- imposing a low maximum payload size (e.g. kilobytes not megabytes)
- limiting the number of concurrent channels

## Unstable prefix

None.

## Dependencies

None.
