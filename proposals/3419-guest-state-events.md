# Guest State Events

## Problem

Currently guest users are not allowed to create arbitrary state events.  This is a problem for MSC3401, where it would be useful for guests to be able to create `m.call.member` events in order to participate in a call.

## Proposal

Let guests send arbitrary state events much like a normal user. Servers may rate limit state events from guests much more aggressively to mitigate abuse.

## Security considerations

The only reason that guests are denied from performing certain operations is to avoid malicious unauthorised users consuming resources and causing a DoS.  In this instance, sending state events can be quite resource intensive, so if we didn't have a good use case that needed them it'd be right to veto them.

## Alternatives

Rather than using guest access, apps could use shared secret registration to work around this limitation. However, that feels like a different MSC.
