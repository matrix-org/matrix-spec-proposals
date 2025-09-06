# MSC4293: Redact on kick/ban

[MSC2244 (accepted)](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/2244-mass-redactions.md)-style
mass redactions are incredibly helpful for cleaning up large volumes of spam, especially because they
reduce the total number of events a server needs to process in order to clean up a room. However, they
have a few issues:

1. To populate the target events, the sender needs to know which event IDs to target. Events may be
   [soft failed](https://spec.matrix.org/v1.15/server-server-api/#soft-failure) by the moderator's
   local homeserver, which may prevent the sender's client from seeing them. Further, there may be
   timeline gaps which limit the sender's visibility on the events to target.

   This may be fixed by adding a "sugar API" like `/room/:roomId/redact/:userId` which causes the
   server to calculate event ID targets and send out one or more mass redactions, though this would
   only be effective if the server had all of the user's events at the time of the call. If an event
   came in late for any reason, the sent redactions might not target it, allowing the likely spam
   through to the room.

   Proposals such as [MSC4194](https://github.com/matrix-org/matrix-doc/pull/4194) explore this
   solution.

2. Dedicated events must still be sent in order to perform the redaction, many of which might not be
   small if there's lots of events being targeted. This can impact bandwidth and data storage, though
   not as badly as trying to redact large volumes of spam without mass redactions.

3. MSC2244 mass redactions are breaking for clients which perform redaction locally due to changing
   the type of `redacts` on `m.room.redaction` events from a string (single event ID) to an array.
   This is in part mitigated by MSC2244 through a new room version, though clients are currently
   unable to opt out of incompatible room versions.

   It's also possible to mitigate this concern by using a new event type for mass redactions instead.
   This alternative is explored in **TODO: Future MSC here**.

4. Due to changes in event authorization, MSC2244 requires a new room version in order to function.
   This limits the feature to new rooms or those which upgrade to a new enough version. Theoretically,
   it's possible to allow mass redactions in existing room versions anyway, though the redactions may
   get rejected due to the very authorization rules MSC2244 changes. This may cause senders to target
   a small number of events per mass redaction to avoid the possibility of spam being left visible
   due to a single event target not being present on the receiving homeserver.

To work around these issues, this proposal suggests adding a new flag to membership events to indicate
to clients and servers that all of that user's events should be redacted in addition to being kicked
or banned. There are still drawbacks for existing room versions with this approach, namely that the
new flag isn't protected from redaction itself and may cause problems, but it does allow moderators
to take an action they were going to anyway: ban & redact everything the user ever sent, without
needing to wait for a new room version to roll out.

By applying the flag to a user ID instead of an event ID (or set of event IDs), the consumer's local
view is considered instead of the sender's: a redaction for "all of `@alice:example.org`'s events"
when applied by a client removes all events visible to that client. Similarly, that redaction applied
by a server to their local database will redact whatever events the server has already seen, or will
see in the future.

Though this MSC isn't breaking for clients in the same way that MSC2244 is, clients (and to a degree,
servers) may not support the MSC right away. This means that senders may still have to send "fallback
redactions" to ensure the room is cleaned up, though those senders can begin to treat those redactions
as best effort (currently, moderation bots in particular work incredibly hard to ensure they get *every*
event redacted, but can run into delivery, reliability, and completeness issues with 1:1 redactions).

It's also important to note that this proposal intends to compliment mass redactions and coexist in
whatever room version mass redactions land in. This proposal has narrow scope and is fairly blunt as
a measure, which may not be desirable in all situations. For example, only a user's last dozen or so
messages may be worth redacting rather than the hundreds they sent prior to the ones which got them
banned. This proposal does not support such a use case, but mass redactions do.

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
events, the redaction doesn't apply. This means having a power level higher than or equal to `redact`
*and* `events["m.room.redaction"]` (if set). We maintain the `events` check despite not actually sending
events of that type to keep the same expectations within rooms. If the sender doesn't have permission
to redact an event normally, no redaction is applied.

If the sender is allowed to redact, the redaction behaviour continues until the membership event itself
is redacted (thus removing the field), another membership event removes the field, or the flag is set
to `false`. Events already redacted up to that point remain redacted after the flag changes to a falsey
value. For example, if the user is unbanned, the moderator MAY NOT choose to carry the `redact_events`
flag to that kick (unban) event. Or, when the user rejoins after a kick, the flag is implicitly dropped.

In essence, the `redact_events` flag applies to all events which topologically come before the falsey
value.

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

If a user is banned using `redact_events: true`, unbanned, rejoins, sends more events, and is banned
again using `redact_events: true`, the user's events between bans will be subsequently redacted. The
events redacted by the first ban may also be re-redacted by servers/clients depending on implementation.
This is considered expected behaviour, and implementations can internally track which events they've
already auto-redacted to avoid duplicate work.

With respect to the fallback behaviour, a client might not know if a server is applying fallback
redactions and may not wish to wait an arbitrary amount of time to see if it does. One solution would
be to have the server expose a [capability](https://spec.matrix.org/v1.15/client-server-api/#capabilities-negotiation),
however such a flag would be longer lived than the fallback behaviour itself (hopefully). Instead,
clients which don't implement watchdog functionality SHOULD send redactions anyway, even if it
duplicates the server's fallback efforts. Further, as already mentioned above, server MAY deduplicate
redactions to lower their federation load, though this is closer to a SHOULD considering clients are
already sending their own redaction events (like in the case of Mjolnir).

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
