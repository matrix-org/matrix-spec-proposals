# Guest State Events

## Problem

Currently guest users are not allowed to create arbitrary state events.  This is
a problem for [MSC3401](https://github.com/matrix-org/matrix-doc/pull/3401), 
where it would be useful for guests to be able to create `m.call.member` events 
in order to participate in a call.

## Proposal

Let guests send arbitrary state events much like a normal user. Servers may rate
limit state events from guests much more aggressively to mitigate abuse.

We also relax the existing requirement that guests are only allowed to send
`m.room.message` events, instead allowing them to send any kind of event
allowed by the room's power level configuration as if they were a normal user.

## Security considerations

The only reason that guests are denied from performing certain operations is to
avoid malicious unauthorised users consuming resources and causing a DoS.  In
this instance, sending state events can be quite resource intensive, so if we
didn't have a good use case that needed them it'd be right to veto them.

Also, by default, users (guest or otherwise) can't send state events, which
further reduces the risk of abuse.  Instead, a room intended for guest-capable
voice/video rooms as per MSC3401 would explicitly set a powerlevel to let users
send `m.call.member` events.  This MSC would simply make it then permissible
for guests to send as well as non-guests, subject to the powerlevels.

## Alternatives

Rather than using guest access, apps could use shared secret registration to
work around this limitation. However, that feels like a different MSC.
