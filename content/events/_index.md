---
title: "Events spec"
weight: 15
type: docs
---

Rooms in Matrix consist of a set of events.

FIXME: ...

This specification outlines several standard event types, all of which
are prefixed with `m.`

{{% boxes/warning %}}
The format of events can change depending on room version. Check the
[room version specification](/rooms) for specific
details on what to expect for event formats. Examples contained within
the client-server specification are expected to be compatible with all
specified room versions, however some differences may still apply.

For this version of the specification, clients only need to worry about
the event ID format being different depending on room version. Clients
should not be parsing the event ID, and instead be treating it as an
opaque string. No changes should be required to support the currently
available room versions.
{{% /boxes/warning %}}

{{% boxes/warning %}}
Event bodies are considered untrusted data. This means that any application using
Matrix must validate that the event body is of the expected shape/schema
before using the contents verbatim.

**It is not safe to assume that an event body will have all the expected
fields of the expected types.**

See [MSC2801](https://github.com/matrix-org/matrix-doc/pull/2801) for more
detail on why this assumption is unsafe.
{{% /boxes/warning %}}

## General event format

### Types of room events

Room events are split into two categories:

* **State events**: These are events which update the metadata state of the room (e.g. room
topic, room membership etc). State is keyed by a tuple of event `type`
and a `state_key`. State in the room with the same key-tuple will be
overwritten.

* **Message events**: These are events which describe transient "once-off" activity in a room:
typically communication such as sending an instant message or setting up
a VoIP call.

This specification outlines several events, all with the event type
prefix `m.`. (See [Room Events](#room-events) for the m. event
specification.) However, applications may wish to add their own type of
event, and this can be achieved using the REST API detailed in the
following sections. If new events are added, the event `type` key SHOULD
follow the Java package naming convention, e.g.
`com.example.myapp.event`. This ensures event types are suitably
namespaced for each application and reduces the risk of clashes.

{{% boxes/note %}}
Events are not limited to the types defined in this specification. New
or custom event types can be created on a whim using the Java package
naming convention. For example, a `com.example.game.score` event can be
sent by clients and other clients would receive it through Matrix,
assuming the client has access to the `com.example` namespace.
{{% /boxes/note %}}

Note that the structure of these events may be different than those in
the server-server API.

#### Event fields

{{% event-fields event_type="event" %}}

#### Room event fields

{{% event-fields event_type="room_event" %}}

#### State event fields

In addition to the fields of a Room Event, State Events have the
following field:

| Key          | Type         | Description                                                                                                  |
|--------------|--------------|--------------------------------------------------------------------------------------------------------------|
| state_key    | string       | **Required.** A unique key which defines the overwriting semantics for this piece of room state. This value is often a zero-length string. The presence of this key makes this event a State Event. State keys starting with an `@` are reserved for referencing user IDs, such as room members. With the exception of a few events, state events set with a given user's ID as the state key MUST only be set by that user.         |

### Size limits

The complete event MUST NOT be larger than 65536 bytes, when formatted
as a [PDU for the Server-Server
protocol](/server-server-api/#pdus), including any
signatures, and encoded as [Canonical
JSON](/appendices#canonical-json).

There are additional restrictions on sizes per key:

-   `sender` MUST NOT exceed 255 bytes (including domain).
-   `room_id` MUST NOT exceed 255 bytes.
-   `state_key` MUST NOT exceed 255 bytes.
-   `type` MUST NOT exceed 255 bytes.
-   `event_id` MUST NOT exceed 255 bytes.

Some event types have additional size restrictions which are specified
in the description of the event. Additional keys have no limit other
than that implied by the total 64 KiB limit on events.

## Core events

Core events are events that affect the core functionality of Matrix, such as
controlling who can send messages to rooms.

### Room creation

{{% event event="m.room.create" %}}

### Room permissions and membership

Several state events control who is in a room and who is allowed to see or send
events to a room.

{{% event event="m.room.member" %}}

{{% event event="m.room.power_levels" %}}

{{% event event="m.room.join_rules" %}}

{{% event event="m.room.guest_access" %}}

#### Room History Visibility

This event controls the visibility of previous events in a room.

In all cases except `world_readable`, a user needs to join a room to
view events in that room. Once they have joined a room, they will gain
access to a subset of events in the room. How this subset is chosen is
controlled by the `m.room.history_visibility` event outlined below.
After a user has left a room, they may see any events which they were
allowed to see before they left the room, but no events received after
they left.

The four options for the `m.room.history_visibility` event are:

-   `world_readable` - All events while this is the
    `m.room.history_visibility` value may be shared by any participating
    homeserver with anyone, regardless of whether they have ever joined
    the room.
-   `shared` - Previous events are always accessible to newly joined
    members. All events in the room are accessible, even those sent when
    the member was not a part of the room.
-   `invited` - Events are accessible to newly joined members from the
    point they were invited onwards. Events stop being accessible when
    the member's state changes to something other than `invite` or
    `join`.
-   `joined` - Events are accessible to newly joined members from the
    point they joined the room onwards. Events stop being accessible
    when the member's state changes to something other than `join`.

{{% boxes/warning %}}
These options are applied at the point an event is *sent*. Checks are
performed with the state of the `m.room.history_visibility` event when
the event in question is added to the DAG. This means clients cannot
retrospectively choose to show or hide history to new users if the
setting at that time was more restrictive.
{{% /boxes/warning %}}

{{% event event="m.room.history_visibility" %}}

##### Client behaviour

Clients may want to display a notice that their events may be read by
non-joined people if the value is set to `world_readable`.

##### Server behaviour

By default if no `history_visibility` is set, or if the value is not
understood, the visibility is assumed to be `shared`. The rules
governing whether a user is allowed to see an event depend on the state
of the room *at that event*.

1.  If the `history_visibility` was set to `world_readable`, allow.
2.  If the user's `membership` was `join`, allow.
3.  If `history_visibility` was set to `shared`, and the user joined the
    room at any point after the event was sent, allow.
4.  If the user's `membership` was `invite`, and the
    `history_visibility` was set to `invited`, allow.
5.  Otherwise, deny.

For `m.room.history_visibility` events themselves, the user should be
allowed to see the event if the `history_visibility` before *or* after
the event would allow them to see it. (For example, a user should be
able to see `m.room.history_visibility` events which change the
`history_visibility` from `world_readable` to `joined` *or* from
`joined` to `world_readable`, even if that user was not a member of the
room.)

Likewise, for the user's own `m.room.member` events, the user should be
allowed to see the event if their `membership` before *or* after the
event would allow them to see it. (For example, a user can always see
`m.room.member` events which set their membership to `join`, or which
change their membership from `join` to any other value, even if
`history_visibility` is `joined`.)

##### Security considerations

The default value for `history_visibility` is `shared` for
backwards-compatibility reasons. Clients need to be aware that by not
setting this event they are exposing all of their room history to anyone
in the room.

#### Server Access Control Lists (ACLs) for rooms

In some scenarios room operators may wish to prevent a malicious or
untrusted server from participating in their room. Sending an
[m.room.server\_acl](#mroomserver_acl) state event into a room is an effective way to
prevent the server from participating in the room at the federation
level.

Server ACLs can also be used to make rooms only federate with a limited
set of servers, or retroactively make the room no longer federate with
any other server, similar to setting the `m.federate` value on the
[m.room.create](#mroomcreate) event.

{{% event event="m.room.server_acl" %}}

{{% boxes/note %}}
Port numbers are not supported because it is unclear to parsers whether
a port number should be matched or an IP address literal. Additionally,
it is unlikely that one would trust a server running on a particular
domain's port but not a different port, especially considering the
server host can easily change ports.
{{% /boxes/note %}}

{{% boxes/note %}}
CIDR notation is not supported for IP addresses because Matrix does not
encourage the use of IPs for identifying servers. Instead, a blanket
`allow_ip_literals` is provided to cover banning them.
{{% /boxes/note %}}

##### Client behaviour

Clients are not expected to perform any additional duties beyond sending
the event. Clients should describe changes to the server ACLs to the
user in the user interface, such as in the timeline.

Clients may wish to kick affected users from the room prior to denying a
server access to the room to help prevent those servers from
participating and to provide feedback to the users that they have been
excluded from the room.

##### Server behaviour

Servers MUST prevent blacklisted servers from sending events or
participating in the room when an [m.room.server\_acl](#mroomserver_acl) event is
present in the room state. Which APIs are specifically affected are
described in the Server-Server API specification.

Servers should still send events to denied servers if they are still
residents of the room.

##### Security considerations

Server ACLs are only effective if every server in the room honours them.
Servers that do not honour the ACLs may still permit events sent by
denied servers into the room, leaking them to other servers in the room.
To effectively enforce an ACL in a room, the servers that do not honour
the ACLs should be denied in the room as well.

### Redactions

Redactions modify events by removing certain properties.  For more information,
see the [Client-Server API](/client-server-api/#redactions).

{{% event event="m.room.redaction" %}}

## Instant Messaging

Several events are used in an instant messaging context.  In addition to
`m.room.message` event type for sending messages, other events are used to
improve user experience, for example by allowing users to set room names and
avatars.

### Room information

{{% event event="m.room.name" %}}

{{% event event="m.room.topic" %}}

{{% event event="m.room.avatar" %}}

{{% event event="m.room.pinned_events" %}}

{{% event event="m.room.canonical_alias" %}}

### Messages

{{% event event="m.room.message" %}}

Each [m.room.message](#m.room.message) MUST have a `msgtype` key which identifies the
type of message being sent. Each type has their own required and
optional keys, as outlined below. If a client cannot display the given
`msgtype` then it SHOULD display the fallback plain text `body` key
instead.

#### Textual messages

{{% event event="m.room.message$m.text" %}}
{{% event event="m.room.message$m.emote" %}}
{{% event event="m.room.message$m.notice" %}}

#### Files

{{% event event="m.room.message$m.file" %}}
{{% event event="m.room.message$m.image" %}}
{{% event event="m.room.message$m.audio" %}}

#### Other

{{% event event="m.room.message$m.location" %}}

#### Rich text

Some message types support HTML in the event content that clients should
prefer to display if available. Currently `m.text`, `m.emote`, and
`m.notice` support an additional `format` parameter of
`org.matrix.custom.html`. When this field is present, a `formatted_body`
with the HTML must be provided. The plain text version of the HTML
should be provided in the `body`.

Clients should limit the HTML they render to avoid Cross-Site Scripting,
HTML injection, and similar attacks. The strongly suggested set of HTML
tags to permit, denying the use and rendering of anything else, is:
`font`, `del`, `h1`, `h2`, `h3`, `h4`, `h5`, `h6`, `blockquote`, `p`,
`a`, `ul`, `ol`, `sup`, `sub`, `li`, `b`, `i`, `u`, `strong`, `em`,
`strike`, `code`, `hr`, `br`, `div`, `table`, `thead`, `tbody`, `tr`,
`th`, `td`, `caption`, `pre`, `span`, `img`, `details`, `summary`.

Not all attributes on those tags should be permitted as they may be
avenues for other disruption attempts, such as adding `onclick` handlers
or excessively large text. Clients should only permit the attributes
listed for the tags below. Where `data-mx-bg-color` and `data-mx-color`
are listed, clients should translate the value (a 6-character hex color
code) to the appropriate CSS/attributes for the tag.

`font`
`data-mx-bg-color`, `data-mx-color`, `color`

`span`
`data-mx-bg-color`, `data-mx-color`, `data-mx-spoiler` (see
[spoiler messages](#spoiler-messages))

`a`
`name`, `target`, `href` (provided the value is not relative and has a
scheme matching one of: `https`, `http`, `ftp`, `mailto`, `magnet`)

`img`
`width`, `height`, `alt`, `title`, `src` (provided it is a [Matrix
Content (MXC) URI](#matrix-content-mxc-uris))

`ol`
`start`

`code`
`class` (only classes which start with `language-` for syntax
highlighting)

Additionally, web clients should ensure that *all* `a` tags get a
`rel="noopener"` to prevent the target page from referencing the
client's tab/window.

Tags must not be nested more than 100 levels deep. Clients should only
support the subset of tags they can render, falling back to other
representations of the tags where possible. For example, a client may
not be able to render tables correctly and instead could fall back to
rendering tab-delimited text.

In addition to not rendering unsafe HTML, clients should not emit unsafe
HTML in events. Likewise, clients should not generate HTML that is not
needed, such as extra paragraph tags surrounding text due to Rich Text
Editors. HTML included in events should otherwise be valid, such as
having appropriate closing tags, appropriate attributes (considering the
custom ones defined in this specification), and generally valid
structure.

A special tag, `mx-reply`, may appear on rich replies (described below)
and should be allowed if, and only if, the tag appears as the very first
tag in the `formatted_body`. The tag cannot be nested and cannot be
located after another tag in the tree. Because the tag contains HTML, an
`mx-reply` is expected to have a partner closing tag and should be
treated similar to a `div`. Clients that support rich replies will end
up stripping the tag and its contents and therefore may wish to exclude
the tag entirely.

{{% boxes/note %}}
A future iteration of the specification will support more powerful and
extensible message formatting options, such as the proposal
[MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767).
{{% /boxes/note %}}

##### Client behaviour

Clients SHOULD verify the structure of incoming events to ensure that
the expected keys exist and that they are of the right type. Clients can
discard malformed events or display a placeholder message to the user.
Redacted `m.room.message` events MUST be removed from the client. This
can either be replaced with placeholder text (e.g. "\[REDACTED\]") or
the redacted message can be removed entirely from the messages view.

Events which have attachments (e.g. `m.image`, `m.file`) SHOULD be
uploaded using the [content repository module](/client-server-api/#content-repository)
where available. The resulting `mxc://` URI can then be used in the `url`
key.

Clients MAY include a client generated thumbnail image for an attachment
under a `info.thumbnail_url` key. The thumbnail SHOULD also be a
`mxc://` URI. Clients displaying events with attachments can either use
the client generated thumbnail or ask its homeserver to generate a
thumbnail from the original attachment using the [content repository
module](/client-server-api/#content-repository).

#### Rich replies

In some cases, events may wish to reference other events. This could be
to form a thread of messages for the user to follow along with, or to
provide more context as to what a particular event is describing.
Currently, the only kind of relation defined is a "rich reply" where a
user may reference another message to create a thread-like conversation.

Relationships are defined under an `m.relates_to` key in the event's
`content`. If the event is of the type `m.room.encrypted`, the
`m.relates_to` key MUST NOT be covered by the encryption and instead be
put alongside the encryption information held in the `content`.

A rich reply is formed through use of an `m.relates_to` relation for
`m.in_reply_to` where a single key, `event_id`, is used to reference the
event being replied to. The referenced event ID SHOULD belong to the
same room where the reply is being sent. Clients should be cautious of
the event ID belonging to another room, or being invalid entirely. Rich
replies can only be constructed in the form of `m.room.message` events
with a `msgtype` of `m.text` or `m.notice`. Due to the fallback
requirements, rich replies cannot be constructed for types of `m.emote`,
`m.file`, etc. Rich replies may reference any other `m.room.message`
event, however. Rich replies may reference another event which also has
a rich reply, infinitely.

An `m.in_reply_to` relationship looks like the following:

```
{
  ...
  "type": "m.room.message",
  "content": {
    "msgtype": "m.text",
    "body": "<body including fallback>",
    "format": "org.matrix.custom.html",
    "formatted_body": "<HTML including fallback>",
    "m.relates_to": {
      "m.in_reply_to": {
        "event_id": "$another:event.com"
      }
    }
  }
}
```

##### Fallbacks for rich replies

Some clients may not have support for rich replies and therefore need a
fallback to use instead. Clients that do not support rich replies should
render the event as if rich replies were not special.

Clients that do support rich replies MUST provide the fallback format on
replies, and MUST strip the fallback before rendering the reply. Rich
replies MUST have a `format` of `org.matrix.custom.html` and therefore a
`formatted_body` alongside the `body` and appropriate `msgtype`. The
specific fallback text is different for each `msgtype`, however the
general format for the `body` is:

    > <@alice:example.org> This is the original body

    This is where the reply goes

The `formatted_body` should use the following template:

    <mx-reply>
      <blockquote>
        <a href="https://matrix.to/#/!somewhere:example.org/$event:example.org">In reply to</a>
        <a href="https://matrix.to/#/@alice:example.org">@alice:example.org</a>
        <br />
        <!-- This is where the related event's HTML would be. -->
      </blockquote>
    </mx-reply>
    This is where the reply goes.

If the related event does not have a `formatted_body`, the event's
`body` should be considered after encoding any HTML special characters.
Note that the `href` in both of the anchors use a [matrix.to
URI](/appendices#matrixto-navigation).

###### Stripping the fallback

Clients which support rich replies MUST strip the fallback from the
event before rendering the event. This is because the text provided in
the fallback cannot be trusted to be an accurate representation of the
event. After removing the fallback, clients are recommended to represent
the event referenced by `m.in_reply_to` similar to the fallback's
representation, although clients do have creative freedom for their user
interface. Clients should prefer the `formatted_body` over the `body`,
just like with other `m.room.message` events.

To strip the fallback on the `body`, the client should iterate over each
line of the string, removing any lines that start with the fallback
prefix ("&gt; ", including the space, without quotes) and stopping when
a line is encountered without the prefix. This prefix is known as the
"fallback prefix sequence".

To strip the fallback on the `formatted_body`, the client should remove
the entirety of the `mx-reply` tag.

###### Fallback for `m.text`, `m.notice`, and unrecognised message types

Using the prefix sequence, the first line of the related event's `body`
should be prefixed with the user's ID, followed by each line being
prefixed with the fallback prefix sequence. For example:

    > <@alice:example.org> This is the first line
    > This is the second line

    This is the reply

The `formatted_body` uses the template defined earlier in this section.

###### Fallback for `m.emote`

Similar to the fallback for `m.text`, each line gets prefixed with the
fallback prefix sequence. However an asterisk should be inserted before
the user's ID, like so:

    > * <@alice:example.org> feels like today is going to be a great day

    This is the reply

The `formatted_body` has a subtle difference for the template where the
asterisk is also inserted ahead of the user's ID:

    <mx-reply>
      <blockquote>
        <a href="https://matrix.to/#/!somewhere:example.org/$event:example.org">In reply to</a>
        * <a href="https://matrix.to/#/@alice:example.org">@alice:example.org</a>
        <br />
        <!-- This is where the related event's HTML would be. -->
      </blockquote>
    </mx-reply>
    This is where the reply goes.

###### Fallback for `m.image`, `m.video`, `m.audio`, and `m.file`

The related event's `body` would be a file name, which may not be very
descriptive. The related event should additionally not have a `format`
or `formatted_body` in the `content` - if the event does have a `format`
and/or `formatted_body`, those fields should be ignored. Because the
filename alone may not be descriptive, the related event's `body` should
be considered to be `"sent a file."` such that the output looks similar
to the following:

    > <@alice:example.org> sent a file.

    This is the reply

    <mx-reply>
      <blockquote>
        <a href="https://matrix.to/#/!somewhere:example.org/$event:example.org">In reply to</a>
        <a href="https://matrix.to/#/@alice:example.org">@alice:example.org</a>
        <br />
        sent a file.
      </blockquote>
    </mx-reply>
    This is where the reply goes.

For `m.image`, the text should be `"sent an image."`. For `m.video`, the
text should be `"sent a video."`. For `m.audio`, the text should be
`"sent an audio file"`.

#### Spoiler messages

{{% added-in v="1.1" %}}

Parts of a message can be hidden visually from the user through use of spoilers.
This does not affect the server's representation of the event content - it
is simply a visual cue to the user that the message may reveal important
information about something, spoiling any relevant surprise.

To send spoilers clients MUST use the `formatted_body` and therefore the
`org.matrix.custom.html` format, described above. This makes spoilers valid on
any `msgtype` which can support this format appropriately.

Spoilers themselves are contained with `span` tags, with the reason (optionally)
being in the `data-mx-spoiler` attribute. Spoilers without a reason must at least
specify the attribute, though the value may be empty/undefined.

An example of a spoiler is:

```json
{
  "msgtype": "m.text",
  "format": "org.matrix.custom.html",
  "body": "Alice [Spoiler](mxc://example.org/abc123) in the movie.",
  "formatted_body": "Alice <span data-mx-spoiler>lived happily ever after</span> in the movie."
}
```

If a reason were to be supplied, it would look like:

```json
{
  "msgtype": "m.text",
  "format": "org.matrix.custom.html",
  "body": "Alice [Spoiler for health of Alice](mxc://example.org/abc123) in the movie.",
  "formatted_body": "Alice <span data-mx-spoiler='health of alice'>lived happily ever after</span> in the movie."
}
```

When sending a spoiler, clients SHOULD provide the plain text fallback in the `body`
as shown above (including the reason). The fallback SHOULD omit the spoiler text verbatim
since `body` might show up in text-only clients or in notifications. To prevent spoilers
showing up in such situations, clients are strongly encouraged to first upload the plaintext
to the media repository then reference the MXC URI in a markdown-style link, as shown above.

Clients SHOULD render spoilers differently with some sort of disclosure. For example, the
client could blur the actual text and ask the user to click on it for it to be revealed.

#### User, room, and group mentions

This module allows users to mention other users, rooms, and groups
within a room message. This is achieved by including a [matrix.to
URI](/appendices/#matrixto-navigation) in the HTML body of an
[m.room.message](#mroommessage) event. This module does not have any server-specific
behaviour to it.

Mentions apply only to [m.room.message](#mroommessage) events where the `msgtype` is
`m.text`, `m.emote`, or `m.notice`. The `format` for the event must be
`org.matrix.custom.html` and therefore requires a `formatted_body`.

To make a mention, reference the entity being mentioned in the
`formatted_body` using an anchor, like so:

```json
{
    "body": "Hello Alice!",
    "msgtype": "m.text",
    "format": "org.matrix.custom.html",
    "formatted_body": "Hello <a href='https://matrix.to/#/@alice:example.org'>Alice</a>!"
}
```

##### Client behaviour

In addition to using the appropriate `matrix.to URI` for the mention,
clients should use the following guidelines when making mentions in
events to be sent:

-   When mentioning users, use the user's potentially ambiguous display
    name for the anchor's text. If the user does not have a display
    name, use the user's ID.
-   When mentioning rooms, use the canonical alias for the room. If the
    room does not have a canonical alias, prefer one of the aliases
    listed on the room. If no alias can be found, fall back to the room
    ID. In all cases, use the alias/room ID being linked to as the
    anchor's text.
-   When referencing groups, use the group ID as the anchor's text.

The text component of the anchor should be used in the event's `body`
where the mention would normally be represented, as shown in the example
above.

Clients should display mentions differently from other elements. For
example, this may be done by changing the background color of the
mention to indicate that it is different from a normal link.

If the current user is mentioned in a message (either by a mention as
defined in this module or by a push rule), the client should show that
mention differently from other mentions, such as by using a red
background color to signify to the user that they were mentioned.

When clicked, the mention should navigate the user to the appropriate
room, group, or user information.

#### Server behaviour

Homeservers SHOULD reject `m.room.message` events which don't have a
`msgtype` key, or which don't have a textual `body` key, with an HTTP
status code of 400.

### Sticker Messages

Sticker messages are specialised image messages that are displayed
without controls (e.g. no "download" link, or light-box view on click,
as would be displayed for for [m.image](#mimage) events).

Sticker messages are intended to provide simple "reaction" events in the
message timeline. The matrix client should provide some mechanism to
display the sticker "body" e.g. as a tooltip on hover, or in a modal
when the sticker image is clicked.

#### Events

Sticker events are received as a single `m.sticker` event in the
`timeline` section of a room, in a `/sync`.

{{% event event="m.sticker" %}}

#### Client behaviour

Clients supporting this message type should display the image content
from the event URL directly in the timeline.

A thumbnail image should be provided in the `info` object. This is
largely intended as a fallback for clients that do not fully support the
`m.sticker` event type. In most cases it is fine to set the thumbnail
URL to the same URL as the main event content.

It is recommended that sticker image content should be 512x512 pixels in
size or smaller. The dimensions of the image file should be twice the
intended display size specified in the `info` object in order to assist
rendering sharp images on higher DPI screens.

## Voice over IP

This module outlines how two users in a room can set up a Voice over IP
(VoIP) call to each other. Voice and video calls are built upon the
WebRTC 1.0 standard. Call signalling is achieved by sending [message
events](#events) to the room. In this version of the spec, only two-party
communication is supported (e.g. between two peers, or between a peer
and a multi-point conferencing unit). This means that clients MUST only
send call events to rooms with exactly two participants.

### Events

{{% event-group group_name="m.call" %}}

### Client behaviour

A call is set up with message events exchanged as follows:

```
    Caller                    Callee
    [Place Call]
    m.call.invite ----------->
    m.call.candidate -------->
    [..candidates..] -------->
                            [Answers call]
           <--------------- m.call.answer
     [Call is active and ongoing]
           <--------------- m.call.hangup
```

Or a rejected call:

```
    Caller                      Callee
    m.call.invite ------------>
    m.call.candidate --------->
    [..candidates..] --------->
                             [Rejects call]
             <-------------- m.call.hangup
```

Calls are negotiated according to the WebRTC specification.

#### Glare

"Glare" is a problem which occurs when two users call each other at
roughly the same time. This results in the call failing to set up as
there already is an incoming/outgoing call. A glare resolution algorithm
can be used to determine which call to hangup and which call to answer.
If both clients implement the same algorithm then they will both select
the same call and the call will be successfully connected.

As calls are "placed" to rooms rather than users, the glare resolution
algorithm outlined below is only considered for calls which are to the
same room. The algorithm is as follows:

-   If an `m.call.invite` to a room is received whilst the client is
    **preparing to send** an `m.call.invite` to the same room:
    -   the client should cancel its outgoing call and instead
        automatically accept the incoming call on behalf of the user.
-   If an `m.call.invite` to a room is received **after the client has
    sent** an `m.call.invite` to the same room and is waiting for a
    response:
    -   the client should perform a lexicographical comparison of the
        call IDs of the two calls and use the *lesser* of the two calls,
        aborting the greater. If the incoming call is the lesser, the
        client should accept this call on behalf of the user.

The call setup should appear seamless to the user as if they had simply
placed a call and the other party had accepted. This means any media
stream that had been setup for use on a call should be transferred and
used for the call that replaces it.

### Security considerations

Calls should only be placed to rooms with one other user in them. If
they are placed to group chat rooms it is possible that another user
will intercept and answer the call.

## End-to-End Encryption

### Enabling encryption in rooms

Encryption is enabled in a room by sending an `m.room.encryption` state event.
Currently, the only supported algorithm is `m.megolm.v1.aes-sha2`.

{{% event event="m.room.encryption" %}}

### Encrypted events

{{% event event="m.room.encrypted" %}}

#### Messaging Algorithms

##### Messaging Algorithm Names

Messaging algorithm names use the extensible naming scheme used
throughout this specification. Algorithm names that start with `m.` are
reserved for algorithms defined by this specification. Implementations
wanting to experiment with new algorithms must be uniquely globally
namespaced following Java's package naming conventions.

Algorithm names should be short and meaningful, and should list the
primitives used by the algorithm so that it is easier to see if the
algorithm is using a broken primitive.

A name of `m.olm.v1` is too short: it gives no information about the
primitives in use, and is difficult to extend for different primitives.
However a name of
`m.olm.v1.ecdh-curve25519-hdkfsha256.hmacsha256.hkdfsha256-aes256-cbc-hmac64sha256`
is too long despite giving a more precise description of the algorithm:
it adds to the data transfer overhead and sacrifices clarity for human
readers without adding any useful extra information.

##### `m.olm.v1.curve25519-aes-sha2`

The name `m.olm.v1.curve25519-aes-sha2` corresponds to version 1 of the
Olm ratchet, as defined by the [Olm
specification](http://matrix.org/docs/spec/olm.html). This uses:

-   Curve25519 for the initial key agreement.
-   HKDF-SHA-256 for ratchet key derivation.
-   Curve25519 for the root key ratchet.
-   HMAC-SHA-256 for the chain key ratchet.
-   HKDF-SHA-256, AES-256 in CBC mode, and 8 byte truncated HMAC-SHA-256
    for authenticated encryption.

Devices that support Olm must include "m.olm.v1.curve25519-aes-sha2" in
their list of supported messaging algorithms, must list a Curve25519
device key, and must publish Curve25519 one-time keys.

An event encrypted using Olm has the following format:

```json
{
  "type": "m.room.encrypted",
  "content": {
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
```

`ciphertext` is a mapping from device Curve25519 key to an encrypted
payload for that device. `body` is a Base64-encoded Olm message body.
`type` is an integer indicating the type of the message body: 0 for the
initial pre-key message, 1 for ordinary messages.

Olm sessions will generate messages with a type of 0 until they receive
a message. Once a session has decrypted a message it will produce
messages with a type of 1.

When a client receives a message with a type of 0 it must first check if
it already has a matching session. If it does then it will use that
session to try to decrypt the message. If there is no existing session
then the client must create a new session and use the new session to
decrypt the message. A client must not persist a session or remove
one-time keys used by a session until it has successfully decrypted a
message using that session.

Messages with type 1 can only be decrypted with an existing session. If
there is no matching session, the client must treat this as an invalid
message.

The plaintext payload is of the form:

```json
{
  "type": "<type of the plaintext event>",
  "content": "<content for the plaintext event>",
  "sender": "<sender_user_id>",
  "recipient": "<recipient_user_id>",
  "recipient_keys": {
    "ed25519": "<our_ed25519_key>"
  },
  "keys": {
    "ed25519": "<sender_ed25519_key>"
  }
}
```

The type and content of the plaintext message event are given in the
payload.

Other properties are included in order to prevent an attacker from
publishing someone else's curve25519 keys as their own and subsequently
claiming to have sent messages which they didn't. `sender` must
correspond to the user who sent the event, `recipient` to the local
user, and `recipient_keys` to the local ed25519 key.

Clients must confirm that the `sender_key` and the `ed25519` field value
under the `keys` property match the keys returned by [`/keys/query`](/client-server-api/#post_matrixclientv3keysquery) for
the given user, and must also verify the signature of the keys from the
`/keys/query` response. Without this check, a client cannot be sure that
the sender device owns the private part of the ed25519 key it claims to
have in the Olm payload. This is crucial when the ed25519 key corresponds
to a verified device.

If a client has multiple sessions established with another device, it
should use the session from which it last received and successfully
decrypted a message. For these purposes, a session that has not received
any messages should use its creation time as the time that it last
received a message. A client may expire old sessions by defining a
maximum number of olm sessions that it will maintain for each device,
and expiring sessions on a Least Recently Used basis. The maximum number
of olm sessions maintained per device should be at least 4.

###### Recovering from undecryptable messages

Occasionally messages may be undecryptable by clients due to a variety
of reasons. When this happens to an Olm-encrypted message, the client
should assume that the Olm session has become corrupted and create a new
one to replace it.

{{% boxes/note %}}
Megolm-encrypted messages generally do not have the same problem.
Usually the key for an undecryptable Megolm-encrypted message will come
later, allowing the client to decrypt it successfully. Olm does not have
a way to recover from the failure, making this session replacement
process required.
{{% /boxes/note %}}

To establish a new session, the client sends an [m.dummy](#mdummy)
to-device event to the other party to notify them of the new session
details.

Clients should rate-limit the number of sessions it creates per device
that it receives a message from. Clients should not create a new session
with another device if it has already created one for that given device
in the past 1 hour.

Clients should attempt to mitigate loss of the undecryptable messages.
For example, Megolm sessions that were sent using the old session would
have been lost. The client can attempt to retrieve the lost sessions
through `m.room_key_request` messages.

##### `m.megolm.v1.aes-sha2`

The name `m.megolm.v1.aes-sha2` corresponds to version 1 of the Megolm
ratchet, as defined by the [Megolm
specification](http://matrix.org/docs/spec/megolm.html). This uses:

-   HMAC-SHA-256 for the hash ratchet.
-   HKDF-SHA-256, AES-256 in CBC mode, and 8 byte truncated HMAC-SHA-256
    for authenticated encryption.
-   Ed25519 for message authenticity.

Devices that support Megolm must support Olm, and include
"m.megolm.v1.aes-sha2" in their list of supported messaging algorithms.

An event encrypted using Megolm has the following format:

```json
{
  "type": "m.room.encrypted",
  "content": {
    "algorithm": "m.megolm.v1.aes-sha2",
    "sender_key": "<sender_curve25519_key>",
    "device_id": "<sender_device_id>",
    "session_id": "<outbound_group_session_id>",
    "ciphertext": "<encrypted_payload_base_64>"
  }
}
```

The encrypted payload can contain any message event. The plaintext is of
the form:

```json
{
  "type": "<event_type>",
  "content": "<event_content>",
  "room_id": "<the room_id>"
}
```

We include the room ID in the payload, because otherwise the homeserver
would be able to change the room a message was sent in.

Clients must guard against replay attacks by keeping track of the
ratchet indices of Megolm sessions. They should reject messages with a
ratchet index that they have already decrypted. Care should be taken in
order to avoid false positives, as a client may decrypt the same event
twice as part of its normal processing.

As with Olm events, clients must confirm that the `sender_key` belongs
to the user who sent the message. The same reasoning applies, but the
sender ed25519 key has to be inferred from the `keys.ed25519` property
of the event which established the Megolm session.

When creating a Megolm session in a room, clients must share the
corresponding session key using Olm with the intended recipients, so
that they can decrypt future messages encrypted using this session. An
`m.room_key` event is used to do this. Clients must also handle
`m.room_key` events sent by other devices in order to decrypt their
messages.

#### Sending encrypted attachments

When encryption is enabled in a room, files should be uploaded encrypted
on the homeserver.

In order to achieve this, a client should generate a single-use 256-bit
AES key, and encrypt the file using AES-CTR. The counter should be
64-bit long, starting at 0 and prefixed by a random 64-bit
Initialization Vector (IV), which together form a 128-bit unique counter
block.

{{% boxes/warning %}}
An IV must never be used multiple times with the same key. This implies
that if there are multiple files to encrypt in the same message,
typically an image and its thumbnail, the files must not share both the
same key and IV.
{{% /boxes/warning %}}

Then, the encrypted file can be uploaded to the homeserver. The key and
the IV must be included in the room event along with the resulting
`mxc://` in order to allow recipients to decrypt the file. As the event
containing those will be Megolm encrypted, the server will never have
access to the decrypted file.

A hash of the ciphertext must also be included, in order to prevent the
homeserver from changing the file content.

A client should send the data as an encrypted `m.room.message` event,
using either `m.file` as the msgtype, or the appropriate msgtype for the
file type. The key is sent using the [JSON Web
Key](https://tools.ietf.org/html/rfc7517#appendix-A.3) format, with a
[W3C extension](https://w3c.github.io/webcrypto/#iana-section-jwk).

##### Extensions to `m.room.message` msgtypes

This module adds `file` and `thumbnail_file` properties, of type
`EncryptedFile`, to `m.room.message` msgtypes that reference files, such
as [m.file](#mfile) and [m.image](#mimage), replacing the `url` and `thumbnail_url`
properties.

`EncryptedFile`

| Parameter | Type             | Description                                                                                    |
|-----------|------------------|------------------------------------------------------------------------------------------------|
| url       | string           | **Required.** The URL to the file.                                                             |
| key       | JWK              | **Required.** A [JSON Web Key](https://tools.ietf.org/html/rfc7517#appendix-A.3) object.       |
| iv        | string           | **Required.** The 128-bit unique counter block used by AES-CTR, encoded as unpadded base64.    |
| hashes    | {string: string} | **Required.** A map from an algorithm name to a hash of the ciphertext, encoded as unpadded base64. Clients should support the SHA-256 hash, which uses the key `sha256`. |
| v         | string           | **Required.** Version of the encrypted attachments protocol. Must be `v2`.                     |

`JWK`

| Parameter | Type     | Description                                                                                                              |
| --------- |----------|--------------------------------------------------------------------------------------------------------------------------|
| kty       | string   | **Required.** Key type. Must be `oct`.                                                                                   |
| key_ops   | [string] | **Required.** Key operations. Must at least contain `encrypt` and `decrypt`.                                             |
| alg       | string   | **Required.** Algorithm. Must be `A256CTR`.                                                                              |
| k         | string   | **Required.** The key, encoded as urlsafe unpadded base64.                                                               |
| ext       | boolean  | **Required.** Extractable. Must be `true`. This is a [W3C extension](https://w3c.github.io/webcrypto/#iana-section-jwk). |

Example:

```json
{
  "content": {
    "body": "something-important.jpg",
    "file": {
      "url": "mxc://example.org/FHyPlCeYUSFFxlgbQYZmoEoe",
      "v": "v2",
      "key": {
        "alg": "A256CTR",
        "ext": true,
        "k": "aWF6-32KGYaC3A_FEUCk1Bt0JA37zP0wrStgmdCaW-0",
        "key_ops": ["encrypt","decrypt"],
        "kty": "oct"
      },
      "iv": "w+sE15fzSc0AAAAAAAAAAA",
      "hashes": {
        "sha256": "fdSLu/YkRx3Wyh3KQabP3rd6+SFiKg5lsJZQHtkSAYA"
      }
    },
    "info": {
      "mimetype": "image/jpeg",
      "h": 1536,
      "size": 422018,
      "thumbnail_file": {
        "hashes": {
          "sha256": "/NogKqW5bz/m8xHgFiH5haFGjCNVmUIPLzfvOhHdrxY"
        },
        "iv": "U+k7PfwLr6UAAAAAAAAAAA",
        "key": {
          "alg": "A256CTR",
          "ext": true,
          "k": "RMyd6zhlbifsACM1DXkCbioZ2u0SywGljTH8JmGcylg",
          "key_ops": ["encrypt", "decrypt"],
          "kty": "oct"
        },
        "url": "mxc://example.org/pmVJxyxGlmxHposwVSlOaEOv",
        "v": "v2"
      },
      "thumbnail_info": {
        "h": 768,
        "mimetype": "image/jpeg",
        "size": 211009,
        "w": 432
      },
      "w": 864
    },
    "msgtype": "m.image"
  },
  "event_id": "$143273582443PhrSn:example.org",
  "origin_server_ts": 1432735824653,
  "room_id": "!jEsUZKDJdhlrceRyVU:example.org",
  "sender": "@example:example.org",
  "type": "m.room.message",
  "unsigned": {
      "age": 1234
  }
}
```

### Sending keys

{{% event event="m.room_key" %}}

### Forwarding keys to devices

If Bob has an encrypted conversation with Alice on his computer, and
then logs in through his phone for the first time, he may want to have
access to the previously exchanged messages. To address this issue,
several methods are provided to allow users to transfer keys from one
device to another.

#### Key requests

When a device is missing keys to decrypt messages, it can request the
keys by sending [m.room\_key\_request](#mroom_key_request) to-device messages to other
devices with `action` set to `request`.

If a device wishes to share the keys with that device, it can forward
the keys to the first device by sending an encrypted
[m.forwarded\_room\_key](#mforwarded_room_key) to-device message. The first device should
then send an [m.room\_key\_request](#mroom_key_request) to-device message with `action`
set to `request_cancellation` to the other devices that it had
originally sent the key request to; a device that receives a
`request_cancellation` should disregard any previously-received
`request` message with the same `request_id` and `requesting_device_id`.

If a device does not wish to share keys with that device, it can
indicate this by sending an [m.room\_key.withheld](#mroom_key.withheld) to-device message,
as described in [Reporting that decryption keys are
withheld](#reporting-that-decryption-keys-are-withheld).

{{% boxes/note %}}
Key sharing can be a big attack vector, thus it must be done very
carefully. A reasonable strategy is for a user's client to only send
keys requested by the verified devices of the same user.
{{% /boxes/note %}}

{{% event event="m.room_key_request" %}}

{{% event event="m.forwarded_room_key" %}}

### Reporting that decryption keys are withheld

When sending an encrypted event to a room, a client can optionally
signal to other devices in that room that it is not sending them the
keys needed to decrypt the event. In this way, the receiving client can
indicate to the user why it cannot decrypt the event, rather than just
showing a generic error message.

In the same way, when one device requests keys from another using [Key
requests](#key-requests), the device from which the key is being
requested may want to tell the requester that it is purposely not
sharing the key.

If Alice withholds a megolm session from Bob for some messages in a
room, and then later on decides to allow Bob to decrypt later messages,
she can send Bob the megolm session, ratcheted up to the point at which
she allows Bob to decrypt the messages. If Bob logs into a new device
and uses key sharing to obtain the decryption keys, the new device will
be sent the megolm sessions that have been ratcheted up. Bob's old
device can include the reason that the session was initially not shared
by including a `withheld` property in the `m.forwarded_room_key` message
that is an object with the `code` and `reason` properties from the
`m.room_key.withheld` message.

{{% event event="m.room_key.withheld" %}}

### Device verification

Before Alice sends Bob encrypted data, or trusts data received from him,
she may want to verify that she is actually communicating with him,
rather than a man-in-the-middle. This verification process requires an
out-of-band channel: there is no way to do it within Matrix without
trusting the administrators of the homeservers.

In Matrix, verification works by Alice meeting Bob in person, or
contacting him via some other trusted medium, and using one of the
verification methods defined below to interactively verify Bob's devices.
Alice and Bob may also read aloud their unpadded base64 encoded Ed25519
public key, as returned by `/keys/query`.

Device verification may reach one of several conclusions. For example:

-   Alice may "accept" the device. This means that she is satisfied that
    the device belongs to Bob. She can then encrypt sensitive material
    for that device, and knows that messages received were sent from
    that device.
-   Alice may "reject" the device. She will do this if she knows or
    suspects that Bob does not control that device (or equivalently,
    does not trust Bob). She will not send sensitive material to that
    device, and cannot trust messages apparently received from it.
-   Alice may choose to skip the device verification process. She is not
    able to verify that the device actually belongs to Bob, but has no
    reason to suspect otherwise. The encryption protocol continues to
    protect against passive eavesdroppers.

{{% boxes/note %}}
Once the signing key has been verified, it is then up to the encryption
protocol to verify that a given message was sent from a device holding
that Ed25519 private key, or to encrypt a message so that it may only be
decrypted by such a device. For the Olm protocol, this is documented at
<https://matrix.org/docs/olm_signing.html>.
{{% /boxes/note %}}

#### Key verification framework

Verifying keys manually by reading out the Ed25519 key is not very
user-friendly, and can lead to errors. In order to help mitigate errors,
and to make the process easier for users, some verification methods are
supported by the specification and use messages exchanged by the user's devices
to assist in the verification. The methods all use a common framework
for negotiating the key verification.

Verification messages can be sent either in a room shared by the two parties,
which should be a [direct messaging](#direct-messaging) room between the two
parties, or by using [to-device](#send-to-device-messaging) messages sent
directly between the two devices involved.  In both cases, the messages
exchanged are similar, with minor differences as detailed below. Verifying
between two different users should be performed using in-room messages, whereas
verifying two devices belonging to the same user should be performed using
to-device messages.

A key verification session is identified by an ID that is established by the
first message sent in that session. For verifications using in-room messages,
the ID is the event ID of the initial message, and for verifications using
to-device messages, the first message contains a `transaction_id` field that is
shared by the other messages of that session.

In general, verification operates as follows:

- Alice requests a key verification with Bob by sending an
  `m.key.verification.request` event. This event indicates the verification
  methods that Alice's client supports. (Note that "Alice" and "Bob" may in
  fact be the same user, in the case where a user is verifying their own
  devices.)
- Bob's client prompts Bob to accept the key verification. When Bob accepts
  the verification, Bob's client sends an `m.key.verification.ready` event.
  This event indicates the verification methods, corresponding to the
  verification methods supported by Alice's client, that Bob's client supports.
- Alice's or Bob's devices allow their users to select one of the verification
  methods supported by both devices to use for verification. When Alice or Bob
  selects a verification method, their device begins the verification by
  sending an `m.key.verification.start` event, indicating the selected
  verification method. Note that if there is only one verification method in
  common between the devices then the receiver's device (Bob) can auto-select
  it.
- Alice and Bob complete the verification as defined by the selected
  verification method. This could involve their clients exchanging messages,
  Alice and Bob exchanging information out-of-band, and/or Alice and Bob
  interacting with their devices.
- Alice's and Bob's clients send `m.key.verification.done` events to indicate
  that the verification was successful.

Verifications can be cancelled by either device at any time by sending an
`m.key.verification.cancel` event with a `code` field that indicates the reason
it was cancelled.

When using to-device messages, Alice may not know which of Bob's devices to
verify, or may not want to choose a specific device. In this case, Alice will
send `m.key.verification.request` events to all of Bob's devices. All of these
events will use the same transaction ID. When Bob accepts or declines the
verification on one of his devices (sending either an
`m.key.verification.ready` or `m.key.verification.cancel` event), Alice will
send an `m.key.verification.cancel` event to Bob's other devices with a `code`
of `m.accepted` in the case where Bob accepted the verification, or `m.user` in
the case where Bob rejected the verification. This yields the following
handshake when using to-device messages, assuming both Alice and Bob each have
2 devices, Bob's first device accepts the key verification request, and Alice's
second device initiates the request. Note how Alice's first device is not
involved in the request or verification process. Also note that, although in
this example, Bob's device sends the `m.key.verification.start`, Alice's device
could also send that message. As well, the order of the
`m.key.verification.done` messages could be reversed.

```
    +---------------+ +---------------+                    +-------------+ +-------------+
    | AliceDevice1  | | AliceDevice2  |                    | BobDevice1  | | BobDevice2  |
    +---------------+ +---------------+                    +-------------+ +-------------+
            |                 |                                   |               |
            |                 | m.key.verification.request        |               |
            |                 |---------------------------------->|               |
            |                 |                                   |               |
            |                 | m.key.verification.request        |               |
            |                 |-------------------------------------------------->|
            |                 |                                   |               |
            |                 |          m.key.verification.ready |               |
            |                 |<----------------------------------|               |
            |                 |                                   |               |
            |                 | m.key.verification.cancel         |               |
            |                 |-------------------------------------------------->|
            |                 |                                   |               |
            |                 |          m.key.verification.start |               |
            |                 |<----------------------------------|               |
            |                 |                                   |               |
            .
            .                       (verification messages)
            .
            |                 |                                   |               |
            |                 |           m.key.verification.done |               |
            |                 |<----------------------------------|               |
            |                 |                                   |               |
            |                 | m.key.verification.done           |               |
            |                 |---------------------------------->|               |
            |                 |                                   |               |
```

When using in-room messages and the room has encryption enabled, clients should
ensure that encryption does not hinder the verification. For example, if the
verification messages are encrypted, clients must ensure that all the
recipient's unverified devices receive the keys necessary to decrypt the
messages, even if they would normally not be given the keys to decrypt messages
in the room. Alternatively, verification messages may be sent unencrypted,
though this is not encouraged.

Upon receipt of Alice's `m.key.verification.request` message, if Bob's device
does not understand any of the methods, it should not cancel the request as one
of his other devices may support the request. Instead, Bob's device should tell
Bob that no supported method was found, and allow him to manually reject the
request.

The prompt for Bob to accept/reject Alice's request (or the unsupported method
prompt) should be automatically dismissed 10 minutes after the `timestamp` (in
the case of to-device messages) or `origin_ts` (in the case of in-room
messages) field or 2 minutes after Bob's client receives the message, whichever
comes first, if Bob does not interact with the prompt. The prompt should
additionally be hidden if an appropriate `m.key.verification.cancel` message is
received.

If Bob rejects the request, Bob's client must send an
`m.key.verification.cancel` event with `code` set to `m.user`. Upon receipt,
Alice's device should tell her that Bob does not want to verify her device and,
if the request was sent as a to-device message, send
`m.key.verification.cancel` messages to all of Bob's devices to notify them
that the request was rejected.

If Alice's and Bob's clients both send an `m.key.verification.start` message,
and both specify the same verification method, then the
`m.key.verification.start` message sent by the user whose ID is the
lexicographically largest user ID should be ignored, and the situation should
be treated the same as if only the user with the lexicographically smallest
user ID had sent the `m.key.verification.start` message.  In the case where the
user IDs are the same (that is, when a user is verifying their own device),
then the device IDs should be compared instead.  If the two
`m.key.verification.start` messages do not specify the same verification
method, then the verification should be cancelled with a `code` of
`m.unexpected_message`.

An `m.key.verification.start` message can also be sent independently of any
request, specifying the verification method to use. This behaviour is
deprecated, and new clients should not begin verifications in this way.
However, clients should handle such verifications started by other clients.

Individual verification methods may add additional steps, events, and
properties to the verification messages. Event types for methods defined
in this specification must be under the `m.key.verification` namespace
and any other event types must be namespaced according to the Java
package naming convention.

{{% event event="m.key.verification.request" %}}

{{% event event="m.key.verification.ready" %}}

{{% event event="m.key.verification.start" %}}

{{% event event="m.key.verification.done" %}}

{{% event event="m.key.verification.cancel" %}}

#### Short Authentication String (SAS) verification

SAS verification is a user-friendly key verification process built off
the common framework outlined above. SAS verification is intended to be
a highly interactive process for users, and as such exposes verification
methods which are easier for users to use.

The verification process is heavily inspired by Phil Zimmermann's ZRTP
key agreement handshake. A key part of key agreement in ZRTP is the hash
commitment: the party that begins the Diffie-Hellman key sharing sends a
hash of their part of the Diffie-Hellman exchange, and does not send
their part of the Diffie-Hellman exchange until they have received the
other party's part. Thus an attacker essentially only has one attempt to
attack the Diffie-Hellman exchange, and hence we can verify fewer bits
while still achieving a high degree of security: if we verify n bits,
then an attacker has a 1 in 2<sup>n</sup> chance of success. For
example, if we verify 40 bits, then an attacker has a 1 in
1,099,511,627,776 chance (or less than 1 in 10<sup>12</sup> chance) of
success. A failed attack would result in a mismatched Short
Authentication String, alerting users to the attack.

To advertise support for this method, clients use the name `m.sas.v1` in the
`methods` fields of the `m.key.verification.request` and
`m.key.verification.ready` events.

The verification process takes place in two phases:

1.  Key agreement phase (based on [ZRTP key
    agreement](https://tools.ietf.org/html/rfc6189#section-4.4.1)).
2.  Key verification phase (based on HMAC).

The process between Alice and Bob verifying each other would be:

1.  Alice and Bob establish a secure out-of-band connection, such as
    meeting in-person or a video call. "Secure" here means that either
    party cannot be impersonated, not explicit secrecy.
2.  Alice and Bob begin a key verification using the key verification
    framework as described above.
3.  Alice's device sends Bob's device an `m.key.verification.start`
    message. Alice's device ensures it has a copy of Bob's device key.
4.  Bob's device receives the message and selects a key agreement
    protocol, hash algorithm, message authentication code, and SAS
    method supported by Alice's device.
5.  Bob's device ensures it has a copy of Alice's device key.
6.  Bob's device creates an ephemeral Curve25519 key pair
    (*K<sub>B</sub><sup>private</sup>*, *K<sub>B</sub><sup>public</sup>*),
    and calculates the hash (using the chosen algorithm) of the public
    key *K<sub>B</sub><sup>public</sup>*.
7.  Bob's device replies to Alice's device with an
    `m.key.verification.accept` message.
8.  Alice's device receives Bob's message and stores the commitment hash
    for later use.
9.  Alice's device creates an ephemeral Curve25519 key pair
    (*K<sub>A</sub><sup>private</sup>*, *K<sub>A</sub><sup>public</sup>*)
    and replies to Bob's device with an `m.key.verification.key`,
    sending only the public key
    *K<sub>A</sub><sup>public</sup>*.
10. Bob's device receives Alice's message and replies with its own
    `m.key.verification.key` message containing its public key
    *K<sub>B</sub><sup>public</sup>*.
11. Alice's device receives Bob's message and verifies the commitment
    hash from earlier matches the hash of the key Bob's device just sent
    and the content of Alice's `m.key.verification.start` message.
12. Both Alice and Bob's devices perform an Elliptic-curve
    Diffie-Hellman
    (*ECDH(K<sub>A</sub><sup>private</sup>*, *K<sub>B</sub><sup>public</sup>*)),
    using the result as the shared secret.
13. Both Alice and Bob's devices display a SAS to their users, which is
    derived from the shared key using one of the methods in this
    section. If multiple SAS methods are available, clients should allow
    the users to select a method.
14. Alice and Bob compare the strings shown by their devices, and tell
    their devices if they match or not.
15. Assuming they match, Alice and Bob's devices calculate the HMAC of
    their own device keys and a comma-separated sorted list of the key
    IDs that they wish the other user to verify, using SHA-256 as the
    hash function. HMAC is defined in [RFC
    2104](https://tools.ietf.org/html/rfc2104). The key for the HMAC is
    different for each item and is calculated by generating 32 bytes
    (256 bits) using [the key verification HKDF](#hkdf-calculation).
16. Alice's device sends Bob's device an `m.key.verification.mac`
    message containing the MAC of Alice's device keys and the MAC of her
    key IDs to be verified. Bob's device does the same for Bob's device
    keys and key IDs concurrently with Alice.
17. When the other device receives the `m.key.verification.mac` message,
    the device calculates the HMAC of its copies of the other device's
    keys given in the message, as well as the HMAC of the
    comma-separated, sorted, list of key IDs in the message. The device
    compares these with the HMAC values given in the message, and if
    everything matches then the device keys are verified.
18. Alice and Bob's devices send `m.key.verification.done` messages to complete
    the verification.

The wire protocol looks like the following between Alice and Bob's
devices:

```
    +-------------+                    +-----------+
    | AliceDevice |                    | BobDevice |
    +-------------+                    +-----------+
          |                                 |
          | m.key.verification.start        |
          |-------------------------------->|
          |                                 |
          |       m.key.verification.accept |
          |<--------------------------------|
          |                                 |
          | m.key.verification.key          |
          |-------------------------------->|
          |                                 |
          |          m.key.verification.key |
          |<--------------------------------|
          |                                 |
          | m.key.verification.mac          |
          |-------------------------------->|
          |                                 |
          |          m.key.verification.mac |
          |<--------------------------------|
          |                                 |
```

##### Error and exception handling

At any point the interactive verification can go wrong. The following
describes what to do when an error happens:

-   Alice or Bob can cancel the verification at any time. An
    `m.key.verification.cancel` message must be sent to signify the
    cancellation.
-   The verification can time out. Clients should time out a
    verification that does not complete within 10 minutes. Additionally,
    clients should expire a `transaction_id` which goes unused for 10
    minutes after having last sent/received it. The client should inform
    the user that the verification timed out, and send an appropriate
    `m.key.verification.cancel` message to the other device.
-   When the same device attempts to initiate multiple verification
    attempts, the recipient should cancel all attempts with that device.
-   When a device receives an unknown `transaction_id`, it should send
    an appropriate `m.key.verification.cancel` message to the other
    device indicating as such. This does not apply for inbound
    `m.key.verification.start` or `m.key.verification.cancel` messages.
-   If the two devices do not share a common key share, hash, HMAC, or
    SAS method then the device should notify the other device with an
    appropriate `m.key.verification.cancel` message.
-   If the user claims the Short Authentication Strings do not match,
    the device should send an appropriate `m.key.verification.cancel`
    message to the other device.
-   If the device receives a message out of sequence or that it was not
    expecting, it should notify the other device with an appropriate
    `m.key.verification.cancel` message.

##### Verification messages specific to SAS

Building off the common framework, the following events are involved in
SAS verification.

The `m.key.verification.cancel` event is unchanged, however the
following error codes are used in addition to those already specified:

-   `m.unknown_method`: The devices are unable to agree on the key
    agreement, hash, MAC, or SAS method.
-   `m.mismatched_commitment`: The hash commitment did not match.
-   `m.mismatched_sas`: The SAS did not match.

{{% event event="m.key.verification.start$m.sas.v1" %}}

{{% event event="m.key.verification.accept" %}}

{{% event event="m.key.verification.key" %}}

{{% event event="m.key.verification.mac" %}}

##### HKDF calculation

In all of the SAS methods, HKDF is as defined in [RFC
5869](https://tools.ietf.org/html/rfc5869) and uses the previously
agreed-upon hash function for the hash function. The shared secret is
supplied as the input keying material. No salt is used. When the
`key_agreement_protocol` is `curve25519-hkdf-sha256`, the info parameter
is the concatenation of:

-   The string `MATRIX_KEY_VERIFICATION_SAS|`.
-   The Matrix ID of the user who sent the `m.key.verification.start`
    message, followed by `|`.
-   The Device ID of the device which sent the
    `m.key.verification.start` message, followed by `|`.
-   The public key from the `m.key.verification.key` message sent by
    the device which sent the `m.key.verification.start` message,
    followed by `|`.
-   The Matrix ID of the user who sent the `m.key.verification.accept`
    message, followed by `|`.
-   The Device ID of the device which sent the
    `m.key.verification.accept` message, followed by `|`.
-   The public key from the `m.key.verification.key` message sent by
    the device which sent the `m.key.verification.accept` message,
    followed by `|`.
-   The `transaction_id` being used.

When the `key_agreement_protocol` is the deprecated method `curve25519`,
the info parameter is the concatenation of:

-   The string `MATRIX_KEY_VERIFICATION_SAS`.
-   The Matrix ID of the user who sent the `m.key.verification.start`
    message.
-   The Device ID of the device which sent the
    `m.key.verification.start` message.
-   The Matrix ID of the user who sent the `m.key.verification.accept`
    message.
-   The Device ID of the device which sent the
    `m.key.verification.accept` message.
-   The `transaction_id` being used.

New implementations are discouraged from implementing the `curve25519`
method.

{{% boxes/rationale %}}
HKDF is used over the plain shared secret as it results in a harder
attack as well as more uniform data to work with.
{{% /boxes/rationale %}}

For verification of each party's device keys, HKDF is as defined in RFC
5869 and uses SHA-256 as the hash function. The shared secret is
supplied as the input keying material. No salt is used, and in the info
parameter is the concatenation of:

-   The string `MATRIX_KEY_VERIFICATION_MAC`.
-   The Matrix ID of the user whose key is being MAC-ed.
-   The Device ID of the device sending the MAC.
-   The Matrix ID of the other user.
-   The Device ID of the device receiving the MAC.
-   The `transaction_id` being used.
-   The Key ID of the key being MAC-ed, or the string `KEY_IDS` if the
    item being MAC-ed is the list of key IDs.

##### SAS method: `decimal`

Generate 5 bytes using [HKDF](#hkdf-calculation) then take sequences of 13 bits
to convert to decimal numbers (resulting in 3 numbers between 0 and 8191
inclusive each). Add 1000 to each calculated number.

The bitwise operations to get the numbers given the 5 bytes
*B<sub>0</sub>*, *B<sub>1</sub>*, *B<sub>2</sub>*, *B<sub>3</sub>*, *B<sub>4</sub>*
would be:

-   First: (*B<sub>0</sub>* ≪ 5|*B<sub>1</sub>* ≫ 3) + 1000
-   Second:
    ((*B<sub>1</sub>*&0x7) ≪ 10|*B<sub>2</sub>* ≪ 2|*B<sub>3</sub>* ≫ 6) + 1000
-   Third: ((*B<sub>3</sub>*&0x3F) ≪ 7|*B<sub>4</sub>* ≫ 1) + 1000

The digits are displayed to the user either with an appropriate
separator, such as dashes, or with the numbers on individual lines.

##### SAS method: `emoji`

Generate 6 bytes using [HKDF](#hkdf-calculation) then split the first 42 bits
into 7 groups of 6 bits, similar to how one would base64 encode
something. Convert each group of 6 bits to a number and use the
following table to get the corresponding emoji:

{{% sas-emojis %}}

{{% boxes/note %}}
This table is available as JSON at
<https://github.com/matrix-org/matrix-doc/blob/master/data-definitions/sas-emoji.json>
{{% /boxes/note %}}

{{% boxes/rationale %}}
The emoji above were chosen to:

-   Be recognisable without colour.
-   Be recognisable at a small size.
-   Be recognisable by most cultures.
-   Be distinguishable from each other.
-   Easily described by a few words.
-   Avoid symbols with negative connotations.
-   Be likely similar across multiple platforms.
{{% /boxes/rationale %}}

Clients SHOULD show the emoji with the descriptions from the table, or
appropriate translation of those descriptions. Client authors SHOULD
collaborate to create a common set of translations for all languages.

{{% boxes/note %}}
Known translations for the emoji are available from
<https://github.com/matrix-org/matrix-doc/blob/master/data-definitions/>
and can be translated online:
<https://translate.riot.im/projects/matrix-doc/sas-emoji-v1>
{{% /boxes/note %}}

#### QR codes

{{% added-in v="1.1" %}}

Verifying by QR codes provides a quick way to verify when one of the parties
has a device capable of scanning a QR code. The QR code encodes both parties'
master signing keys as well as a random shared secret that is used to allow
bi-directional verification from a single scan.

To advertise the ability to show a QR code, clients use the names
`m.qr_code.show.v1` and `m.reciprocate.v1` in the `methods` fields of the
`m.key.verification.request` and `m.key.verification.ready` events. To
advertise the ability to scan a QR code, clients use the names
`m.qr_code.scan.v1` and `m.reciprocate.v1` in the `methods` fields of the
`m.key.verification.request` and `m.key.verification.ready` events.
Clients that support both showing and scanning QR codes would advertise
`m.qr_code.show.v1`, `m.qr_code.scan.v1`, and `m.reciprocate.v1` as
methods.

The process between Alice and Bob verifying each other would be:

1. Alice and Bob meet in person, and want to verify each other's keys.
2. Alice and Bob begin a key verification using the key verification
   framework as described above.
3. Alice's client displays a QR code that Bob is able to scan if Bob's client
   indicated the ability to scan, an option to scan Bob's QR code if her client
   is able to scan.  Bob's client prompts displays a QR code that Alice can
   scan if Alice's client indicated the ability to scan, and an option to scan
   Alice's QR code if his client is able to scan. The format for the QR code
   is described below. Other options, like starting SAS Emoji verification,
   can be presented alongside the QR code if the devices have appropriate
   support.
5. Alice scans Bob's QR code.
6. Alice's device ensures that the keys encoded in the QR code match the
   expected values for the keys. If not, Alice's device displays an error
   message indicating that the code is incorrect, and sends a
   `m.key.verification.cancel` message to Bob's device.

   Otherwise, at this point:
   - Alice's device has now verified Bob's key, and
   - Alice's device knows that Bob has the correct key for her.

   Thus for Bob to verify Alice's key, Alice needs to tell Bob that he has the
   right key.
7. Alice's device displays a message saying that the verification was
   successful because the QR code's keys will have matched the keys
   expected for Bob. Bob's device hasn't had a chance to verify Alice's
   keys yet so wouldn't show the same message. Bob will know that
   he has the right key for Alice because Alice's device will have shown
   this message, as otherwise the verification would be cancelled.
8. Alice's device sends an `m.key.verification.start` message with `method` set
   to `m.reciprocate.v1` to Bob (see below).  The message includes the shared
   secret from the QR code.  This signals to Bob's device that Alice has
   scanned Bob's QR code.

   This message is merely a signal for Bob's device to proceed to the next
   step, and is not used for verification purposes.
9. Upon receipt of the `m.key.verification.start` message, Bob's device ensures
   that the shared secret matches.

   If the shared secret does not match, it should display an error message
   indicating that an attack was attempted.  (This does not affect Alice's
   verification of Bob's keys.)

   If the shared secret does match, it asks Bob to confirm that Alice
   has scanned the QR code.
10. Bob sees Alice's device confirm that the key matches, and presses the button
    on his device to indicate that Alice's key is verified.

    Bob's verification of Alice's key hinges on Alice telling Bob the result of
    her scan.  Since the QR code includes what Bob thinks Alice's key is,
    Alice's device can check whether Bob has the right key for her.  Alice has
    no motivation to lie about the result, as getting Bob to trust an incorrect
    key would only affect communications between herself and Bob.  Thus Alice
    telling Bob that the code was scanned successfully is sufficient for Bob to
    trust Alice's key, under the assumption that this communication is done
    over a trusted medium (such as in-person).
11. Both devices send an `m.key.verification.done` message.

##### QR code format

The QR codes to be displayed and scanned using this format will encode binary
strings in the general form:

- the ASCII string `MATRIX`
- one byte indicating the QR code version (must be `0x02`)
- one byte indicating the QR code verification mode.  Should be one of the
  following values:
  - `0x00` verifying another user with cross-signing
  - `0x01` self-verifying in which the current device does trust the master key
  - `0x02` self-verifying in which the current device does not yet trust the
    master key
- the event ID or `transaction_id` of the associated verification
  request event, encoded as:
  - two bytes in network byte order (big-endian) indicating the length in
    bytes of the ID as a UTF-8 string
  - the ID as a UTF-8 string
- the first key, as 32 bytes.  The key to use depends on the mode field:
  - if `0x00` or `0x01`, then the current user's own master cross-signing public key
  - if `0x02`, then the current device's device key
- the second key, as 32 bytes.  The key to use depends on the mode field:
  - if `0x00`, then what the device thinks the other user's master
    cross-signing key is
  - if `0x01`, then what the device thinks the other device's device key is
  - if `0x02`, then what the device thinks the user's master cross-signing key
    is
- a random shared secret, as a byte string.  It is suggested to use a secret
  that is about 8 bytes long.  Note: as we do not share the length of the
  secret, and it is not a fixed size, clients will just use the remainder of
  binary string as the shared secret.

For example, if Alice displays a QR code encoding the following binary string:

```
      "MATRIX"    |ver|mode| len   | event ID
 4D 41 54 52 49 58  02  00   00 2D   21 41 42 43 44 ...
| user's cross-signing key    | other user's cross-signing key | shared secret
  00 01 02 03 04 05 06 07 ...   10 11 12 13 14 15 16 17 ...      20 21 22 23 24 25 26 27
```

this indicates that Alice is verifying another user (say Bob), in response to
the request from event "$ABCD...", her cross-signing key is
`0001020304050607...` (which is "AAECAwQFBg..." in base64), she thinks that
Bob's cross-signing key is `1011121314151617...` (which is "EBESExQVFh..." in
base64), and the shared secret is `2021222324252627` (which is "ICEiIyQlJic" in
base64).

##### Verification messages specific to QR codes

{{% event event="m.key.verification.start$m.reciprocate.v1" %}}

### Other events

{{% event event="m.dummy" %}}

## Moderation policy lists

With Matrix being an open network where anyone can participate, a very
wide range of content exists and it is important that users are
empowered to select which content they wish to see, and which content
they wish to block. By extension, room moderators and server admins
should also be able to select which content they do not wish to host in
their rooms and servers.

The protocol's position on this is one of neutrality: it should not be
deciding what content is undesirable for any particular entity and
should instead be empowering those entities to make their own decisions.
As such, a generic framework for communicating "moderation policy lists"
or "moderation policy rooms" is described. Note that this module only
describes the data structures and not how they should be interpreting:
the entity making the decisions on filtering is best positioned to
interpret the rules how it sees fit.

Moderation policy lists are stored as room state events. There are no
restrictions on how the rooms can be configured (they could be public,
private, encrypted, etc).

There are currently 3 kinds of entities which can be affected by rules:
`user`, `server`, and `room`. All 3 are described with
`m.policy.rule.<kind>` state events. The `state_key` for a policy rule
is an arbitrary string decided by the sender of the rule.

Rules contain recommendations and reasons for the rule existing. The
`reason` is a human-readable string which describes the
`recommendation`. Currently only one recommendation, `m.ban`, is
specified.

### `m.ban` recommendation

When this recommendation is used, the entities affected by the rule
should be banned from participation where possible. The enforcement of
this is deliberately left as an implementation detail to avoid the
protocol imposing its opinion on how the policy list is to be
interpreted. However, a suggestion for a simple implementation is as
follows:

-   Is a `user` rule...
    -   Applied to a user: The user should be added to the subscriber's
        ignore list.
    -   Applied to a room: The user should be banned from the room
        (either on sight or immediately).
    -   Applied to a server: The user should not be allowed to send
        invites to users on the server.
-   Is a `room` rule...
    -   Applied to a user: The user should leave the room and not join
        it
        ([MSC2270](https://github.com/matrix-org/matrix-doc/pull/2270)-style
        ignore).
    -   Applied to a room: No-op because a room cannot ban itself.
    -   Applied to a server: The server should prevent users from
        joining the room and from receiving invites to it.
-   Is a `server` rule...
    -   Applied to a user: The user should not receive events or invites
        from the server.
    -   Applied to a room: The server is added as a denied server in the
        ACLs.
    -   Applied to a server: The subscriber should avoid federating with
        the server as much as possible by blocking invites from the
        server and not sending traffic unless strictly required (no
        outbound invites).

### Subscribing to policy lists

This is deliberately left as an implementation detail. For
implementations using the Client-Server API, this could be as easy as
joining or peeking the room. Joining or peeking is not required,
however: an implementation could poll for updates or use a different
technique for receiving updates to the policy's rules.

### Sharing

In addition to sharing a direct reference to the room which contains the
policy's rules, plain http or https URLs can be used to share links to
the list. When the URL is approached with a `Accept: application/json`
header or has `.json` appended to the end of the URL, it should return a
JSON object containing a `room_uri` property which references the room.
Currently this would be a `matrix.to` URI, however in future it could be
a Matrix-schemed URI instead. When not approached with the intent of
JSON, the service could return a user-friendly page describing what is
included in the ban list.

#### Events

The `entity` described by the state events can contain `*` and `?` to
match zero or more and one or more characters respectively. Note that
rules against rooms can describe a room ID or room alias - the
subscriber is responsible for resolving the alias to a room ID if
desired.

{{% event event="m.policy.rule.user" %}}

{{% event event="m.policy.rule.room" %}}

{{% event event="m.policy.rule.server" %}}

### Client behaviour

As described above, the client behaviour is deliberately left undefined.

### Server behaviour

Servers have no additional requirements placed on them by this module.

### Security considerations

This module could be used to build a system of shared blacklists, which
may create a divide within established communities if not carefully
deployed. This may well not be a suitable solution for all communities.

Depending on how implementations handle subscriptions, user IDs may be
linked to policy lists and therefore expose the views of that user. For
example, a client implementation which joins the user to the policy room
would expose the user's ID to observers of the policy room. In future,
[MSC1228](https://github.com/matrix-org/matrix-doc/pulls/1228) and
[MSC1777](https://github.com/matrix-org/matrix-doc/pulls/1777) (or
similar) could help solve this concern.

## Room upgrades

{{% event event="m.room.tombstone" %}}

## Server Notices

Homeserver hosts often want to send messages to users in an official
capacity, or have resource limits which affect a user's ability to use
the homeserver. For example, the homeserver may be limited to a certain
number of active users per month and has exceeded that limit. To
communicate this failure to users, the homeserver would use the Server
Notices room.

The aesthetics of the room (name, topic, avatar, etc) are left as an
implementation detail. It is recommended that the homeserver decorate
the room such that it looks like an official room to users.

### Events

Notices are sent to the client as normal `m.room.message` events with a
`msgtype` of `m.server_notice` in the server notices room. Events with a
`m.server_notice` `msgtype` outside of the server notice room must be
ignored by clients.

The specified values for `server_notice_type` are:

`m.server_notice.usage_limit_reached`  
The server has exceeded some limit which requires the server
administrator to intervene. The `limit_type` describes the kind of limit
reached. The specified values for `limit_type` are:

`monthly_active_user`  
The server's number of active users in the last 30 days has exceeded the
maximum. New connections are being refused by the server. What defines
"active" is left as an implementation detail, however servers are
encouraged to treat syncing users as "active".

{{% event event="m.room.message$m.server_notice" %}}

### Client behaviour

Clients can identify the server notices room by the `m.server_notice`
tag on the room. Active notices are represented by the [pinned
events](#mroompinned_events) in the server notices room. Server notice
events pinned in that room should be shown to the user through special
UI and not through the normal pinned events interface in the client. For
example, clients may show warning banners or bring up dialogs to get the
user's attention. Events which are not server notice events and are
pinned in the server notices room should be shown just like any other
pinned event in a room.

The client must not expect to be able to reject an invite to join the
server notices room. Attempting to reject the invite must result in a
`M_CANNOT_LEAVE_SERVER_NOTICE_ROOM` error. Servers should not prevent
the user leaving the room after joining the server notices room, however
the same error code must be used if the server will prevent leaving the
room.

### Server behaviour

Servers should manage exactly 1 server notices room per user. Servers
must identify this room to clients with the `m.server_notice` tag.
Servers should invite the target user rather than automatically join
them to the server notice room.

How servers send notices to clients, and which user they use to send the
events, is left as an implementation detail for the server.

## Historical events

Some events within the `m.` namespace might appear in rooms, however
they serve no significant meaning in this version of the specification.
They are:

-   `m.room.aliases`

Previous versions of the specification have more information on these
events.
