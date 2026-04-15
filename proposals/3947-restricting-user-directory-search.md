# MSC3947: Allow Clients to Request Searching the User Directory Constrained to Only Homeserver-Local Users

Searching for local users is an extremely common task for users on
organization-owned homeservers. Currently, the client-server protocol does not
allow to constrain the search to local users. In practice, this often leads to
irrelevant users from federated servers being returned.

This proposal aims to fix that by allowing a client to ask for local users
only.


## Proposal

### Proposed Protocol Extension

Extend the
[`client/v3/user_directory/search`](https://spec.matrix.org/v1.5/client-server-api/#post_matrixclientv3user_directorysearch)
endpoint to take an optional argument that specifies whether search should be
constrained to local users, federated users, or both.

#### Syntactic Change

`client/v3/user_directory/search` request body becomes

```text
{
  limit: integer              The maximum number of results to return. Defaults to 10.
  search_term*: string        The term to search for
  exclude_sources: integer    Whether to exclude no users from directory search (0),
                              exclude non-local users (1), exclude local users (2).
			      Defaults to 0 (search and return all users)
}
```

The difference here is purely the addition of the new `exclude_sources`
optional parameter, which defaults to the current behaviour, so that legacy
servers can just ignore the parameter and let the client filter results.

The option to explicitly return only non-local users is especially meant to
avoid returning duplicate results in case a client wants to separately request
local users, and users known through federation.

The usage of an integer allows for later extensibilty.

#### Semantic Change

* If `exclude_sources` is unspecified or `0`, execute user directory search as before
* Else:
  * if the first bit in `exclude_sources` is set (`exclude_sources & 0x1`),
    exclude non-local users (only search (or at least return) local users)
  * if the second bit in `exclude_sources` is set (`exclude_sources & 0x2`), 
    exclude local users (only search (or at least return) non-local users)

Note that the `if` above are *not* `else, if`s.

#### Alternative Implementations

The `exclude_sources` parameter might also be a set of string constants, or
renamed to `include_sources` (with the downside of then no longer being a
comfortable bitmask, and not being able to default to `0` meaning "behave as if
parameter did not exist").

## Potential issues

* **Computational Overhead** is unlikely to be a problem. As the most important
  server implementation, Synapse already handles local users separately (to
  prefer them if configured to do so).
* **Privacy** is unaffected
* **Security** no effects
* **Social and Environmental Impact** is expected to be positive – this makes
  user directories more useful to organizational Matrix users, and has the
  potential to reduce traffic and search effort, if not in meaningful ways.

## Outlook

Clients should implement an interface to allow for this feature to be used.
Ideally, smartness is invested in allowing something like
`Firstname:myownhomeserver.com`, `Firstname:local` to be decomposed into a
search term and a term that specifies that only the local users should be
searched.

## Dependencies

None.
