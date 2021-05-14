Failures
--------

A server may encouter an error when trying to process an event received from a
remote server. In these cases the server may send a `failure` to the remote.

A `failure` references both the event that it was trying to process and the
event that triggered the processing. For example, a failure may be emitted if
one of the parents of the received events was not authorized.

A failure also includes a `severity` field that indicates what action was taken
by the server. There are three valid values:

  * `Fatal`: The server failed to parse the event. The event is dropped by the
    server as well as all descendants.
  * `Error`: The server rejected the event, for example due to authorization.
    That event is dropped, but descendants may be accepted.
  * `Warn`: The server accepted all events, but believes the remote did
    something wrong. For example, references an event the local server believes
    is unauthorized.


Data Flows
----------

Invite
++++++

To invite a remote user to an existing room a server distributes an invitiation
event signed by the remote invitee's server (allowing other servers in the room
to be sure that the invitee's server had seen the invite.)

To get the remote server's signature on the event it is sent in a special
request to the remote server, which then responds with the signed invite (if it
accepted it as valid.) The remote server may respond with an error if the user
does not exist.

Join
++++

If a server is already in the room it can simply emit a join event for the user
joining.

If the server is not currently in the room it needs to join via a remote server
in the room, therefore to join a room a server must have have both the room id
and a list of remote servers that may be in the room.

To join via a remote server the local server first requests a valid join event
for the room from the remote server. The local then fills it out, signs it, and
then sends the final join event to the remote server for distribution. The
remore responds to this second request with the current state of the room at
the join request and the auth chain for that state.


Authorization
-------------

The authorization for an event depends solely on the current state at that
event. If a policy server is configured for the room, then the authorization
for the event is the signature of the policy server.

The state events that affect whether an event is authorized are called
`protocol events`, and are:

  * `m.room.create`
  * `m.room.power_levels`
  * `m.room.member`
  * `m.room.join_rules`

All events *must* list all the protocol events that grant them their
authorization. All origin servers *must* serve up on request the full graph of
protocol events for all events it has sent. The graph of protocol events is the
connected directed acyclic graph with events as nodes and the list of protocol
events their edges.


Join
++++

A user may join a room if:

  * The join rule is "public".
  * The join rule is "invite" and the user has been invited by a user that has
    already joined.
  * The user is in the `may_join` list.


Invite
++++++

A user may invite another user if the join rule is either "public" or "invite"
and the user has joined the room.


Creation
++++++++

A `m.room.create` must be the first event in the room.


Ban, Kick and Redaction
+++++++++++++++++++++++

To ban or kick another user in the room, or to redact an event, then the user
must have a power level of at least that specificied in the
`m.room.power_level` event for kick, ban and redactions.


Other Events
++++++++++++

A user may send an event if all the following hold true:

  * The user is in the room.
  * If the type of the event is listed in the `m.room.power_levels`, then the
    user must have at least that power level. Otherwise, the user must have a
    power level of at least `events_default` or `state_default`, depending on
    if the event is a message or state event respectively.


Unauthorized Events
-------------------

An unauthorized event should not be accepted into the event graph, i.e. new
events should not reference any unauthorized events. There are situations where
this can happen and so it is not considered an error to include an unauthorized
event in the event graph. It is an error for events to refer unauthorized
events in their `auth_events` section and will in turn be considered
unauthorized.

A server may choose to store only the redacted form of an unauthorized event if
it is included in the event graph.

A server may emit a warning to a remote server if it references an event it
considers unauthorized.


State and Authorization Querying
--------------------------------

A local server may become aware that it and a remote server's view of the
current state are inconsistent. The local server may then send its current
state to the remote, which responds with its view of the current state. Both
servers should then recompute the local state. If they are conforming
implementations then they will reach the same conclusions.

