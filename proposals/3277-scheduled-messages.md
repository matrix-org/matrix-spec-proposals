# MSC3277: Scheduled messages

## Introduction

It's sometimes useful to schedule messages so that recipients will read them
at a point in the future rather than immediately.  Use cases include:

 * Not wanting to disturb the recipient(s) out-of-hours
 * Wanting to remind yourself or others of some information in future
 * Releasing embargoed information at a given time.

This is a simplified proposal derived from Travis' [original draft](https://docs.google.com/document/d/1vFbQuCnCNURBRs4_zukxiKLW_p2Ka7Ogo42oahpXnz4),
which aims to incorporate all the feedback gathered there.

## Proposal

A new query parameter, `at`, is added to the [/send](https://matrix.org/docs/spec/client_server/r0.6.1#put-matrix-client-r0-rooms-roomid-send-eventtype-txnid)
and [PUT /state](https://matrix.org/docs/spec/client_server/r0.6.1#put-matrix-client-r0-rooms-roomid-state-eventtype-statekey)
endpoints to indicate when the origin server should aim to send the event
(milliseconds since the unix epoch). The message is added to the room DAG
when the sender creates the event, but is only relayed to other members of
the room at the scheduled `at` time (or as close to it as the server can
manage).

The event is effectively treated as if it had been received over federation
after a federation delay. As such, all event types can be scheduled in this
manner, including state events.  Normal event ID and redaction behaviour
applies.  At the scheduled time, the server re-auths the event, and then
sends it on to the users in the room (if appropriate, otherwise it soft-fails
it), including the sender.  Therefore if the event is no longer acceptable in
the room at its scheduled time (e.g. if the sender is no longer in the room,
or no longer has PL to send events) then the event is soft-failed - just as
if a federated server tried to circumvent a user ban by sending old messages
into the DAG. Scheduled events are sent out over federation at the scheduled
time in order to minimise embargo leaks.

The server must set the `origin_server_ts` of the message is set to be its
`at` time, given in practice this is the label used for clients to display
the intended delivery timestamp of a message.  It must also set `scheduled:
true` on the event (not the contents) in order to let servers know to treat
it differently for history visibility purposes, and so the sender's clients
all know that it's scheduled.  The recipients can then also see the message
is scheduled. (A future MSC may define how to suppress this field from
recipients if desired).

For rooms with non-shared history visibility, servers must special-case the
visibility of scheduled events based on the membership of the room at the
scheduled time, rather than based on its DAG position (which reflects the
creation time).

The sender's clients will want to track the unsent scheduled messages in its
various rooms, such that the sender can cancel them by redacting them, or
edit them (optionally redacting earlier versions, providing private
drafting).  We propose using the same mechanism as for tracking 'starred'
(aka 'favourited' or 'flagged') messages, to avoid sprouting two different
APIs for almost identical functionality.  This is deferred to a future MSC.

## Encryption considerations

In an E2EE room, the sending client must distribute the megolm session used to
encrypt the scheduled message immediately to the devices currently in the
room. We then rely on the normal mechanisms used to share megolm keys with
new devices (i.e. keyshare requests; online key backup; MSC3061-style sharing
room keys for past messages) to avoid the messages being undecryptable by
future devices.

The megolm session must be a one-off used just for this scheduled message
(meaning that as it's shared for future participants in the room, it only exposes
the session used to encrypt that particular message rather than any surrounding
non-scheduled ones).

E2EE implementations must not discard 'unused' megolm sessions, given they
may be shared long in advance of the scheduled message.

Sender's clients may optionally attempt to wake themselves up at the deadline
in order to re-share the megolm session to the current participants in the
room (and/or be available to respond to keyshare reqs), in order to reduce
the risk of UISIs.

MSC3061-style 'sharing room keys for past messages' will need to special-case
history visibility rules for scheduled messages. Therefore we need to know
which sessions are for scheduled messages, and include them when sharing keys
with new users/devices... but stop once the scheduled message has been
received.  Therefore we add a `m.forward_until: timestamp` field to the
`m.room_key` to-device message to indicate the session's lifetime. The
timestamp should be that of the scheduled event; users who join the room
after that timestamp should not be able to read the message.

## Possible issues

A risk is that E2EE key distribution mechanisms which rely on clients seeing
an undecryptable message (i.e. keyshare reqs) will not take effect until the
scheduled message is sent - by which point clients which could service the
keyshare reqs will be more likely to be absent due to the passage of time.
One mitigation to this could be to relax the rules on who can service the
keyshare request and let any device in the room share to the newcomer if they
believe the newcomer should be entitled to decrypt the message. This
introduces the attack that a malicious server admin could add a fake
user/device to their local copy of a room, and could use this to exfiltrate
keys from bystanders - but this may be an acceptable tradeoff to improve
the chances of the message being decryptable in the distant future.
Alternatively, MLS may solve this(??)

Users who send a scheduled message and are then kicked out of a room will have
no way of being able to cancel their scheduled message.  This could either be
a feature (ex-employees shouldn't be able to destroy their scheduled
messages), or a bug (i want to GDPR erase my scheduled messages!).  We
consider it a feature.

Another problem is that because we share E2EE to users at msg authoring time, if
users subsequently leave the room, they will still have the keys to read the
scheduled message when it's revealed.  This is probably inevitable.


## Alternatives

The origin server could queue the message with a fake event ID and only
attempt to add it to the DAG when it's time to send.  This two-phase commit
complicates the implementation significantly - although it does provide a
slightly simpler solution to the history visibility problem and the problem
of needing to be in a room to cancel your scheduled messages.

Alternatively, the scheduled messages could queue on the receiving client
(thus letting users choose to see them at their leisure).  However, this
kills the "embargo" use case, and complicates the implementation as receiving
clients have to be able to filter for scheduled events and generally shifts
complexity to clients, which is always undesirable as there way more clients
than servers and we want clients to be as simple as possible.

Separately, there's a trade-off between whether you send the queued message
out over federation at the time it's created or at the scheduled time.  If
you send at create-time, it means that the origin server doesn't need to
still be running at the scheduled time. On the other hand, it means that you
are much more likely to break embargos, as one-person homeservers will get
the message ahead of schedule.  We've gone for the more privacy preserving
option (send over federation at the scheduled time).  Plus it acts as an
incentive for people to keep the origin server running ;P

Another alternative would be to use an API shape where you put a field on the
event contents (e.g. `m.pts` for presentation timestamp) to tell servers and
clients alike that a given message is scheduled.  However, this ends up with
two timestamps on the event (confusing), complicates E2EE further
(don't encrypt the `m.pts`), and makes it harder to hide from recipients
whether a message was scheduled.  So we've stuck with `?at=`.

## Security considerations

This MSC allows for spammers to potentially pre-plan their attacks for
off-peak hours when the moderators may not be present. It also potentially
allows a user to stack up a large number of pending events which all get sent
throughout the day as a disruption attempt. Servers should impose harsh
limits to the number of events a user may schedule, such as a maximum of 3
pending events, to reduce the potential for abuse while still maintaining an
amount of usability for common scenarios.

Users could also try to schedule many events at once or schedule such that
they all get sent at once - servers should apply rate limiting on both the
scheduling and sending sides to limit the user’s ability to spam a room.

This proposal relies on absolute timestamps, and so for it to work sensibly
servers need to have an accurate (e.g. NTP-synced) clock.

## Unstable prefix

Implementations should use `org.matrix.msc3277.at` in place of the at query
parameter, and expose/look for `org.matrix.msc3277` in the
``unstable_features` of `/versions` while this MSC is not in a released
version of the spec.