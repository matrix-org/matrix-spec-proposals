# MSC3348: Server-Server Room based extensible communication

## Background and Introduction

Currently homeservers talk to each other over the federation using a set of API endpoints specialised
for exactly what the other homeserver wants to talk about. This works well and good for a lot of things
but well its not exactly the most extensible thing in the world or flexible thing in the world. 

Using rooms for Server to Server (This document uses the word server even tho saying node is probably
more accurate to compensate for clients that are Hybrids of Homeserver and Client as is the case for P2P Clients)
communication has benefits in that interfacing with rooms is well a whole world easier for developers
and will allow for having presistent states that the servers can agree on via state resolution
of the rooms utilised for this.

## The basics

These rooms can also be extended quite easily with custom functionality. One example of how this functionality
could be extended is to add a mjolnir module that upon seeing a event that it listens for it will cause
the homeserver to drop any event coming from its own HS that matches a rule it has been asked to follow.
So if purple.example informs blue.example that invites to Smith from John are automatically rejected
by Smith then blue.example could just drop the events in the first place as to not waste the resources
of both homeservers. This system would ofc rely on that blue does what purple asks but in the case blue
doesn't no harm has been done to purple that was not possible in the past. But if Blue and Purple are
both upstanding members of the federation they participate in they have now reduced load on the federation.
And implementing this would actually be very easy with this proposal as the mjolnir could be
granted permission by its home server to participate in the Server to Server communication room
between the 2 home servers in question. 

### The identifiers that servers should use to identify the server users

The IDs the homeservers should use is currently recommended to be a simple @:identifier
(identifier in this case replaces domain just to accommodate that P2P is a thing so we cant count on
it always being domain.) The author is currently not aware that using essentially a empty identifier
would be a problem. This identifier is currently completely off-limits and therefore perfect
and its completely implementation agnostic so it wont discriminate certain implementations or come into clash
with cases where a user has chosen to call them self's for example @dendrite:example.com or @synapse:example.com
or @conduit:example.com since that would also be a logical naming scheme to have the name be up to
each Homeserver implementation but this would complicate matters more than need be. 

## Clients need not support this room type

Server to Server communication rooms should also use a special type attribute as to communicate to clients
and other servers about their special nature. The type of `'type': 'm.s2s' should be used for this.
The nature of these rooms is important for clients to be aware of because well. Clients are not expected
to need to implement support for rendering a lot of the events in these rooms what so ever. 

By dictating that clients do not need to support rendering of the special standardised events used
for Server Server communication we effectively remove them from consideration for any client
that does not want to interact with these rooms thru Homeserver integration like in the case of
using a Modules interface like that Synapse offers or clients that respond to events getting sent. 

This is similar to the use case mentioned in [Insert MSC here] where a IOT room might be filled with
events that would not be properly rendered by a normal IM client but will be completely understandable
to a IOT client.

This MSC it self is not a Room Types MSC and just builds upon the `type` attribute introduced in MSC1772.

An other potential application for this MSC is to use it to build a MSC for Federating Reports and the author
of this MSC has plans to write an MSC like this separately as it is better to leave that as a companion MSC
that is dependent on this one as to have the Federated Reporting functionality not be essential to this MSC
being able to pass in the case it is determined that the solution to federated reporting is not desired.

## Room Upgrade Negotiation

Room upgrades for S2S rooms should not be handeled in the completely normal way. They can be done
essentially as normal once started but the procedure to get there is special.

This MSC defines 2 Types of upgrade path for Negotiation to Follow. These 2 paths are Vendor
or Standard Server 2 Server Upgrade. 

Standard Upgrade Server 2 Server upgrades will be started by one homeserver sending
a `m.s2s.upgrade.proposal` event that follows the following structure where it lists
its room versions it will accept upgrading to and what it prefers.

`Event Breakdown here`
The next step is for the other Homeserver to send a `m.s2s.upgrade.reply` event where it sends back
its own list of room versions if its list is diffrent. If the list is has matches the list of
the other homeserver it will send a `m.s2s.upgrade.accept` event if they match. This is expected
if both homeservers are running the Exact same software or if they follow the same system for
determining when its time to jump to a new room version for S2S.

After the homeserver that initiated the process recives a `m.s2s.upgrade.accept` event it will send
a `m.s2s.upgrade.ack` event in reply to the accept event and wait for a `m.s2s.upgrade.ack` reply.
This has the goal of making it so that both homeservers have to atleast once see the other homeserver
accept the upgrade plan. If this passes upgrade the room using the upgrade invite only room procedure
from MSC3325 and the room version to upgrade to is the one that has been accepted by both homeservers
as their most prefered choice. 

If the homeservers dissagree on their lists the process is to go down the list and check
what room versions they do agree on and what ratings they have. The version that both parties agrees
on with the highest rating in each servers list that is in both servers lists gets choosen.
If the servers fail to find a room version that they can agree on the server who started the process
is to send a `m.s2s.upgrade.fail` event with a `error` field with the contents `no match`. This error
is to be expected by servers choosing to operate in the highest Security mode where you only accept
to upgrade to the most secure room version avavible and not to compromise on this. 

Vendor exists to allow custom behavior like if we say for example the Synapse and Dendrite homeservers
want to only allow v6 to upgrade to v8 then they can call their vendor upgrade type and then negotiate
using their own rules. 

Vendor upgrades are initiated by sending a `m.s2s.upgrade` event and then in the event specifying
what vendor method you want to use. If the other homeserver does not accept your given vendor upgrade method
it replies to your `m.s2s.upgrade` event with a `m.s2s.upgrade.fail` with the `error` of `invalid method`. 

## Security considerations
Server users may be used to snoop into end-to-end conversation. To solve this problem, this paper
proposes server users joining rooms without `"type":  "m.s2s"` be ill-formed.

Room Upgrade Negotiation is vulnernable to Downgrade attacks in theory if the HS is not properly configured
but the author consideres this an acceptable compromise.

The MSC also provides a Very clear way to avoid the downgrade attack problem as a HS by saying
to other homeservers that you refuse to upgrade to a non secure room version.

## Alternatives
The only alternatives the author is aware of at this point are the 2 alternatives of that we either use the
mechanism of introducing a new endpoint for this and skpping the use of room logic and there is the alternative
of allowing every feature to use its own specialised systems. Now there are alternatives to the proposed problems 
this system solves but that is left for their MSCs.

## Unstable prefix

Use `support.feline.s2s` instead of `m.s2s` as the value of the `type` attribute in the `m.room.create` event
of such rooms. Events in the room need not be unstably-prefixed. Then, migrate it into the stable `m.s2s`
type using the room upgrade mechanism once this proposal lands.
