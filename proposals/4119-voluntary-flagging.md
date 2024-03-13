# MSC4119: Voluntary content flagging

When a user on Matrix sends content which violates a room's code of conduct or a server's terms of
service, other users often [report](https://spec.matrix.org/v1.9/client-server-api/#reporting-content)
the event to expediate its removal. Clients typically offer to [ignore](https://spec.matrix.org/v1.9/client-server-api/#ignoring-users)
the sender as well, preventing further events from being shown to the reporter.

Most server implementations of the existing reporting system simply send the report to the server
administrators rather than the accused sender's server or applicable room moderators. This can lead
to some delay in the content being taken down, particularly when it is federated from a non-local
server. This proposal leaves improving the reporting communication line to another MSC, but does aim
to address expediated content removal where it's obvious that the content is against the rules.

With this MSC, when a user reports content they *should* be presented with an option to disclose to
the room that they submitted a report. Ideally, these disclosures would protect the sender's identity
to avoid targeted abuse, but for now this is left to a future MSC. Contributors for such a feature
should consider revealing the sender's identity to moderators to reduce abuse of the system.

This MSC's proposed system can additionally be expanded to social media use cases, similar to Twitter's
[Community Notes](https://en.wikipedia.org/wiki/Community_Notes) feature. For now, the added context
from this MSC is rather mechanical to suggest that other clients hide or blur the content.

## Proposal

Mentioned in the introduction, when a user reports content, their client should offer them an ability
to disclose to the room that a report was submitted. This is done by sending an `m.room.context` event
into the room, referencing the reported content. Clients may wish to consider requiring the user to
ignore the event sender as well, preventing retaliation until anonymous event sending is possible.

An `m.room.context` event looks similar to the following:

```jsonc
{
  // unused fields elided
  "type": "m.room.context",
  "content": {
    "m.relates_to": {
      "event_id": "$reported",
      "rel_type": "m.reference"
    },
    "m.flags": [
      // Flags are borrowed from MSC0001: Report reasons
      // TODO: Publish MSC0001
      "m.spam",
      "org.example.custom"
    ]
  }
}
```

`m.relates_to` is a standard [reference relation](https://spec.matrix.org/v1.9/client-server-api/#reference-relations)
to the reported event, or event which is getting context appended to it. `m.flags` acts as an
[Extensible Events Content Block](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/1767-extensible-events.md)
to allow for future expansion of the event, such as including text context akin to a Twitter Community
Note.

Clients can then make decisions based on the `m.room.context` events it sees. How the client processes
these data points is left as an implementation detail, though a suggested approach is:

* If several people append the same flag to an event, the event should be minimized or have a click
  barrier to prevent the content from being immediately accessible. The sender's avatar should additionally
  be blurred, and display name/user ID hidden if possible. "Several" may be defined as a percentage
  of room members in small-medium sized rooms, or 10+ senders in larger rooms.
* If a "trusted" user flags content, the client applies the above actions immediately without waiting
  for further confirmation. If the sender is partially trusted, the client may require a couple more
  confirmations before actually minimizing the content. "Trusted" has a range of values:

  * Untrusted - default value.
  * Partially trusted - sender has a DM with the user.
  * Trusted - user has explicitly listed the sender as a trusted person, or has cross-sign verified
    the user.

Through use of a future MSC, clients may also incorporate feedback about an `m.room.context` event
into their decision tree for when to minimize content. For example, poorly rated context events reduce
the chances of content being minimized.

Clients SHOULD NOT send `m.room.context` events until after a `/report` is sent. This is to ensure
that the content is at least reported to someone, and is more applicable when a revamped reporting
system is in place.

## Potential issues

As previously mentioned, this approach discloses who reported who to the whole room. While this is
helpful for other users to minimize content, it can result in targeted abuse or retaliation towards
the reporter. Clients are strongly encouraged to require the user to [ignore](https://spec.matrix.org/v1.9/client-server-api/#ignoring-users)
who they report to prevent the spread of the targeted abuse. In future, an MSC should be written to
permit anonymous events, thus hiding the sender. To prevent abuse of the system (ie: constantly flagging
everyone's events), senders should be disclosed to moderators but not other members of the room, if
possible. Note that this has its own privacy concerns, such as moderators (un)intentionally revealing
who is reporting who to non-moderators, thus resulting in targeted abuse again.

## Alternatives

[MSC3531](https://github.com/matrix-org/matrix-spec-proposals/pull/3531) is currently the major
alternative, though requires moderators to identify the content before the (typically) larger community
does.

Another alternative may be to expand [policy lists](https://spec.matrix.org/v1.9/client-server-api/#moderation-policy-lists)
to include event IDs, thus allowing clients (and users) to subscribe to "feeds" from trusted sources
and hide/minimize content accordingly.

## Security considerations

See potential issues. There are privacy concerns here.

## Unstable prefix

While this proposal is not considered stable, implementations should use `org.matrix.msc4119.room.context`
and `org.matrix.msc4119.flags` over the stable identifiers.

## Dependencies

This MSC has a soft dependency on MSC0001: Report reasons.
// TODO: Publish MSC0001
