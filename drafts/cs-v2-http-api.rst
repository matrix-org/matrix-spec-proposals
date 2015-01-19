Client-Server v2 HTTP API Draft
===============================

Filter API
----------

The intersection of the parameters given defines the filter.  Unions of filters
can be achieved by querying multiple filters in parallel.

XXX: Filters describe both what data to query and how to present it, so could
perhaps be better described as 'queries' or even 'subscriptions'?

XXX: Is this actually sensible - should we instead have ordering & pagination &
limits etc provided per-query rather than lost in the filter?  Or you provide the
defaults in the filter definition, and then clobber them with query params.

You can define a reusable filter with the below POST API.  The resulting filter_id
can then be passed to methods which can be filter.

You can only create filters for your own user (filters are namespaced per user
as they are defined per-user data, like profiles etc)

TODO: excluding filters (e.g. filter out "org.matrix.neb.*")

XXX: how do we transition between non-coalesced pagination and coalesced pagination for related_to/updates

::

    POST /user/{userId}/filter

.. code:: javascript    
    
    {
        // selectors: (bluntly selecting on the unencrypted fields)
        types: [ "m.*", "net.arasphere.*" ],    // default: all
        not_types: [ "m.presence" ],            // default: none
        rooms: [ "!83wy7whi:matrix.org" ],      // default: all (may be aliases or IDs. wildcards supported)
        not_rooms: [],
        senders: [ "@matthew:matrix.org" ],  // default: all (e.g. for narrowing down presence, and stalker mode. wildcards supported)
        not_senders: [],
        
        // XXX: do we want this per-query; is it valid to reuse it?
        // we probably don't need this as querying per-event-ID will be a parameter from a seperate API,
        // with its own seperate filter token & pagination semantics.
        event_ids: [ "$192318719:matrix.org" ], // default: all - useful for selecting relates_to data for a given event
        not_event_ids: [] // questionable
        
        // parameters
        
        // 'format' gives the desired shape of the response
        //   federation = include the federation layer as well as the raw content of events.
        //   events = the plain events
        format: "federation",
        
        // select specific specific fields of the event to be returned.
        // N.B. you cannot guaranteeing filter content fields as they may be encrypted.
        // e.g. selecting just event_id could be useful for doing server-side
        // sorting/pagination/threading
        select: [ "event_id", "origin_server_ts", "thread_id", "content", "content.body" ], 
        
        // include bundled child-event updates (default false)
        bundle_updates: true,
        
        // include bundled related events
        bundle_relates_to: [
            {
                relationship: "in_reply_to",
                // As this is an optimisation to avoid having to explicitly select/paginate the
                // related messages per-message, we have to include a limit here as if we were
                // actually executing the query per-message for the initial result set.
                // Limit gives the number of related events to bundle; the bundled events return chunk tokens
                // to let you seperately paginate on them.
                limit: 10, // maximum number of related events to bundle in the results of this filtered result set.
                ancestors: true, // include all ancestors (default: true)
                descendents: true, // include all descendents (default: true)
                
                <recursively include a filter definition here for the subset of events>
                // need to support a sort criteria which reflects the linearised ordering of the relation graph
            },
        ],
        
        // server-side sorting, so we can paginate serverside on a thin client.
        // N.B. we can only order by unencrypted fields.
        // N.B. clients will need to handle out-of-order messages intelligently
        // N.B. subset of things you're allowed to sort by may be arbitrarily
        // restricted by the server impl (XXX: capabilities?)
        // Servers must support the "timeline" ordering - which is linearised logical chronological ordering.
        // N.B. This only takes effect when paginating, and is ignored for streaming data, and can only be specified once per filter.
        sort: [
            // sort by sender, and then by the timeline
            {   
                type: "sender",
                dir: "asc", // default asc
            },
            {   
                type: "timeline",
                dir: "asc",
            },
        ],
    }

Returns ``200 OK``::
    
    {
        "filter_id": "583e98c2d983"
    }


"Sync API" (was Event Stream API / Global initial sync API)
-----------------------------------------------------------

There is no difference between an incremental initial sync of events and polling for updates on the eventstream.  They both transfer a delta of events from the server to the client, and both deltas need to be capped to avoid DoSing the client if too much time has elapsed between syncs.  Initial sync is thus a capped incremental delta of events relative to clean client-side state.

Therefore we propose combining them into a single /sync API.  It's important to note that we should not design out server->client pushed event updates - the data returned by /sync polling should also be suitable for pushing if available (with suitable gapping/capping to avoid DoSing the client).  XXX: do this!

``GET /sync``

TODO: https://matrix.org/jira/browse/SYN-168
    /initialSync should return the actual m.room.member invite, not random keys from it

