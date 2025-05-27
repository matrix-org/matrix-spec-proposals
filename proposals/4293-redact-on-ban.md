# MSC4293: Redact on ban

[MSC2244 (accepted)](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/2244-mass-redactions.md)-style
mass redactions are incredibly helpful for cleaning up large volumes of spam, but still require sending
a dedicated event to clean up the spam. In a typical case, a user will get kicked/banned from a room
and the moderators will further redact some or all of their messages. Mass redactions have more use
cases, but the specific case of "redact everything upon ban" is something which may be easily backported
to existing room versions.

This proposal suggests adding a new flag to membership events to indicate to clients and servers that
all of that user's events should be redacted in addition to being kicked or banned. The flag isn't
protected from redaction itself, so may have some consistency issues, but overall should still provide
relatively high amounts of protection to rooms.

This proposal is exploratory and subject to change. Implementations may validate the idea through
early feature support, but MUST expect that things will change (or become completely rejected).

## Proposal

A new flag is added to [`m.room.member`](https://spec.matrix.org/v1.14/client-server-api/#mroommember)
events where the target user is kicked or banned (**TODO**: Allow on self-leaves too?): `redact_events`.
This flag is a boolean and, when `true`, causes servers (and clients) to redact all of the user's events
as though they received an [`m.room.redaction`](https://spec.matrix.org/v1.14/client-server-api/#mroomredaction),
including adding [`redacted_because`](https://spec.matrix.org/v1.14/client-server-api/#redactions) to
`unsigned` where applicable.

**Note**: This also means that if the user was kicked/banned with a `reason`, that event is automatically
compatible with the redaction `reason` field and shows up accordingly.

This redaction behaviour continues until the membership event itself is redacted (thus removing the
field) or another membership event removes the field. For example, if the user is unbanned, the moderator
MAY NOT choose to carry the `redact_events` flag to that kick (unban) event. Or, when the user rejoins
after a kick, the flag is implicitly dropped.

Other membership states with the flag no-op, such as joins.

Moderation bots and similar MAY still wish to issue (mass) redactions upon kick/ban to protect users
on servers or clients which don't have this feature.

Example ban:

```jsonc
{
  // Irrelevant fields excluded
  "type": "m.room.member",
  "state_key": "@spam:example.org",
  "sender": "@mod:example.org",
  "content": {
    "membership": "ban",
    "reason": "flooding", // this is copied to `redacted_because`, leading to clients showing it
    "redact_events": true
  }
}
```

The new field is proxied through to the event by the [`/kick`](https://spec.matrix.org/v1.14/client-server-api/#post_matrixclientv3roomsroomidkick)
and [`/ban`](https://spec.matrix.org/v1.14/client-server-api/#post_matrixclientv3roomsroomidban)
sugar APIs, like `reason` is.

## Potential issues

It's a little annoying that the flag is redacted when the membership event is redacted, however it's
extremely rare for a moderator/admin to redact a kick or ban event. We can fix this in a room version
trivially if it proves to be an issue.

Clients may miss the membership event if they are using lazy loading, though servers should already
be tracking which membership events the client has received and needs to render events in the timeline.
This should mean that those clients will still receive the event.

Servers which miss the event will eventually receive or retrieve it, just like they would with any
other event.

## Alternatives

Mass redactions are the cited major alternative, where a single event can target approximately 1500
other events in the room. New rooms can benefit from that functionality, especially for cases not
covered by this proposal, while existing rooms can be given an option to protect their users with
relative ease.

## Security considerations

As the room moderator/administrator would already send redactions, and may still for full protection,
it's not deemed any more risk than today. This may change if self-leaves are permitted to also carry
the field.

There may also be implementation or reliability bugs which inhibit the "stop redacting now" point
from working as intended. Server implementations in particular should ensure that an event received
after a membership event which asks for redaction is *really* affected by that redaction. ie: whether
it's just a late delivery, or if there's a join waiting for state res to make a determination.


## Unstable prefix

While this proposal is not considered stable, implementations should use `org.matrix.msc4293.redact_events`
instead of `redact_events`.

## Dependencies

This MSC has no direct dependencies.

## Credits

Credit goes to Erik of the Spec Core Team for the suggestion to look into this.
