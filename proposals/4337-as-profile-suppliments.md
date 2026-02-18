# MSC4337: Appservice API to supplement user profiles

User profiles in Matrix are currently largely stored on the homeserver statically. Clients can
update the static information as often as they like, but it's expected that the homeserver
maintains a copy in it's datastore. This means that having dynamic profile values that may change
depending on a user's status (e.g. "In a meeting") or profiles that may change depending on the
requester are hard to achieve. 

This proposal extends the appservice API to offer a new route to supplement a user's profile with
additional fields, or to replace existing ones. 

## Proposal

A new route is introduced on the Application Service API:

`GET /_matrix/app/v1/profile/{userId}/{key}`

This API is authenticated as with the rest of the application service APIs, and takes two additional
*optional* query parameters:

 - `origin_server` The server name of the server requesting the profile, *if* the profile is requested
   over federation. Otherwise, omit.
 - `from_user_id` The user MxID of the user requesting the profile, *if* the requesting user is known.
   Otherwise, omit.

The path parameters match the C-S API `/profile` GET parameters, where `userId` is the user profile to be
fetched and `key` is an optional field on the profile. If the `key` is omitted, the full profile should be returned.

The response to the API should be an object representing the profile. Homeservers should call this API
whenever a user's profile is requested by a client or a federated service, and the appservice should return
a profile object. If a `key` is specified then an object should be returned only containing the value for `key`.

### Examples

`GET /_matrix/app/v1/profile/@alice:example.org` would return

```json
{
  "displayName": "Alice S.",
  "org.example.holiday": true
}
```

and

`GET /_matrix/app/v1/profile/@alice:example.org/org.example.holiday` would return

```json
{
  "org.example.holiday": true
}
```

### Merging behaviour

The homeserver should *always* request the profile from the application service even if the `key` is already
present in the user's stored profile. For instance, given a profile of:

```json
{
  "displayName": "Bob",
  "avatar_url": "mxc://foo/bar"
}
```

and an appservice response of:

```json
{
  "displayName": "Alice S.",
  "org.example.holiday": true
}
```

then the resulting profile for the user will be:

```json
{
  "avatar_url": "mxc://foo/bar",
  "displayName": "Alice S.",
  "org.example.holiday": true
}
```

### Error codes

Application services may respond with a `404` `M_NOT_FOUND` if they do not provide any information
for the given `userId`. They may also choose to do this if they do not want to divulge information
about a given user to another user or service.


### Caching

Homeservers should not cache responses to this endpoint as the values may change dynamically.

TODO: Should we introduce a ETag-like system here so homeservers can cache?

### Application service selection

Any homeserver with a matching `namespaces.users` field for the requested `userId` should be used
when querying the profile. The resulting profile should be merged together. The order of application services
here is **NOT** stable, and so if multiple application services set the same field on the same user
then there is potential for instability. Server admins should take care not to register multiple application
services with overlapping namespaces, if they may both alter the profile.

Implementations MAY choose to specify a guaranteed ordering for application service queries but this is out
of scope for the spec.

The registration file **MUST** contain `supports_profile_lookup: true` to be considered for profile queries
to reduce the number of requests made to appservices not supporting this feature.

## Potential issues

### Performance

This can place additional delay on the profile endpoint, as now an additional HTTP hit will need to be made. A sensible
maximum response time should probably be specified to reduce the risk of a profile endpoint timing out. Additionally,
the timeout should not prevent a client from reading the resulting profile, without the missing application service response.

### Instability

As per the previous section, application service querying is not inheriently stable across homeserver implementations
so overlaps in profiles may lead to unpredictable results.

## Alternatives

Application services already can modify profiles, albeit with no controls over who can view them and with the added
cost of these profiles being stored in the homeserver. There is also no way to update on-demand to reduce the amount
of changes needed to be made to the homeservers stores.

## Security considerations

The most obvious security risk is that this MSC opens up the ability to do authed profile requests and alter the response
depending on the requester. The application service and the homeserver must ensure not to cache these responses globally,
and be careful when validating the requester.

TODO: There must be more things that can go wrong here.

## Unstable prefix

While this MSC is not considered stable:
  - the endpoint will be `/_matrix/app/uk.half-shot.msc4337/profile/@alice:example.org`
  - the registration file flag will be `msc4337_supports_profile_lookup`

## Dependencies

None.