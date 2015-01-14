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

POST /user/{userId}/filter
{
    // selectors: (bluntly selecting on the unencrypted fields)
    types: [ "m.*", "net.arasphere.*" ],    // default: all
    rooms: [ "!83wy7whi:matrix.org" ],      // default: all (may be aliases or IDs. wildcards supported)
    sender_ids: [ "@matthew:matrix.org" ],  // default: all (e.g. for narrowing down presence, and stalker mode. wildcards supported)
    
    // XXX: do we want this per-query; is it valid to reuse it?
    // we probably don't need this as querying per-event-ID will be a parameter from a seperate API,
    // with its own seperate filter token & pagination semantics.
    event_ids: [ "$192318719:matrix.org" ], // default: all - useful for selecting relates_to data for a given event
    
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
       restricted by the server impl (XXX: capabilities?)
    // Servers must support the "timeline" ordering - which is linearised logical chronological ordering.
    // XXX: should this be done per-request rather than per-filter?  Given streaming APIs (like eventStream)
    // will be limited to sorting via timeline due to causality...
    sort: [
        // sort by sender, and then by the timeline
        {   
            type: "sender_id",
            dir: "asc", // default asc
        },
        {   
            type: "timeline",
            dir: "asc",
        },
    ],
}

Returns:
200 OK
{
    "filter_id": "583e98c2d983",
}


Global initial sync API
-----------------------

GET /initialSync

GET parameters::
    limit: maximum number of events per room to return
    sort: fieldname, direction (e.g. "sender_id,asc"). // default: "timeline,asc". may appear multiple times.
    since: <chunk token> to request an incremental update (*not* pagination) since the specified chunk token
        We call this 'since' rather than 'from' because it's not for pagination,
    backfill: true/false (default true): do we want to pull in state from federation if we have less than <limit> events available for a room?
    presence: true/false (default true): return presence info
    compact: boolean (default false): factor out common events.
             XXX: I *really* think this should be turned on by default --matthew
    filter: <filter_id> (XXX: allow different filters per room?)
    # filter overrides:
    filter_type: wildcard event type match e.g. "m.*": default, all.  may appear multiple times.
    filter_room: wildcard room id/name match e.g. "!83wy7whi:matrix.org": default, all.  may appear multiple times.
    filter_sender_id: wildcard sender id match e.g. "@matthew:matrix.org": default, all.  may appear multiple times.
    filter_event_id: event id to match e.g. "$192318719:matrix.org" // default, all: may appear multiple times
    filter_format: "federation" or "events"
    filter_select: event fields to return: default, all.  may appear multiple times
    filter_bundle_updates: true/false: default, false. bundle updates in events.

// FIXME: kegan: how much does the v1 response actually change here?

Returns:
200 OK
// where compact is false:
{
    "end": "s72595_4483_1934", // the chunk token we pass to from=
    
    // global presence info (if presence=true)
    "presence": [{
        "content": {
            "avatar_url": "http://matrix.tp.mu:8008/_matrix/content/QG1hdHRoZXc6dHAubXUOeJQMWFMvUdqdeLovZKsyaOT.aW1hZ2UvanBlZw==.jpeg",
            "displayname": "Matthew Hodgson",
            "last_active_ago": 368200528,
            "presence": "online",
            "user_id": "@matthew:tp.mu"
        },
        "type": "m.presence"
    }],
    
    "rooms": [{
        "membership": "join",
        "eventStream": { // rename messages to eventstream as this is a list of all events, not just messages (non-state events)
            "chunk": [{
                "content": {
                    "avatar_url": "https://matrix.org/_matrix/content/QG1hdHRoZXc6bWF0cml4Lm9yZwxaesQWnqdynuXIYaRisFnZdG.aW1hZ2UvanBlZw==.jpeg",
                    "displayname": "Matthew",
                    "membership": "join"
                },
                "event_id": "$1417731086506PgoVf:matrix.org",
                "membership": "join",
                "origin_server_ts": 1417731086795,
                "prev_content": {
                    "avatar_url": "https://matrix.org/_matrix/content/QG1hdHRoZXc6bWF0cml4Lm9yZwxaesQWnqdynuXIYaRisFnZdG.aW1hZ2UvanBlZw==.jpeg",
                    "displayname": "Ara4n",
                    "membership": "join"
                }
                "prev_state": [["$1416420706925RVAWP:matrix.org", {
                    "sha256": "zVzi02R5aeO2HQDnybu1XuuyR6yBG8utLE/i1Sv8eyA"
                }
                ]],
                "room_id": "!KrLWMLDnZAyTapqLWW:matrix.org",
                "state_key": "@matthew:matrix.org",
                "type": "m.room.member",
                "user_id": "@matthew:matrix.org"
            }],
            "end": "s72595_4483_1934",
            "start": "t67-41151_4483_1934"
        },
        "room_id": "!KrLWMLDnZAyTapqLWW:matrix.org",
        "state": [{
            "content": {
                "avatar_url": "https://matrix.org/_matrix/content/QG1hdHRoZXc6bWF0cml4Lm9yZwxaesQWnqdynuXIYaRisFnZdG.aW1hZ2UvanBlZw==.jpeg",
                "displayname": "Matthew",
                "membership": "join"
            },
            "event_id": "$1417731086506PgoVf:matrix.org",
            "membership": "join",
            "origin_server_ts": 1417731086795,
            "room_id": "!KrLWMLDnZAyTapqLWW:matrix.org",
            "state_key": "@matthew:matrix.org",
            "type": "m.room.member",
            "user_id": "@matthew:matrix.org"
        }],
        "visibility": "public"
    }]
}


