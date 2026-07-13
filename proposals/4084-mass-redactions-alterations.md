# MSC4084: Improving security of MSC2244

[MSC2244](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/2244-mass-redactions.md)
introduces an idea of "mass redactions", where a single redaction event can target more than one event.
This provides significantly improved performance when dealing with large volumes of spam or redacting
one's own messages, but is also irreversible.

This proposal amends MSC2244 to accommodate previously-undisclosed security considerations.

## Background context

MSC2244 was accepted through FCP under an older process where implementation was not required before
FCP. Some time later, the SCT noted significant process overhead when implementation happens second,
so updated the process to require implementation before FCP can begin. MSC2244 however had already
finished FCP at the time - it's now stuck in a state where FCP is completed, but the MSC is not
accepted because it is not implemented.

Implementation on MSC2244 was blocked on internal security context from the SCT as of March 2022,
despite the MSC successfully completing FCP in November 2019. The concerns, now captured by this MSC,
were discovered through a brief attempt to implement the MSC during development of another feature.

After some unintended process delays, this MSC exists to cover the internal context captured throughout
2022.

With the new process in place, issues like the ones covered by this MSC are easier to catch before an
MSC is accepted then merged. Unfortunately, because of the older process in play, the MSC needs to
be modified by another MSC first - namely, the MSC described by this document.

### Unstable implementation

Under the older process MSC2244 falls under, implementation can happen *after* FCP is completed. To
qualify as "accepted", the MSC will need such an implementation and review from the SCT before it
can continue. It's not until the MSC is assigned a stable room version that it becomes merged to the
specification, and unstable identifiers (including the unstable room version) can be dropped.

Acceptance on MSC2244 is additionally qualified on resolution of the concerns described in this MSC,
though the exact solutions may vary. Once both implementation and security considerations are made,
the SCT will mark MSC2244 as accepted. The MSC would then qualify for inclusion in a (future) stable
room version.

## Problem

MSC2244 provides room moderators a way to redact multiple messages in a single event, reducing overall
traffic and therefore speed of removal. This is an incredibly useful tool when dealing with volumetric
spam - the sender is not required to generate the same volume of redactions (an amplification attack).

Mass redactions can also be used to remove an entire user from the conversation history, either
electively or by choice of a room moderator. When performed electively, the user is essentially trying
to erase their presence from the network/room. Though some metadata is retained, the conversation
history is completely destroyed in this scenario. This causes two problems of varying severity:

1. A choice has been imposed upon other members of the room, where their copy of the conversation has
   been altered. Matrix is structured with a belief that everyone has an equal right to the conversation,
   and a built-in tool which *easily* allows that conversation to be altered is not ideal. However,
   servers wishing to perform such a function on behalf of their users are already able to remove/disable
   rate limits on sending individual redaction events. Many servers over the years have elected to do
   exactly that to erase a user from the network as best as possible. Therefore, for the purposes of
   this MSC, it is considered a non-issue to support mass redactions in Matrix.

