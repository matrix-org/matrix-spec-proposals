# MSC1767: Extensible events in Matrix

While events are currently JSON blobs which accept additional metadata appended to them,
there is no formal structure for how to represent this information or interpret it on the
client side, particularly in the case of unknown event types.

When specifying new events, the proposals often reinvent the same wheel instead of reusing
existing blocks or types, such as in cases where captions, thumbnails, etc need to be
considered for an event. This has further issues of clients not knowing how to render these
newly-specified events, leading to mixed compatibility within the ecosystem.

The above seriously hinders the uptake of new event types (and therefore features) within
the Matrix ecosystem. In the current system, a new event type would be introduced and
all implementations slowly gain support for it - if we instead had reusable types then
clients could automatically support a "good enough" version of that new event type while
"proper" support is written in over time. Such an example could be polls: not every
client will want polls right away, but it would be quite limiting as a user experience
if some users can't even see the question being posed.

This proposal introduces a structure for how extensible events are represented, using
the existing extensible nature of events today, laying the groundwork for more reusable
blocks of content in future events.

With text being the simplest form of representation for events today, this MSC also
specifies a relatively basic text schema for room messages that can be reused in other
events. Other building block types are specified by other MSCs:

* [MSC3927 - Audio](https://github.com/matrix-org/matrix-doc/pull/3927)
* [MSC3551 - Files](https://github.com/matrix-org/matrix-doc/pull/3551)
* [MSC3552 - Images and Stickers](https://github.com/matrix-org/matrix-doc/pull/3552)
* [MSC3553 - Videos](https://github.com/matrix-org/matrix-doc/pull/3553)
* [MSC3554 - Translatable text](https://github.com/matrix-org/matrix-doc/pull/3554)

Some examples of new features/events using extensible events are:

* [MSC3488 - Location data](https://github.com/matrix-org/matrix-doc/pull/3488)
* [MSC3381 - Polls](https://github.com/matrix-org/matrix-doc/pull/3381)
* [MSC3245 - Voice messages](https://github.com/matrix-org/matrix-doc/pull/3245)
* [MSC2192 - Inline widgets](https://github.com/matrix-org/matrix-doc/pull/2192)
* [MSC3765 - Rich text topics](https://github.com/matrix-org/matrix-doc/pull/3765)

**Note**: Readers might find [Andy's blog](https://www.artificialworlds.net/blog/2022/03/08/comparison-of-matrix-events-before-and-after-extensible-events/)
useful for understanding the problem space, however please be aware that it's
based on an earlier draft of this proposal (as of writing). Unfortunately, for
those who need to understand the changes to the protocol/specification, the only
option is to read this proposal.

## Proposal

In a new room version (why is described later in this proposal), events are declared
to be represented by their extensible form, as described by this MSC. `m.room.message`
is formally deprecated by this MSC, with "removal" happening as part of the room
version adoption. Clients are expected to use extensible events only in rooms versions
which explicitly declare such support.

An extensible event is made up of two critical parts: an event type and zero or more
content blocks. The event type describes the information being carried in the event,
and the content blocks describe how to render that information (whether the client
understands the event type or not).

Content blocks are simply any top-level key in `content` on the event. They can have
any value type, and are namespaced using the
[Matrix conventions for namespacing](https://spec.matrix.org/v1.4/appendices/#common-namespaced-identifier-grammar).

Unlike previous iterations of this proposal, it is not expected that content block
types (the key in `content`) have a suitably defined event type schema to go along
with them: instead, content blocks can be invented independent of event types if the
need arises. For clarity, in previous drafts, this proposal suggested that a "primary"
event type also have a "reusable" event type in `content`, implying it was possible
to send a standalone `m.caption` event (for example) - this is not the case in this
iteration. Instead, an `m.caption` content block can be defined *without* specifying
an `m.caption` event type. However, event types and content block types can be named
the same way: they must not be interpretted to be the same logical type.

Per the introduction, text is the baseline format that most/all Matrix clients support
today, often through use of HTML and `m.room.message`. Instead of using `m.room.message`
to represent this content, clients would instead use an `m.message` event with, at
a minimum, a `m.markup` content block:


```json5
{
    // irrelevant fields not shown
    "type": "m.message",
    "content": {
        "m.markup": [
            { "body": "<i>Hello world</i>", "mimetype": "text/html" },
            { "body": "Hello world" }
        ]
    }
}
```

`m.markup` has the following definitions associated with it:
* An ordered array of mimetypes and applicable string content to represent a single
  marked-up blob of text. Each element is known as a representation.
* `body` in a representation is required, and must be a string.
* `mimetype` is optional in a representation, and defaults to `text/plain`.
* Zero representations are permitted, however senders should aim to always specify
  at least one.
* Invalid representations are skipped by clients (missing `body`, not an object, etc).
* The first representation a renderer understands should be used.
* Senders are strongly encouraged to always include a plaintext representation,
  however are equally permitted to send an HTML representation instead.
* The `mimetype` of a representation determines its `body` - no effort is made to
  limit what is allowed in the `body` (ie: we don't specify what is allowable HTML),
  therefore it is the client's responsibility to validate/sanitize the content further,
  such as by using the [existing spec](https://spec.matrix.org/v1.4/client-server-api/#mroommessage-msgtypes)
  for recommended allowable HTML.
* Custom markups in a representation are specified by a suitably custom `mimetype`.
  For example, extending HTML or XML or an all-new format. This can be used to create
  bridge-compatible clients where the destination network's markup is first in the
  array, followed by more common HTML and text formats.

Like with the event described above, all event types now describe which content blocks
they expect to see on their events. These content blocks could be required, as is the
case of `m.markup` in `m.message`, or they could be optional depending on the situation.
Of course, senders are welcome to send even more blocks which aren't specified in the
schema for an event type, however clients which understand that event type might not
consider them at all.

In `m.message`'s case, `m.markup` is the only required content block and it is required.
The `m.markup` block can be reused by other events to include a text-like markup for
the event, such as a text fallback for clients which do not understand how to render
a custom event type.

When a client encounters an unknown event type, it first tries to see which, if any,
content blocks it can use to render it. If it finds a suitable block, it simply uses
that block to render the event as best it can. The client is permitted to use multiple
blocks to try and render the event, such as combining image and caption blocks for
a fallback. It is deliberately left as an implementation detail to decide which
content blocks to look for, in what order, and what to combine them with (if anything).

If a client is unable to find a suitable content block, or combination of blocks,
the message is unrenderable and treated as such. For most clients, this will mean
simply not showing the event at all. To avoid this situation happening too often,
clients are encouraged to add support for at least `m.markup` to allow all events
to have a terse fallback option.

### Worked example: Custom temperature event

In a hypothetical scenario, a temperature event might look as such:

```json5
{
    // irrelevant fields not shown
    "type": "org.example.temperature",
    "content": {
        "m.markup": [{"body": "It is 22 degrees at Home"}],
        "org.example.probe_value": {
            "label": "Home",
            "units": "org.example.celsius",
            "value": 22
        }
    }
}
```

In this scenario, clients which understand how to render an `org.example.temperature`
event might use the information in `org.example.probe_value` exclusively, leaving the
`m.markup` block for clients which *don't* understand the temperature event type.

Another event type might find inspiration and use the probe value block for their
event as well. Such an example might be in a more industrial control application:

```json5
{
    // irrelevant fields not shown
    "type": "org.example.tank.level",
    "content": {
        "m.markup": [{"body": "[Danger] The water tank is 90% full."}],
        "org.example.probe_value": {
            "label": "Tank 3",
            "units": "org.example.litres",
            "value": 9037
        },
        "org.example.danger_level": "alert"
    }
}
```

This event also demonstrates a `org.example.danger_level` block, which uses a string
value type instead of the previously demonstrated objects and values - this is a legal
content block, as blocks can be of any type.

Clients should be cautious and avoid reusing too many unspecified types as it can create
opportunities for confusion and inconsistency. There should always be an effort to get
useful event types into the Matrix spec for others to benefit from.

### Emotes and notices

Though regular text messages cover a lot of cases, `m.room.message` also supports emote
and notice as possible message types. Under extensible events, the `m.emote` event type
replaces the `m.emote` msgtype, as does `m.notice` for notice events, as shown:

```json5
{
    // irrelevant fields not shown
    "type": "m.emote",
    "content": {
        "m.markup": [{"body": "says hi"}]
    }
}
```

```json5
{
    // irrelevant fields not shown
    "type": "m.notice",
    "content": {
        "m.markup": [{"body": "this is a bot message"}]
    }
}
```

These event types do not define any additional content blocks, instead reusing the markup
block from earlier in this proposal. `m.markup` is a required block for these event types.

To support event types which may need an emote or notice fallback, `m.emote` and `m.notice`
are defined as content blocks with an object containing the `content` of a normal `m.emote`
or `m.notice` event:

```json5
{
    // irrelevant fields not shown
    "type": "org.example.temperature",
    "content": {
        "m.notice": {
            "m.markup": [{"body": "It is 22 degrees at Home"}]
        },
        "org.example.probe_value": {
            "label": "Home",
            "units": "org.example.celsius",
            "value": 22
        }
    }
}
```

While technically possible to include an `m.notice`/`m.emote` content block on an `m.message`
event, doing so wouldn't really do much: as most clients are expected to understand `m.message`
events, they would ignore `m.notice` or `m.emote` blocks. Adding the block does *not* turn the
event into a notice/emote - it is still a regular text message, and the sender probably should
have used the `m.notice` or `m.emote` event type specifically.

### Room version

This MSC requires a room version to make the transition process clear and coordinated. In previous
drafts of this proposal, a timeline was set out for when the ecosystem moves forward: while this
sort of timeline does work for some features, it is not necessarily the best way to push for a
whole new event format and gain adoption in a reasonable timeframe.

In that room version, clients MUST only send extensible events. Deprecated event types (to be
enumerated at the time of making the room version) MUST NOT be sent into rooms of that version,
or based on that room version, and clients MUST treat those event types as invalid (unrenderable).
At a minimum, this means clients will NOT send `m.room.message` events in that room version anymore,
and clients MUST treat `m.room.message` as an invalid event type.

While enforcement of this restriction is not possible, servers are encouraged to block client-server
API requests for sending known-banned event types into applicable rooms. This obviously does not
help when the room is encrypted though, which is why clients MUST treat the deprecated event types
as invalid in the room.

The Spec Core Team (SCT) will be responsible for determining when it is reasonable to include extensible
events in a published room version.

Meanwhile, client authors can send mixed support for extensible events if they prefer, however SHOULD
NOT send largely-unknown event types into room versions which do not support extensible events. For
example, a client might send `m.room.message` events with `m.markup` content blocks, but should not
send the new `m.message` event type into that same room.

### State events

State events typically contain metadata about the room and are not rendered themselves, however there
are some cases where rendering the state event change might be useful. For example, it might be desirable
to render a bridge state change with `m.markup` to clearly indicate a bridge was added/edited.

State events MUST make use of content blocks, noting that values like `join_rule` and `membership` found
in `content` today are implicitly legal content blocks, however are not required to offer "sensible"
fallback options for rendering.

Clients are not required to render state events as extensible events, though clients which do should
take care to ensure the events get rendered as applicable events and *not* with any existing state
event styling. As a specific example, Element Web *should not* render state events with `m.markup`
fallback as inline system messages, but rather as text messages (as though the user said the words).

### Encryption

Like `m.room.message`, `m.room.encrypted` is also deprecated in favour of a new `m.encrypted` event
type. `m.encrypted` expects an `m.encrypted` content block, which is the current `content` schema for
an `m.room.encrypted` event:

```json5
{
    // irrelevant fields not shown
    "type": "m.encrypted",
    "content": {
        "m.encrypted": {
            "algorithm": "m.olm.v1.curve25519-aes-sha2",
            "sender_key": "<sender_curve25519_key>",
            "ciphertext": {
                "<device_curve25519_key>": {
                    "type": 0,
                    "body": "<encrypted_payload_base_64>"
                }
            }
        }
    }
}
```

This allows the `m.encrypted` content block to be reused by other event types, if required.

For clarity, this is *not* intended to allow unencrypted fallback on an encrypted event - doing
so would be extraordinarily dangerous and is explicitly discouraged.

### Notifications

Currently [push notifications](https://spec.matrix.org/v1.3/client-server-api/#push-notifications)
describe how an event can cause a notification to the user, though it makes the assumption
that there are `m.room.message` events flying around to denote "messages" which can trigger
keyword/mention-style alerts. With extensible events, the same might not be possible as it
relies on understanding how/when the client will render the event to cause notifications.

For simplicity, when `content.body` is used in an `event_match` condition, it now looks for
an `m.markup` block's `text/plain` representation (implied or explicit) in room versions
supporting extensible events. This is not an easy rule to represent in the existing push
rules schema, and this MSC has no interest in designing a better schema. Note that other
conditions applied to push notifications, such as an event type check, are not affected by
this: clients/servers will have to alter applicable push rules to handle the new event types.

A future MSC is expected to address the default push rules having a hardcoded event type.

A future MSC is also expected to introduce a better system for handling push notifications
on extensible events. This MSC aims for basic compatibility with the shortest turnaround
rather than getting riled in discussion about a notifications system structure.

### Power levels

This MSC proposes no changes to how power levels interact with events: they are still
capable of restricting which users can send an event type. Though events might be rendered
as a different logical type (ie: unknown event being rendered as a message), this does not
materially impact the room's ability to function. Thus, considerations for how to handle
power levels more intelligently are details left for a future MSC.

As of writing, most rooms fit into two categories: any event type is possible to send, or
specific cherry-picked event types are allowed (announcement rooms: reactions & redactions).
Extensible events don't materially change the situation implied by this power levels structure.

## Potential issues

It's a bit ugly to not know whether a given key in `content` will take a string, object or array.

It's a bit arbitrary as to which fields are allowed lists of fallbacks (eg image thumbnails).

It's a bit ugly that you have to look over the keys of contents to see what blocks
are present, but better than duplicating this into an explicit `blocks` list within the
event content (on balance).

We're skipping over defining rules for which fallback combinations to display
(i.e. "display hints") for now; these can be added in a future MSC if needed.
[MSC1225](https://github.com/matrix-org/matrix-doc/issues/1225) contains a proposal for this.

Placing content blocks at the top level of `content` is a bit unfortunate, particularly
when mixing in `m.room.message` compatibility, though mixes nicely thanks to namespacing.
Potentially conflicting cases in the wild would be namespaced fields, which would get
translated as unknown event types, and thus skipped by the rendering machinery.

This MSC does not rewrite or redefine all possible events in the specification: this is
deliberately left as an exercise for several future MSCs.

## Security considerations

Like today, it's possible to have the different representations of an event not match,
thus introducing a potential for malicious payloads (text-only clients seeing something
different to HTML-friendly ones). Clients could try to do similarity comparisons, though
this is complicated with features like HTML and arbitrary custom markup (markdown, etc)
showing up in the plaintext or in tertiary formats on the events. Historically, room
moderators have been pretty good about removing these malicious senders from their rooms
when other users point out (quite quickly) that the event is appearing funky to them.

## Unstable prefix

While this MSC is not considered stable by the specification, implementations *must* use
`org.matrix.msc1767` as a prefix to denote the unstable functionality. For example, sending
an `m.message` event would mean sending an `org.matrix.msc1767.message` event instead.

Implementations looking to mix extensible events with past events, per elsewhere in this
proposal, would do something like the following (in the case of `m.room.message`, at least):

```json5
{
    "type": "m.room.message",
    "content": {
        "msgtype": "m.text",
        "body": "Hello World",
        "format": "org.matrix.custom.html",
        "formatted_body": "<b>Hello</b> World",
        "org.matrix.msc1767.markup": [
            {"body": "Hello World"},
            {"body": "<b>Hello</b> World", "mimetype": "text/html"}
        ]
    }
}
```

For purposes of testing, implementations can use a dynamically-assigned unstable room version
`org.matrix.msc1767.<version>` to use extensible events within. For example, `org.matrix.msc1767.10`
for room version 10 or `org.matrix.msc1767.org.example.cool_ver` for a hypothetical
`org.example.cool_ver` room version. Any events sent in these room versions *can* use stable
identifiers given the entire room version itself is unstable, however senders *must* take care
to ensure stable identifiers do not leak out to other room versions - it may be simpler to not
send stable identifiers at all.

## Changes from MSC1225

* converted from googledoc to MD, and to be a single PR rather than split PR/Issue.
* simplifies it by removing displayhints (for now - deferred to a future MSC).
* removes all references to mixins, as the term was scaring people and making it feel far too type-theoretic.
* replaces the clunky m.text.1 idea with lists for types which support fallbacks.
* removes the concept of optional compact form for m.text by instead having m.text always in compact form.
* tries to accomodate most of the feedback on GH and Google Docs from MSC1225.

## Historical changes

* Anything that wasn't simple text rendering was broken out to dedicated MSCs in an effort to get the
  structure approved and adopted while the more complex types get implemented independently.
* Renamed subtypes/reusable types to just "content blocks".
* Allow content blocks to be nested.
* Fix push rules in the most basic sense, deferring to a future MSC on better support.
* Explicitly make no changes to power levels, deferring to a future MSC on better support.
* Drop timeline for transition in favour of an explicit room version.

## MSC Dependencies

This proposal mentions that some functionality is left for a future MSC, and some of that
functionality might seem like a reasonable blocker for this proposal entering FCP. Specifically,
while this MSC lays the groundwork for extensible events and deprecates `m.room.message`, it
does not have an immediate answer to all of the existing `msgtype` options: it is a goal to
land this proposal as a nod towards the system working, with other MSCs being accepted at their
own pace to build a complete system. Once enough of a system is defined (ie: all `msgtype` options
covered), it is expected that "Extensible Events" as a system enters the specification - not
in pieces.
