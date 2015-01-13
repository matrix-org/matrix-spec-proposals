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
    rooms: [ "!83wy7whi:matrix.org" ],      // default: all
    sender_ids: [ "@matthew:matrix.org" ],  // default: all (e.g. for narrowing down presence, and stalker mode)
    
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
    
    // include bundled child-event updates
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

200 OK
{
    "filter_id": "583e98c2d983",
}


Global initial sync API
-----------------------

XXX: need much more concrete general API definition first

GET /initialSync

GET parameters::
    limit: maximum number of events
    <generic pagination parameters (per room)>
    <some way of doing an incremental sync using streaming_tokens>
    filter: filter_id (XXX: allow different filters per room?)
    presence: true/false
    compact: boolean (default false): factor out common events.
             XXX: I *really* think this should be turned on by default --matthew


FIXME: example using v1 API just for compact proofing.  Needs to be updated with streaming_token voodoo
200 OK
// where compact is false:
{
    // XXX: does "end" die now?
    "end": "s72595_4483_1934",
    
    // global presence info. (XXX: should we only send content deltas if this is an delta initialsync - e.g. to avoid re-sending all avatar_urls?)
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
        "messages": {
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
        "messages": {
            "chunk": [ "$1417731086506PgoVf:matrix.org" ],
            "end": "s72595_4483_1934",
            "start": "t67-41151_4483_1934"
        },
        "room_id": "!KrLWMLDnZAyTapqLWW:matrix.org",
        "state": [ "$1417731086506PgoVf:matrix.org" ],
        "visibility": "public"
    }]
}

Event Stream API
----------------

Room Creation API
-----------------

Joining API
-----------

Scrollback API
--------------

Contextual windowing API
------------------------

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

Typing API
----------

Relates_to pagination API
-------------------------

Capabilities API
----------------

