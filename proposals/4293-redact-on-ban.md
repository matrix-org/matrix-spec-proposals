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

## Proposal

A new flag is added to [`m.room.member`](https://spec.matrix.org/v1.14/client-server-api/#mroommember)
events where the target user is kicked or banned: `redact_events`. This flag is a boolean and, when
`true`, causes servers (and clients) to redact all of the user's events as though they received an
[`m.room.redaction`](https://spec.matrix.org/v1.14/client-server-api/#mroomredaction), including
adding [`redacted_because`](https://spec.matrix.org/v1.14/client-server-api/#redactions) to `unsigned`
where applicable. An `m.room.redaction` event is not actually sent, however.

**Note**: This also means that if the user was kicked/banned with a `reason`, that event is automatically
compatible with the redaction `reason` field and shows up accordingly.

Similar to regular redactions, if the sender of the membership event can't actually redact the target's
events, the redaction doesn't apply. This means having a power level higher than or equal to `redacts`
*and* `events["m.room.redaction"]` (if set). We maintain the `events` check despite not actually sending
events of that type to keep the same expectations within rooms. If the sender doesn't have permission
to redact an event normally, no redaction is applied.

If the sender is allowed to redact, the redaction behaviour continues until the membership event itself
is redacted (thus removing the field) or another membership event removes the field. For example, if
the user is unbanned, the moderator MAY NOT choose to carry the `redact_events` flag to that kick
(unban) event. Or, when the user rejoins after a kick, the flag is implicitly dropped.

Events which are delivered after the ban are likely [soft failed](https://spec.matrix.org/v1.14/server-server-api/#soft-failure)
and are still redacted if the current membership event in the room has a valid `redact_events`
field.

Other membership states with the flag no-op, such as joins, knocks, and invites.

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

## Fallback behaviour

Servers which don't support this feature may be served redacted events over federation when attempting
to fill gaps or backfill. This is considered expected behaviour.

Clients which don't support this feature may see events remain unredacted until they clear their local
cache. Upon clearing or invalidating their cache, they will either receive redacted events if their
server supports the feature or unredacted events otherwise.

To (primarily) help protect users on unsupported *clients*, implementations SHOULD continue to try
sending individual redaction events in addition to the redact-on-ban flag. They MAY cease to do so
once they are comfortable with the level of adoption for this proposal. Servers in particular SHOULD
assist clients and send individual redaction events on their behalf, meaning clients SHOULD wait a
little bit before trying to issue redactions themselves. For example, a client may ban a user, wait
a minute, then start sending redactions if it hasn't seen an `m.room.redaction` event targeting some
of the banned user's events. Servers MAY deduplicate redactions to lower federation load, as they
always could.

**Note**: It is possible due to implementation and real-world constraints that not all individual
redactions will "make it" over federation to another server. This is why mass redaction approaches
are preferred, as they are significantly more reliable.

## Potential issues

It's a little annoying that the flag is redacted when the membership event is redacted, however it's
extremely rare for a moderator/admin to redact a kick or ban event. This can be fixed in a future
room version, like what is proposed by [MSC4298](https://github.com/matrix-org/matrix-spec-proposals/pull/4298).

Though extremely rare, if an existing server in the room didn't apply the redactions *and* a sender's
ban was redacted, a new server to the room may backfill through that existing server and see unredacted
events without knowing it's supposed to redact them due to the ban having lost the `redact_events`
field. This is fixed for future room versions by implementing something like [MSC4298](https://github.com/matrix-org/matrix-spec-proposals/pull/4298).

Clients may miss the membership event if they are using lazy loading, though servers should already
be tracking which membership events the client has received and needs to render events in the timeline.
This should mean that those clients will still receive the event.

Servers which miss the event will eventually receive or retrieve it, just like they would with any
other event.

Moderation bots/clients which attempt to reduce the amount of duplicate work they do may need to
inspect `redacted_because` instead of checking for its presence to determine which kind of redaction
was applied to a given event. This is especially true if the moderation bot/client is providing the
fallback support described above.

## Alternatives

Mass redactions are the cited major alternative, where a single event can target approximately 1500
other events in the room. New rooms can benefit from that functionality, especially for cases not
covered by this proposal, while existing rooms can be given an option to protect their users with
relative ease.

## Future considerations

It may be desirable to place this behaviour on self-leaves too, allowing for faster removal of one's
own messages/events. This proposal doesn't suggest adding this functionality here to maintain narrow
scope on T&S functionality. A future proposal may introduce this, or rely on regular mass redactions
instead.

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
