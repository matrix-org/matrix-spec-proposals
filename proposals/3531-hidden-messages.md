
# **MSC3531: Letting moderators hide messages pending review**

Matrix supports **redacting** messages as a mechanism to remove unwanted
content. **Redacting** events, as defined in the Matrix spec, is a mechanism that
entirely removes the content of an event. Users can redact their own events, and
room moderators can redact unwanted events, including illegal content.
At present, there is no manner of **undoing** these redactions.

Historically, redacting messages has been useful for two use cases:

1. a user accidentally posting a password, credit card number or other confidential information,
   in which case the information must be scrubbed as fast as possible from all places;
2. a moderator removing spam, bullying, etc. from a malicious user / spam bot.

Experience shows that redacting messages for case 2. is not always the best solution:

1. moderators make mistakes and there is currently no way for them to fix these;
2. in many cases, it may be desirable for a moderator to quickly hide a message
   before having a conversation with other moderators to determine whether the
   message should be let through (e.g. discussing whether the local room's CoC
   should allow a possibly inflamatory political message - or a newbie moderator
   waiting for experienced moderators to come online to ask them for clarifications
   on borderline content);
3. some bots automatically remove messages based on heuristics (e.g. users sending
   too many messages or too many images) but may get it wrong, in which case the
   moderator currently cannot fix the errors of these bots.

In addition, proposals such as MSC3215, which aims to decentralize moderation,
will very likely increase the number of moderators - and in particular, the
number of moderators who may not be familiar with moderation tools, hence will
make mistakes.

For all these reasons, it would be very useful to have a mechanism that would
let moderators undo their own redactions. Unfortunately, reversing a redaction
is tricky, as we cover in the **Alternatives** section.

Rather, we propose a spec to let moderators *hide messages pending review*. This
mechanism is entirely client-based and will not prevent hidden messages
from being distributed, only from being seen by non-moderator users. This spec
can then be used by clients or bots such as Mjölnir to implement two phase
redaction:
   1. a first phase during which messages are flagged for moderation (either by
      a bot or manually) and hidden from general consumption;
   1. a second phase during which moderators may either restore the message or
      `redact` it entirely.

## **Proposal**
We introduce a new type of relation: `m.visibility`, with the following syntax:

```jsonc
"m.relates_to": {
    "rel_type": "m.visibility",
    "event_id": "$event_id",
    "visibility": "hidden"// or "visible"
}
```

Events with relation `m.visibility` are ignored if they are sent by users with
powerlevel below `m.visibility`. This relation controls whether *clients* should
display an event or hide it.

Additionally, an event with relation `m.visibility` may have a content field `reason`
used to display a human-readable reason for which the original event is hidden
(e.g. "Message pending moderation", "First time posters are moderated", etc.)

### Server behavior

No changes in server behavior.

### Client behavior

   1. When a client receives an event `event` with `rel_type` `m.visibility`
      relating to an existing event `original_event` in room `room`:
       1. If the powerlevel of `event.sender` in `room` is greater or equal to `m.visibility`
           1. If `event` specifies a visibility of "hidden", mark `original_event` as hidden
               1. In every display of `original_event`, either by itself or in a reaction
                   1. If the current user is the sender of `original_event`
                       1. Label the display of `original_event` with a label such as `(pending moderation)`
                       1. If `event.content` contains a string field `reason`, this field may be used to display a reason for moderation.
                   1. Otherwise, if the current user has a powerlevel greater or
                      equal to `m.visibility`
                       1. Display `original_event` as a spoiler.
                       1. Label the display of `original_event` with a label such as `(pending moderation)`
                       1. If `event.content` contains a string field `reason`, this field may be used to display a reason for moderation.
                   1. Otherwise
                       1. Instead of displaying `original_event`, display a message such as `Message is pending moderation`
                       1. If `event.content` contains a string field `reason`, this field may be used to display a reason for moderation.
           1. Otherwise, if `event` specifies a visibility of "visible", mark `original_event` as visible
               1. Display `original_event` exactly as it would be displayed without this MSC
           1. Otherwise, ignore
       1. Otherwise, ignore
   1. When a client prepares to display a message `original_event` with visibility "hidden", whether by itself or in a reaction
       1. (see 1.1.1.1.1. for details on how to display `original_event`)
   1. If an event `event` with `rel_type` `m.visibility` and relating to an existing event `original_event` is redacted, update the display or `original_event` as per the latest event with `rel_type` `m.visibility` in this room relating to the same `original_event`.

