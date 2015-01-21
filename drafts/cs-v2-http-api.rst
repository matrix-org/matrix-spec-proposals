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
        // N.B. types can be used to filter out presence and server-generated events (e.g. m.profile), but see *_user_data below
        not_types: [ "m.presence" ],            // default: none
        rooms: [ "!83wy7whi:matrix.org" ],      // default: all (may be aliases or IDs. wildcards supported)
        not_rooms: [],
        senders: [ "@matthew:matrix.org" ],  // default: all (e.g. for narrowing down presence, and stalker mode. wildcards supported)
        not_senders: [],
        
        public_user_data: true,  // include events describing public user data (as we might not know their types) - default: true
        private_user_data: true, // include events describing private user data (as we might not know their types) - default: true
        // XXX: How do these interact with specific type/non_type selectors prioritywise?
                
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
        
        // include bundled child-event updates (default false) // V2.0
        bundle_updates: true,
        
        // include bundled related events: // V2.1
        bundle_relates_to: [
            {
                relationship: "in_reply_to",
                // As this is an optimisation to avoid having to explicitly select/paginate the
                // related messages per-message, we have to include a limit here as if we were
                // actually executing the query per-message for the initial result set.
                // Limit gives the number of related events to bundle; the bundled events return batch tokens
                // to let you seperately paginate on them.
                limit: 10, // maximum number of related events to bundle in the results of this filtered result set.
                ancestors: true, // include all ancestors (default: true)
                descendents: true, // include all descendents (default: true)
                
                <recursively include a filter definition here for the subset of events>
                // need to support a sort criteria which reflects the linearised ordering of the relation graph
            },
        ],
                
        // XXX: we may also want room_sort to specify the order of rooms returned by /sync,
        // as well as pagination for rooms returned by /sync...
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

    limit: maximum number of events per room to return.  If this limit is exceeded and gap is true:
            1. the server must flag the gap in the response (to avoid ambiguity between hitting the limit and exceeding the limit)
            2. the client must either throw away older timeline information or model a 'gap' in the timeline
            3. the server must include the full delta of state keys since the last sync, but will truncate the timeline delta.
           If this limit is exceeded and gap is false:
            1. we just send through the next batch of events in the next call to /sync, without any gapping.
           
    gap: boolean - should we drop events and do a non-delta sync for rooms whose limit is exceeded.  default: true.

    // server-side sorting, so we can paginate events serverside on a thin client.
    // N.B. we can only order by unencrypted fields.
    // N.B. clients will need to handle out-of-order messages intelligently
    // N.B. subset of things you're allowed to sort by may be arbitrarily
    // restricted by the server impl (XXX: capabilities?)
    // Servers MUST support the "timeline" ordering - which is linearised logical chronological ordering.
    // N.B. This only takes effect when paginating, and is ignored for streaming data, and can only be specified once per filter.
    //
    // the sort order of messages in the room, *only honoured during an initial sync*. default: "timeline,asc". may appear multiple times
    // subsequent calls to /sync will always return event updates in timeline order (thanks to causality)
    // the batch tokens per-room are dependent on the sort order and cannot be mixed between different uses of the same filter.
    // the use case here is to start paginating a room sorted by not-timeline (e.g. by sender id - e.g. mail client use case)
    sort: fieldname, direction (e.g. "sender,asc",).
    
    // XXX: this needs to be made prettier.  you can't be a boolean because normal server behaviour allows small misorderings.
    // This this is an optimisation to allow thin clients to save bandwidth and not see out-of-order events which they can't
    // do anything useful with.  However, small races should be allowed.
    // v2.1
    // exclude_out_of_order_events_older_than: 10000 // ignore misorderings worse than 10s
    
    since: <batch token> to request an incremental delta since the specified batch token
        We call this 'since' rather than 'from' because it's not for pagination but a delta.
        The specified batch token would be taken from the most recent sync request that completed for this filter.
    timeout: maximum time to poll (in milliseconds) before returning this request. Only meaningful if performing an incremental sync (i.e. `since` is set)
        
    set_presence: "offline" // optional parameter to tell the server not to interpret this request as a client (device) as coming online (and as a convenience method for overriding presence state in general - e.g. setting straight to "idle" rather than having to PUT to /users/{userId}/devices/{deviceId}/presence.  It's meaningless to set "online" as that's the default behaviour on the server.)
        
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
        "next_batch": "s72595_4483_1934", // the batch token we pass to /sync's since param
        
        // updates about our own user data
        "private_user_data": {
            "$15zxhijvwguye:matrix.org": {
                "sender": "@matthew:tp.mu"
                type: "net.arasphere.weird.setting",
                content: {
                    setting1: true,
                    setting2: false,
                }
            },
        },
                
        // updates about publically published users' data
        "public_user_data": [
            "$14qwtyeufet783:matrix.org": {
                "sender": "@matthew:tp.mu"
                type: "m.profile.avatar_url",
                content: {
                    avatar_url: "mxc://matrix.org/QG1hdHRoZXc6d",
                }
            },
            "$14qwtyeufet784:matrix.org": {
                "sender": "@matthew:tp.mu"
                type: "m.profile.display_name",
                content: {
                    display_name: "Matthew",
                }
            },
            "$14qwtyeufet785:matrix.org": {
                "sender": "@matthew:tp.mu"
                type: "m.presence", // the global per-user presence as calculated serverside by aggregating the per-device presence data
                content: {
                    presence: "idle" // one of online/idle/offline
                    "last_active": 368200528, // when did the server last see proactive interaction from this user on any client.
                }
            },
        ],
        
        "rooms": [{       
            "room_id": "!KrLWMLDnZAyTapqLWW:matrix.org",
            "limited": true, // has the limit been exceeded for the number of events returned for this room? if so, the client should be aware that there's a gap in the event stream
            "published": true, // HS telling us that this room has been published in our aliases directory
         
            "event_map": {
                "$1417731086506PgoVf:matrix.org": {
                    "type": "m.room.member",
                    "content": {
                        "membership": "join"
                    },
                    "origin_server_ts": 1417731086795,
                    "state_key": "@matthew:matrix.org",
                    "sender": "@matthew:matrix.org"    
                },
        
                "$13275681auxsabj:matrix.org": {
                    "type": "m.room.member.profile",
                    content: {
                        "avatar_url": "mxc://matrix.org/QG1hdHRoZXc6d",
                        "displayname": "Matthew",
                    },
                    prev_content: {
                        "avatar_url": "mxc://matrix.org/QG1hdHRoZXc6d",
                        "displayname": "Arathorn",
                    },
                    "origin_server_ts": 1417731086796,
                    "state_key": "@matthew:matrix.org",
                    "sender": "@matthew:matrix.org"    
                },

                "$15e789t23987:matrix.org": {
                    "type": "m.room.message",
                    "unsigned": {
                        "age": "124524",
                        "txn_id": "1234", // the transaction ID that the client specified in /send/{event_type}
                    },
                    content: {
                        "body": "I am a fish",
                        "msgtype": "m.text",
                    },
                    "origin_server_ts": 1417731086797,
                    "sender": "@matthew:matrix.org"    
                },
            },
        
            // "membership": "join",  // this now gets removed as redundant with state object, likewise invite keys (i.e. "invitee")
            "events": { // rename messages to events as this is a list of all events, not just messages (non-state events).
                        // gives a list of events, limited to $limit in length
                "batch": [
                    "$1417731086506PgoVf:matrix.org",
                    "$13275681auxsabj:matrix.org",
                    "$15e789t23987:matrix.org", ...
                ],
                
                // We don't have a next_batch because if we want to stream forwards we use
                // GET /sync?since=batch&filter_room=!KrLWMLDnZAyTapqLWW:matrix.org
                
                "prev_batch": "t67-41151_4483_1934" // for scrollback.
                // N.B. if you use prev_batch to scroll backwards you will receive events you already saw
                // if you have been calling /sync multiple times.  This is only useful for really thin clients.
                // If the client is tracking client-side history, then they should only store the prev_batch if
                // `limited` is true.
            },

            "state": [
                "$1417731086506PgoVf:matrix.org"
                "$13275681auxsabj:matrix.org", ...
            ],
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

    from: the batch token to paginate from
    Otherwise same as /sync, except "since", "timeout", "presence" and "set_presence" are not implemented

Returns ``200 OK``:

.. code:: javascript

    // events precisely as per a room's events key as returned by sync, with the events expanded out inline
    {
        "batch": [{
            "unsigned": {
                "age": 28153452, // how long (ms) as the destination HS had the message + how long the origin HS had the message
            },
            "content": {
                "body": "but obviously the XSF believes XMPP is the One True Way",
                "msgtype": "m.text"
            },
            "event_id": "$1421165049511TJpDp:matrix.org",
            "origin_server_ts": 1421165049435,
            "type": "m.room.message",
            "sender": "@irc_Arathorn:matrix.org"
        }, {
            "unsigned": {
                "age": 28167245,
            },
            "content": {
                "body": "which is all fair enough",
                "msgtype": "m.text"
            },
            "event_id": "$1421165035510CBwsU:matrix.org",
            "origin_server_ts": 1421165035643,
            "type": "m.room.message",
            "sender": "@irc_Arathorn:matrix.org"
        }],
        "prev_batch": "t9571-74545_2470_979",
    }

Contextual windowing API
~~~~~~~~~~~~~~~~~~~~~~~~

Supports bookmarking of specific events allowing you to jump into history and scroll back and forth.
We don't support reporting on historical user_data (profiles, presence) unless it's in the message graph.

Bookmarks look like::

    mx://{homeserver}/{event_id}
        // `homeserver` is the HS of the person who's handing out the link
    e.g. mx://matrix.org/$128397978128aho:arasphere.net

Client hits their own homeserver passing in the details from the mx:// URL.
The user MUST be joined to the room in order to read its history - this 403s
if the user is not in the room and returns `{ room_id: "!1249y83ty98:matrix.org", room_aliases: [ "#foobar:matrix.org" ] }`
so that the user can then decide whether to join and view the history.  We have to validate the room_alias to check
the server isn't lying.

::  
  
    GET /events/{event_id}?homeserver={homeserver}
    
GET parameters::

    context: "before", "after" or "around"
    homeserver: the homeserver to talk to in order to find out the room ID for this event
    Otherwise same as sync, without "since", "presence", "timeout" and "set_presence"
    
Returns ``200 OK``:

.. code:: javascript

    // the room in question, formatted exactly as a room entry returned by /sync with the events expanded out inline
    // with the event in question present in the list as determined by the context param
    {
        "room_id": "!KrLWMLDnZAyTapqLWW:matrix.org",
        "published": true,    
        "event_map": {
            "$1417731086506PgoVf:matrix.org": {
                "type": "m.room.member",
                "content": {
                    "membership": "join"
                },
                "origin_server_ts": 1417731086795,
                "state_key": "@matthew:matrix.org",
                "sender": "@matthew:matrix.org"    
            },
        
            "$13275681auxsabj:matrix.org": {
                "type": "m.room.member.profile",
                content: {
                    "avatar_url": "mxc://matrix.org/QG1hdHRoZXc6d",
                    "displayname": "Matthew",
                },
                prev_content: {
                    "avatar_url": "mxc://matrix.org/QG1hdHRoZXc6d",
                    "displayname": "Arathorn",
                },
                "origin_server_ts": 1417731086796,
                "state_key": "@matthew:matrix.org",
                "sender": "@matthew:matrix.org"    
            },

            "$15e789t23987:matrix.org": {
                "type": "m.room.message",
                content: {
                    "body": "I am a fish",
                    "msgtype": "m.text",
                },
                "origin_server_ts": 1417731086797,
                "sender": "@matthew:matrix.org"    
            },
        },
        "events": {
            "batch": [
                "$13275681auxsabj:matrix.org",
                "$15e789t23987:matrix.org",
            ],
            "next_batch": "s72595_4483_1934",
            "prev_batch": "t67-41151_4483_1934"
        },
        "state": [
            "$1417731086506PgoVf:matrix.org",
            "$13275681auxsabj:matrix.org",
         ],
    }


Room Alias API
--------------

Room Directory API
------------------

User Profile API
----------------

Provides arbitrary published per-user global state JSON storage with namespaced keys,
some of which have specific predefined serverside semantics. Keys must be named
(we don't support POSTing to anonymous key names)

::

    PUT /user/{userId}/public/{eventType}
    
    e.g.:

    PUT /user/{userId}/public/m.profile.displayname
    {
        // this is event content (like /send)
        display_name: "Matthew"
    }    
    
    PUT /user/{userId}/public/m.profile.avatar_url
    PUT /user/{userId}/public/m.profile.contact_vcard

    PUT /user/{userId}/public/m.profile.status // was "presence status" - e.g. "Do Not Disturb".
    // XXX: do we need to distinguish between internationalisable presets like DND
    // and free-form textual status messages?

You subscribe to particular events in your filter if you're not interested in particular info.

/*    
XXX: Preemie optimisation:
As per the profile propagation section, we can optimise merging profile
data into a single logical server-generated event in /sync as a special
case for specific data fields, e.g:::

    {
        type: "m.profile",
        content: {
            display_name: "Matthew",
            avatar_url: "mxc://...",
        }
    }
*/
    
User Data API
-------------

Provides arbitrary private per-user storage for synchronising settings etc.  Symmetrical with public info (see above)::

    PUT /user/{userId}/private/{eventType}


    PUT /user/{userId}/private/m.global_presence_offline
    {
        presence: "offline",
    }

    PUT /user/{userId}/private/net.arasphere.client.preferences
    {
        setting1: true,
        setting2: false,
    }

// XXX: Matthew wants this to be a generic object datastore so that clients can store
// their arbitrary data in here... but for v2 let's keep it as key-values to avoid total gallumphing creature feep.
// N.B. filters would then need to filter by path.

You subscribe to the events namespaces you care about in your filter.

Address Book API
----------------

XXX: We probably don't need this any time soon - synchronising addressbooks between devices is hardly core.

FIXME: XXX: Dave - can we do better than this?
XXX: also, can we extend the generic user data API above.

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

::

    // batched PUT  // v2.05

    // without batch PUT, clients will need to execute PUTs serially to maintain ordering.
    // Batching will avoid the client falling behind.

    // transaction IDs:
    PUT /room/{room_id}/send/{event_type}?txn_id=1234 // arbitrary txn_id token assigned by client per access_token

Presence API
------------

::

    // the server observes this in order to detect when the device
    // is overriding its online/idle/offline state.
    // this is what you hit if you don't specify set_presence on /sync
    // or the device wants to declare that it's idle.
    PUT /user/{userId}/private/devices/{deviceId}/m.device.presence
    {
        presence: "idle"
    }

// see Address Profile API for storing FB-style status    

Typing API
----------

Relates_to pagination API
-------------------------

Capabilities API
----------------