2. As mentioned above, mass redactions can be used by servers to erase as much of a user's footprint
   as possible. With redaction events supporting approximately 1500 targets and large public rooms
   typically having ~2000 messages per sender on average, a user can erase themselves in a few dozen
   events. This is an irreversible action undertaken by the user, and well within common rate limits
   for servers. Therefore, this action should be treated as a form of [deactivation](https://spec.matrix.org/v1.9/client-server-api/#post_matrixclientv3accountdeactivate)
   and require confirmation of identity before going forward with it, as a malicious user may have
   acquired the access token for the user. This MSC proposes changes to MSC2244 in line with this
   idea.

Further, MSC2244's authentication and acceptance rules for the new `m.room.redaction` event are unclear,
potentially allowing for a client to redact events which are not legally possible to redact with the
original event. The MSC tries to ensure clients are not made aware of event IDs that the server does
not have itself (or which are illegally included in the array), though it's theoretically possible for
a client to gain access to the unmodified `m.room.redaction` event and redact the illegal targets
anyways. This MSC proposes changes to how MSC2244 handles redactions to eliminate potential points of
abuse/trickery from malicious actors.

## Proposal

To help ensure that malicious actors are not able to effectively deactivate a user's account, the
existing [`PUT /_matrix/client/v3/rooms/:roomId/send/:eventType/:txnId`](https://spec.matrix.org/v1.9/client-server-api/#put_matrixclientv3roomsroomidsendeventtypetxnid)
endpoint MUST NOT accept `m.room.redaction` events in room versions supporting mass redactions. The
server MUST respond with a 400 HTTP status code and `M_BAD_STATE` error code for this condition.
Clients are still able to redact individual events at a time using the `/redact` endpoint, if desired.

To ensure that clients are able to actually use mass redactions, a copy of `/send` is introduced with
[User-Interactive Authentication](https://spec.matrix.org/v1.9/client-server-api/#user-interactive-authentication-api)
(UIA) optionally used by the server. The new `PUT /_matrix/client/v4/rooms/:roomId/send/:eventType/:txnId`
endpoint moves the event content from the top level down into a `content` key. At the top level is the
required `auth` key from UIA. Clients SHOULD NOT provide `auth` on the first request (per event type
and transaction ID pair), as the server might not require UIA. If the server *does* require UIA, it
will respond with the normal 401 and stages information described by UIA - the client would then be
required to repeat the request with the added `auth`.

In examples, the request flow may look like the following:

```
> PUT /_matrix/client/v4/rooms/!example/send/m.room.redaction/1234
> Authorization: Bearer accesstoken
> Content-Type: application/json

{
  "content": {
    "redacts": [/* ... */]
  }
}

< HTTP/1.1 401 Unauthorized
< Content-Type: application/json

{
  "completed": [],
  "flows": [{"stages": "m.login.password"}],
  "params": {},
  "session": "abc"
}

> PUT /_matrix/client/v4/rooms/!example/send/m.room.redaction/1234
> Authorization: Bearer accesstoken
> Content-Type: application/json

{
  "content": {
    "redacts": [/* ... */]
  },
  "auth": {
    "type": "m.login.password",
    "identifier": {
      "type": "m.id.user",
      "user": "@self:example.org"
    },
    "password": "CorrectHorseBatteryStaple",
    "session": "abc"
  }
}

< HTTP/1.1 200 OK
< Content-Type: application/json

{
  "event_id": "$whatever"
}
```

Alternatively, if the server does not require UIA to send the given event, the 401 intermediary error
can be skipped, as demonstrated below:

```
> PUT /_matrix/client/v4/rooms/!example/send/m.room.redaction/1234
> Authorization: Bearer accesstoken
> Content-Type: application/json

{
  "content": {
    "redacts": [/* ... */]
  }
}

< HTTP/1.1 200 OK
< Content-Type: application/json

{
  "event_id": "$whatever"
}
```

When a server decides to apply UIA is left as an implementation detail. It is recommended that at a
minimum servers require UIA for a user to redact more than 25 of their own events in a single redaction
event. Other restrictions are not currently suggested, though in future more event types may require
UIA in order to be sent.

The existing `PUT /_matrix/client/v3/rooms/:roomId/send/:eventType/:txnId` endpoint is additionally
[deprecated](https://spec.matrix.org/v1.9/#deprecation-policy) by this proposal. Note that besides
the change in request body to support UIA (and associated error condition), the request is otherwise
unchanged.

MSC2244's authorization rules and redaction handling are additionally replaced to be in line with
[room version 3](https://spec.matrix.org/v1.9/rooms/v3/#handling-redactions) and greater. Instead
of sending a filtered redaction event down to a client, the redaction event is withheld until *all*
target events are known by the server, and are valid targets. The server SHOULD attempt to retrieve
unknown target events from other servers in the room with appropriate backoff to avoid needlessly
delaying the redaction's effect.

This approach helps diminish the impact of a redaction event targeting future or deliberately missing
events causing future issues in clients, servers, and conversation history. Further, by assuming that
a server listing an event ID in the redaction means they have knowledge of that event ID, the sender
is discouraged from including known-invalid entries. They would be the first server to be contacted
when every other server is attempting to locate that missing event.

Servers should note that a malicious server may still include deliberately malicious entries to consume
time spent retrying (and failing) on every other server, slowing them down. Servers should give up
trying to locate missing target events after a reasonable period of time. Specifics are left as an
implementation detail.

## Potential issues

UIA is theoretically going away or changing with the OIDC work from the core team. This proposal makes
the transition harder or at least more verbose once OIDC is ready. Ideally, the fewest transitions
possible would be performed, though with OIDC potentially being further out than this MSC, it feels
appropriate to continue using UIA for now.

This MSC also forces servers to withhold redactions until *all* target events are received and validated.
In the case of volumetric spam, this means a server will be required to first download that spam then
redact it. With each event being maximum 65kb in size, this could be significant network traffic. The
alternative is a malicious sender could cause future problems or confuse clients due to trivially
possible bugs in servers, thus exploiting individual implementation bugs to alter the conversation
history depending on viewer.

## Alternatives

No significant alternatives not already discussed identified.

## Security considerations

This proposal discloses a consideration around mass redaction being the same as deactivation, and
identifies a potential security issue relating to malicious redaction events. How these issues are
resolved from a security standpoint is described inline by the proposal text.

## Unstable prefix

MSC2244 is from a time before an unstable prefix section was included in proposals. This proposal adds
one, described here.

While MSC2244 is not considered stable, implementations should use `org.matrix.msc2244` as the room
version identifier, using [v11](https://spec.matrix.org/v1.9/rooms/v11) as a base. Note that this
inherits MSC2244's backwards compatibility clauses as [formal specification](https://spec.matrix.org/v1.9/rooms/v11/#moving-the-redacts-property-of-mroomredaction-events-to-a-content-property).

For clarity, the `org.matrix.msc2244` room version additionally includes the changes described by
this MSC too.

## Dependencies

This proposal has no direct dependencies.
