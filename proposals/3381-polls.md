# MSC3381: Chat Polls

Polls are additive functionality in a room, allowing someone to pose a question and others to answer
until the poll is closed. In chat, these are typically used for quick questionares such as what to
have for lunch or when the next office party should be, not elections or anything needing truly
secret ballot.

[MSC2192](https://github.com/matrix-org/matrix-doc/pull/2192) does introduce a different way of doing
polls (originally related to inline widgets, but diverged into `m.room.message`-based design). That
MSC's approach is discussed at length in the alternatives section for why it is inferior.

## Proposal

Polls are to be handled completely client-side and encrypted when possible in a given room. They are
simply started by sending an appropriate event, responded to with more events, and closed (eventually)
by the sender. Servers have no added requirements in order to support this MSC: they simply need to
be able to send arbitrary event types, which they already should be capable of.

The events in this MSC make heavy use of [MSC1767: Extensible Events](https://github.com/matrix-org/matrix-doc/pull/1767).

A poll can be started by sending an `m.poll.start` room event, similar to the following:

```json5
{
  "type": "m.poll.start",
  "sender": "@alice:example.org",
  "content": {
    "m.poll.start": {
      "question": {
        "m.text": "What should we order for the party?"
      },
      "kind": "m.poll.disclosed",
      "max_selections": 1,
      "answers": [
        { "id": "pizza", "m.text": "Pizza 🍕" },
        { "id": "poutine", "m.text": "Poutine 🍟" },
        { "id": "italian", "m.text": "Italian 🍝" },
        { "id": "wings", "m.text": "Wings 🔥" }
      ]
    },
    "m.message": [
      {
        "mimetype": "text/plain",
        "body": "What should we order for the party?\n1. Pizza 🍕\n2. Poutine 🍟\n3. Italian 🍝\n4. Wings 🔥"
      },
      {
        "mimetype": "text/html",
        "body": "<b>What should we order for the party?</b><ol><li>1. Pizza 🍕</li><li>2. Poutine 🍟</li><li>3. Italian 🍝</li><li>4. Wings 🔥</li></ol>"
      }
    ]
  },
  // other fields that aren't relevant here
}
```

As mentioned above, this is already making use of Extensible Events: The fallback for clients which don't
know how to render polls is to just post the message to the chat. Some of the properties also make use of
extensible events within them, such as the `question` and the elements of `answers`: these are effectively
`m.message` events (under the Extensible Events structure), which means they're required to have a plain
text component to them. HTML is allowed, though clients are generally encouraged to rely on the plain text
representation for an unbiased rendering. Meme value of HTML might be desirable to some clients, however.

The `kind` refers to whether the poll's votes are disclosed while the poll is still open. `m.poll.undisclosed`
means the results are revealed once the poll is closed. `m.poll.disclosed` is the opposite: the votes are
visible up until and including when the poll is closed. Custom values are permitted using the standardized
naming convention are supported. Unknown values are to be treated as `m.poll.undisclosed` for maximum
compatibility with theoretical values. More specific detail as to the difference between two polls come up
later in this MSC.

`answers` must be an array with at least 1 option and no more than 20. Lengths outside this range are invalid
and must not be rendered by clients. Most polls are expected to have 2-8 options. The answer `id` is an
arbitrary string used within the poll events. Clients should not attempt to parse or understand the `id`.

`max_selections` is optional and denotes the maximum number of responses a user is able to select. Users
can select fewer options, but not more. This defaults to `1`. Cannot be less than 1.

The `m.message` fallback should be representative of the poll, but is not required and has no mandatory
format. Clients are encouraged to be inspired by the example above when sending poll events.

To respond to a poll, the following event is sent:

```json5
{
  "type": "m.poll.response",
  "sender": "@bob:example.org",
  "content": {
    "m.relates_to": {
      "rel_type": "m.annotation", // from MSC2677: https://github.com/matrix-org/matrix-doc/pull/2677
      "key": "poutine",
      "event_id": "$poll"
    },
    "m.poll.response": {
      // empty object: useful information is in the relationship `key`.
    }
  },
  // other fields that aren't relevant here
}
```

Like `m.poll.start`, this `m.poll.response` event supports Extensible Events. However, it is strongly discouraged
for clients to include renderable types like `m.text` and `m.message` which could impact the usability of
the room (particularly for large rooms with lots of responses).

Note that the response event annotates the poll start event, forming a relationship which can be aggregated
by the server under [MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675). The event also supports
only one answer: for polls which permit multiple responses, and where multiple responses are given, the
client would send multiple response events. If the user deselected (unvoted) an option, the corresponding
response event would be redacted to match [MSC2677](https://github.com/matrix-org/matrix-doc/pull/2677)'s
handling of "un-reacting" to an event.

This MSC borrows a lot of the structure provided by reactions in [MSC2677](https://github.com/matrix-org/matrix-doc/pull/2677)
but intentionally does not define how notifications (if desired) or other UX features work: this MSC
purely intends to use the server-side aggregation capability where possible.

If a user sends multiple responses for the same answer, the user is considered to have voted for the answer
only once. They will need to redact/unvote *all* of those answers to have been fully considered as not voting
for that answer.

Votes are accepted until the poll is closed according to timestamp: servers/clients which receive votes
which are timestamped before the close event's timestamp (or, when no close event has been sent) are valid.
Late votes should be ignored. Early votes (from before the start event) are considered to be valid for the
sake of handling clock drift as gracefully as possible.

To enforce `max_selections`, distinct responses are ordered by timestamp and truncated at `max_selections`.
For example, if a user votes as `[A, B, A, A, D]` and `max_selections` is 2, then the valid votes would be
`[B, A]` (because `A` was voted for multiple times, the most recent being after `B` was voted for). `D`
would simply be ignored as it is out of range. If the user redacted *all* of their `A` votes, then it'd
be `[B, D]`.

Responses with a non-sensical `key` (eg: not a valid answer) are simply ignored. This is primarily important
when using server-side endpoints for fetching all relations: some will be emoji or short text strings to
denote reactions. Those events can be implicitly ignored with sufficiently complex/unlikely answer IDs as
the client would automatically filter out `👍` reactions. This is particularly important in a world where
the event type for all associated events is `m.room.encrypted` rather than `m.reaction` or `m.poll.response`
from a server's perspective.

Only the poll creator or anyone with a suitable power level for redactions can close the poll. The rationale
for using the redaction power level is to help aid moderation efforts: while moderators can just redact the
original poll and invalidate it entirely, they might prefer to just close it and leave it on the historical
record.

Closing a poll is done as follows:

```json5
{
  "type": "m.poll.end",
  "sender": "@bob:example.org",
  "content": {
    "m.relates_to": {
      "rel_type": "m.reference", // from MSC3267: https://github.com/matrix-org/matrix-doc/pull/3267
      "event_id": "$poll"
    },
    "m.poll.end": {},
    "m.text": "The poll has ended. Top answer: Poutine 🍟"
  },
  // other fields that aren't relevant here
}
```

Once again, Extensible Events make an appearance here. There's nothing in particular metadata wise that
needs to appear in the `m.poll.end` property of `content`, though it is included for future capability. The
backup `m.text` representation is for fallback purposes and is completely optional with no strict format
requirements: the example above is just that, an example of what a client *could* do. Clients should be
careful to include a "top answer" in the end event as server lag might allow a few more responses to get
through while the closure is sent. Votes sent on or before the end event's timestamp are valid votes - all
others must be disregarded by clients.

**Rationale**: Although clock drift is possible, as is clock manipulation, it is not anticipated that
polls will be closed while they are still receiving high traffic. There are some cases where clients might
apply local timers to auto-close polls, though these are typically used in extremely high traffic cases
such as Twitch-style audience polls - rejecting even 100 responses is unlikely to significantly affect
the results. Further, if a server were to manipulate its clock so that poll responses are sent after the
poll was closed, but timestamped for when it was open, the server is violating a social contract and likely
will be facing a ban from the room. This MSC does not propose a mitigation strategy beyond telling people
not to ruin the fun. Also, don't use polls for things that are important.

Clients should disable voting interactions with polls once they are closed. Events which claim to close
the poll from senders other than the creator are to be treated as invalid and thus ignored.

### Disclosed versus undisclosed polls

Disclosed polls are most similar to what is seen on Twitch and often Twitter: members of the room are able
to see the results and vote accordingly. Clients are welcome to hide the poll results until after the user
has voted to avoid biasing the user.

Undisclosed polls do track who voted for what, though don't reveal the results until the poll has been
closed, even after a user has voted themselves. This is enforced visually and not by the protocol given
the votes are sent to the room for local tallying - this is considered more of a social trust issue than
a technical one. This MSC expects that rooms (and clients) won't spoil the results of an undisclosed poll
before it is closed.

In either case, once the poll ends the results are shown regardless of kind. Clients might wish to avoid
disclosing who voted for what in an undisclosed poll, though this MSC leaves that at just a suggestion.

### Server behaviour

Much of the handling for this proposal is covered by other MSCs already:

* [MSC2677](https://github.com/matrix-org/matrix-doc/pull/2677) defines how to aggregate the annotations
  (poll responses), though notes that encrypted events can potentially be an issue. The aggregation is
  also unaware of a stop time to honour the poll closure. MSC2677 also defines that users may only annotate
  with a given key once, preventing most issues of users voting for the same answer multiple times.
* [MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675) defines the server-side aggregation approach
  which can be useful to clients to determine which votes there are on an event.
* [MSC0001](https://github.com/matrix-org/matrix-doc/pull/0001) defines how clients can get all relations
  for an event between point A and B (namely the poll start and close).

No further behaviour is defined by this MSC: servers do not have to understand the rules of a poll in order
to support the client's implementation. They do however need to implement a lot of server-side handling for
the above MSCs.

### Client behaviour

Clients should rely on [MSC0001](https://github.com/matrix-org/matrix-doc/pull/0001) and
[MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675) for handling limited ("gappy") syncs.
Otherwise, it is anticipated that clients re-process polls entirely on their own to ensure accurate counts
with encrypted events (the response events might be encrypted, so the server-side aggregations endpoint
will be unaware of whether an event is a reaction, poll response, or some other random type). As mentioned
in the proposal text, clients should filter out non-sensical `key`s to automatically filter out reactions
and other non-poll-response types.

## Potential issues

As mentioned, poll responses are sent to the room regardless of the kind of poll. For open polls this
isn't a huge deal, but it can be considered an issue with undisclosed polls. This MSC strongly considers
the problem a social one: users who are looking to "cheat" at the results are unlikely to engage with the
poll in a productive way in the first place. And, of course, polls should never be used for something
important like electing a new leader for a country.

Poll responses are also de-anonymized by nature of having the sender attached to a response. Clients
are strongly encouraged to demonstrate anonymization by not showing who voted for what, but should consider
warning the user that their vote is not anonymous. For example, saying "22 total responses, including
from TravisR, Matthew, and Alice" before the user casts their own vote.

Limiting polls to client-side enforcement could be problematic if the MSC was interested in reliable
or provable votes, however as a chat feature this should reasonably be able to achieve user expectations.
Bolt-on support for signing, verification, validity, etc can be accomplished as well in the future.

The fallback support relies on clients already knowing about extensible events, which might not be
the case. Bridges (as of writing) do not have support for extensible events, for example, which can
mean that polls are lost in transit. This is perceived to be a similar amount of data loss when a Matrix
user reacts to an IRC user's message: the IRC user has no idea what happened on Matrix. Bridges, and
other clients, can trivially add message parsing support as described by extensible events to work
around this. The recommendations of this MSC specifically avoid the vote spam from being bridged, but
the start of poll and end of poll (results) would be bridged. There's an argument to be made for
surrounding conversation context being enough to communicate the results without extensible events,
though this is slightly less reliable.

Though more important for Extensible Events, clients might get confused about what they should do
with the `m.message` parts of the events. For absolute clarity: if a client has support for polls,
it can outright ignore any irrelevant data from the events such as the message fallback or other
representations that senders stick onto the event (like thumbnails, captions, attachments, etc).

## Alternatives

The primary competition to this MSC is the author's own [MSC2192](https://github.com/matrix-org/matrix-doc/pull/2192)
which describes not only polls but also inline widgets. The poll implementation in MSC2192 is primarily
based around `m.room.message` events, using `msgtype` to differentiate between the different states. As
[a thread](https://github.com/matrix-org/matrix-doc/pull/2192/files#r514497274) notes on the MSC, this
is an awful experience on clients which do not support polls properly, leaving an irritating amount of
contextless messages in the timeline. Though not directly mentioned on that thread, polls also cannot be
closed under that MSC which leads to people picking options hours or even days after the poll has "ended".
This MSC instead proposed to only supply fallback on the start and end of a poll, leading to enough context
for unsupporting clients without flooding the room with messages.

Originally, MSC2192 was intended to propose polls as a sort of widget with access to timeline events
and other important information, however the widget infrastructure is just not ready for this sort of
thing to exist. First, we'd need to be able to send events to the widget which reference itself (for
counting votes), and allow the widget to self-close if needed. This is surprisingly difficult when widgets
can be "popped out" or have a link clicked in lieu of rendering (for desktop clients): there's no
communication channel back to the client to get the information back and forth. Some of this can be solved
with scoped access tokens for widgets, though at the time of writing those are a long ways out. In the
end, it's simply more effective to use Extensible Events and Matrix directly rather than building out
the widgets infrastructure to cope - MSC2192 is a demonstration of this, considering it ended up taking
out all the widget aspects and replacing them with fields in the content.

Finally, MSC2192 is simply inferior due to not being able to restrict who can post a poll. Responses
and closures can also be limited arbitrarily by room admins, so clients might want to check to make
sure that the sender has a good chance of being able to close the poll they're about to create just
to avoid future issues.

## Security considerations

As mentioned a multitude of times throughout this proposal, this MSC's approach is prone to disclosure
of votes and has a couple abuse vectors which make it not suitable for important or truly secret votes.
Do not use this functionality to vote for presidents.

Clients should apply a large amount of validation to each field when interacting with polls. Event
bodies are already declared as completely untrusted, though not all clients apply a layer of validation.
In general, this MSC aims to try and show something of use to users so they can at least figure out
what the sender intended, though clients are also welcome to just hide invalid events/responses (with
the exception of spoiled votes: those are treated as "unvoting" or chosing nothing). Clients are
encouraged to try and fall back to something sensible, even if just an error message saying the poll
is invalid.

Users should be wary of polls changing their question after they have voted. Considering polls can be
edited, responses might no longer be relevant. For example, if a poll was opened for "do you like
cupcakes?" and you select "yes", the question may very well become "should we outlaw cupcakes?" where
your "yes" no longer applies. This MSC considers this problem more of a social issue than a technical
one, and reminds the reader that polls should not be used for anything important/serious at the moment.

## Future considerations

Some aspects of polls are explicitly not covered by this MSC, and are intended for another future MSC
to solve:

* Allowing voters/room members to add their own freeform options. The edits system doesn't prevent other
  members from editing messages, though clients tend to reject edits which are not made by the original
  author. Altering this rule to allow it on some polls could be useful in a future MSC.

* Verifiable or cryptographically secret polls. There is interest in a truly enforceable undisclosed poll
  where even if the client wanted to it could not reveal the results before the poll is closed. Approaches
  like [MSC3184](https://github.com/matrix-org/matrix-doc/pull/3184) or Public Key Infrastructure (PKI)
  might be worthwhile to investigate in a future MSC.

## Other notes

If a client/user wishes to make a poll statically visible, they should check out
[pinned messages](https://matrix.org/docs/spec/client_server/r0.6.1#m-room-pinned-events).

## Unstable prefix

While this MSC is not eligible for stable usage, the `org.matrix.msc3381.` prefix can be used in place
of `m.`. Note that extensible events has a different unstable prefix for those fields.

**Note**: Due to changes during the unstable period, poll responses are additionally annotated with a
`v2` to denote a change on November 21, 2021. For details, see below.

The 3 examples above can be rewritten as:

```json5
{
  "type": "org.matrix.msc3381.poll.start",
  "sender": "@alice:example.org",
  "content": {
    "org.matrix.msc3381.poll.start": {
      "question": {
        "org.matrix.msc1767.text": "What should we order for the party?"
      },
      "kind": "org.matrix.msc3381.poll.disclosed",
      "answers": [
        { "id": "pizza", "org.matrix.msc1767.text": "Pizza 🍕" },
        { "id": "poutine", "org.matrix.msc1767.text": "Poutine 🍟" },
        { "id": "italian", "org.matrix.msc1767.text": "Italian 🍝" },
        { "id": "wings", "org.matrix.msc1767.text": "Wings 🔥" }
      ]
    },
    "org.matrix.msc1767.message": [
      {
        "mimetype": "text/plain",
        "body": "What should we order for the party?\n1. Pizza 🍕\n2. Poutine 🍟\n3. Italian 🍝\n4. Wings 🔥"
      },
      {
        "mimetype": "text/html",
        "body": "<b>What should we order for the party?</b><ol><li>1. Pizza 🍕</li><li>2. Poutine 🍟</li><li>3. Italian 🍝</li><li>4. Wings 🔥</li></ol>"
      }
    ]
  },
  // other fields that aren't relevant here
}
```

```json5
{
  "type": "org.matrix.msc3381.v2.poll.response", // note the v2 in the event type!
  "sender": "@bob:example.org",
  "content": {
    "m.relates_to": {
      "rel_type": "m.annotation",
      "key": "italian",
      "event_id": "$poll"
    },
    "org.matrix.msc3381.poll.response": {
      // empty body
    }
  },
  // other fields that aren't relevant here
}
```

```json5
{
  "type": "org.matrix.msc3381.poll.end",
  "sender": "@bob:example.org",
  "content": {
    "m.relates_to": {
      "rel_type": "m.reference",
      "event_id": "$poll"
    },
    "org.matrix.msc3381.poll.end": {},
    "org.matrix.msc1767.text": "The poll has ended. Top answer: Poutine 🍟"
  },
  // other fields that aren't relevant here
}
```

Note that the extensible event fallbacks did not fall back to `m.room.message` in this MSC: this
is deliberate to ensure polls are treated as first-class citizens. Client authors not willing/able
to support polls are encouraged to instead support Extensible Events for better fallbacks.

### Historical implementation: November 22, 2021

As of November 21, 2021 this proposal moved away from a global `m.reference` relationship to using
`m.annotation` on poll responses. The following documents the previous behaviour for implementations
which might run across the now-legacy event types/format.

Unstable representation (never made it to stable):
```json5
{
  "type": "org.matrix.msc3381.poll.response", // note the *lack* v2 in the event type!
  "sender": "@bob:example.org",
  "content": {
    "m.relates_to": {
      "rel_type": "m.reference", // this changed!
      "event_id": "$poll"
    },
    "org.matrix.msc3381.poll.response": {
      "answers": ["italian"] // answers are recorded here!
    }
  },
  // other fields that aren't relevant here
}
```

The processing rules for this kind of response event were:

1. Only the latest response event is considered. All others are ignored.
2. `answers` is truncated to `max_selections` - the remainder are ignored.
3. Users can un-vote by casting a ballot of `[]` or redacting all of their response events.

All other rules (particularly related to late responses) remain the same.

Clients can theoretically rely on the server-side relations endpoint for gappy syncs, though this
has not been fully verified. It is intended that implementations switch over to the proposal's new
text instead.
