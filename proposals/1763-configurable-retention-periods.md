# Proposal for specifying configurable retention periods for messages.

A major shortcoming of Matrix has been the inability to specify how long
events should stored by the servers and clients which participate in a given
room.

This proposal aims to specify a simple yet flexible set of rules which allow
users, room admins and server admins to determine how long data should be
stored for a room, from the perspective of respecting the privacy requirements
of that room (which may range from "burn after reading" ephemeral messages,
through to FOIA-style public record keeping requirements).

As well as enforcing privacy requirements, these rules provide a way for server
administrators to better manage disk space (e.g. to enforce rules such as "don't
store remote events for public rooms for more than a month").

## Problem:

Matrix is inherently a protocol for storing and synchronising conversation
history, and various parties may wish to control how long that history is stored
for.

 * Users may wish to specify a maximum age for their messages for privacy
   purposes, for instance:
   * to avoid their messages (or message metadata) being profiled by
     unscrupulous or compromised homeservers
   * to avoid their messages in public rooms staying indefinitely on the public
     record
   * because of legal/corporate requirements to store message history for a
     limited period of time
   * because of legal/corporate requirements to store messages forever
     (e.g. FOIA)
   * to provide "ephemeral messaging" semantics where messages are best-effort
     deleted after being read.
 * Room admins may wish to specify a retention policy for all messages in a
   room.
   * A room admin may wish to enforce a lower or upper bound on message
     retention on behalf of its users, overriding their preferences.
   * A bridged room should be able to enforce the data retention policies of the
     remote rooms.
 * Server admins may wish to specify a retention policy for their copy of given
   rooms, in order to manage disk space.

Additionally, we would like to provide this behaviour whilst also ensuring that
users generally see a consistent view of message history, without lots of gaps
and one-sided conversations where messages have been automatically removed.

At the least, it should be possible for people participating in a conversation
to know the expected lifetime of the other messages in the conversation **at the
time they are sent** in order to know how best to interact with them (i.e.
whether they are knowingly participating in a future one-sided conversation or
not).

We would also like to discourage users from setting low message retention as a
matter of course, as it can result in very antisocial conversation patterns to
the detriment of Matrix as a useful communication mechanism.

This proposal does not try to solve the problems of:
 * GDPR erasure (as this involves retrospectively changing the lifetime of
   messages)
 * Bulk redaction (e.g. to remove all messages from an abusive user in a room,
   as again this is retrospectively changing message lifetime)
 * Limiting the number (rather than age) of messages stored per room (as this is
   more a question of quotaing rather than empowering privacy)

## Proposal

### User-specified per-message retention

Users can specify per-message retention by adding the following fields to the
event within its content.  Retention is only considered for non-state events.

`max_lifetime`:
	the maximum duration in seconds for which a well-behaved server should store
	this event. If absent, or null, it should be interpreted as 'forever'.


`min_lifetime`:
	the minimum duration for which a well-behaved server should store this event.
	If absent, or null, should be interpreted as 'forever'

`self_destruct`:
	a boolean for whether wellbehaved servers should remove this event after
	seeing an explicit read receipt delivered for it.

`expire_on_clients`:
	a boolean for whether well-behaved clients should expire messages clientside
	to match the min/max lifetime and/or self_destruct semantics fields.

For instance:

```json
{
	"max_lifetime": 86400,
}
```

The above example means that servers receiving this message should store the
event for a only 86400 seconds (1 day), as measured from that event's
origin_server_ts, after which they MUST prune all references to that event ID
from their database.

We consciously do not redact the event, as we are trying to eliminate
metadata here at the cost of deliberately fracturing the DAG (which will
fragment into disparate chunks).

```json
{
	"min_lifetime": 2419200,
}
```

The above example means that servers receiving this message SHOULD store the
event forever, but MAY choose to prune their copy after 28 days (or longer) in
order to reclaim diskspace.

```json
{
	"self_destruct": true,
	"expire_on_clients": true,
}
```

The above example describes 'self-destructing message' semantics where both server
and clients MUST prune/delete the event and associated data as soon as a read
receipt is received from the recipient.

TODO: do we want to pass these in as querystring params when sending, instead of
putting them inside event.content?

### User-advertised per-message retention

If we had extensible profiles, users could advertise their intended per-message
retention in their profile (in global profile or per-room profile) as a useful
social cue.  However, this would be purely informational.

### Room Admin-specified per-room retention

We introduce a `m.room.retention` state event, which room admins can set to
override the retention behaviour for a given room.  This takes the same fields
described above.

If set, these fields directly override any per-message retention behaviour
specified by the user - even if it means forcing laxer privacy requirements on
that user.  This is a conscious privacy tradeoff to allow admins to specify
explicit privacy requirements for a room.  For instance, a room may explicitly
disable self-destructing messages by setting `self_destruct: false`, or may
require all messages in the room be stored forever with `min_lifetime: null`.

In the instance of `min_lifetime` or `max_lifetime` being overridden, the
invariant that `max_lifetime > min_lifetime` must be maintained by clamping
max_lifetime to be greater than `min_lifetime`.

If the user's retention settings conflicts with those in the room, then the user's
clients should warn the user.

### Server Admin-specified per-room retention

Server admins have two ways of influencing message retention on their server:

1) Specifying a default `m.room.retention` for rooms created on the server, as
defined as a per-server implementation configuration option which inserts the
state events after creating the room (effectively augmenting the presets used
when creating a room).  If a server admin is trying to conserve diskspace, they
may do so by specifying and enforcing a relatively low min_lifetime (e.g. 1
month), but not specify a max_lifetime, in the hope that other servers will
retain the data for longer.

