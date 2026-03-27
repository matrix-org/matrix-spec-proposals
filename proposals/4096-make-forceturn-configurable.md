# MSC4096: Make forceTurn option configurable

This proposal extends the Matrix protocol to allow servers to ask the client application to force use of TURN server for video calls. Currently, use of the TURN or a P2P protocol to establish the WebRTC connection is left to the client's discretion. This raises security issues when the server administrator needs to make sure client IPs are never exposed.

## Background

Element is increasingly used by European agencies, ministries, universities, etc. In these ecosystems, where data can be sensitive, the risk of users being targeted by cyber-attacks is heightened, and encourages the system administrator to impose stricter security rules. We've had CIOs from such organizations mention this security aspect as a blocking factor in Element adoption.

## Proposal

Introduce an optional configuration for Matrix servers that allows them to force TURN. If TURN is forced server-side, then this configuration should override client-side configuration (in Element's case, the configuration is stored in the "forceTurn" localStorage key).

This could be put into .well-known:
```json
{
  "m.homeserver": {  },
  "im.vector.riot.jitsi": {},
  "im.vector.riot.e2ee": {},
  "im.vector.riot.forceTurn": true,
}
```

## Potential issues

- If the TURN server is down, then even 1-to-1 calls would fail.
- If the client application still displays the option while it's forced server-side, this may be confusing for the user. The client-side configuration should actually be hidden if forced server-side.

## Alternatives

The alternative is to force the configuration client-side, but this works only if we bundle the client application ourselves. It will be still possible for the user to connect from a client application built by another party, so this does not really address the issue.

## Security considerations

Not revealing the IP addresses of the communicating parties to each other can be important in situations where the anonymity of the parties is a concern.

TURN servers can be configured to provide DDoS protection, which is not the case in direct P2P connections.