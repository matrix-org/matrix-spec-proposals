# MSC2197 – Search Filtering in Public Room Directory over Federation

This MSC proposes introducing the `POST` method to the `/publicRooms` Federation
API endpoint, including a `filter` argument which allows server-side filtering
of rooms.

We are motivated by the opportunity to make searching the public Room Directory
more efficient over Federation.

## Motivation

Although the Client-Server API includes the filtering capability in
`/publicRooms`, the Federation API currently does not.

This leads to a situation that is wasteful of effort and network traffic for
both homeservers; searching a remote server involves first downloading its
entire room list and then filtering afterwards.

## Proposal

Having a filtered `/publicRooms` API endpoint means that irrelevant or
uninteresting rooms can be excluded from a room directory query response.
In turn, this means that these room directory query responses can be generated
more quickly and then, due to their smaller size, transmitted over the network
more quickly, owing to their smaller size.

These benefits have been exploited in the Client-Server API, which implements
search filtering using the `filter` JSON body parameter in the `POST` method on
the `/publicRooms` endpoint.

It should be noted that the Client-Server and Federation APIs both currently
possess `/publicRooms` endpoints which, whilst similar, are not equivalent.

Ignoring the `server` parameter in the Client-Server API, the following specific
differences are noticed:

* the Federation API endpoint only accepts the `GET` method whereas the
  Client-Server API accepts the `POST` method as well.
* the Federation API accepts `third_party_instance_id` and
  `include_all_networks` parameters through the `GET` method, whereas the
  Client-Server API only features these in the `POST` method.

This MSC proposes to introduce support for the `POST` method in the Federation
API's `/publicRooms` endpoint, with all but one of the parameters from that of
the Client-Server API. The copied parameters shall have the same semantics as
they do in the Client-Server API.

In the interest of clarity, the proposed parameter set is listed below, along
with a repetition of the definitions of used substructures. The response format
has been omitted as it is the same as that of the current Client-Server and
Federation APIs, which do not differ in this respect.

### `POST /_matrix/federation/v1/publicRooms`

#### Query Parameters

There are no query parameters. Notably, we intentionally do not inherit the
`server` query parameter from the Client-Server API.

#### JSON Body Parameters

* `limit` (`integer`): Limit the number of search results returned.
* `since` (`string`): A pagination token from a previous request, allowing
  clients to get the next (or previous) batch of rooms. The direction of
  pagination is specified solely by which token is supplied, rather than via an
  explicit flag.
* `filter` (`Filter`): Filter to apply to the results.
* `include_all_networks` (`boolean`): Whether or not to include all known
  networks/protocols from application services on the homeserver.
  Defaults to false.
* `third_party_instance_id` (`boolean`): The specific third party
  network/protocol to request from the homeserver.
  Can only be used if `include_all_networks` is false.

### `Filter` Parameters

* `generic_search_term` (`string`): A string to search for in the room metadata,
e.g. name, topic, canonical alias etc. (Optional).

## Tradeoffs

An alternative approach might be for implementations to carry on as they are but
also cache (and potentially index) remote homeservers' room directories.
This would not require a spec change.

However, this would be unsatisfactory because it would lead to outdated room
directory results and/or caches that provide no benefit (as room directory
searches are generally infrequent enough that a cache would be outdated before
being reused, on small – if not most – homeservers).

## Potential issues

### Backwards Compatibility

After this proposal is implemented, outdated homeservers will still exist which
do not support the room filtering functionality specified in this MSC. In this
case, homeservers will have to fall-back to downloading the entire room
directory and performing the filtering themselves, as currently happens.
This is not considered a problem since it will not lead to a situation that is
any worse than the current one, and it is expected that large homeservers
– which cause the most work with the current search implementations –
would be quick to upgrade to support this feature once it is available.

In addition, as the `POST` method was not previously accepted on the
`/publicRooms` endpoint over federation, then it is not a difficult task to use
a `405 Method Not Allowed` HTTP response as a signal that fallback is required.

## Security considerations

There are no known security considerations.

## Privacy considerations

At current, remote homeservers do not learn about what a user has searched for.

However, under this proposal, in the context of using the Federation API to
forward on queries from the Client-Server API, a client's homeserver would end
up sharing the client's search terms with a remote homeserver, which may not be
operated by the same party or even trusted. For example, users' search terms
could be logged.

The privacy implications of this proposal are not overly major, as the data
that's being shared is [\[1\]][1]:

- only covered by GDPR if:
    - the search terms contain personal data, or
    - the user's homeserver IP address is uniquely identifying (because it's a
      single-person homeserver, perhaps)
- likely to be *expected* to be shared with the remote homeserver

[1]: https://github.com/matrix-org/matrix-doc/pull/2197#issuecomment-517641751

For the sake of clarity, clients SHOULD display a warning that a remote search
will take the user's data outside the jurisdiction of their own homeserver,
before using the `server` parameter of the Client-Server API `/publicRooms`, as
it can be assumed that this will lead to the server invoking the Federation
API's `/publicRooms` – on the specified remote server – with the user's search
terms.

## Conclusion

By allowing homeservers to pass on search filters, we enable remote homeservers'
room directories to be efficiently searched, because, realistically speaking,
only the remote homeserver is in a position to be able to perform search
efficiently, by taking advantage of indexing and other such optimisations.