If several reactions race against each other to mark a message as visible or
hidden, we consider the most recent one (by order of `origin_server_ts`) the
source of truth.

### Example use

A moderation bot such as Mjölnir might implement two-phase redaction as follows:
   1. When a room protection rule or a moderator requires Mjölnir to redact a
      message `original_message` in `room`
       1. Copy `original_message` to a "moderation pending" room as message `backup_message`, with some UX to
          decide whether `backup_message` should be PASS or REJECT.
       1. Mark `original_message` in `room` as hidden, using the current MSC.
   1. When a moderator marks `backup_message` as PASS
       1. Mark `original_message` in `room` as visible, using the current MSC.
       1. Remove `backup_message` from the "moderation pending" room.
   1. When a moderator marks clone `backup_message` as REJECT
       1. Send a message `m.room.redaction` to `room` to fully redact message `original_message`.
       1. Remove `backup_message` from the "moderation pending" room.
   1. If, after <some retention duration, e.g. one week>, a clone `backup_message` has been
      marked neither PASS nor REJECT
       1. Behave as if `backup_message` had been marked REJECT

## Potential issues
### Abuse by moderators
This proposal does not give substantial new powers to moderators, so we don't
think that there is cause for concern here.

### Race conditions
There may be race conditions between e.g. an edition (https://github.com/matrix-org/matrix-doc/pull/2676) and marking a message visible/hidden. We do not think that this can cause any real issue.

### Hidden channel
As messages are hidden but still distributed to all clients in the room, it is
entirely possible to write a client/bot that ignores hiding and one could
imagine using hidden messages to semi-covertly exchange messages in a room.

As there are already countless ways to implement this, we don't foresee this to
cause any problem.

### Liabilities

It is possible that, in some countries, if moderators decide to mark content as
hidden but fail to redact it, this could make the homeserver owner legally
responsible for illegal content being exchanged through this covert channel.

We believe that using a bot that automatically redacts hidden messages after a
retention period would avoid such liabilities.

## Alternatives
### Server behavior changes

We could amend this proposal to have the server reject messages with relation
`m.visibility` if these messages are sent by a user with a powerlevel below
`m.visibility`. However, this would require changes to the flow of encryption
to let the server read the relation between events, something that is less than
ideal.

We prefer requiring that clients ignore messages sent by users without a sufficient
powerlevel.

### A message to undo a redaction

As the original objective of this proposal is to undo redactions, one could
imagine a message `m.room.undo_redaction` with the following behavior:

   * The ability to send a `m.room.undo_redaction` is controlled by a
     powerlevel, just as `m.room.redaction`.
   * When a server receives a `m.room.undo_redaction` for event E, event E loses
     its "redacted" status, in particular in any future `sync` or
     `/room/.../event/...` or other, the original event E is returned, rather
     than its redacted status.
   * When a client receives a `m.room.undo_redaction` for an event E, they need
     to refetch event E from the homeserver.

This proposal would have the benefit of removing the hidden channel.

However, servers are intended to redact events immediately and permanently, though
regulations for some areas of operation require the contents to be preserved for a
short amount of time. In any case, it is not possible to determine
how long a server is willing or able to keep event contents, so we can only assume
it has not kept them at all. Any attempt to undo redaction would, at best, race
against this retention duration, which may differ across homeservers in the same
room, and might end up causing divergence between the room views.

Thus, undoing is not possible, in practice.

### Injecting content in redacted messages
An alternative mechanism to undo redactions would be to let moderators un-redact
a message by injecting new content in it. This would let clients or moderation
bots such as Mjölnir implement undoing redactions by first backing up redacted
messages (in a manner similar to what we discuss in "Example use"), then if a
redaction is canceled, reinjecting content. We decided not to pursue this
mechanism as it is more complicated and it opens abuse vectors by malicious
moderators de facto modifying the content of other user's messages (even if this
could be mitigated by clients displaying who has modified a user's messages).

## Security considerations
### Old clients

Old clients that do not implement this MSC will continue displaying messages that
should be hidden. We believe that it's an acceptable risk, as it does not expose
data that is meant to be kept private.

## Unstable prefix

During the prototyping phase:

- `rel_type` `m.visibility` should be prefixed into
  `org.matrix.msc3531.visibility`;
- field `visibility` should also be prefixed into
  `org.matrix.msc3531.visibility`;
- field `reason` should also be prefixed into
  `org.matrix.msc3531.reason`;
- constants `visible` and `hidden` remain unchanged.