GET parameters::

    limit: maximum number of events per room to return.  If this limit is exceeded:
           1. the server must flag the gap in the response (to avoid ambiguity between hitting the limit and exceeding the limit)
           2. the client must either throw away older timeline information or model a 'gap' in the timeline
           3. the server must include the full delta of state keys since the last sync, but will truncate the timeline delta.

    // the sort order of messages in the room, *only honoured during an initial sync*. default: "timeline,asc". may appear multiple times
    // subsequent calls to /sync will always return event updates in timeline order (thanks to causality)
    // the chunk tokens per-room are dependent on the sort order and cannot be mixed between different uses of the same filter.
    // the use case here is to start paginating a room sorted by not-timeline (e.g. by sender id - e.g. mail client use case)
    sort: fieldname, direction (e.g. "sender,asc"). 
    
    since: <chunk token> to request an incremental delta since the specified chunk token
        We call this 'since' rather than 'from' because it's not for pagination but a delta.
        The specified chunk token would be taken from the most recent sync request that completed for this filter.
    timeout: maximum time to poll (in milliseconds) before returning this request. Only meaningful if performing an incremental sync (i.e. `since` is set)
        
    set_presence: "offline" // optional parameter to tell the server not to interpret this request as a client as coming online (and as a convenience method for overriding presence state in general)
    
    presence: true/false (default true): do we want to show presence updates?
    userdata: true/false (default true): do we want to include updates to user data?
    
    backfill: true/false (default true): do we want to pull in state from federation if we have less than <limit> events available for a room?
             
    filter: <filter_id> // filters can change between requests, to allow us to narrow down a global initial sync to a given room or similar use cases.
    // filter overrides (useful for changing filters between requests)
    filter_type: wildcard event type match e.g. "m.*", "m.presence": default, all.  may appear multiple times.
    filter_room: wildcard room id/name match e.g. "!83wy7whi:matrix.org": default, all.  may appear multiple times.
    filter_sender: wildcard sender id match e.g. "@matthew:matrix.org": default, all.  may appear multiple times.
    filter_event_id: event id to match e.g. "$192318719:matrix.org" // default, all: may appear multiple times
    filter_format: "federation" or "events"
    filter_select: event fields to return: default, all.  may appear multiple times
    filter_bundle_updates: true/false: default, false. bundle updates in events.
    // we deliberately don't specify filter_bundle_relates_to, as it's too hard to serialise into querystring params

Returns ``200 OK``:

.. code:: javascript
    
    // where compact is false:
    {
        "next_chunk": "s72595_4483_1934", // the chunk token we pass to /sync's since param
        
        "eventMap": {
            "$14qwtyeufet783:matrix.org": {
                    "avatar_url": "http://matrix.tp.mu:8008/_matrix/content/QG1hdHRoZXc6dHAubXUOeJQMWFMvUdqdeLovZKsyaOT.aW1hZ2UvanBlZw==.jpeg",
                    "displayname": "Matthew Hodgson",
                    "last_active_ago": 368200528,
                    "presence": "online",
                    "sender": "@matthew:tp.mu"
                },
                "type": "m.presence", 
                "edu": true, // N.B. explicitly flag EDUs as not to be stored 
            },
            
            "$1417731086506PgoVf:matrix.org": {
                "content": {
                    "avatar_url": "https://matrix.org/_matrix/content/QG1hdHRoZXc6bWF0cml4Lm9yZwxaesQWnqdynuXIYaRisFnZdG.aW1hZ2UvanBlZw==.jpeg",
                    "displayname": "Matthew",
                    "membership": "join"
                },
                "membership": "join",
                "origin_server_ts": 1417731086795,
                "prev_state": [["$1416420706925RVAWP:matrix.org", {
                    "sha256": "zVzi02R5aeO2HQDnybu1XuuyR6yBG8utLE/i1Sv8eyA"
                }
                ]],
                // "room_id": "!KrLWMLDnZAyTapqLWW:matrix.org", // remove this in compact form as it's redundant
                "state_key": "@matthew:matrix.org",
                "type": "m.room.member",
                "sender": "@matthew:matrix.org"    
            }
        }
        
        // updates about our own user data
        "user": {
            // XXX: need a way to map user data (presence updates, profile updates, contact updates etc) into here - either as events or something else
        },
                
        // updates about other users' data (that the server thinks we care about - XXX: how do we filter this, beyond turning it bluntly on & off?)
        // XXX: Should this be combined with "user"?
        "presence": [
            "$14qwtyeufet783:matrix.org"
        ],
        
        "rooms": [{
            // "membership": "join",  // this now gets removed as redundant with state object, likewise invite keys (i.e. "invitee")
            "events": { // rename messages to events as this is a list of all events, not just messages (non-state events).
                        // gives a list of events, limited to $limit in length
                "chunk": [
                    "$1417731086506PgoVf:matrix.org", ...
                ],
                "next_chunk": "s72595_4483_1934",   // for syncing forwards, filtered just to this room? XXX: feels a bit too magical to imply a new filter...
                "prev_chunk": "t67-41151_4483_1934" // for scrollback
            },
            "room_id": "!KrLWMLDnZAyTapqLWW:matrix.org",
            "state": [ "$1417731086506PgoVf:matrix.org" ],
            "limited": true, // has the limit been exceeded for the number of events returned for this room? if so, the client should be aware that there's a gap in the event stream
            "visibility": "public",  // this means it's a published room... but needs to be better represented and not use the word 'public'
        }]
    }
    
