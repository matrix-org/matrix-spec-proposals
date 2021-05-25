This is a standalone description of the data architecture of Synapse. There is a
lot of overlap with the current specification, so it has been split out here for
posterity. Hopefully all the important bits have been merged into the relevant
places in the main spec.


Model
-----

Overview
~~~~~~~~

Matrix is used to reliably distribute data between sets of `users`.

Users are associated with one of many matrix `servers`. These distribute,
receive and store data on behalf of its registered users. Servers can be run on
any host accessible from the internet.

When a user wishes to send data to users on different servers the local server
will distribute the data to each remote server. These will in turn distribute
to their local users involved.

A user sends and receives data using one or more authenticated `clients`
connected to his server. Clients may persist data locally or request it when
required from the server.

Events
~~~~~~
An event is a collection of data (the `payload`) and metadata to be distributed
across servers and is the primary data unit in Matrix.  Events are extensible
so that clients and servers can add extra arbitrary fields to both the payload
or metadata.

Events are distributed to interested servers upon creation. Historical events
may be requested from servers; servers are not required to produce all
or any events requested.

All events have a metadata `type` field that is used by client and servers to
determine how the payload should be processed and used. There are a number of
types reserved by the protocol for particular uses, but otherwise types may be
defined by applications, clients or servers for their own purposes.

.. TODO : Namespacing of new types.

Graph
+++++
Each event has a list of zero or more `parent` events. These relations form
directed acyclic graphs of events called `event graphs`. Every event graph has
a single root event, and each event graph forms the basis of the history of a
matrix room.

Event graphs give a partial ordering of events, i.e. given two events one may
be considered to have come before the other if one is an ancestor of the other.
Since two events may be on separate branches, not all events can be compared in
this manner.

Every event has a metadata `depth` field that is a positive integer that is
strictly greater than the depths of any of its parents. The root event should
have a depth of 1.

[Note: if one event is before another, then it must have a strictly smaller
depth]

Integrity
+++++++++

.. TODO: Specify the precise subset of essential fields

Portions of events will be signed by one or more servers or clients. The parent
relations, type, depth and payload (as well as other metadata fields that will
be specified) must be signed by the originating server. [Note: Thus, once an
event is distributed and referenced by later events, they effectively become
immutable].

The payload may also be encrypted by clients, except in the case where the
payload needs to be interpreted by the servers. A list of event types that
cannot have an encrypted payload are given later.


State
~~~~~
Event graphs may have meta information associated with them, called `state`.
State can be updated over time by servers or clients, subject to
authorisation.

The state of a graph is split into `sections` that can be atomically updated
independently of each other.

State is stored within the graph itself, and can be computed by looking at the
graph in its entirety. We define the state at a given event to be the state of
the sub graph of all events "before" and including that event.

Some sections of the state may determine behaviour of the protocol, including
authorisation and distribution. These sections must not be encrypted.

State Events
++++++++++++
`State events` are events that update a section of state data for a room. These
state events hold all the same properties of events, and are part of the event
graph. The payload of the event is the replacement value for the particular
section of state being updated.

State events must also include a `state_key` metadata field. The pair of fields
type and state_key uniquely defines the section of state that is to be updated.

State Resolution
++++++++++++++++
A given state section may have multiple state events associated with it in a
given graph. A consistent method of selecting which state event takes
precedence is therefore required.

This is done by taking the latest state events, i.e. the set of events that are
either incomparable or after every other event in the graph. A state resolution
algorithm is then applied to this set to select the single event that takes
precedence.

The state resolution algorithm must be transitive and not depend on server
state, as it must consistently select the same event irrespective of the server
or the order the events were received in.

State Dictionary
++++++++++++++++
The state dictionary is the mapping from sections of state to the state events
which set the section to its current value.  The state dictionary, like the
state itself, depends on the events currently in the graph and so is updated
with each new event received.

Since the sections of the state are defined by the pair of strings from the
type and state_key of the events that update them, the state dictionary can be
defined as a mapping from the pair (type, state_key) to a state event with
those values in the graph.

Deleting State
++++++++++++++
State sections may also be deleted, i.e. removed from the state dictionary. The
state events will still be present in the event graph.

This is done by sending a special state event indicating that the given entry
should be removed from the dictionary. These events follow the same rules for
state resolution, with the added requirement that it loses all conflicts.
[Note: This is required to make the algorithm transitive.]
