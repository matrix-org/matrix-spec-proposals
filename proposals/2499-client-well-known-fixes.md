# MSC2499: Fixes for Client Well-known URI

Several minor issues and inconsistencies have cropped up since the `/.well-known/matrix/client`
method was added to allow clients to discover servers. This proposal intends to fix these issues.

## Proposal

The following changes should be made to the client server spec:

1. The spec does not mention that redirects should be followed. The spec should be changed to
state that when a client is looking up the well-known URI, it should follow HTTP 3xx redirects
up to 30 times. This is consistent with the redirects followed when a server resolves a
server name using `/.well-known/matrix/server`.

1. Currently the spec does not mention which Content-Type should be used for the response to
`/.well-known/matrix/client`. The Content-Type SHOULD be `application/json` however it
should be assumed to be JSON regardless of type. This is consistent with the Server-Server API.

1. When a client is following the flow described in the spec for looking up `/.well-known/matrix/client`,
the spec currently states, in part:

    > 3․ Make a GET request to https://hostname/.well-known/matrix/client.<br>
	>>  a․ If the returned status code is 404, then `IGNORE`.<br>
    >>  b․ If the returned status code is not 200, or the response body is empty, then `FAIL_PROMPT`.

    In practice most web servers do not add CORS headers on 404 errors by default. Therefore
    web based clients cannot always determine if the status code is 404. Step 3b should be 
    changed from `FAIL_PROMPT` to `IGNORE` so that a non 200 response is treated in the same
    way as 404. This change is intended to fix issues like https://github.com/vector-im/riot-web/issues/7875.
  
    This change does have potential security concerns, see https://github.com/vector-im/riot-web/issues/11136.

1. Step 3f in the flow should be changed to use the modern `/_matrix/identity/v2` API to
validate the identity server rather than the deprecated `/_matrix/identity/api/v1`. Clients
should fall back to the v1 API as described in the identity service spec.
