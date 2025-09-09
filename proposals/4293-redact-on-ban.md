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
   This alternative is explored in [MSC4343](https://github.com/matrix-org/matrix-spec-proposals/pull/4343).

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
events where the target user is kicked or banned: `redact_events`. Discussed later, this new flag has
no effect when applied to self-leaves or other membership states. This flag is a boolean and has two
effects when `true`:

1. Clients apply the redaction algorithm to events sent by that user which are cached locally, up to
   the point of the user's previous membership event. No [`m.room.redaction`](https://spec.matrix.org/v1.14/client-server-api/#mroomredaction)
   events are sent by the client, but the user's events are redacted as though there was such an event.

2. Servers perform the same function as clients, also not actually sending any `m.room.redaction`
   events. Instead, the user's events are redacted locally by the server. When serving events redacted
   in this way, the [`redacted_because`](https://spec.matrix.org/v1.14/client-server-api/#redactions)
   field is populated using the membership event, like so:

   ```jsonc
   {
    // irrelevant fields not shown

    "type": "m.room.message",
    "sender": "@banned:example.org",
    "content": {}, // because the event is redacted, `content` is empty
    "unsigned": {
      "redacted_because": {
        // irrelevant fields also not shown here

        "type": "m.room.member",
        "sender": "@moderator:example.org",
        "state_key": "@banned:example.org",
        "content": {
          "membership": "ban",
          "reason": "spam",
          "redact_events": true
        }
      }
    }
   }
   ```

   Note that because `m.room.redaction` supports a `reason` field in the same place as `m.room.member`,
   clients which look up that reason by going `event["unsigned"]["content"]["reason"]` will still get
   a renderable, human-readable, string for their UI regardless of how the event was actually redacted.

When `redact_events` is `false`, it acts as though it was not specified: no redactions are applied,
exactly like how bans work prior to this proposal.

Prior to applying the effects of redaction above, clients and servers MUST ensure that the sender of
the kick or ban has power level to redact the target user's events. This means having a power level
higher than or equal to `redact` *and* `events["m.room.redaction"]` (if set). We maintain the `events`
check despite not actually sending events of that type to keep the same expectations within rooms. If
the sender doesn't have permission to redact an event normally, the `redact_events` flag is ignored
(and therefore no redaction effect is applied).

Events which are delivered after the kick or ban are likely [soft failed](https://spec.matrix.org/v1.14/server-server-api/#soft-failure)
and are still redacted by servers if the user's *current* membership event has `redact_events: true`.

The `redact_events` flag has no effect when present on any other membership state, such as joins,
knocks, invites, and voluntary leaves (non-kicks).

**Note**: Due to this proposal being enabled in existing room versions, the `redact_events` flag may
become redacted when a user's `m.room.member` event is redacted too. When this happens, the redactions
already applied up to that point are *not* undone, though clients/servers which purge the events and
re-fetch them might receive unredacted copies if they originate from a server which didn't apply this
proposal's effects. Future proposals like [MSC4298](https://github.com/matrix-org/matrix-spec-proposals/pull/4298)
protect the flag from redaction, avoiding the awkward state where events might be redacted for no
discernible reason after the membership event itself is redacted.

`redact_events` is also added to the [`/kick`](https://spec.matrix.org/v1.14/client-server-api/#post_matrixclientv3roomsroomidkick)
and [`/ban`](https://spec.matrix.org/v1.14/client-server-api/#post_matrixclientv3roomsroomidban)
endpoints and is proxied to the resulting event just like `reason` is. It is optional on these endpoints.

An example ban event is:

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

An example scenario would be:

1. Alice joins the room.
2. Alice sends events A, B, and C.
3. Alice leaves the room.
4. For whatever reason, Alice rejoins the room.
5. Alice sends events D, E, and F.
6. Bob bans Alice with `redact_events: true`.
7. Clients and servers apply redactions to events D, E, and F, but *not* A, B, or C. No actual
   `m.room.redaction` events are sent in this example.
8. Alice's event F arrive's late to Bob's server.
9. Bob's server soft fails F because it fails current auth state (Alice is banned), and redacts it
   because `redact_events: true` is set on Alice's ban. There are still no actual `m.room.redaction`
   events sent here.

Events A, B, and C are not redacted because Alice's leave event at step 3 has an implied `redact_events: false`.

Moderation bots and similar MAY still wish to issue (mass) redactions upon kick/ban to protect users
on servers or clients which don't have this feature.


## Fallback behaviour

Servers which don't support this feature may be served redacted events over federation when attempting
to fill gaps or backfill. This is considered expected behaviour.

Clients which don't support this feature may see events remain unredacted until they clear their local
cache. Upon clearing or invalidating their cache, they will either receive redacted events if their
server supports the feature, or unredacted events otherwise. This is also considered expected behaviour.

Though this proposal makes it clear that `m.room.redaction` events aren't actually sent, senders of
kicks/bans MAY still send actual redactions in addition to `redact_events: true` to ensure that older
clients and servers have the best possible chance of redacting the event. These redactions SHOULD be
considered "best effort" by the sender as they may encounter delivery issues, especially when using
1:1 redactions instead of mass redactions. "Best effort" might mean using endpoints like
[MSC4194](https://github.com/matrix-org/matrix-spec-proposals/pull/4194)'s batch redaction, or using
the less reliable `/messages` endpoint to locate target event IDs to redact. Senders SHOULD note that
this fallback behaviour will only target events they can see (or be made to see via MSC4194) and might
not be the same events that a receiving client or server sees.

Senders are encouraged to evaluate when they can cease sending fallback redactions like those described
above to minimize the event traffic involved in a ban. For moderation bots this may mean waiting for
sufficiently high *client* implementations existing in their communities.

## Potential issues

1. It's a little annoying that the flag is redacted when the membership event is redacted, however it's
   extremely rare for a moderator/admin to redact a kick or ban event. This can be fixed in a future
   room version, like what is proposed by [MSC4298](https://github.com/matrix-org/matrix-spec-proposals/pull/4298).

2. Though extremely rare, if an existing server in the room didn't apply the redactions *and* a sender's
   ban was redacted, a new server to the room may backfill through that existing server and see unredacted
   events without knowing it's supposed to redact them due to the ban having lost the `redact_events`
   field. This is fixed for future room versions by implementing something like [MSC4298](https://github.com/matrix-org/matrix-spec-proposals/pull/4298).

3. Clients may miss the membership event if they are using lazy loading, though servers should already
   be tracking which membership events the client has received and needs to render events in the timeline.
   This should mean that those clients will still receive the event.

   Servers which miss the event will eventually receive or retrieve it, just like they would with any
   other event.

4. Moderation bots/clients which attempt to reduce the amount of duplicate work they do may need to
   inspect `redacted_because`'s `type` instead of checking for its presence to determine which kind of redaction
   was applied to a given event. This is especially true if the moderation bot/client is providing the
   fallback support described above.

5. If a user is banned using `redact_events: true`, unbanned, rejoins, sends more events, and is banned
   again using `redact_events: true`, the user's events between bans will be subsequently redacted. The
   events redacted by the first ban may also be re-redacted by servers/clients depending on implementation.
   This is considered expected behaviour, and implementations can internally track which events they've
   already auto-redacted to avoid duplicate work.

6. With respect to the fallback behaviour, it's not great that implementations, and in particular
   moderation bots, need to maintain their "find all events sent by this user and redact them" behaviour.
   [MSC4194](https://github.com/matrix-org/matrix-spec-proposals/pull/4194) should help with this, though
   has the limitations discussed throughout this MSC when applied to this proposal's use case.

7. If a user is banned without the flag then banned again with the flag, their events sent before the
   first ban won't be redacted. This is already the case with moderation bots which support autoredaction
   when certain ban reasons are used: if there's a typo/problem with the reason, the bot's operator
   may need to issue more commands/requests to reach the intended result.

   Clients and moderation bots are encouraged to implement UX which reduces the chances of this sort
   of thing happening. Moderation teams are also encouraged to develop operating procedures which
   limit the opportunity for accidentally encountering this case.

8. A spammer may attempt to work around this MSC's effects by joining and leaving the room during
   their spam. This has relatively high cost (the impact of spam is lesser when they aren't joined
   to the room, and re-joining will hit a more restrictive rate limit on most servers).

   Moderation bots and similar community safety tools are encouraged to add restrictions to the number
   of join+leave cycles a user may perform in a short window. This will further reduce the effectiveness
   of such an attack. Issue 7 above also applies here.

## Alternatives

Alternatives are discussed inline on this proposal and in the introduction.

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
