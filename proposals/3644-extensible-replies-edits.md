# MSC3644: Extensible Events: Edits and replies

[Extensible Events (MSC1767)](https://github.com/matrix-org/matrix-doc/pull/1767) are a new way of
representing renderable events in clients, with a focus on providing fallbacks for rendering unknown
event types.

[Replies](https://spec.matrix.org/v1.1/client-server-api/#rich-replies) are a specified feature which
allows a user to incorporate the context of a previous message in their own, forming a sort of
"reply chain". Note that this is different from a concept of "threads" which typically have more
powerful UI on top of them.

[Edits (MSC2676)](https://github.com/matrix-org/matrix-doc/pull/2676) are simply a way to "replace"
the `content` of an event with new contents, allowing users to fix typos and such on their messages.

Both replies and edits have a built-in fallback system and aren't completely compatible with the
way extensible events are intended to operate. Building off of [MSC2781](https://github.com/matrix-org/matrix-doc/pull/2781),
this proposal aims to describe the additional subtle differences for how edits and replies work
on fully extensible events.

**Note**: [MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767) defines a transitional format
for room messages. As far as this proposal is concerned, those transitional events are left untouched
for backwards compatibility. This proposal only affects the after-transition events (or any other event
types which happen to use extensible events from the start, like [Polls (MSC3381)](https://github.com/matrix-org/matrix-doc/pull/3381))).

## Dependencies

This MSC requires the following to pass (or likely pass) FCP before being able to be FCP'd itself:

* [MSC1767: Extensible events](https://github.com/matrix-org/matrix-doc/pull/1767)
* [MSC2676: Edits](https://github.com/matrix-org/matrix-doc/pull/2676)
* [MSC2781: Remove edit & reply fallbacks](https://github.com/matrix-org/matrix-doc/pull/2781)

## Proposal

As described by [MSC2781](https://github.com/matrix-org/matrix-doc/pull/2781), replies will have already
lost their fallback representation. This means they will look something like this on a legacy event:

```json5
{
  "type": "m.room.message",
  "content": {
    "m.relates_to": {
      "m.in_reply_to": {
        "event_id": "$context"
      }
    },
    "msgtype": "m.text",
    "body": "That looks like a great idea!"
  }
}
```

Quite simply, extensible events use the same format:

```json5
{
  "type": "m.message",
  "content": {
    "m.relates_to": {
      "m.in_reply_to": {
        "event_id": "$context"
      }
    },
    "m.text": "That looks like a great idea!"
  }
}
```

Edits are a bit more complicated, however. [MSC2676](https://github.com/matrix-org/matrix-doc/pull/2676)
defines edits which have a `rel_type` of `m.replace` and `m.new_content` in `content`. Extensible
events simply drop the fallback and move `m.new_content` up a level.

An edited message would look similar to:

```json5
{
  "type": "m.message",
  "content": {
    "m.relates_to": {
      "rel_type": "m.replace",
      "event_id": "$original"
    },
    "m.text": "That looks like a great idea!"
  }
}
```

As mentioned, the fallback text (asterisk-prefixed message from MSC2676) is not present. This is to
follow the spirit of [MSC2781](https://github.com/matrix-org/matrix-doc/pull/2781).

For clarity, edits in this structure replace the entire event. This can technically mean that events
are able to change type, though this shouldn't have too many unintended side effects for rendering
in clients. For example, a message being replaced with a poll feels entirely valid (even if complicated
to represent in a client's UX). Going from a poll to a question is possible, though unlikely.

In cases where the client wants to append/alter a reply to a message, it'd simply include both relation
types. Because they are non-conflicting by nature, this allows for a reply to be added, removed, or
changed. For example:

```json5
{
  "type": "m.message",
  "content": {
    "m.relates_to": {
      "rel_type": "m.replace",
      "event_id": "$original",
      "m.in_reply_to": {
        "event_id": "$context"
      }
    },
    "m.text": "That looks like a great idea!"
  }
}
```

A downside of this system is that relation-requiring events, such as poll responses and reactions,
are not editable because the relation will be overridden. Other proposals, like
[MSC3051](https://github.com/matrix-org/matrix-doc/pull/3051), aim to change the relation structure
wholesale to account for these cases. For the purposes of extensible events, and this proposal, the
intention is that these relation-requiring events describe overload mechanics on their own. For
example, polls only take into consideration the most recent event while reactions effectively rely
upon redact & re-send approaches.

## Potential issues

As described, not being able to edit relation-requiring events is a bit unfortunate though managed
external to this proposal.

Also as described, events can effectively change type under this system. This could have consequences
on systems like the [key verification framework](https://spec.matrix.org/v1.1/client-server-api/#key-verification-framework),
though those systems are typically built to be resilient against malicious attack. For example, key
verification will have already completed or could fail due to edits - clients will still need to
determine if the change is malicious, or if it is even valid, to potentially warn the user of bad
behaviour from their verification partner. A future MSC will aim to solve the key verification
framework for an extensible events world specifically.

Lack of fallbacks could be concerning to some readers, particularly for edits, however given the
unique position of extensible events causing an ecosystem-wide change the risk is relatively minor.
Clients which don't implement `m.message` and similar event types will be left behind when the
ecosystem moves ahead with sending them after the transition period, which also means fallbacks
won't help them all that much. Clients which do support the new primary event types will potentially
have to do a bit of additional work to support replies and edits.

To reiterate, this proposal affects new primary event types under the extensible events structure.
That includes `m.message`, but also affects extensible-first features like polls. Similar to the
argument that clients will be left behind for not implementing `m.message` and friends, clients
which are implementing extensible-first features should be expected to handle replies and edits as
per this proposal, though unstable implementations should note the details in the unstable prefix
section later on in this proposal.

## Alternatives

Edits could remain unchanged, however given a general desire to remove fallbacks from events and a
complete ecosystem change on events this feels like a great opportunity to take advantage of. Other
aspects of events that were previously thought to be unfixable might additionally be able to take a
similar approach.

We could also introduce an `m.edit` or `m.reply` primary type, however this feels overly complicated
to implement given the relation type would be pulled away from the referenced event ID. Instead, we
risk allowing clients to change event types for generally improved event shape.

## Security considerations

Changing event types is potentially dangerous. Aside from the key verification framework, which is
planned to be looked at by a future MSC, the author is not aware of any likely conflicts that could
occur. All other event-based systems appear to be "fine" with being removed/replaced by completely
different event types, and the consequences for doing so are clear. For example, a poll being replaced
with a plain message means the poll results are lost.

## Unstable prefix

Unstable implementations of this MSC and extensible events in general should be wary that some clients
will not be completely aware of the new edits structure. Therefore, while unstable, those implementations
should treat `m.new_content` with higher priority if present on the replacement event. The semantics are
otherwise the same.

This MSC otherwise does not introduce any functionality which requires a specific unstable namespace.
