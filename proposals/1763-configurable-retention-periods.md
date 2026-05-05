# Proposal for specifying configurable per-room message retention periods.

A major shortcoming of Matrix has been the inability to specify how long events
should stored by the servers and clients which participate in a given room.

This proposal aims to specify a simple yet flexible set of rules which allow
users, room admins and server admins to determine how long data should be stored
for a room, from the perspective of respecting the privacy requirements of that
room (which may range from a "burn after reading" ephemeral conversation,
through to FOIA-style public record keeping requirements).

As well as enforcing privacy requirements, these rules provide a way for server
administrators to better manage disk space (e.g. to enforce rules such as "don't
store remote events for public rooms for more than a month").

This proposal originally tried to also define semantics for per-message
retention as well as per-room; this has been split out into
[MSC2228](https://github.com/matrix-org/matrix-doc/pull/2228) in order to get
the easier per-room semantics landed.


## Problem

Matrix is inherently a protocol for storing and synchronising conversation
history, and various parties may wish to control how long that history is stored
for.

Room administrators, for instance, may wish to control how long a message can be
stored (e.g. to comply with corporate/legal requirements to store message
history for at least a specific amount of time), or how early a message can be
deleted (e.g. to address privacy concerns of the room's members, to avoid
messages staying in the public record forever, or to comply with corporate/legal
requirements to only store specific kinds of information for a limited amount of
time).

Additionally, server administrators may also wish to control how long message
history is kept in order to better manage their server's disk space, or to
enforce corporate/legal requirements for the organisation managing the server.

We would like to provide this behaviour whilst also ensuring that users
generally see a consistent view of message history, without lots of gaps and
one-sided conversations where messages have been automatically removed.

We would also like to set the expectation that rooms typically have a long
message retention - allowing those who wish to use Matrix to act as an archive
of their conversations to do so.  If everyone starts defaulting their rooms to
finite retention periods, then the value of Matrix as a knowledge repository is
broken.

This proposal does not try to solve the problems of:
 * GDPR erasure (as this involves retrospectively changing the lifetime of
   messages)
 * Bulk redaction (e.g. to remove all messages from an abusive user in a room,
   as again this is retrospectively changing message lifetime)
 * Specifying history retention based on the number of messages (as opposed to
   their age) in a room. This is descoped because it is effectively a disk space
   management problem for a given server or client, rather than a policy
   problem of the room. It can be solved as an implementation specific manner, or
   a new MSC can be proposed to standardise letting clients specify disk quotas
   per room.
 * Per-message retention (as having a mix of message lifetime within a room
   complicates implementation considerably - for instance, you cannot just
   purge arbitrary events from the DB without fracturing the DAG of the room,
   and so a different approach is required)


## Proposal

### Per-room retention

We introduce a `m.room.retention` state event, which room admins or moderators
can set to mandate the history retention behaviour for a given room. It follows
the default PL semantics for a state event (requiring PL of 50 by default to be
set). Its state key is an empty string (`""`).

The following fields are defined in the `m.room.retention` contents:  

* `max_lifetime`: the maximum duration in milliseconds for which a server must
  store events in this room. Must be null or an integer in range [0,
  2<sup>53</sup>-1]. If absent or null, should be interpreted as not setting an
  upper bound to the room's retention policy.

* `min_lifetime`: the minimum duration in milliseconds for which a server should
  store events in this room. Must be null or an integer in range [0,
  2<sup>53</sup>-1]. If absent or null, should be interpreted as not setting a
  lower bound to the room's retention policy.

In the instance of both `max_lifetime` and `min_lifetime` being provided,
`max_lifetime` must always be higher or equal to `min_lifetime`.


For instance:

```json
{
	"max_lifetime": 86400000
}
```

The above example means that servers receiving messages in this room should
store the event for only 86400000 milliseconds (1 day), as measured from that
event's `origin_server_ts`, after which they MUST purge all references to that
event (e.g. from their db and any in-memory queues).

We consciously do not redact the event, as we are trying to eliminate metadata
and save disk space at the cost of deliberately discarding older messages from
the DAG.

```json
{
	"min_lifetime": 2419200000
}
```

The above example means that servers receiving this message SHOULD store the
event forever, but can choose to purge their copy after 28 days (or longer) in
order to reclaim diskspace.

```json
{
	"min_lifetime": 2419200000, 
    "max_lifetime": 15778800000
}
```

The above example means that servers SHOULD store their copy of the event for at least 28
days after it has been sent, and MUST delete it at the latest after 6 months.


## Server-defined retention

Server administrators can benefit from a few capabilities to control how long
history is stored:

* the ability to set a default retention policy for rooms that don't have a
  retention policy defined in their state
* the ability to override the retention policy for a room
* the ability to cap the effective `max_lifetime` and `min_lifetime` of the rooms the
  server is in

The implementation of these capabilities in the server is left as an
implementation detail.

We introduce the following authenticated endpoint to allow clients to enquire
about how the server implements this policy:


```
GET /_matrix/client/v3/retention/configuration
```

200 response properties:

* `policies` (required): An object mapping room IDs to a retention policy. If
  the room ID is `*`, the associated policy is the default policy. Each policy
  follows the format for the content of an `m.room.retention` state event.
* `limits` (required): An object defining the limits to apply to policies
  defined by `m.room.retention` state events. This object has two optional
  properties, `min_lifetime` and `max_lifetime`, which each define a limit to
  the equivalent property of the state events' content. Each limit defines an
  optional `min` (the minimum value, in milliseconds) and an optional `max` (the
  maximum value, in milliseconds).

If both `policies` and `limits` are included in the response, the policies
specified in `policies` __must__ comply with the limits defined in `limits`.

Example response:

```json
{
    "policies": {
        "*": {
            "max_lifetime": 15778800000
        },
        "!someroom:test": {
            "min_lifetime": 2419200000, 
            "max_lifetime": 15778800000
        }
    },
    "limits": {
        "min_lifetime": {
            "min": 86400000,
            "max": 172800000
        },
        "max_lifetime": {
            "min": 7889400000,
            "max": 15778800000
        }
    }
}
```

In this example, the server is configured with:

* a default policy with a `max_lifetime` of 6 months and no `min_lifetime` (i.e. messages
  can only be kept up to 6 months after they have been sent)
* an override for the retention policy in room `!someroom:test`
* limits on `min_lifetime` that 

Example response with no policy or limit set:

```json
{
    "policies": {},
    "limits": {}
}
```

Example response with only a default policy and an upper limit on `max_lifetime`:

```json
{
    "policies": {
        "*": {
            "min_lifetime": 86400000,
            "max_lifetime": 15778800000
        }
    },
    "limits": {
        "max_lifetime": {
            "max": 15778800000
        }
    }
}
```

### Defining the effective retention policy of a room

In this section, as well as in the rest of this document, we define the
"effective retention policy" of a room as the retention policy that is used to
determine whether an event should be deleted or not. This may be the policy
determined by the `m.room.retention` event in the state of the room, but it
might not be depending on limits set by the homeserver.

The algorithm implementation must implement to determine the effective retention
policy of a room is


* if the homeserver defines a specific retention policy for this room, then use
  this policy as the effective retention policy of the room.
* otherwise, if the state of the room does not include a `m.room.retention`
  event with an empty state key:
    * if the homeserver defines a default retention policy, then use this policy
      as the effective retention policy of the room.
    * if the homeserver does not define a default retention policy, then don't
      apply a retention policy in this room.
* otherwise, if the state of the room includes a `m.room.retention` event with
  an empty state key:
    * if no limit is set by the homeserver use the policy in the state of the
      room as the effective retention policy of the room.
    * for `min_lifetime` and `max_lifetime`:
        * if there is no limit for the property, use the value specified in the
          room's state for the effective retention policy of the room (if any).
        * if there is a limit for the property:
            * if the value specified in the room's state complies with the
              limit, use this value for the effective retention policy of the
              room.
                * if the value specified in the room's state is lower than the
                  limit's `min` value, use the `min` value for the effective
                  retention policy of the room.
                * if the value specified in the room's state is greater than the
                  limit's `max` value, use the `max` value for the effective
                  retention policy of the room.
                * if there is no value specified in the room's state, use the
                  limit's `min` value for the effective retention policy of the
                  room (which can be null or absent).
* otherwise, don't apply a retention policy in this room.

So, for example, if a homeserver defines a lower limit on `max_lifetime` of
`86400000` (a day) and no limit on `min_lifetime`, and a room's retention policy
is the following:

```json
{
  "max_lifetime": 43200000,
  "min_lifetime": 21600000
}
```

Then the effective retention policy of the room is:

```json
{
  "max_lifetime": 86400000,
  "min_lifetime": 21600000
}
```


## Enforcing a retention policy

Retention is only considered for non-state events. Retention is also not
considered for the most recent event in a room, in order to allow a new event
sent to that room to reference it in its  `prev_events`.

When purging events in a room, only the latest retention policy state event in
that room is considered. This means that in a room where the history looks like
the following (oldest event first):

1. Retention policy A
2. Event 1
3. Event 2
4. Retention policy B

Then the retention policy B is used to determine the effective retention that
defines whether events 1 and 2 should be purged, even though they were sent when
the retention policy A was in effect. This is to avoid creating wholes in the
room's DAG caused by events in the middle of the timeline being subject to a
lower `max_lifetime` than other events being sent before and after them. Such
holes would make it more difficult for homeservers to calculate room timelines
when showing them to clients. They would also force clients to display
potentially incomplete or one-sided conversations without being able to easily
tell which parts of the conversation is missing.

Servers decide whether an event should or should not be purged by calculating
how much time has passed since the event's `origin_server_ts` property, and
comparing this duration with the room's effective retention policy.

Note that, for performance reasons, a server might decide to not purge an event
the second it hits the end of its lifetime (e.g. so it can batch several events
together). In this case, the server must make sure to omit the expired events
from reponses to client requests. Similarly, if the server is sent an expired
event over federation, it must omit it from responses to client requests (and
ensure it is eventually purged).

## Tradeoffs

This proposal specifies that the lifetime of an event is defined by the latest
retention policy in the room, rather than the one in effect when the event was
sent. This might be controversial as, in Matrix, the state that an event is
subject to is usually the state of the room at the time it was sent. However,
there are a few issues with using the retention that was in effect at the time
the event was sent:

* it would create holes in the DAG of a room which would complexify the
  server-side handling of the room's history
* malicious servers could potentially make an event evade retention policies by
  selecting their event's `prev_events` and `auth_events` so that the event is
  on a portion of the DAG where the policy does not exist
* it would be difficult to translate the configuration of retention policies
  into a clear and easy to use UX (especially considering server-side
  configuration applies to the whole history of the room)
* it would not allow room administrators to retroactively update the lifetime of
  events that have already been sent (e.g. if the context of a room administered
  by an organisation which requirements for data retention change over time)

This proposal does not cover per-message retention (i.e. the ability to set
different lifetimes to different messages). This has been split out into
[MSC2228](https://github.com/matrix-org/matrix-spec-proposals/pull/2228) to
simplify this proposal.

This proposal does also not cover the case where a room's administrator wishes
to only restrict the lifetime of a specific section of the room's history. This
is left to be covered by a separate MSC, possibly built on top of MSC2228.

## Security considerations

In a context of open federation, it is worth keeping in mind the possibility
that not all servers in a room will enforce its retention policy. Similarly,
different servers will likely enforce different server-side configuration, and
as a result calculate different lifetimes for a given event. This proposal aims
at trying to compromise between finding an absolute consensus on an event's
lifetime and working within the constraints of a server's operator in terms of
data retention.

In a kind of contradictory way with the previous paragraph, a server may keep an
expired event in its database for some time after its expiration, while not
sharing it with clients and federating servers. This is in order to prevent
abusers from using low lifetime values in a room's retention policy in order to
erase any proof of such abuse and avoid being investigated.

Basing the expiration time of an event on its `origin_server_ts` is not ideal as
this field can be falsified by the sending server. However, there currently
isn't a more reliable way to certify the send time of an event.

As mentioned previously in this proposal, servers might store expired events for
longer than their lifetime allows, either for performance reason or to mitigate
abuse. This is considered acceptable as long as:

* an expired event is not kept permanently
* an expired event is not shared with clients and federated servers

## Unstable prefixes

While this proposal is under review, the `m.room.retention` event type should be
replaced by the `org.matrix.msc1763.retention` type.

Similarly, the `/_matrix/client/v3/retention/configuration` path should be replaced with `/_matrix/client/unstable/org.matrix.msc1763/retention/configuration`.
