# MSC3773: Notifications for threads

Since the unread notification count does not consider threads, a client is unable
to separate the unread message counts into threads (as defined by
[MSC3440](https://github.com/matrix-org/matrix-doc/pull/3440))
without iterating over every missing message. Without this, clients are unable to:

* Let users know that a thread has new messages since they last read it.
* Accurately display a count of unread messages in a room (or a thread).

## Proposal

### Modification to push rule processing

When an event which is part of a thread (i.e. has a valid `m.relates_to` with
`rel_type` of `m.thread`) matches a push rule which results in a `notify` action
then the homeserver should partition the resulting notification count per-thread.
(This is needed for the [proposed `/sync` changes](#unread-thread-notifications-in-the-sync-response)).

Similar behavior should be applied for an event which results in `notify` action
with a `highlight` tweak set.

This MSC does not propose any changes to the payload sent to push gateways.

### Unread thread notifications in the sync response

Threaded clients can opt into receiving unread thread notifications by passing
a new `unread_thread_notifications` parameter
[as part of the `RoomEventFilter`](https://spec.matrix.org/v1.2/client-server-api/#filtering).
(This is [similar to `lazy_load_members`](https://spec.matrix.org/v1.2/client-server-api/#lazy-loading-room-members),
but only applies to the `/sync` endpoint.):

* `unread_thread_notifications`:  If `true`, enables partitioning of unread notification
  counts by thread. Defaults to false.

If this flag is set to `true`, for each ["Joined Room" in the `/sync` response](https://spec.matrix.org/v1.3/client-server-api/#get_matrixclientv3sync)
a new field is added:

* `unread_thread_notifications`: Counts of unread thread notifications for this
  room, an object which maps thread ID (the parent event ID) to
  `Unread Notification Counts`.

Additionally, the `unread_notifications` dictionary is modified to only include
unread notifications from events which are not part of a thread.

An example of a joined room from a sync response:

```json5
{
  "account_data": {
    // ...
  },
  "ephemeral": {
    // ...
  },
  "state": {
    // ...
  },
  "summary": {
    // ...
  },
  "timeline": {
    "events": [
      {
        "event_id": "$143273582443PhrSn:example.org",
        // other fields ...
      },
      {
        "event_id": "$SGNxGPGUopcPBUoTTL:example.org",
        "m.relates_to": {
          "event_id": "$143273582443PhrSn:example.org",
          "rel_type": "m.thread"
        }
        // other fields ...
      }
    ]
  },
  "unread_notifications": {
    "highlight_count": 2,
    "notification_count": 18
  },
  "unread_thread_notifications": {
    "$143273582443PhrSn:example.org": {
      "highlight_count": 0,
      "notification_count": 1
    }
  }
}
```

## Potential issues

### Events related to thread events

Events which are related to thread events (e.g. a reaction to a message which is
part of a thread) would not be represented in the notification count for that
thread, it would still appear in the main timeline's notification count.

With the default push rules this does not seem to be a problem as thread notifications
mostly apply to `m.room.message` and `m.room.encrypted` events.

### Scalability

Rooms with many unread threads could cause some downsides:

* The size of the `/sync` response would increase without bound.
* The effort to generate and process the receipts for each room would increase
  without bound.

This is not dissimilar to rooms which are never read, however, as their unread
counts are continually tracked and returned as part of the `/sync` response.

### Clearing unread notifications

This MSC does not attempt to modify how unread notifications (for a thread or
otherwise) are cleared. It currently assumes the rules set forth by
[read receipts](https://spec.matrix.org/v1.3/client-server-api/#receiving-notifications)
still apply. This will cause some flakiness with unread notifications, as the current
receipt infrastructure assumes that a room's timeline is linear, which is no
longer true.

[MSC3771](https://github.com/matrix-org/matrix-spec-proposals/pull/3771) is a
potential solution for this.

## Alternatives

### Using push rules

It might seem that a new push rule `action` (or `tweak`) should be used to control
the behavior of whether an event generates a notification for a thread or the
room itself. There are issues with either approach though:

A new `action` (e.g. `notify_thread`) would mean that additional logic would
need to be defined and added for events which aren't part of a thread but attempt
to use this action. It also conflicts with [MSC3768](https://github.com/matrix-org/matrix-spec-proposals/pull/3768),
which attempts to define another `action` which should also work fine for threads.

A new `tweak` (e.g. `threaded`) does make much sense since there is not need to
pass this through to the push server, which is at odds with the current `tweaks`
mechanism.

Regardless, the main issue with using push rules is that it becomes necessary to
define rules which match threaded events. Whenever adding a new rule, matching rules
would need to be added, but as a thread-specific version.

## Security considerations

N/A

## Unstable prefix

While this feature is in development the following unstable prefixes should be used:

* `unread_thread_notifications` --> `org.matrix.msc3773.unread_thread_notifications`

To detect server support, clients can either rely on the spec version (when stable)
or the presence of a `org.matrix.msc3773` flag in `unstable_features` on `/versions`.

## Dependencies

N/A
