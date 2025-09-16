# MSC3381: Chat Polls

Polls are additive functionality in a room, allowing someone to pose a question and others to answer
until the poll is closed. In chat, these are typically used for quick questionnaires such as what to
have for lunch or when the next office party should be, not elections or anything needing truly
secret ballot.

[MSC2192](https://github.com/matrix-org/matrix-doc/pull/2192) does introduce a different way of doing
polls (originally related to inline widgets, but diverged into `m.room.message`-based design). That
MSC's approach is discussed at length in the alternatives section for why it is inferior.

## Proposal

Polls are intended to be handled completely client-side and encrypted when possible in a given room.
They are started by sending an event, responded to using events, and closed using more events - all
without involving the server (beyond being the natural vessel for sending the events). Other MSCs
related to polls might require changes from servers, however this MSC is intentionally scoped so that
it does not need server-side involvement.

The events in this MSC make use of the following functionality:

* [MSC1767](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/1767-extensible-events.md) (extensible events & `m.text`)
* [Event relationships](https://spec.matrix.org/v1.6/client-server-api/#forming-relationships-between-events)
* [Reference relations](https://spec.matrix.org/v1.6/client-server-api/#reference-relations)

To start a poll, a user sends an `m.poll.start` event into the room. An example being:

```json5
{
  "type": "m.poll.start",
  "sender": "@alice:example.org",
  "content": {
    "m.text": [
      // Simple text is used as a fallback for text-only clients which don't understand polls. Specific formatting is
      // not specified, however something like the following is likely best.
      {
        "mimetype": "text/plain",
        "body": "What should we order for the party?\n1. Pizza 🍕\n2. Poutine 🍟\n3. Italian 🍝\n4. Wings 🔥"
      }
    ],
    "m.poll": {
      "kind": "m.disclosed",
      "max_selections": 1,
      "question": {
        "m.text": [{"body": "What should we order for the party?"}]
      },
      "answers": [
        {"m.id": "pizza", "m.text": [{"body": "Pizza 🍕"}]},
        {"m.id": "poutine", "m.text": [{"body": "Poutine 🍟"}]},
        {"m.id": "italian", "m.text": [{"body": "Italian 🍝"}]},
        {"m.id": "wings", "m.text": [{"body": "Wings 🔥"}]},
      ]
    }
  }
}
```

With consideration for extensible events, a new `m.poll` content block is defined:

* `kind` - An optional namespaced string to represent a poll's general approach. Currently specified
  values being `m.disclosed` and `m.undisclosed`. Clients which don't understand the `kind` should
  assume `m.undisclosed` for maximum compatibility. The definitions for these values are specified
  later in this proposal.
* `max_selections` - An optional integer to represent how many answers the user is allowed to select
  from the poll. Must be greater than or equal to `1`, and defaults to `1`.
* `question` - A required object to represent the question being posed by the poll. Takes an `m.text`
  content block within. More blocks might be added in the future. Clients should treat this similar
  to how they would an `m.message` event.
* `answers` - Array of options users can select. Each entry is an object with an `m.text` content
  block, similar to `question`, and an opaque string field `m.id` for use in response events. More
  blocks might be added in the future. Clients should treat each entry similar to how they would an
  `m.message` event. The array is truncated to 20 maximum options.

  Note that arrays are inherently ordered. Clients *should* render options in the order presented in
  the array - a future MSC may add a flag to permit rendering in a different or random order.

Together with content blocks from other proposals, an `m.poll.start` is described as:

* **Required** - An `m.text` block to act as a fallback for clients which can't process polls.
* **Required** - An `m.poll` block to describe the poll itself. Clients use this to show the poll.

The above describes the minimum requirements for sending an `m.poll.start` event. Senders can add additional
blocks, however as per the extensible events system, receivers which understand poll events should not
honour them.

If a client does not support rendering polls inline, the client would instead typically represent
the event as a plain text message. This would allow users of such clients to participate in the poll,
even if they can not vote properly on it (ie: by using text messages or reactions).

To respond or vote in a poll, a user sends an `m.poll.response` event into the room. An example being:

```json5
{
  "type": "m.poll.response",
  "sender": "@bob:example.org",
  "content": {
    // Reference relationship formed per spec
    // https://spec.matrix.org/v1.6/client-server-api/#reference-relations
    "m.relates_to": {
      "rel_type": "m.reference",
      "event_id": "$poll_start_event_id"
    },
    "m.selections": ["poutine"]
  }
}
```

With consideration for extensible events, a new `m.selections` content block is defined:

* An array of string identifiers to denote a user's selection. Can be empty to denote "no selection".
  Identifiers are determined by the surrounding event type context, if available.

Together with content blocks from other proposals, an `m.poll.response` is described as:

* **Required** - An `m.relates_to` block to form a reference relationship to the poll start event.
* **Required** - An `m.selections` block to list the user's preferred selections in the poll. Clients
  must truncate this array to `max_selections` during processing. Each entry is the `m.id` of a poll
  answer option from the poll start event. If *any* of the supplied answers is unknown, the sender's
  vote is spoiled (as if they didn't make a selection). If an entry is repeated after truncation, only
  one of those entries counts as the sender's vote (each sender gets 1 vote).

The above describes the minimum requirements for sending an `m.poll.response` event. Senders can add
additional blocks, however as per the extensible events system, receivers which understand poll events
should not honour them.

There is deliberately no textual or renderable fallback on poll responses: the intention is that clients
which don't understand how to process these events will hide/ignore them. This is to mirror what a
client which *does* support polls would do: they wouldn't render each vote as a new message, but would
aggregate them into a single result at the end of the poll. By not having a text fallback, the vote
is only revealed when the poll ends, which does have a text fallback.

Only a user's most recent vote (by `origin_server_ts`) is accepted, even if that event is invalid.
Votes with timestamps after the poll has closed are ignored, as if they never happened. Note
that redaction currently removes the `m.relates_to` information from the event, causing the vote to be
detached from the poll. In this scenario, the user's vote is *reverted* to its previous state rather
than explicitly spoiled. To "unvote" or otherwise override the previous vote state, clients should send
a response with an empty `m.selections` array.

To close a poll, a user sends an `m.poll.end` event into the room. An example being:

```json5
{
  "type": "m.poll.end",
  "sender": "@alice:example.org",
  "content": {
    // Reference relationship formed per spec
    // https://spec.matrix.org/v1.6/client-server-api/#reference-relations
    "m.relates_to": {
      "rel_type": "m.reference",
      "event_id": "$poll_start_event_id"
    },
    "m.text": [{
      // Simple text is used as a fallback for text-only clients which don't understand polls. Specific formatting is
      // not specified, however something like the following is likely best.
      "body": "The poll has closed. Top answer: Poutine 🍟"
    }],
    "m.poll.results": { // optional
      "pizza": 5,
      "poutine": 8,
      "italian": 7,
      "wings": 6
    }
  }
}
```

With consideration for extensible events, a new `m.poll.results` content block is defined:

* A dictionary object keyed by answer ID (`m.id` from the poll start event) and value being the integer
  number of votes for that option as seen by the sender's client. Note that these values might not be
  accurate, however other clients can easily validate the counts by retrieving all relations from the
  server.
  * User IDs which voted for each option are deliberately not included for brevity: clients requiring
    more information about the poll are required to gather the relations themselves.

Together with content blocks from other proposals, an `m.poll.end` is described as:

* **Required** - An `m.relates_to` block to form a reference relationship to the poll start event.
* **Required** - An `m.text` block to act as a fallback for clients which can't process polls.
* **Optional** - An `m.poll.results` block to show the sender's perspective of the vote results. This
  should not be used as a trusted block, but rather as a placeholder while the client's local results
  are tabulated.

The above describes the minimum requirements for sending an `m.poll.end` event. Senders can add additional
blocks, however as per the extensible events system, receivers which understand poll events should not
honour them.

If a client does not support rendering polls (generally speaking), the client would instead typically
represent the poll start event as text (per above), and thus would likely do the same for the closure
event, keeping users in the loop with what is going on.

If a `m.poll.end` event is received from someone other than the poll creator or user with permission to
redact other's messages in the room, the event must be ignored by clients due to being invalid. The
redaction power level is chosen to support moderation: while moderators can just remove the poll from the
timeline entirely, they may also wish to simply close it to keep context visible.

**Rationale**: Although clock drift is possible, as is clock manipulation, it is not anticipated that
polls will be closed while they are still receiving high traffic. There are some cases where clients might
apply local timers to auto-close polls, though these are typically used in extremely high traffic cases
such as Twitch-style audience polls - rejecting even 100 responses is unlikely to significantly affect
the results. Further, if a server were to manipulate its clock so that poll responses are sent after the
poll was closed, but timestamped for when it was open, the server is violating a social contract and likely
will be facing a ban from the room. This MSC does not propose a mitigation strategy beyond telling people
not to ruin the fun. Also, don't use polls for things that are important.

The `m.poll.end`'s `origin_server_ts` determines when the poll closes exactly: if no valid end event
is received, the poll is still open. If the poll is closed, only votes sent on or before that timestamp
are considered, even if those votes are from before the start event. This is to handle clock drift over
federation as gracefully as possible.

Repeated end events are ignored - only the first (valid) closure event by `origin_server_ts` is counted.
Clients should disable voting interactions with polls once they are closed.

### Poll kinds

This proposal defines an `m.poll` content block with a `kind` field accepting namespaced strings, with
`m.disclosed` and `m.undisclosed` being mentioned (`m.undisclosed` being the default), however it does
not describe what these values represent.

In short, `m.disclosed` means the votes for poll are shown to users while the poll is still open. An
`m.undisclosed` poll would only show results when the poll is closed.

**Note**: because poll responses are sent into the room, non-compliant clients or curious users could
tally up results regardless of the poll being explicitly disclosed or not. This proposal acknowledges
the issue, but does not fix it.

Custom poll kinds are possible using the [standardized namespace grammar](https://spec.matrix.org/v1.4/appendices/#common-namespaced-identifier-grammar),
and clients which do not recognize the kind are to assume `m.undisclosed` for maximum compatibility
with other poll kinds.

#### Disclosed versus undisclosed polls

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

### Client implementation notes

Clients can rely on the [`/relations`](https://spec.matrix.org/v1.4/client-server-api/#get_matrixclientv1roomsroomidrelationseventidreltype)
API to find votes which might have been received during limited ("gappy") syncs, or whenever they become
descynchronized and need to recalculate events. Ranged approaches, such as [MSC3523](https://github.com/matrix-org/matrix-spec-proposals/pull/3523),
are not suitable for this particular case because the gap between syncs might contain events which are not
revealed by the range. For example, if a remote server took an extra hour to send events and the receiving
client had a gappy sync over a span of 15 minutes: the client might not know that it needs to go back potentially
hours to see the missing event.

This MSC does not describe an aggregation approach for poll events, hence the need for the client to retrieve
all referenced events rather than simply relying on bundles.

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

Due to the reference relationship between responses and the poll start event, it's possible that a
client facing an "unable to decrypt" error on the response won't know if it's a poll response specifically
or some other reference relationship. Clients are encouraged to tell users when there's a possibility
that not all responses are known, potentially impacting the results, such as where related events are
undecryptable.

## Alternatives

The primary competition to this MSC is the author's own [MSC2192](https://github.com/matrix-org/matrix-doc/pull/2192)
which describes not only polls but also inline widgets. The poll implementation in MSC2192 is primarily
based around `m.room.message` events, using `msgtype` to differentiate between the different states. As
[a thread](https://github.com/matrix-org/matrix-doc/pull/2192/files#r514497274) notes on the MSC, this
is an awful experience on clients which do not support polls properly, leaving an irritating amount of
contextless messages in the timeline. Though not directly mentioned on that thread, polls also cannot be
closed under that MSC which leads to people picking options hours or even days after the poll has "ended".
This MSC instead proposes to only supply fallback on the start and end of a poll, leading to enough context
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

### Aggregations instead of references?

A brief moment in this MSC's history described an approach which used aggregations (annotations/reactions)
instead of the proposed reference relationships, though this had immediate concerns of being too
complicated for practical use.

While it is beneficial for votes to be quickly tallied by the server, the client still needs to do
post-processing on the data from the server in order to accurately represent the valid votes. The
server should not be made aware of the poll rules as it can lead to over-dependence on the server,
potentially causing excessive network requests from clients.

As such, the reference relationship is maintained by this proposal in order to remain consistent with
how the poll close event is sent: instead of clients having to process two paginated requests they can
use a single request to get the same information, but in a more valuable form.

For completeness, the approach of aggregations-based responses is summarized as:

* `m.annotation` `rel_type`
* `key` is an answer ID
* Multiple response events for multi-select polls. Only the most recent duplicate is considered valid.
* Unvoting is done through redaction.

Additional concerns are how the client needs to ensure that the answer IDs won't collide with a reaction
or other annotation, adding additional complexity in the form of magic strings.

## Security considerations

As mentioned a multitude of times throughout this proposal, this MSC's approach is prone to disclosure
of votes and has a couple abuse vectors which make it not suitable for important or truly secret votes.
Do not use this functionality to vote for presidents.

Clients should apply a large amount of validation to each field when interacting with polls. Event
bodies are already declared as completely untrusted, though not all clients apply a layer of validation.
In general, this MSC aims to try and show something of use to users so they can at least figure out
what the sender intended, though clients are also welcome to just hide invalid events/responses (with
the exception of spoiled votes: those are treated as "unvoting" or choosing nothing). Clients are
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
[pinned messages](https://spec.matrix.org/v1.4/client-server-api/#mroompinned_events).

Notifications support for polls have been moved to [MSC3930](https://github.com/matrix-org/matrix-spec-proposals/pull/3930).

Normally extensible events would only be permitted in a specific room version. However, unlike other proposals
related to extensible events, this proposal's events don't replace any existing events in the spec. Additionally,
the only extensible events component this proposal depends on is `m.text` which has already entered the spec via
[MSC3765](https://github.com/matrix-org/matrix-spec-proposals/pull/3765) in version 1.15. Therefore, this proposal's
events are permitted in any room version.

## Unstable prefix

While this MSC is not considered stable, implementations should use `org.matrix.msc3381.*` as a namespace
instead of `m.*` throughout this proposal, with the added considerations below. Note that extensible events
and content blocks might have their own prefixing requirements.

Unstable implementations should note that a previous draft is responsible for defining the event format/schema
for the unstable prefix. The differences are rooted in a change in MSC1767 (Extensible Events) where the approach
and naming of fields changed. The differences are:

* For `m.poll.start` / `org.matrix.msc3381.poll.start`:
  * `m.text` throughout becomes a single string, represented as `org.matrix.msc1767.text`
  * `m.poll` becomes `org.matrix.msc3381.poll.start`, retaining all other fields as described. Note the `m.text`
    under `question` and `answers`, and the `org.matrix.msc3381.poll` prefix for `kind` enum values. `m.id` under
    `answers` additionally becomes `id`, without prefix.
* For `m.poll.response` / `org.matrix.msc3381.poll.response`:
  * `m.selections` becomes an `org.matrix.msc3381.poll.response` object with a single key `answers` being the
    array of selections.
  * `m.relates_to` is unchanged.
* For `m.poll.end` / `org.matrix.msc3381.poll.end`:
  * `m.text` has the same change as `m.poll.start`.
  * `m.poll.results` is removed.
  * `org.matrix.msc3381.poll.end` is added as an empty object, and is required.

Examples of unstable events are:

```json
{
  "type": "org.matrix.msc3381.poll.start",
  "content": {
    "org.matrix.msc1767.text": "What should we order for the party?\n1. Pizza 🍕\n2. Poutine 🍟\n3. Italian 🍝\n4. Wings 🔥",
    "org.matrix.msc3381.poll.start": {
      "kind": "org.matrix.msc3381.poll.disclosed",
      "max_selections": 1,
      "question": {
        "org.matrix.msc1767.text": "What should we order for the party?",
      },
      "answers": [
        {"id": "pizza", "org.matrix.msc1767.text": "Pizza 🍕"},
        {"id": "poutine", "org.matrix.msc1767.text": "Poutine 🍟"},
        {"id": "italian", "org.matrix.msc1767.text": "Italian 🍝"},
        {"id": "wings", "org.matrix.msc1767.text": "Wings 🔥"}
      ]
    }
  }
}
```

```json
{
  "type": "org.matrix.msc3381.poll.response",
  "content": {
    "m.relates_to": {
      "rel_type": "m.reference",
      "event_id": "$fw8dod4VdLCkakmKiD6XiVj7-RrFir9Jwc9RW6llJhU"
    },
    "org.matrix.msc3381.poll.response": {
      "answers": ["pizza"]
    }
  }
}
```

```json
{
  "type": "org.matrix.msc3381.poll.end",
  "content": {
    "m.relates_to": {
      "rel_type": "m.reference",
      "event_id": "$fw8dod4VdLCkakmKiD6XiVj7-RrFir9Jwc9RW6llJhU"
    },
    "org.matrix.msc1767.text": "The poll has ended. Top answer: Italian 🍝",
    "org.matrix.msc3381.poll.end": {},
  }
}
```
