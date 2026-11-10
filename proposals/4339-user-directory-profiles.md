# MSC4339: Allow the user directory to return full profiles

The user directory endpoint [POST /_matrix/client/v3/user_directory/search](https://spec.matrix.org/v1.10/client-server-api/#post_matrixclientv3user_directorysearch)
currently allows a response including the `displayname` and `avatar_url`, but otherwise doesn't allow
any other fields to be returned. Now that extensible profiles have landed in the Matrix spec, this
limitation could be lifted.

## Proposal

A new field, `profile_fields`, is optionally available on the request body of the endpoint:

```json
{
  "limit": 10,
  "search_term": "foo",
  "m.profile_fields": ["display_name", "avatar_url", "org.example.job_title"]
}
```

A new field is included on the `results` objects from the search endpoint, `m.profile`. This will contain
the user's profile:

```json
{
  "limited": false,
  "results": [
    {
      "m.profile": {
        "avatar_url": "mxc://bar.com/foo",
        "display_name": "Foo",
        "org.example.job_title": "Breaker of things"
      },
      "user_id": "@foo:bar.com"
    }
  ]
}
```

The `profile_fields` field controls which fields SHOULD be in `m.profile`. If no `profile_fields` value is given, the
implementation MAY choose which fields are returned by default. The intention of this field is to reduce the amount of
data needed to be transmitted to render the client's UI for user search, without prescribing the fields that every
client should use.

Because this changes the response format of the endpoint, the new endpoint should use `v4`. The full
endpoint would be `POST /_matrix/client/v4/user_directory/search`.

## Potential issues

This will increase the response size of `user_directory`, but since the client has control over the
fields returned this can be carefully managed.


## Alternatives

It's possible today for clients to request a `GET /_matrix/client/v3/profile/{user_id}` for each user,
but this is intensive for search results and if the client wishes to further refine the fields returned
then they need to make one request per field.


## Security considerations

Implementations need to be careful not to be prone to DDOS attacks by frequent requests for large profile
fields. Otherwise, this doesn't increase the surface of available information.

## Unstable prefix

While this proposal is not considered stable, implementations should use `/_matrix/client/unstable/org.matrix.msc4339/user_directory/search` 
instead. Clients should note the [`M_UNRECOGNIZED` behaviour](https://spec.matrix.org/v1.10/client-server-api/#common-error-codes)
for servers which do not support the (un)stable endpoint.

## Dependencies

No dependencies.