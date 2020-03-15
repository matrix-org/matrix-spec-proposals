# Authenticated Content Repository API
Currently anyone can fetch resources from content repositories.
This can be undesired behaviour for several reasons as discussed
in [synapse#2150](https://github.com/matrix-org/synapse/issues/2150) and [synapse#2133](https://github.com/matrix-org/synapse/issues/2133).
Homeservers might want to be able to restrict access to the content they serve.

## Proposal
Homeservers may reject unauthenticated access to media endpoints.

When an unauthenticated client accesses an endpoint, the homeserver
may reject the request like it would with an authenticated endpoint.

Thus it returns status code 401 and an error
with an errcode of M_MISSING_TOKEN or M_UNKNOWN_TOKEN as apropriate.

Example response:
```json
{
  "errcode": "M_MISSING_TOKEN",
  "error": "Media access is restricted to authenticated clients"
}
```

### Configuration
To allow clients to predetermine whether authentication is required,
the configuration field m.media.unauthenticated is added.
It specifies what content can be accessed unauthenticated.

The following behaviours are defined:

| Enum value | Description |
| ---------- | ----------- |
| null / missing | All content can be accessed unauthenticated |
| m.cached | Only cached content can be accessed unauthenticated |
| m.local | Only content with an authority the server is responsible for can be accessed unauthenticated |
| m.unspecified | Unauthenticated access is possible but not specified |
| m.none | No content can be accessed unauthenticated |

Example response:
```json
{
  "m.media.unauthenticated": "m.local"
}
```

Clients can decide based on this
if sharing a download link to a non Matrix user is possible.

### Server to server
To reduce the amount of server to server communication,
when one homeserver tries to fetch content from another homeserver,
the configuration should first be retrieved and cached.
When the value is m.none the server should not attempt to fetch the
content from the remote server
and return status code 404 and an error with an errcode of M_NOT_FOUND.

Example response:
```json
{
  "errcode": "M_NOT_FOUND",
  "error": "Remote homeserver rejected access"
}
```

## Potential issues
Once homeservers enable this behaviour with a m.media.unauthenticated
value other than null, older clients will not be able to access some content.
This is desired for the server operator and undesired for the user.

Additionally older clients and servers might encounter an unexpected error code
which may lead to unknown behaviour.

## Alternatives
All media endpoints could always require authentication,
but then the server to server exchange would still need
to be extended to allow access for remote homeservers.

## Security considerations
None