// where compact is true:
{
    "end": "s72595_4483_1934",
    // global presence info
    "presence": [{
        "content": {
            "avatar_url": "http://matrix.tp.mu:8008/_matrix/content/QG1hdHRoZXc6dHAubXUOeJQMWFMvUdqdeLovZKsyaOT.aW1hZ2UvanBlZw==.jpeg",
            "displayname": "Matthew Hodgson",
            "last_active_ago": 368200528,
            "presence": "online",
            "user_id": "@matthew:tp.mu"
        },
        "type": "m.presence"
    }],
    "rooms": [{
        "events": {
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
                "user_id": "@matthew:matrix.org"    
            }
        },
        "membership": "join",
        "eventStream": { // rename messages to eventstream as this is a list of all events, not just messages (non-state events)
            "chunk": [ "$1417731086506PgoVf:matrix.org" ],
            "end": "s72595_4483_1934",
            "start": "t67-41151_4483_1934" // XXX: do we need start?
        },
        "room_id": "!KrLWMLDnZAyTapqLWW:matrix.org",
        "state": [ "$1417731086506PgoVf:matrix.org" ],
        "visibility": "public"
    }]
}

Event Stream API
----------------

GET /eventStream
GET parameters::
    from: chunk token to continue streaming from (e.g. "end" given by initialsync)
    filter*: as per initialSync (XXX: do we inherit this from the chunk token?)
    // N.B. there is no limit or sort param here, as we get events in timeline order as fast as they come.
    access_token: identifies both user and device
    timeout: maximum time to poll before returning the request
    presence: "offline" // optional parameter to tell the server not to interpret this as coming online

XXX: this needs to be updated from v1.  Presumably s/user_id/sender_id/?

Returns:
200 OK

// events precisely as per a room's eventStream key as returned by initialSync
// includes non-graph events like presence
{
    "chunk": [{
        "content": {
            "avatar_url": "https://matrix.org/_matrix/content/QG1hdHRoZXc6bWF0cml4Lm9yZwxaesQWnqdynuXIYaRisFnZdG.aW1hZ2UvanBlZw==.jpeg",
            "displayname": "Matthew",
            "last_active_ago": 1241,
            "presence": "online",
            "user_id": "@matthew:matrix.org"
        },
        "type": "m.presence"
    }, {
        "age": 2595,
        "content": {
            "body": "test",
            "msgtype": "m.text"
        },
        "event_id": "$14211894201675TMbmz:matrix.org",
        "origin_server_ts": 1421189420147,
        "room_id": "!cURbafjkfsMDVwdRDQ:matrix.org",
        "type": "m.room.message",
        "user_id": "@matthew:matrix.org"
    }],
    "end": "s75460_2478_981",
    "start": "s75459_2477_981" // XXX: do we need start here?
}

Room Creation API
-----------------

Joining API
-----------

Room History
------------

Scrollback API
~~~~~~~~~~~~~~

GET /rooms/<room_id>/events
GET parameters::
    from: the chunk token to paginate from
    Otherwise same as initialSync, except "compact", "since" and "presence" are not implemented

Returns:
200 OK

// events precisely as per a room's eventStream key as returned by initialSync
{
    "chunk": [{
        "age": 28153452, // XXX: age and origin_server_ts are redundant here surely
        "content": {
            "body": "but obviously the XSF believes XMPP is the One True Way",
            "msgtype": "m.text"
        },
        "event_id": "$1421165049511TJpDp:matrix.org",
        "origin_server_ts": 1421165049435,
        "room_id": "!cURbafjkfsMDVwdRDQ:matrix.org",
        "type": "m.room.message",
        "user_id": "@irc_Arathorn:matrix.org"
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
        "user_id": "@irc_Arathorn:matrix.org"
    }],
    "end": "t9571-74545_2470_979",
    "start": "t9601-75400_2470_979" // XXX: don't we just need end here as we can only paginate one way?
}

Contextual windowing API
~~~~~~~~~~~~~~~~~~~~~~~~

GET /events/<event_id>
GET parameters:
    context: "before", "after" or "around"
    Otherwise same as initialSync, except "since" and "presence" are not implemented
    
Returns:
200 OK

// the room in question, formatted exactly as a room entry returned by /initialSync
// with the event in question present in the list as determined by the context param
{
    "events": {
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
            "user_id": "@matthew:matrix.org"    
        }
    },
    "membership": "join",
    "eventStream": {
        "chunk": [ "$1417731086506PgoVf:matrix.org" ],
        "end": "s72595_4483_1934",
        "start": "t67-41151_4483_1934"
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

PUT /user/{userId}/data/m.displayname
PUT /user/{userId}/data/m.avatar_url
PUT /user/{userId}/data/m.contact_vcard
PUT /user/{userId}/data/net.arasphere.client.preferences

Account Management API
----------------------

Actions API
-----------

Presence API
------------

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

