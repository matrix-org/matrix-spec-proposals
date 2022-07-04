# MSC1767: Extensible events in Matrix

While events are currently JSON blobs which accept additional metadata appended to them,
there is no formal structure for how to represent this information or interpret it on the
client side.

New events also typically reinvent the wheel rather than reuse existing types, such as in
cases where captions, thumbnails, etc need to be considered. This has further issues of
clients not knowing how to render these unknown events, leading to mixed compatibility
within the ecosystem.

The above seriously hinders the uptake of new event types (and therefore features) within
the Matrix ecosystem. In the current system, a new event type would be introduced and
all implementations slowly gain support for it - if we instead had reusable types then
clients could automatically support a "good enough" version of that new event type while
"proper" support is written in over time. Such an example could be polls: not every
client will want polls right away, but it would be quite limiting as a user experience
if some users can't even see the question being posed.

This proposal introduces a structure for how to represent events using the extensible
nature of Matrix events, laying the groundwork for more and more types which can be
used in future events.

Text is typically the simplest form of representation for events currently sent over
Matrix, and so this MSC covers not only the schema for extensible events but also the
(rich) text representation that events can use if they like. Other representations,
such as file/image attachments, are described by other MSCs:

* [MSC3246 - Audio (non-voice)](https://github.com/matrix-org/matrix-doc/pull/3246)
* [MSC3551 - Files](https://github.com/matrix-org/matrix-doc/pull/3551)
* [MSC3552 - Images and Stickers](https://github.com/matrix-org/matrix-doc/pull/3552)
* [MSC3553 - Videos](https://github.com/matrix-org/matrix-doc/pull/3553)
* [MSC3554 - Translatable text](https://github.com/matrix-org/matrix-doc/pull/3554)

Some examples of new features/events using this schema are:

* [MSC3488 - Location data](https://github.com/matrix-org/matrix-doc/pull/3488)
* [MSC3381 - Polls](https://github.com/matrix-org/matrix-doc/pull/3381)
* [MSC3245 - Voice messages](https://github.com/matrix-org/matrix-doc/pull/3245)

**Note**: Readers only concerned with how to use this new proposed system might
find [Andy's blog](https://www.artificialworlds.net/blog/2022/03/08/comparison-of-matrix-events-before-and-after-extensible-events/)
more understandable. Unfortunately for those who need to understand the changes
to the protocol/specification, the only option is to read this proposal.

## Proposal

*Extensible events* are events which make use of other events to fully describe
themselves. The event types used to describe another event are referred to as
*reusable* events.

Any event type can be used by extensible events as *reusable*, however not all
events are expected to be extensible. The extensible events structure should only
be used when the client *should* be rendering the event, but might not know the
intricate details in order to do that.

An example of an extensible events are [MSC3381 Polls](https://github.com/matrix-org/matrix-doc/pull/3381).
These events have a *primary event type* (the literal `type` field of an event)
which most clients will not understand, but also make use of the *reusable* `m.message`
event type described later by this proposal. This would allow clients to at least
render something in place of a poll, though the poll itself will not function for
users of that client.

Most examples of events which are not anticipated to support extensible events are
state events: membership, room name, history visibility, etc all don't *need* to
be rendered by the client, however senders are welcome to stick `m.message` or
similar reusable types onto those events if they want. The minimum schema for these
*non-extensible events* will not include it, however.

Reusable event types carry with them a semantic meaning which governs how they are
used in extensible events. For example, `m.message` describes text-based messages
though contains features like rich text which might be desirable in other events.
[MSC3765 Rich Text Topics](https://github.com/matrix-org/matrix-spec-proposals/pull/3765)
are such an example: they would like to use the same features that `m.message`
supplies, but *not* for showing the event as a text message. Therefore, the MSC
copies the schema offered by `m.message` and places it into a new `m.topic` reusable
event. Other events which need rich topics might reuse the `m.topic` event in a
similar vein.

A simplified example of an extensible event would be:

```json5
{
    "type": "org.example.temperature", // primary event type
    "content": {
        "org.example.temperature": { // reusable event type
            "deg_c": 24
        },
        "m.message": [ // reusable event type (described by this proposal)
            { "mimetype": "text/plain", "body": "It is 24 Celsius" },
            { "mimetype": "text/html", "body": "It is <strong>24 Celsius</strong>" },
        ]
    }
    // irrelevant fields not shown, like `sender`
}
```

Here, the `org.example.temperature` event type has two roles: as a primary type and
as a reusable type. The primary type here is unlikely to be recognized by clients, but
`m.message` should be easily understood - clients which don't know how to, or don't
want to have custom support for rendering `org.example.temperature` events would instead
render the event as `m.message` for the user.

Since all event types can be reusable event types, another Matrix implementation might
become inspired and define an event type for their IoT fridge:

```json5
{
    "type": "org.example.fridge_state", // primary event type
    "content": {
        "org.example.fridge_state": { // reusable event type
            "phase": "cooling",
            "target_temp": {
                "deg_c": 4
            }
        },
        "org.example.temperature": { // reusable event type from prior example
            "deg_c": 6
        },
        "m.message": [ // reusable event type (described by this proposal)
            { "mimetype": "text/plain", "body": "The fridge is cooling to 4C from 6C" },
            { "mimetype": "text/html", "body": "The fridge is <strong>cooling</strong> to 4C from 6C" },
        ]
    }
    // irrelevant fields not shown, like `sender`
}
```

Because `org.example.temperature` is described as *current* temperature by the earlier
example, the fridge state event doesn't need to describe how to get the current temperature
information out of the event. Clients would simply inspect the `org.example.temperature`
event in `content` for that information. What the current temperature doesn't describe
is other information about the fridge, so a new event type is used to contain such details.
The `m.message` event is used as a fallback in case the client doesn't understand how to
render anything else, however a temperature-aware (but not fridge-aware) client might
decide to render the event as `org.example.temperature` instead.

At this point it's also clear that the temperature event should go into the Matrix spec
somewhere given it is being reused all over the place. Likely handled by a
[non-core registry](https://github.com/matrix-org/matrix-spec/issues/1064) in this case,
someone would open an MSC to describe `m.current_temperature` (or whatever) so it can
be safely relied upon by other clients.

Clients should be cautious and avoid reusing too many unspecified types as it can create
opportunities for confusion and inconsistency. There should always be an effort to get
useful event types into the Matrix spec for others to benefit from.

### Extensible event schema

To spell out the implied details from the examples above, a *primary event type* (the
literal `type` on an event) describes which other *reusable* event types must appear
in the event's `content`. Senders can include more than the minimum, though should never
include less.

An extensible event does *not* need to have the primary event type show up as a reusable
event in `content` if it would serve no purpose. For example, [stickers](https://spec.matrix.org/v1.3/client-server-api/#sticker-messages)
as currently defined by the spec are images with special UX for rendering. They could
reasonably be represented as follows without a `m.sticker` reusable type:

```json5
{
    "type": "m.sticker", // primary event type
    "content": {
        "m.image": { /* ... */ },
        "m.file": { /* ... */ },
        "m.message": [ /* ... */ ],
    }
    // irrelevant fields not shown, like `sender`
}
```

Clients which know how to render `m.sticker` events will pick out the details from the
other events in `content`, showing a sticker, and clients which do not know how stickers
are supposed to be rendered will show an image, file, or message (typically) in its
place.

To reiterate: events *do not* need to be extensible. Events such as power levels,
membership, join rules, etc don't have significant meaning to be rendered in the timeline
by a client and thus are not touched by this proposal.

For clarity, an extensible event can only describe one logical piece of information,
just like events today. It is best to consider a reusable event as an alternative
representation or rendering of the primary event type rather than as containers of
information. An illegal extensible event (in terms of MSC process) would be something
which doesn't represent a single thing, like an event which tries to describe an image
and temperature: these two event types are not directly related to each other and
likely wouldn't make sense if some clients chose to render a temperature and others
an image. If a sender would like to refer a temperature to an image (or whatever),
they can use [event relationships](https://spec.matrix.org/v1.3/client-server-api/#forming-relationships-between-events).

How the client decides to pick reusable event types to render in place of unknown
primary event types is deliberately left as an implementation detail. This MSC suggests
that clients use the following order:

1. All known primary event types not listed in this list.
   * Some events, like [polls](https://github.com/matrix-org/matrix-doc/pull/3381), might not make sense to
     fall back to. Clients should only use types which make sense for their specific application,
     which might typically mean not using this Step 1 at all.
2. `m.video` (from [MSC3553](https://github.com/matrix-org/matrix-doc/pull/3553))
3. `m.audio` / `m.voice` (from [MSC3246](https://github.com/matrix-org/matrix-doc/pull/3246)
   and [MSC3245](https://github.com/matrix-org/matrix-doc/pull/3245))
4. `m.image` (from [MSC3552](https://github.com/matrix-org/matrix-doc/pull/3552))
5. `m.file` (from [MSC3551](https://github.com/matrix-org/matrix-doc/pull/3551))
6. `m.location` (from [MSC3488](https://github.com/matrix-org/matrix-doc/pull/3488))
9. `m.message` (and shortcuts defined by this MSC)
10. Ignore the event

### `m.message`

This proposal **deprecates** `m.room.message` in favour of the new `m.message` described
here, however it's unreasonable to expect that clients will be able to change over fast
enough to not lose history. The full deprecation plan is described later by this proposal.

`m.message` describes text content intended to be represented as a message. Currently in
Matrix, this is a responsibility of the `m.text`, `m.emote`, and `m.notice` `msgtype`s
on `m.room.message` events, which also has support for HTML using `format` and `formatted_body`.

An `m.message` event is an array of *text renderings* for the same message:

```json5
[
    { "mimetype": "text/html", "body": "i am a <strong>fish</strong>" },
    { "mimetype": "text/plain", "body": "i am a fish" }
]
```

The array is preferentially ordered, meaning clients *should* attempt to render the message
using the first known `mimetype`. Clients can still pick a rendering which makes the most
sense for their use-case regardless of order, such as in the case of Element where the client
will hunt for an HTML representation to show even if the plaintext representation is "first".

`mimetype` is optional and defaults to `text/plain`. `body` is simply the text message using
the `mimetype`. The `mimetype` should only be a discrete type from [RFC 6838](https://datatracker.ietf.org/doc/html/rfc6838).
Unknown or multipart `mimetype`s (from the perspective of the client) are simply ignored as
viable renderings.

While not required, all `m.message` events *should* have a `text/plain` rendering. All clients
should be capable of rendering a `text/plain` rendering.

If the client cannot find a suitable rendering (all `mimetype`s are unknown/unrenderable),
or the array is empty, the event is simply ignored by the client.

To cover emotes and notices, `m.emote` and `m.notice` are introduced as primary event types
containing `m.message` as the reusable type:

```json5
{
    "type": "m.emote",
    "content": {
        "m.message": [
            { "mimetype": "text/plain", "body": "is a fish" }
        ]
    }
}
```
```json5
{
    "type": "m.notice",
    "content": {
        "m.message": [
            { "mimetype": "text/plain", "body": "i am a fish that is sending a notice" }
        ]
    }
}
```

To use `m.emote` or `m.notice` as a reusable event type on a custom/other primary event type
the event type can be associated with an empty object:

```json5
{
    "type": "org.example.custom.event",
    "content": {
        "m.text": "is a fish",
        "m.emote": {}, // denotes that this should fall back to an emote, but worst case gets rendered as text
    }
}
```

**Note**: it is technically possible with this structure to have someone send an event that is
both a notice and emote. Given order of preference is a deliberate implementation detail, it is
left to the implementation to determine how it wants to handle this. It might, for example, show
the event as an emote with a bot-like style, or simply as a notice (no emote semantics).

#### Shortcuts

In order to make demonstrating the protocol significantly easier and to help developers/curious
invididuals in understanding what a message event is, two shortcuts are defined: `m.text` and
`m.html`.

These shortcuts are an easier way to describe the `text/plain` and `text/html` mimetypes, as
shown below:

```json5
{
    "type": "m.message",
    "content": {
        "m.text": "i am a fish",
        "m.html": "i am a <strong>fish</strong>"
    }
}
```

If `m.message` is supplied, `m.html` and `m.text` are ignored. If none of the 3 are supplied
then the event should be ignored as unrenderable. When `m.message` isn't supplied, it is
strongly recommended to at least include `m.text`, however `m.html` can appear without `m.text`
present.

**Note**: We specify `m.html` and not other shortcuts because of the prevelance of HTML in
instant messaging communication today. We could in theory add more shortcuts for `m.markdown`
(of some flavour), `m.rtf`, etc however those are not typically transmitted over the wire
in a reliable or common way.

**Note**: We specifically support these shortcuts to ensure that funding for Matrix is not
interrupted due to perceived complexity. While the shortcuts do add technical complexity for
clients, the simplicity of the example shown above helps demonstrate that it's "easy" to
manually send a message into Matrix. Nested objects for "simple" events demonstrates complexity
which can/has affected funding in the past, though are neccessary for the obviously more
complicated event types (such as polls or RTF events).

### Rendering (un)known events

A client's approach to rendering a known event is unchanged: if the primary event type is known, the
client will pick out the details it needs from `content` and render accordingly.

If the primary type is not known, the client should inspect `content` for types it does know and render
the best match. Determining the best match is intentionally left as an implementation detail, as mentioned
previously in this proposal.

Note that this additionally allows clients to fall back gracefully on some event types it might not want
to implement specifically, but still want to support, such as stickers which are effectively images with
largely optional additional rendering requirements.

### Transition

It's simply not feasible to change the entirety of the Matrix ecosystem to a whole new set of events
overnight, so this proposal includes a time-constrained transition period to encourage all client
implementations to update their support for this schema before the ecosystem starts to move forward with
sending the newly-proposed primary event types.

Upon being included in a **released** version of the specification, the following happens:
* `m.room.message` is deprecated **but still used**.
* Clients include the fallback support described below in their outgoing events.
* Clients prefer the extensible/new format in events which include it.
* Clients support the new primary event types, but continue to send `m.room.message` instead.
* A 1 year timer begins for clients to implement the above conditions.
  * This can be shortened if the ecosystem adopts the format sooner.
  * After the (potentially shortened) timer, an MSC is introduced to remove the deprecated `m.room.message`
    event format. Once accepted under the relevant process, clients/implementations start sending the proper
    primary event types instead of `m.room.message`.

Unfortunately, this approach does effectively mean that most clients will have eternal technical debt of
having to support the fallback approach as the vast majority of user-facing clients will want to preserve
the visibility of history before this MSC's introduction. Some clients, like bridges and bots, are likely
able to drop their support for rendering `m.room.message` events as they would have already processed the
older events (or have no reason/desire to backfill in a room).

As a fallback, a client simply smashes `m.room.message` together with the relevant event contents:

```json5
{
    "type": "m.room.message",
    "content": {
        "msgtype": "m.text",
        "body": "Hello World",
        "format": "org.matrix.custom.html",
        "formatted_body": "<b>Hello</b> World",
        "m.text": "Hello World",
        "m.html": "<b>Hello</b> World"
    }
}
```
or
```json5
{
    "type": "m.room.message",
    "content": {
        "msgtype": "m.text",
        "body": "Hello World",
        "format": "org.matrix.custom.html",
        "formatted_body": "<b>Hello</b> World",
        "m.message": [
            {"mimetype": "text/plain", "body": "Hello world"},
            {"mimetype": "text/html", "body": "<b>Hello world</b>"}
        ]
    }
}
```

A client can infer the intended primary type from the `msgtype` and otherwise engage their fallback process
to try and render unknown `msgtype`s.

Note that this fallback only applies in cases where the `m.room.message` `msgtype` was converted to a dedicated
primary event: new features, or events which don't have a `msgtype`, should send their primary event type instead.
Such an example is [Polls](https://github.com/matrix-org/matrix-doc/pull/3381).

### State events

State events are typically not rendered as they usually contain metadata for the room rather than information for
the historical record, however there are a few cases where rendering a state event might be desirable. Clients are
not required to look for event types in state event contents, though are recommended to do so.

This proposal does not introduce any additional requirement for state events to include these rendering details.

A hypothetical scenario would be a bridge state event that includes `m.text` to say a bridge has been added/edited.

### Encryption

For abundance of clarity, encrypted events are unchanged here. The client prepares a payload (which can
be an extensible event), encrypts it, and sends an `m.room.encrypted` event. The schema of `m.room.encrypted`
is deliberately left unchanged by this proposal.

### Notifications

Currently [push notifications](https://spec.matrix.org/v1.3/client-server-api/#push-notifications)
describe how an event can cause a notification to the user, though it makes the assumption
that there are `m.room.message` events flying around to denote "messages" which can trigger
keyword/mention-style alerts. With extensible events, the same might not be possible as it
relies on understanding how/when the client will render the event to cause notifications.

As such, to reduce the complexity of this proposal it is explicitly deferred to another MSC
on how to handle notifications. More information can be found in the "MSC Dependencies" section
of this MSC.

### Power levels

Similar to notifications, permission to send an extensible event might depend on how the client
chooses to render the event. A solution might be to accept that users can "bypass" power levels
to send events which fall back to illegal types, or potentially some sort of agreement among
clients on how to behave when processing extensible events.

It is worth noting that this is presently an issue with encrypted events.

Due to the complexity of the problem at hand, it is explicitly deferred to another MSC on how
to handle power levels. More information can be found in the "MSC Dependencies" section
of this MSC.

## Potential issues

It's a bit ugly to not know whether a given key in `content` will take a string, object or array.

It's a bit arbitrary as to which fields are allowed lists of fallbacks (eg image thumbnails).

It's a bit ugly that you have to look over the keys of contents to see what types
are present, but better than duplicating this into an explicit `types` list within the
event content (on balance).

We're skipping over defining rules for which fallback combinations to display
(i.e. "display hints") for now; these can be added in a future MSC if needed.
[MSC1225](https://github.com/matrix-org/matrix-doc/issues/1225) contains a proposal for this.

Placing event types at the top level of `content` is a bit unfortunate, particularly
when mixing in `m.room.message` compatibility, though mixes nicely thanks to namespacing.
Potentially conflicting cases in the wild would be namespaced fields, which would get
translated as unknown event types, and thus skipped by the rendering machinery.

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

Implementations wishing to trial the migration ahead of this MSC's inclusion in the spec would
use the unstable prefix mentioned above. A fallen back `m.room.message` example event becomes:

```json5
{
    "type": "m.room.message",
    "content": {
        "msgtype": "m.text",
        "body": "Hello World",
        "format": "org.matrix.custom.html",
        "formatted_body": "<b>Hello</b> World",
        "org.matrix.msc1767.text": "Hello World",
        "org.matrix.msc1767.html": "<b>Hello</b> World"
    }
}
```

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

## MSC Dependencies

Within this proposal are a couple mentions of functionality being deferred to future MSCs,
though it does seem sensible to block this MSC on that functionality existing. The goal of
this MSC is to enter/pass FCP as a nod that the system will work, giving time and room for
discussions around the remaining pieces like power levels and notifications. If for some
reason the discussions around those deferred areas fail, extensible events will convert itself
from "accepted" to "rejected", pending potential revamp/iteration.
