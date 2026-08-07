# MSC4460: Extensible Events - Alternative unstable support

[MSC1767 (accepted)](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/1767-extensible-events.md)
outlines a system for rendering unknown event types in clients called "Extensible Events".

The original proposal gates using extensible events (meaning "content blocks") behind a room version
to ensure that clients are not exposed to events they might not be able to render. A previous draft
of the proposal tried to allow `m.room.message` and similar event types to use content blocks, though
that was later removed to discourage long-term use of `m.room.message`.

It's also been over 3 years since the extensible events design was accepted by the Spec Core Team (SCT).
Back in 2023, it was intended to keep momentum moving and land the remainder of the core content block
types. Changes to project priority ended up causing the extensible events MSCs to fall below an activity
threshold, but the intent to land the overall system remains.

Over the last 3 years there's been interest in using extensible events for more functionality, and the
SCT is interested in actually merging proposals like [MSC3381: Polls (accepted)](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/3381-polls.md)
which use extensible events. [MSC3765: Rich topics (merged)](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/3765-rich-room-topics.md)
was able to avoid the room version requirement by coincidentally aligning with MSC1767's structure,
but this isn't always possible to do.

This proposal adjusts the room version requirement in MSC1767 to allow it to (finally) enter the spec
alongside other "core" content block types. Polls are additionally included in the exemption due to
the length of time they've been stuck in the process. Other features, like live location sharing and
voice messages, are *not* exempted because they're blocked in an earlier process stage. Other MSCs
may change the exemption for those proposals.

## Process note

This proposal doesn't actually change anything in the spec itself, but it does introduce a material
change to a couple of MSCs. Such proposals are required to go through the normal spec process to
ensure SCT alignment and agreement on the changes.

Proposal-modifying MSCs are also expected to actually modify the proposals they impact in the same
Github PR to reduce administrative/review load on the SCT. This proposal modifies both MSC1767 and
MSC3381 inline.

Because this proposal doesn't actually change anything in the spec, it can *technically* jump from
`finished-final-comment-period` to `merged`. To avoid confusion in the overall spec process though,
this proposal is expected to mirror the state of MSC1767 after the `finished-final-comment-period`
stage. MSC3381's status is not mirrored in this proposal's state to avoid a situation where either
MSC1767 or MSC3381 moves faster/slower than the other.

If this proposal is put for FCP rejection or postponement, the above does not apply.


## Proposal

