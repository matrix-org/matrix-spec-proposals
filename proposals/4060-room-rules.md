# MSC4060: Accept room rules before speaking

A common feature among other chat platforms is a requirement for users to
acknowledge that they've read the room's rules before they're allowed to send
a message. It's typically a challenge to implement such a feature reliably as
there's rarely anything preventing an automated client from accepting the rules
and promptly spamming, however for the typical case a sufficient barrier is
simply one which appears *most* of the time in front of users.

This proposal introduces a feature where rooms can define rules that users must
accept before they're allowed to speak. Perhaps controversially, this MSC does
*not* require a new room version as it does not tie acceptance of the rules into
the event authorization rules. This is a deliberate choice as a change in rules
would constitute a requirement that all past agreements are rendered invalid,
which may be a desired trait in some communities but not all. This is explored
in a little bit more detail in the Alternatives section.

## Proposal

A new `m.room.rules` state event with empty string state key is defined to
contain the rules themselves. Like [MSC3765](https://github.com/matrix-org/matrix-spec-proposals/pull/3765),
this is done using Extensible Events:

```jsonc
{
  "type": "m.room.rules",
  "state_key": "",
  "content": {
    "m.text": [
      {"body": "1. Don't be mean\n2. Be kind"},
      {"mimetype": "text/html", "body": "<ol><li>Don't be mean</li><li>Be kind</li></ol>"}
    ]
  }
  // other fields not shown
}
```

A user "accepts" the rules by referencing the rules event. **TODO**: Pick method.

**TODO**: Options include:

1. [MSC4058](https://github.com/matrix-org/matrix-spec-proposals/pull/4058) -
   the accepting user adds some structured metadata to the rules event.
2. [MSC4059](https://github.com/matrix-org/matrix-spec-proposals/pull/4059) -
   if changed to support mutations from unoriginal senders, mutating the event
   content in some way. This is probably dangerous though.
3. [Event relationships](https://spec.matrix.org/v1.8/client-server-api/#forming-relationships-between-events) -
   like we've done for pretty much everything else.

When `m.room.rules` is present in a room, and the user hasn't accepted them, the
client SHOULD prompt the user to accept the rules before allowing them to send
a message. In this MSC, it is expected that a bot will enforce acceptance before
allowing the user to send a message. For example, redacting all of the user's
events.

Servers SHOULD require the user to accept the rules before allowing them to send
events in the room.

Notable exceptions for clients, servers, and moderation bots are events which
are required for accepting the rules and membership events (ie: leaving rather
than accepting).

It is expected that a future MSC will define a structure or system to *require*
acceptance of the rules at the room level, potentially tied into a
[MSC4056](https://github.com/matrix-org/matrix-spec-proposals/pull/4056)-style
role. Using a role would allow a subset of users to bypass the rules (in cases
where they can't be bridged, for example), require this MSC's soft limit
approach, or enforce the rules via event authorization.

## Potential issues

**TODO**: Detail.

## Alternatives

This MSC deliberately does not tie acceptance of the rules into the event
authorization algorithm. Doing so with the current power level structure in
Matrix rooms could potentially lead to over-imposed opinions on what it means
to "speak" in a room, as well as requiring users to frequently accept rule
changes.

Instead, this MSC asks that a bot or local server make the decisions on what is
allowable before acceptance, and whether the rules need to be accepted every
time or not. It is expected that the protocol will eventually support many of
the constraints implemented by these servers and bots through future MSCs, such
as the role-based access control approach described in the proposal text above.

## Security considerations

**TODO**: Detail.

## Unstable prefix

While this MSC is not considered stable, implementations should use
`org.matrix.msc4060.room.rules` in place of `m.room.rules`.

**TODO**: Describe prefix for "accepting" the rules too.

## Dependencies

**TODO**: Declare.
