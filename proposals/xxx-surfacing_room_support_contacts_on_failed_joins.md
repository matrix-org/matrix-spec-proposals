# MSCXXXX: Surfacing room contacts on failed joins

When a user's attempt to join or knock on a room is rejected — because they are
banned, because their server is denied, or for any other reason — they typically
see a generic message such as "You have been banned from this room" or "This
server is not permitted to join this room". They are given no path to contest
the decision, even when the room has explicitly published a contact for exactly
this purpose.

[MSCXXXX](https://github.com/matrix-org/matrix-spec-proposals/pull/XXXX)
introduces the `m.room.contact` state event, which lets a room advertise
responsible contacts. However, a user who is banned or whose server is blocked
generally cannot read room state, so they cannot read that event through normal
means. This proposal lets the resident server include the room's published
contact information in the rejection response, so the joining server can forward
it to the user's client for display.

## Proposal

This builds on MSCXXXX and changes only the *delivery* of already-published
information on a failed join or knock; it introduces no new place for a room to
declare contacts and defines no new error conditions.

### Federation response

When a resident server rejects a remote user's attempt to join or knock on a
room — at whichever point in the join or knock handshake the rejection is issued
(currently the `make_join`, `send_join`, `make_knock`, and `send_knock`
endpoints) — and that room has an `m.room.contact` state event with the empty
state key, the server MAY include the content of that event in the error
response under a dedicated `contact` key:

```json
{
  "errcode": "M_FORBIDDEN",
  "error": "You are banned from this room",
  "contact": {
    "contacts": [
      {
        "matrix_id": "@alice:example.org",
        "email_address": "appeals@example.org",
        "role": "m.role.admin"
      }
    ],
    "support_page": "https://example.org/room-support-page"
  }
}
```

The `contact` value, when present, MUST be the verbatim `content` of the room's
`m.room.contact` state event. This proposal adds only an OPTIONAL field to
existing rejection responses: it does not change the `errcode` or HTTP status
code of any response and introduces no new error conditions or error codes. A
server MAY omit the field (for example if the event is absent, or by policy),
and consumers MUST treat its absence as "no contact information available"
rather than as an error.

Because this only adds an optional field to error responses that are already
produced by the join and knock endpoints, it introduces no new authentication,
rate-limiting, or guest-access requirements on either the Server-Server or
Client-Server side, and no new request path.

### Client-Server delivery

When a user's own server receives a federated join or knock rejection containing
`contact`, it SHOULD propagate that object to the client in the corresponding
Client-Server API error response (e.g. the response to
`POST /_matrix/client/v3/join/{roomIdOrAlias}`,
`/_matrix/client/v3/rooms/{roomId}/join`, or
`/_matrix/client/v3/knock/{roomIdOrAlias}`) under the same `contact` key.

For a purely local rejection (the user's own server is the resident server and
rejects the join or knock), the server MAY populate `contact` directly from
local room state using the same rules.

### Client behaviour

A client that receives a rejection containing `contact` SHOULD, instead of (or
in addition to) the generic rejection message, present the contact information
so the user can seek help or appeal — for example, "You have been banned from
this room. To appeal, contact @alice:example.org or visit \<support_page\>."
Clients MUST apply the same security treatment defined in MSCXXXX: the data is
an unverified claim by the room, contacts MUST NOT be shown as verified
identities, and `support_page` MUST be handled with the client's normal
untrusted-URL safety measures.

## Potential issues

- **Information disclosure to rejected users.** This intentionally exposes the
  contact event to a user who could not otherwise read room state. As the event
  is explicitly intended to be reachable by people seeking to appeal — including
  banned users — this is the desired behaviour. No other room state is exposed.
- **Server discretion causes inconsistency.** Because inclusion is OPTIONAL,
  whether a rejected user sees contact info depends on the resident server's
  implementation and policy. This is acceptable: the field is a best-effort
  courtesy, and the fallback is exactly today's behaviour.

## Alternatives

- **Require clients to fetch the event via a peek/`/state` request after a
  failed join.** Rejected users generally cannot peek or read `/state`, so this
  does not work for the banned/blocked case that motivates the proposal.
- **A dedicated "appeal info" endpoint keyed by room ID.** This adds a new
  endpoint (with its own auth, rate-limiting, abuse, and enumeration concerns)
  to deliver data the rejection response can already carry inline. Inlining is
  simpler and leaks no more than the rejection itself.
- **Folding this into MSCXXXX.** Kept separate deliberately so that the state
  event (useful to existing members and in-room bots on its own) is not blocked
  on federation and client changes.

## Security considerations

In addition to the considerations inherited from MSCXXXX (impersonation, email
harvesting, `support_page` phishing, and the no-authorisation-signal rule, all
of which apply unchanged to the forwarded copy):

- **Disclosure scope.** The `contact` field MUST contain only the `content` of
  the room's `m.room.contact` event; a resident server MUST NOT place any other
  room state inside this field. The event's content is the only thing the room
  has designated as publicly contactable. This says nothing about other fields
  in the rejection response, which remain governed by their own definitions.
- **Spoofed rejection responses.** A malicious resident server could attach an
  arbitrary `contact` object to a rejection, directing a rejected user's appeal
  to an attacker-controlled address. This is bounded by the fact that the
  resident server already controls the room's state and the rejection itself; a
  user who does not trust the resident server has no stronger guarantee
  elsewhere. Clients MUST therefore present the contact as room-supplied and
  unverified.
- **Untrusted content handling.** The `contact` object is room-controlled
  content delivered to a non-member, and a receiving server MUST treat it as
  untrusted. It MUST apply the same size and validation limits it already
  applies to the response in question, and MUST handle a malformed or oversized
  object gracefully — dropping the field rather than failing the rejection it
  accompanies. A resident server MAY decline to include the field for any
  reason.

## Unstable prefix

Until this proposal is accepted, the response field uses
`net.codestorm.mscXXXX.contact` (rather than the bare `contact`), in both the
Server-Server and Client-Server rejection responses:

| Proposed (this MSC)        | Unstable form                   |
|----------------------------|---------------------------------|
| `contact` (response field) | `net.codestorm.mscXXXX.contact` |

The embedded object reuses the event content defined by MSCXXXX and follows that
proposal's own unstable-prefix rules for its inner fields.

## Dependencies

This proposal depends on
[MSC4489](https://github.com/matrix-org/matrix-spec-proposals/pull/4489)
(`m.room.contact` state event), which MUST be accepted first.