Room Creation API
-----------------

Joining API
-----------

Room History
------------

Scrollback API
~~~~~~~~~~~~~~

::

    GET /rooms/<room_id>/events

GET parameters::

    from: the chunk token to paginate from
    Otherwise same as /sync, except "since", "timeout", "presence" and "set_presence" are not implemented

Returns ``200 OK``:

.. code:: javascript

    // events precisely as per a room's events key as returned by sync, with the events expanded out inline
    {
        "chunk": [{
            "age": 28153452, // how long as the destination HS had the message + how long the origin HS had the message
            "content": {
                "body": "but obviously the XSF believes XMPP is the One True Way",
                "msgtype": "m.text"
            },
            "event_id": "$1421165049511TJpDp:matrix.org",
            "origin_server_ts": 1421165049435,
            "room_id": "!cURbafjkfsMDVwdRDQ:matrix.org",
            "type": "m.room.message",
            "sender": "@irc_Arathorn:matrix.org"
        }, {
            "age": 28167245,
            "content": {
                "body": "which is all fair enough",
                "msgtype": "m.text"
            },
            "event_id": "$1421165035510CBwsU:matrix.org",
            "origin_server_ts": 1421165035643,
            "room_id": "!cURbafjkfsMDVwdRDQ:matrix.org",
            "type": "m.room.message",
            "sender": "@irc_Arathorn:matrix.org"
        }],
        "prev_chunk": "t9571-74545_2470_979",
    }

Contextual windowing API
~~~~~~~~~~~~~~~~~~~~~~~~
::

    GET /events/<event_id>

GET parameters::

    context: "before", "after" or "around"
    Otherwise same as sync, without "since", "presence", "timeout" and "set_presence"
    
Returns ``200 OK``:

.. code:: javascript

    // the room in question, formatted exactly as a room entry returned by /sync with the events expanded out inline
    // with the event in question present in the list as determined by the context param
    {
        "event_map": {
            "$1417731086506PgoVf:matrix.org": {
                "content": {
                    "avatar_url": "https://matrix.org/_matrix/content/QG1hdHRoZXc6bWF0cml4Lm9yZwxaesQWnqdynuXIYaRisFnZdG.aW1hZ2UvanBlZw==.jpeg",
                    "displayname": "Matthew",
                    "membership": "join"
                },
                "membership": "join",
                "origin_server_ts": 1417731086795,
                "prev_state": [["$1416420706925RVAWP:matrix.org", {
                    "sha256": "zVzi02R5aeO2HQDnybu1XuuyR6yBG8utLE/i1Sv8eyA"
                }
                ]],
                "room_id": "!KrLWMLDnZAyTapqLWW:matrix.org",
                "state_key": "@matthew:matrix.org",
                "type": "m.room.member",
                "sender": "@matthew:matrix.org"    
            }
        },
        "membership": "join",
        "events": {
            "chunk": [ "$1417731086506PgoVf:matrix.org" ],
            "next_chunk": "s72595_4483_1934",
            "prev_chunk": "t67-41151_4483_1934"
        },
        "room_id": "!KrLWMLDnZAyTapqLWW:matrix.org",
        "state": [ "$1417731086506PgoVf:matrix.org" ],
        "visibility": "public"
    }


Room Alias API
--------------

Room Directory API
------------------

User Profile API
----------------

Provides arbitrary per-user global state JSON storage with namespaced keys,
some of which have specific predefined serverside semantics. Keys must be named
(we don't support POSTing to anonymous key names)

::

    PUT /user/{userId}/data/m.displayname
    PUT /user/{userId}/data/m.avatar_url
    PUT /user/{userId}/data/m.contact_vcard
    PUT /user/{userId}/data/net.arasphere.client.preferences

Address Book API
----------------

FIXME: XXX: Dave - can we do better than this?

Store basic JSON vcards into per-user data.

::
    PUT /user/{userId}/contacts/{deviceId}?baseVer=???
    { bulk incremental update of contacts relative to baseVer, keyed by an contactId (as defined by the client) }
    returns the new 'ver' version of the updated contact datastructure

    GET /user/{userId}/contacts/{deviceId}?baseVer=???
    returns the delta of contact information for this device since baseVer.


Account Management API
----------------------

Actions API
-----------

Presence API
------------

::

    PUT /user/{userId}/presence/m.status // set DND/asleep/on holiday etc -
    // XXX: do we need to distinguish between internationalisable presets like DND
    // and free-form textual status messages?
    // XXX: should this be in /user/{userId}/data/m.status instead?
    // what's actually the difference? surely status is no different to avatar
    // updates in terms of needing to be pushed around
    
    PUT /device/{deviceId}/presence/m.presence // explicitly set online/idle/offline
    // or /presence/device/{deviceId}
    
    // XXX: need to remember how to handle activity notifications

Typing API
----------

Relates_to pagination API
-------------------------

Capabilities API
----------------

