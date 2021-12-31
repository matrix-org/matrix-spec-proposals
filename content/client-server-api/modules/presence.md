---
type: module
---

### Presence

Each user has the concept of presence information. This encodes:

-   Whether the user is currently online
-   How recently the user was last active (as seen by the server)
-   Whether a given client considers the user to be currently idle
-   Arbitrary information about the user's current status (e.g. "in a
    meeting").

This information is collated from both per-device (`online`, `idle`,
`last_active`) and per-user (status) data, aggregated by the user's
homeserver and transmitted as an `m.presence` event. Presence events are
sent to interested parties where users share a room membership.

User's presence state is represented by the `presence` key, which is an
enum of one of the following:

-   `online` : The default state when the user is connected to an event
    stream.
-   `unavailable` : The user is not reachable at this time e.g. they are
    idle.
-   `offline` : The user is not connected to an event stream or is
    explicitly suppressing their profile information from being sent.

#### Events

{{% event-group group_name="m.presence" %}}

#### Client behaviour

Clients can manually set/get their presence using the HTTP APIs listed
below.

{{% http-api spec="client-server" api="presence" %}}

##### Last active ago

The server maintains a timestamp of the last time it saw a pro-active
event from the user. A pro-active event may be sending a message to a
room or changing presence state to `online`. This timestamp is presented
via a key called `last_active_ago` which gives the relative number of
milliseconds since the pro-active event.

To reduce the number of presence updates sent to clients the server may
include a `currently_active` boolean field when the presence state is
`online`. When true, the server will not send further updates to the
last active time until an update is sent to the client with either a)
`currently_active` set to false or b) a presence state other than
`online`. During this period clients must consider the user to be
currently active, irrespective of the last active time.

The last active time must be up to date whenever the server gives a
presence event to the client. The `currently_active` mechanism should
purely be used by servers to stop sending continuous presence updates,
as opposed to disabling last active tracking entirely. Thus clients can
fetch up to date last active times by explicitly requesting the presence
for a given user.

##### Idle timeout

The server will automatically set a user's presence to `unavailable` if
their last active time was over a threshold value (e.g. 5 minutes).
Clients can manually set a user's presence to `unavailable`. Any
activity that bumps the last active time on any of the user's clients
will cause the server to automatically set their presence to `online`.

#### Security considerations

Presence information is shared with all users who share a room with the
target user. In large public rooms this could be undesirable.
