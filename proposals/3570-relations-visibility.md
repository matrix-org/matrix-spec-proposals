# MSC3570: Relation history visibility changes

Edit as defined in [MSC2676](https://github.com/matrix-org/matrix-doc/pull/2676) and reactions as defined in [MSC2677](https://github.com/matrix-org/matrix-doc/pull/2677) only make sense in the context of their target event. To ensure that all
users in the room share the same view (exception: relations sent by ignored users), this MSC proposes to change the
room history visibility rules for certain kinds of relations.

## Proposal

The visibility rules (whether or not a user should receive a given event through
the client-server API) for relations events are adjusted in this MSC.
The visibility for relation events is dependent on the `rel_type`, with two options:
 
  - Visibility is derived from the visibility of the target event (the event
    referred to by the `event_id` in the relation) under some circumstances:
    the relation should be visible if the relation target event is visible to
    a user but the relation event would not be visible according to regular
    event history visibility rules (e.g. the user has since left in a room with
    joined or invite room history visibility).
    If according to regular event room history visibility rules, the relation
    event would be visible to a user, then the visibility of target event
    should not be considered and the relation event should be visible.
    This option means that events can still be visible to a user after
    the user left the room, and has implications
    for [End-to-end encryption](#end-to-end-encryption).
    [`m.replace`](https://github.com/matrix-org/matrix-doc/pull/2676) and [`m.annotation`](https://github.com/matrix-org/matrix-doc/pull/2677) relation events have this visilibilty, see those respective MSCs.
  - Visibility is the same as a non-relation event.
    [`m.thread`](https://github.com/matrix-org/matrix-doc/pull/3440) relation events have this visilibilty, see the respective MSC.

Visibility derived from the visibility of the target event is the default for relation events;
if the MSC introducing the relation type doesn't specify any other visibility this is assumed.

The change of visilibilty rules will require a new room version.

### End to end encryption

When sending relation events whose [visibility is derived from the target event](#relation-visibility),
clients should ensure that the end-to-end encryption key for the encrypted
relation event is shared with all devices that could see the target event
if those relation events are encrypted with a different key than
the target event (e.g. after key rotation), even if the receiving user has
since left the room.

## Dependencies

This MSC builds on MSC2676 and MSC2677 (which at the time of writing have not yet been accepted
into the spec).
