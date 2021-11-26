
# **MSCXXXX: Letting moderators hide messages pending review**

Matrix supports **redacting** messages as a mechanism to remove unwanted content. At present, there is no manner of **undoing** these redactions.

After attempting to come up with a mechanism to undo redactions, we came to the conclusion that
this cannot be robustly and simply implemented at Matrix-level. Rather, we propose a spec to let moderators *hide messages pending review*. This spec can then be used by clients or bots such as Mjölnir
to implement two phase redaction:
   1. a first phase during which messages are flagged for moderation (either by a bot or manually) and hidden from general consumption;
   1. a second phase during which moderators may either restore the message or `redact` it entirely.


## **Proposal**

### **Introduction**

**Redacting** events, as defined in the Matrix spec, is a mechanism that entirely removes the content of an event. Users can redact their own events, and room moderators can redact unwanted events, including illegal content.

The Matrix spec does not offer a mechanism to **undo** a redaction. This means that if a user or moderator makes a mistake, there is no way to restore the original message. Tolerance for mistakes supports innovation, as well as reducing the risks of proposals such as MSC3215, which aims to decentralize moderation.

Reversing a redaction is tricky, as we cover in the **Alternatives** section. However, if we allow moderators to flag a message as hidden, a moderator can easily restore the content of a message that has been flagged. In particular, if a moderator uses a bot such as Mjölnir, the bot may implement a room of "messages pending review by moderators", letting moderators review flagged messages leisurely while being certain that inappropriate messages are not visible by users on compliant clients.

In this proposal, the bulk of the work of hiding is *performed by clients*. Messages marked as "hidden" are distributed to all clients by should be visible only to their author and moderators. This keeps the proposal minimal and simple to implement.

### **Proposal**
We introduce a new type of relation: `m.visibility`, with the following syntax:

```jsonc
"m.relates_to": {
    "rel_type": "m.visibility",
    "event_id": "$event_id",
    "visibility": "hidden"// or "visible"
}
```

Only moderators may send events with relation `m.visibility`. This relation controls whether *clients* should display an event or hide it.

#### Server behavior

When a homeserver receives an event with `rel_type` `m.visibility` sent by user U in room R:
   1. if the powerlevel of U in R is greater or equal to `m.visibility`
       1. accept the event
   1. otherwise
       1. respond with error code M_FORBIDDEN

#### Client behavior

   1. When a client receives an event with `rel_type` `m.visibility` and visibility V sent by user U in room R and relating to an existing event E in room R:
       1. If the powerlevel of U in R is greater or equal to `m.visibility` (note: we add this check to ensure that the proposal works to a large extent even without support from the homeserver)
           1. If V is "hidden", mark E as hidden
               1. In every display of E, either by itself or in a reaction
                   1. If the current user is the sender of E
                       1. Label the display of E with a label such as `(pending moderation)`
                   1. Otherwise, if the current user has a powerlevel greater or equal to `m.visibility`
                       1. Display E as a spoiler.
                       1. Label the display of E with a label such as `(pending moderation)`
                   1. Otherwise
                       1. Instead of displaying E, display a message such as `Message is pending moderation`
           1. Otherwise, if V is "visible", mark E as visible
               1. Display E exactly as it would be displayed without this MSC
           1. Otherwise, ignore
       1. Otherwise, ignore
   1. When a client prepares to display a message E with visibility "hidden", whether by itself or in a reaction
       1. (see 1.1.1.1.1. for details on how to display E)

If several reactions race against each other to mark a message as visible or hidden, we consider the most recent one (by order of origin_server_ts) the source of truth.

#### Example use

A moderation bot such as Mjölnir may implement two-phase redaction as follows:
   1. When a room protection rule or a moderator requires Mjölnir to redact a message E in room R
       1. Copy E to a "moderation pending" room as message E', with some UX to decide whether E should be PASS or REJECT.
       1. Mark E in R as hidden, using the current MSC.
   1. When a moderator marks clone E' as PASS
       1. Mark E in R as visible, using the current MSC.
       1. Remove E' from the "moderation pending" room.
   1. When a moderator marks clone E' as REJECT
       1. Send a message `m.room.redaction` to R to fully redact message E.
       1. Remove E' from the "moderation pending" room.
   1. If, after <some retention duration, e.g. one week>, a clone E' has been marked neither PASS nor REJECT
       1. Behave as if E' had been marked REJECT

### Potential issues
#### Abuse by moderators
This proposal does not give substantial new powers to moderators, so we don't think that there is cause for concern here.

#### Race conditions
There may be race conditions between e.g. an edition (MSC2767) and marking a message visible/hidden. We do not think that this can cause any real issue.

#### Hidden channel
As messages are hidden but still distributed to all clients in the room, it is entirely possible to write a client/bot that ignores hiding and one could imagine using hidden messages to semi-covertly exchange messages in a room.

As there are already countless ways to implement this, we don't foresee this to cause any problem.

#### Liabilities

It is possible that, in some countries, if moderators decide to mark content as hidden but fail to redact it, this could make the homeserver owner legally responsible for illegal content being exchanged through this covert channel.

We believe that using a bot that expunges automatically hidden messages after a retention period would avoid such liabilities.

### Alternatives
#### A message to undo a redaction

As the original objective of this proposal is to undo redactions, one could imagine a message `m.room.undo_redaction` with the following behavior:

   * The ability to send a `m.room.undo_redaction` is controlled by a powerlevel, just as `m.room.redaction`.
   * When a server receives a `m.room.undo_redaction` for event E, event E loses its "redacted" status, in particular in any future `sync` or `/room/.../event/...` or other, the original event E is returned, rather than its redacted status.
   * When a client receives a `m.room.undo_redaction` for an event E, they need to refetch event E from the homeserver.

This proposal would have the benefit of removing the hidden channel.

However, servers typically purge redacted events after a while, both to save space and to comply with regulations. Unfortunately, if two servers receive a `m.room.undo_redaction` for the same event E, one of the servers may have purged E already. Both servers could make different choices (one server keeping E redacted, the other one making it unredacted). In turn, these choices would end up having different consequences if E subsequently receives a reaction. These consequences would cause divergence between the room views, which is not desirable.

We could solve this by requiring that homeservers backup any redacted event, at least for some time, but this might contradict legal requirements in some countries, as well as the privacy preferences of individual administrators.

Furthermore, this proposal opens different abuse vectors, through which a malicious moderator could undo a self-redaction by a user, e.g. after accidentally revealing private information.

This could be mitigated by not allowing moderators to undo self redactions.

#### Injecting content in redacted messages
An alternative mechanism to undo redactions would be to let moderators un-redact a message by injecting new content in it. This would let clients or moderation bots such as Mjölnir implement undoing redactions by first backing up redacted messages (in a manner similar to what we discuss in "Example use"), then if a redaction is canceled, reinjecting content.
We decided not to pursue this mechanism as it is more complicated and it opens abuse vectors by malicious moderators de facto modifying the content of other user's messages (even if this could be mitigated by clients displaying who has modified a user's messages).

### Security considerations
We do not think that this proposal could cause any security issue.

### Unstable prefix

During the prototyping phase:

- `rel_type` `m.visibility` should be prefixed into `org.matrix.mscXXXX.visibility`;
- field `visibility` should also be prefixed into `org.matrix.mscXXXX.visibility`.
