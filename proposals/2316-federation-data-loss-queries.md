# Federation queries to aid with database recovery
Thanks to the federated nature of Matrix, servers losing their database does
not necessarily mean they lose all data: users and messages remain on other
servers in federated rooms. However, there is currently no way to find which
rooms a server was in, in order to re-synchronize them after data loss.

## Proposal
The proposed solution is a new `members` query type for the existing
`GET /_matrix/federation/v1/query/{queryType}` federation endpoint.

### Request
A server can make this request to any other server in the federation. The
responding server should only honor requests for information about the
requesting server. The response is a list of `m.room.member` events, either in
full or limited to `event_id`'s depending on a query string parameter. The list
of events is gathered from every room the responding server has persisted.

* A required query string parameter `origin=` requests data for a specific
  matrix origin (server name). Servers SHOULD deny `origin` values that do not
  match the `X-Matrix-Authorization` origin provided in the signed federation
  request.
* A query string parameter `pdus` can be used to alter the response from event
  IDs to full event objects.
* A query string parameter `limit_per_room=` specifies the maximum number of
  membership events to return per room. The responding server may enforce its
  own upper limit on the number of events per room as well.

### Response
200: An array of membership event IDs or events (depending on request) from the
current state of any rooms where this origin has any members that this server
is aware of.

## Tradeoffs

## Potential issues

## Security considerations
