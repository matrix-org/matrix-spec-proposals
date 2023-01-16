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

* [MSC3954 - Emotes](https://github.com/matrix-org/matrix-doc/pull/3954)
* [MSC3955 - Notices / automated events](https://github.com/matrix-org/matrix-doc/pull/3955)
* [MSC3956 - Encryption](https://github.com/matrix-org/matrix-doc/pull/3956)
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
useful for understanding the problem space. Unfortunately, for those who need to
understand the changes to the protocol/specification, the best option is to read
this proposal.

## Proposal

In a new room version (why is described later in this proposal), events are declared
to be represented by their extensible form, as described by this MSC. `m.room.message`
is formally deprecated by this MSC, with removal from the specification happening as
part of a room version adopting the feature. Clients are expected to use extensible
events only  in rooms versions which explicitly declare such support (in both unstable
and stable settings).

An extensible event is made up of two critical parts: an event type and zero or more
content blocks. The event type defines which content blocks a receiver can expect,
and the content blocks carry the information needed to render the event (whether the
client understands the event type or not).

Content blocks are simply any top-level key in `content` on the event. They can have
any value type (that is also legal in an event generally: string, integer, etc), and
are namespaced using the
[Matrix conventions for namespacing](https://spec.matrix.org/v1.4/appendices/#common-namespaced-identifier-grammar).

Content blocks can be invented independent of event types and *should* be reusable
in nature. For example, this proposal introduces an `m.markup` content block which
can be reused by other event types to represent textual fallback.

When a client encounters an extensible event (any event sent in a supported room
version) that it does *not* understand, the client begins searching for a best match
based on event type schemas it *does* know. For example, a client might attempt to
parse the event as a video event first, then try parsing it as audio, then as an
image, then as a file, and finally as a plain text message. If all of the client's
options are exhausted, the event is unrenderable by that client (as it would be
prior to extensible events even existing).

Note that a "client" in an extensible events sense will typically mean an application
using the Client-Server API, however in reality a client will be anything which needs
to parse and understand event contents (servers for some functions like push rules,
application services, etc).

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

In `m.message`'s case, `m.markup` is the only required content block. The `m.markup`
block can be reused by other events to include a text-like markup for the event, such
as a text fallback for clients which do not understand how to render a custom event
type.

To reiterate, when a client encounters an unknown event type it first tries to see
if there's a set of content blocks present that it can associate with a known event
type. If it finds suitable content blocks, it parses the event as though the event
were of the known type. If it doesn't find anything useful, the event is left as
unrenderable, just as it likely would today.

It is left as a deliberate client implementation detail to decide which content blocks
to search for, and in what order/combination. For example, a client might decide that
although it understands how to parse an `org.example.type` event, it will deliberately
not try to "cast" unknown events into that type.

To avoid a situation where events end up being unrenderable, it is strongly
recommended that all event types support at least an `m.markup` content block in
their schema, thus allowing all events to theoretically be rendered as message
events (in a worst case scenario).

For clarity, events are not able to specify *how* they are handled when the receiver
doesn't know how to render the event type: the sender simply includes all possible or
feasible representations for the data, hoping the receiver will pick the richest form
for the user. As an example, a special medical imaging event type might also be
represented as a video, static image, or text (URL to some healthcare platform): the
sender includes all 3 fallbacks by specifying the needed content blocks, and the
receiver may pick the video, image, or text depending on its own rules.

Events must still only represent a single logical piece of information, thus encouraging
sensible fallback options in the form of content blocks. The information being represented
is described by the event type, as it always has been before this MSC. It is explicitly
not permitted to represent two or more pieces of information in a single event, such
as a livestream reference and poll: senders should look into
[relationships](https://spec.matrix.org/v1.5/client-server-api/#forming-relationships-between-events)
instead.

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

### Room version

This MSC requires a room version to make the transition process clear and coordinated.
Normally for a feature such as this, an effort would be made to attempt to support
backwards compatibility for a duration of time, however for a feature that requires
significant overhaul of clients, servers, and Matrix as a whole it feels more important
to bias towards a clear switch between legacy and modern (extensible) events.

**Note**: A previous draft of this proposal (codenamed "v1 extensible events") did attempt
to describe a timeline-based approach, allowing for event types to mix concepts of content
blocks and legacy fields, however that approach did not give sufficient reason for clients
to fully adopt the extensible events changes.

In room versions supporting extensible events, clients MUST only send extensible events.
Deprecated event types (to be enumerated at the time of making the room version) MUST NOT
be sent into extensible event-supporting room versions, and clients MUST treat deprecated
event types as unrenderable by force. For example, if a client sees an `m.room.message` in
an extensible event-supporting room version, it must not render it, even if it knows how
to render that type.

While full enforcement of this restriction is not feasible, servers are encouraged to block
Client-Server API requests for sending known-banned event types into applicable rooms. This
obviously does not help when the room is encrypted, or the client is sending custom events
in a non-extensible form, hence the requirement that clients treat the events as invalid too.

The Spec Core Team (SCT) will be responsible for determining when it is reasonable to include
extensible events in a published (stable) room version.

Meanwhile, clients can send mixed support for extensible events if they prefer (such as by
mixing in `m.markup` onto `m.room.message`), however should avoid sending largely-unknown
extensible event types into room versions which don't support extensible events. Some event
types declare explicit support for what would normally be an unsupported room version - client
authors should check the applicable MSC or specification for the feature to determine if they
are allowed to do this. Such examples include MSC3381 Polls and MSC3245 Voice Messages.

### State events

Unknown state event types generally should not be parsed by clients. This is to prevent situations
where the sender overly masks a state change as some other, non-state, event. For example, even
if a state event has an `m.markup` content block, it should not be treated as a room message.

Note that state events MUST still make use of content blocks in applicable room versions, and that
any top-level key in `content` is defined as a content block under this proposal. As such, this
MSC implicitly promotes all existing content fields of `m.*` state events to indepdent content
blocks as needed. Other MSCs may override this decision on a per-event type basis (ie: redeclaring
how room topics work to support content blocks, deprecating the existing `m.room.topic` event in
the process). Unlike most content blocks, these promoted-to-content-blocks are not realistically
meant to be reused: it is simply a formality given this MSC's scope.

### Notifications

Currently [push notifications](https://spec.matrix.org/v1.5/client-server-api/#push-notifications)
describe how an event can cause a notification to the user, though it makes the assumption
that there are `m.room.message` events flying around to denote "messages" which can trigger
keyword/mention-style alerts. With extensible events, the same might not be possible as it
relies on understanding how/when the client will render the event to cause notifications.

For simplicity, when `content.body` is used in an `event_match` condition, it now looks for
an `m.markup` block's `text/plain` representation (implied or explicit) in room versions
supporting extensible events. This is not an easy rule to represent in the existing push
rules schema, and this MSC has no interest in designing a better schema. Note that other
conditions applied to push notifications, such as an event type check, are not affected by
this: clients/servers will have to alter applicable push rules to handle the new event types
(see also: [MSC3933](https://github.com/matrix-org/matrix-spec-proposals/pull/3933) and friends).

### Power levels

This MSC proposes no changes to how power levels interact with events: they are still
capable of restricting which users can send an event type. Though events might be rendered
as a different logical type (ie: unknown event being rendered as a message), this does not
materially impact the room's ability to function. Thus, considerations for how to handle
power levels more intelligently are details left for a future MSC.

As of writing, most rooms fit into two categories: any event type is possible to send, or
specific cherry-picked event types are allowed (announcement rooms: reactions & redactions).
Extensible events don't materially change the situation implied by this power levels structure.

### Mixins specifically allowed

[Mixins](https://en.wikipedia.org/wiki/Mixin) are supported by Extensible Events through
dedicated content blocks. Though this MSC does not describe any such mixins itself,
MSC3955 does by allowing events to be flagged as "automated". Previously it was only possible
to flag a text message as an `m.notice` event, however with MSC3955 any event could become
described as sent by a bot, thus reducing feedback loops.

### Uses of HTML & text throughout the spec

For an abundance of clarity, all functionality not explicitly called out in this MSC which
relies on the `formatted_body` of an `m.room.message` is expected to transition to using
an appropriate `m.markup` representation instead. For example, the HTML representation of
a [mention](https://spec.matrix.org/v1.5/client-server-api/#user-and-room-mentions) will
now appear under `m.markup`'s `text/html` representation (adding one if required).

A similar condition is applied to `body` in `m.room.message`: all existing functionality
will instead use the `text/plain` representation within `m.markup`, if not explicitly
called out by this MSC.

## Potential issues

It's a bit ugly to not know whether a given key in `content` will take a string, object,
boolean, integer, or array.

It's a bit ugly to not know at a glance if a content block is a mixin or not.

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

## Note about spec process

Extensible events as a spec feature requires dozens of different MSCs, with this MSC being
the structure definition and text baseline. It is *not* expected that this MSC will be
written into spec once it has passed FCP. Instead, it is expected that all of the "core"
extensible events MSCs will pass FCP and extensible events be assigned a stable room version
before any spec authoring begins. Thus, this particular MSC should be anticipated to sit
in accepted-but-not-merged (stable, not formal spec yet) for a while, and that's okay.

The Spec Core Team (SCT) has decision making power over what is considered core for extensible
events, though the recommendation is to ensure replacements for all non-state `m.room.*` types
have accepted (successful FCP) MSCs to replace them.

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
* Move most push rule changes and such into their own/future MSCs.
* Move emotes, notices, and encryption out to their own dedicated MSCs.
