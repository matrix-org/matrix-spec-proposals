# MSC1776: Proposal for implementing peeking via /sync in the CS API

## Problem

Peeking into rooms without joining them currently relies on the deprecated v1
/initialSync and /events APIs.

This poses the following issues:

 * Servers and clients must implement two separate sets of event-syncing logic,
   doubling complexity.
 * Peeking a room involves setting a stream of long-lived /events requests going.
   Having multiple streams is racey, competes for resources with the /sync stream,
   and doesn't scale given each room requires a new /events stream.

## Solution

We extend /sync to support peeking into rooms on demand.

This can be done as part of extending /sync to also support paginating results
per-room, which is desirable for reducing the size of initial /syncs and making
them more granular, in order to speed up login.

Proposal: we add a POST form of /sync, which lets the user add/remove additional
filters on the fly in order to aid peeking into specific sets of rooms with
specific filters.  Filtering on rooms which you are not joined to is considered
a request to peek.  We also let it support paginating results by grouping them
into batches of rooms.

**Conceptually** this could look like something like:
```json
POST /sync
{
    "filters": [
        "normal sync filter (limit results to 10 rooms at a time)",
        "peek just m.flair on this set of rooms (to discover flair for users)"
        "peek full room that we're previewing",
        "peek full room a profile-room we're looking at",
        "peek just m.room.{name,avatar}, m.subgroup on this set of rooms (to display groups-as-rooms)",
    ],
    "pagination": {
        "room_limit": 10
    }
}
```

The `pagination` field would support two fields:
 * `room_limit` (which limits the number of rooms returned in a given /sync
    response) parameter
 * `room_order` (a constant that defines the ordering of the rooms within a /sync
    response. only "m.origin_ts" would be defined).

To avoid the hassle of manually maintaining filters, the act of specifying a
filter could automatically memoize it on the server so that it can be
efficiently referred to in future.  (The resulting filter ID could be returned
in the /sync response).

So, **concretely**, this would look something like:

```json
POST /sync
{
    "filters": [
        {
            "room": {
                "state": {
                    "lazy_load_members": true
                },
                "timeline": {
                    "limit": 20
                },
            }
        },
        {
            "room": {
                "rooms": [
                    "!pr0file1:example.com",
                    "!pr0file2:example.com",
                    "!pr0file3:example.com",
                ],
                "state": {
                    "types": [
                        "m.flair"
                    ]
                }
            }
        },
    ],
    "paginate": {
        "room_limit": 10
    }
}
```

...to request a sync which gives us both the normal timeline, as well as peek
changes in flair events for 3 users we're stalking because they're in the timeline
currently displayed on screen.

In case of receiving large sync responses (initial or catchup sync), we request
them to be batched with no more than 10 rooms per response.

The sync response would include:

```json
{
    "filter_ids": [123, 124]
}
```

...to give the user the IDs of the filter objects which were implicitly created
from the POST, so that they can be reused in subsequent invocations of /sync
directly.  Alternatively, the filter IDs could be encoded into the sync token so
that subsequent `GET /sync` did the right thing without needing to restate the
filters.

## Hybrid sync

This pattern also enables "hybrid sync" (proposed during the June 2018
brainstorm with Manu/Erik/Matthew and others when considering how to speed up
initial sync), in that a slow large granular incremental sync could be
interrupted and later resumed in order to prioritise loading specific rooms as
the user navigates the app.

## Tradeoffs

The API shape here is picked quite naively as it seems to do the job.  There are
probably many other ways to skin the cat.

## Security considerations

Need to worry about clients DoSing by requesting overly unpleasant filters?

## Issues

How do we represent peek failures?

## Dependencies

This unblocks MSC1769 (profiles as rooms) and MSC1772 (groups as rooms)
This depends on MSC1777 (peeking over federation) to work well in practice.

## History

This takes some inspiration from Erik's original 'paginated sync' PR to Synapse
from 2016: https://github.com/matrix-org/synapse/pull/893/files
