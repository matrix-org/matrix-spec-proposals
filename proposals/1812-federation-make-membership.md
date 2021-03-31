# MSC 1813 - Federation Make Membership Room Version

This proposal adds a new `room_version` field to the responses of `/make_leave`
and `/make_join` APIs.

## Motivation

It is planned for future room versions to be able to change the format of events
in various ways. To support this, all servers must know the room version
whenever they need to parse an event.  Currently the `/make_*` APIs do not
include the room version in the response, so the requesting server is unable to
parse the event included in the response body.

## Proposal

Add a new `room_version` field to the response body of the `v1` `/make_join` and
`/make_leave` APIs, which describes the room version.

For backwards compatibility servers must correctly handle responses that do not
include the new field. In which case the room version is assumed to be one of
either `1` or `2`.
