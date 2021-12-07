# MSC1767: Extensible events in Matrix

While events are currently JSON blobs which accept additional metadata appended to them,
there is no formal structure for how to represent this information or interpret it on the
client side.

New events also typically reinvent the wheel rather than reuse existing types, such as in
cases where captions, thumbnails, etc need to be considered. This has further issues of
clients not knowing how to render these unknown events, leading to mixed compatibility
within the ecosystem.

The above is seriously hindering uptake of new event types in Matrix - whether that’s
richer data types (stickers, location, calendaring, etc) or IOT-style use cases.
It also means we are currently using an underspecified solution for rich
messaging, as there has never been a previous agreed way of a jury rig solution
for rich messaging as we never previously agreed a way of expressing alternate
formats of displaying the same event.

This proposal introduces a structure for how new events operate and covers the plain
text messaging component of Matrix. Further/future MSCs cover additional functionality
and the remaining messaging components. As of writing, those MSCs are:

* [MSC3488 - Location data](https://github.com/matrix-org/matrix-doc/pull/3488)
* [MSC3381 - Polls](https://github.com/matrix-org/matrix-doc/pull/3381)
* [MSC3245 - Voice messages](https://github.com/matrix-org/matrix-doc/pull/3245)
* [MSC3246 - Audio (non-voice)](https://github.com/matrix-org/matrix-doc/pull/3246)
* [MSC3551 - Files](https://github.com/matrix-org/matrix-doc/pull/3551)
* [MSC3552 - Images and Stickers](https://github.com/matrix-org/matrix-doc/pull/3552)
* [MSC3553 - Videos](https://github.com/matrix-org/matrix-doc/pull/3553)
* [MSC3554 - Translatable text](https://github.com/matrix-org/matrix-doc/pull/3554)

## Proposal

Events continue having a primary type when sending them in Matrix, but the contents
are grouped together into different types. This allows events to easily extend an
event with additional metadata, re-use existing structures, and have the event
renderable on clients which have not special-cased support for the primary type yet.

The names of the keys in the contents are expected to be namespaced, aligned with
event types, though some keys might not be labeled as such for backwards compatibility.

When types are represented as arrays, they are ordered in preference for rendering.
For example, an `m.thumbnail` might have multiple sizes: a client which does not
support/understand thumbnail sizing would use the first available thumbnail rather
than finding the best possible one.

The event types referenced in the event content MUST refer to the same event and
cannot be used to multiplex data into a single event. Relationships between events
are formed with `m.relates_to` and similar structures. For clarity, and as an example,
this means that an image event refers to exactly one image - an album of images can
be represented as a thread/relationship chain of singular images.

Because events are generally sent in the context of a room, all primary types introduced
to the Matrix specification are expected to drop their "room" part. For example, instead
of `m.room.event` the type would be `m.event`. Where features have multiple events, such
as polls, the expectation is that they'll declare a relevant namespace like `m.poll.*`.

### Text messaging

Currently text content can be identified from the `msgtype` on `m.room.message` events:
`m.text`, `m.emote`, and `m.notice` being the values.

All three additionally support HTML through a combination of `format` and `formatted_body`.

When translated to Extensible Events, the primary type now maps to a slightly different
value:
* A `msgtype` of `m.text` would be a primary type of `m.message`
* A `msgtype` of `m.emote` would be a primary type of `m.emote`
* A `msgtype` of `m.notice` would be a primary type of `m.notice`

All 3 primary types have the same event content structure:

```json5
{
    "type": "m.message",
    "content": {
        // short form

        "m.text": "i am a *fish*", // doesn't have to be markdown, but useful as a "fallback" for HTML
        "m.html": "i am a <b>fish</b>"
    }
}
```
```json5
{
    "type": "m.message",
    "content": {
        // longer form

        "m.message": [
            {
                "mimetype": "text/html", // optional, default text/plain
                "body": "i am a <b>fish</b>"
            },
            {
                "mimetype": "text/plain",
                "body": "i am a *fish*" // doesn't have to be markdown, but useful as a "fallback"
            }
        ],
    }
}
```

`m.text` and `m.html` are shortform types used to represent the most common scenarios. In cases
where either `m.text` and `m.html` are specified alongside `m.message`, `m.message` should be
preferred.

For completeness, here are emotes and notices:

```json5
{
    "type": "m.emote",
    "content": {
        "m.text": "is a fish" // note the semantics of the old msgtype are preserved
    }
}
```
```json5
{
    "type": "m.notice",
    "content": {
        "m.text": "I am a bot who does not wish to use normally-styled text"
    }
}
```

### Rendering (un)known events

A client's approach to rendering a known event is unchanged: if the primary event type is known, the
client will pick out the details it needs from `content` and render accordingly.

If the primary type is not known, the client should inspect `content` for types it does know and render
the best match. Determining the best match is intentionally left as an implementation detail, however
clients might wish to use a modified version of the following sequence:

1. All known primary event types not listed in this list.
2. `m.video`
3. `m.audio` / `m.voice`
4. `m.image`
5. `m.file`
6. `m.location`
9. `m.message` (implying `m.text` and `m.html` too)
10. Fail to render due to unrepresentable event

Note that this additionally allows clients to fall back gracefully on some event types it might not want
to implement specifically, but still want to support, such as stickers which are effectively images with
largely optional additional rendering requirements.

To aid clients in their rendering capabilities, all primary event types in the specification include the
relevant types in `content` to fall back as gracefully as possible. Text is generally considered the
minimum for a client to implement.

In the case an event needs to fallback to `m.emote` or `m.notice`, the appropriate type can be included
in the event content as such:

```json5
{
    "type": "org.example.custom.event",
    "content": {
        "m.text": "is a fish",
        "m.emote": {}, // denotes that this should fall back to an emote, but worst case gets rendered as text
    }
}
```

### Transition

It's simply not feasible to change the entirety of the Matrix ecosystem to a whole new set of events
overnight, so this proposal includes a time-constrained transition period to encourage all client
implementations to update their support for this schema before the ecosystem starts to move forward with
sending the newly-proposed primary event types.

Upon being included in a released version of the specification, the following happens:
* `m.room.message` is deprecated **but still used**.
* Clients include the fallback support described below in their outgoing events.
* Clients prefer the new format in events which include it.
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

A client can infer the intended primary type from the `msgtype` and otherwise engage their fallback process
to try and render unknown `msgtype`s.

Note that this fallback only applies in cases where the `m.room.message` `msgtype` was converted to a dedicated
primary event: new features, or events which don't have a `msgtype`, should send their primary event type instead.

### State events

State events are typically not rendered as they usually contain metadata for the room rather than information for
the historical record, however there are a few cases where rendering a state event might be desirable. Clients are
not required to look for event types in state event contents, though are recommended to do so.

This proposal does not introduce any additional requirement for state events to include these rendering details.

A hypothetical scenario would be a bridge state event that includes `m.text` to say a bridge has been added/edited.

### Hypothetical IOT event example

with text fallback:

```json5
{
    "type": "net.arasphere.temperature",
    "content": {
        "m.text": "The temperature is 37C",
        "m.html": "The temperature is <font color='#f00'>37C</font>",
        "net.arasphere.temperature": {
            "temperature": 37.0
        }
    }
}
```

## Potential issues

It's a bit ugly to not know whether a given key will take a string, object or array.

It's a bit arbitrary as to which fields are allowed lists of fallbacks (eg image thumbnails).

It's a bit ugly that you have to look over the keys of contents to see what types
are present, but better than duplicating this into an explicit `types` list (on balance).

We're skipping over defining rules for which fallback combinations to display
(i.e. "display hints") for now; these can be added in a future MSC if needed.
[MSC1225](https://github.com/matrix-org/matrix-doc/issues/1225) contains a proposal for this.

Placing event types at the top level of `content` is a bit unfortunate, particularly
when mixing in `m.room.message` compatibility, though mixes nicely thanks to namespacing.
Potentially conflicting cases in the wild would be namespaced fields, which would get
translated as unknown event types, and thus skipped by the rendering machinery.

## Security considerations

We can't apply ACLs serverside to the types embedded in the event contents.
However, this is inevitable given the existence of E2EE, so we have no choice but
for clients to apply ACLs clientside (e.g. refuse to render an `m.image` contents
on an event if the sender doesn't have enough PL to send an `m.image` event).

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
an `m.text` event would mean sending an `org.matrix.msc1767.text` event instead.


Implementations wishing to trial the migration ahead of this MSC's inclusion in the spec would
use the unstable prefix mentioned above. An fallen back `m.room.message` example event becomes:

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