Where a content block overlaps with an [`m.room.message` `msgtype`](https://spec.matrix.org/v1.18/client-server-api/#mroommessage-msgtypes),
it MAY appear in `m.room.message` events provided *all* of the following conditions are true:

1. The `body` is an exact match to the `m.text` `text/plain` representation.
2. The `formatted_body` is an exact match to the `m.text` `text/html` representation. If there is
   no `formatted_body`, there MUST NOT be any `m.text` `text/html` representation either.
3. The `url` is an exact match to the [MSC3551 `m.file`](https://github.com/matrix-org/matrix-doc/pull/3551)
   URL. If there is no `url`, there MUST NOT be any `m.file` content block either.
4. Only content blocks which are relevant for the `msgtype` are present. Those are:

   | `msgtype`     | Allowed content blocks |
   |---------------|------------------------|
   | `m.text`      | `m.text`               |
   | `m.emote`     | `m.text`               |
   | `m.notice`    | `m.text`, [MSC3955 `m.automated` mixin](https://github.com/matrix-org/matrix-spec-proposals/pull/3955) |
   | `m.image`[^1] | `m.text`, [MSC3551 `m.file`](https://github.com/matrix-org/matrix-doc/pull/3551), [MSC3552 `m.image_details` and `m.thumbnail`](https://github.com/matrix-org/matrix-doc/pull/3552) |
   | `m.file`[^1]  | `m.text`, [MSC3551 `m.file`](https://github.com/matrix-org/matrix-doc/pull/3551) |
   | `m.audio`[^1] | `m.text`, [MSC3551 `m.file`](https://github.com/matrix-org/matrix-doc/pull/3551), [MSC3927 `m.audio_details`](https://github.com/matrix-org/matrix-spec-proposals/pull/3927) |
   | `m.location`  | `m.text`[^2]           |
   | `m.video`[^1] | `m.text`, [MSC3551 `m.file`](https://github.com/matrix-org/matrix-doc/pull/3551), [MSC3553 `m.video_details` and `m.thumbnail`](https://github.com/matrix-org/matrix-spec-proposals/pull/3553) |

   [^1]: These message types also support `m.caption`, but there is no single MSC which defines what
   `m.caption` is at the moment. If one gets defined, these message types permit `m.caption` too.

   [^2]: Location messages have a few different options, so are limited to only `m.text` content blocks
   for now. This may change in future when one of the location sharing proposals is accepted.

   **Note**: Many of the listed content blocks are *unstable*, therefore requiring prefixed content
   block types.

   All content blocks MUST additionally match their non-content block form. Events MUST have all
   allowed and required content blocks if they use any content blocks. For example, an `m.image`
   message type using the `m.text` content block *must* also have `m.file` and `m.image_details`.
   Those `m.file` and `m.image_details` content blocks *must* further match the `url`, `size`, `mimetype`,
   etc on the `m.room.message` event's `content`.

   For `m.text` content blocks: other representations besides HTML and plain text are permitted,
   provided conditions 1 and 2 above are met.

If any of the above are not met in full, clients MUST NOT use any of the content blocks to render the
event. Clients which are unaware of content blocks automatically do this. This also has the effect
where an `m.room.message` event without any content blocks is rendered normally.

**Note**: Because many of these content blocks are unstable, changes in how those content blocks work
is possible. This proposal matches *intent* rather than precise field location. For example, if `m.file`
becomes named something else then message types which allow `m.file` allow whatever that new name is.
Similarly, if `url` inside `m.file` becomes represented differently, then whatever replaces the old
style `m.room.message` `url` field is used instead.

Similar conditions are applied to the following event types:

* [`m.sticker`](https://spec.matrix.org/v1.18/client-server-api/#msticker) events permit the same
  content blocks as though they are `m.room.message` events with `msgtype: m.image`.
* `m.poll.start`, `m.poll.response`, and `m.poll.end` from MSC3381 permit content blocks as proposed.
* [`m.room.topic`](https://spec.matrix.org/v1.18/client-server-api/#mroomtopic) permits the `m.topic`
  content block (with `m.text` sub-block). This is already the case in the spec, but is listed here
  for clarity.

For all other event types, only unstable content block types are permitted. A room version is still
required to use stable content block types, as per MSC1767. Clients SHOULD NOT render `m.text`,
MSC3551 (files), MSC3552 (images), MSC3553 (videos), MSC3955 (notices), and MSC3927 (audio) content
blocks on non-`m.room.message` event types outside of an extensible events-supporting room version.


## Safety considerations

The measures this proposal takes are intended to deter malicious usage of content blocks where a sender
can potentially show entirely different content to different clients depending on their extensible
events support. By forcing clients to fall back to the legacy fields on these so-called hybrid events,
clients will always show a consistent message to users.



## Potential issues

* For `m.room.message` events, the 4th condition prevents "other" content blocks from appearing on
  those events. In practice, bots and other proposals add all sorts of stuff to the `content` of
  `m.room.message` events such as new `is_animated` flags and ping/pong stats. Having extra data
  doesn't cause the event to be ignored, but does prevent clients from using the content blocks to
  render the event. However, because the `m.text` content blocks *should* be the same as the legacy
  fields, this should be a non-issue.

* Moderation tooling might enforce the conditions on events through redactions, rejections (in the
  case of [policy servers](https://spec.matrix.org/v1.18/client-server-api/#policy-servers)), or
  similar. This is ultimately a choice for individual rooms to make when configuring their moderation
  tooling. Rooms should consider the above potential issue regarding "unknown" (but probably fine)
  fields being present on `m.room.message` events - rejecting an event because it has ping/pong stats
  may be undesirable.


## Alternatives

The major alternative to this is to land the remaining "core" content block types then pursue the
room version outlined by MSC1767. The first part of that is expected to happen regardless of this
proposal's fate, however cutting a room version is non-trivial. There is a logistical challenge
where most/all of the ecosystem needs to gain extensible events support before a switch is flipped
to enable the new room version for everyone. Proposals like [MSC4292](https://github.com/matrix-org/matrix-spec-proposals/pull/4292)
make that easier to do, but risk clients needing to build, test, and support a major shift in how
events are represented on Matrix.

Instead, this proposal aims to expose clients to content blocks in a slow/safe way. Clients will need
to gain an understanding of how content blocks work to determine if they match the legacy event content,
and will have a "known good" state to compare against when rendering an event. Assuming both legacy
and extensible fields match, clients can render both versions of the event to test their extensible
events rendering code.


## Security considerations

The security considerations are the same as the safety considerations in this proposal.


## Unstable prefix

None relevant - this proposal is adjusting the unstable prefix (effectively) for other proposals.


## Dependencies

This proposal requires the following already-accepted MSCs to be accepted:

* [MSC1767 (accepted)](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/1767-extensible-events.md)
* [MSC3381 (accepted)](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/3381-polls.md)
* [MSC3765 (merged)](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/3765-rich-room-topics.md)