XXX: is this the correct approach to take? It's how we force E2E encryption on,
but it feels very fragmentory to have magical presets which do different things
depending on which server you're on.

2) By adjusting how aggressively their server enforces the the `min_lifetime`
value for message retention.  For instance, a server admin could configure their
server to attempt to automatically remote purge messages in public rooms which
are older than three months (unless min_lifetime for those messages was set
higher).

A possible configuration here could be something like:
 * target_lifetime_public_remote_events: 3 months
 * target_lifetime_public_local_events: null # forever
 * target_lifetime_private_remote_events: null # forever
 * target_lifetime_private_local_events: null # forever

...which would try to automatically purge remote events from public rooms after
3 months (assuming their individual min_lifetime is not higher), but leave
others alone.

XXX: should this configuration be specced or left as an implementation-specific
config option?

Server admins could also override the requested retention limits (e.g. if resource
constrained), but this isn't recommended given it may result in history being
irrevocably lost against the senders' wishes.

## Client-side behaviour

Clients should independently calculate the retention of a message based on the
event fields and the room state, and show the message lifespan in the UI.  If a
message has a finite lifespan that fact MUST be indicated clearly in the timeline
to allow users to correctly interact with the message.  (The details of the
lifespan can be shown on demand, however).

If `expire_on_clients` is true, then clients should also calculate expiration for
said events and delete them from their local stores as required.

## Tradeoffs

This proposal deliberately doesn't address GDPR erasure or mega-redaction scenarios,
as it attempts to build a coherent UX around the use case of users knowing their
privacy requirements *at the point they send messages*.  Meanwhile GDPR erasure is
handled elsewhere (and involves hiding rather than purging messages, in order to
avoid annhilating conversation history), and mega-redaction is yet to be defined.

## Potential issues

How do we handle scenarios where users try to re-backfill in history which has
already been purged?  This should presumably be a server admin option on whether
to allow it or not, and if allowed, configure how long the backfill should persist
for before being purged again?

How do we handle retention of media uploads (especially for E2E rooms)?  It feels
the upload itself might warrant retention values applied to it.


## Security considerations

There's scope for abuse where users can send abusive messages into a room with a
short max_lifetime and/or self_destruct set true which promptly self-destruct.

One solution for this could be for server implementations to implement a quarantine
mode which initially marks purged events as quarantined for N days before deleting
them entirely, allowing server admins to address abuse concerns.

## Conclusion

Previous attempts to solve this have got stuck by trying to combine together too many
disparate problems (e.g. reclaiming diskspace; aiding user data privacy; self-destructing
messages; mega-redaction; clearing history on specific devices; etc) - see
https://github.com/matrix-org/matrix-doc/issues/440 and https://github.com/matrix-org/matrix-doc/issues/447
for the history.

This proposal attempts to simplify things to strictly considering the question of
how long servers should persist events for (with the extension of self-destructing
messages added more to validate that the design is able to support such a feature).