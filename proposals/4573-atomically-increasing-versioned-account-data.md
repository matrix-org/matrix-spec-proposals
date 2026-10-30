# MSC4573: Atomically Increasing Versioned Account Data via ETags

Account data, including Secret Storage data used for encryption key backup, suffers from
the lost-update-problem: with two client publishing an update of any account data they
may overwrite any previously updated data without notice. 

This proposal suggests a solution to this problem by introducing an atomically increasing
version counter per account data entry and use the HTTP ETag framework to enforce proper
upgrade procedures by the client.

## Atomically Increasing Version Counter

For each account data entry, the server holds a counter, starting at 0 and going to u64::MAX.
When the client now wants to update an account entry, they must add a `If-Match` header of
the current version counter the update was build on. Should this not match the server's current
version for the entry, the request is rejected and the client MUST pull the latest version,
reapply the update on that result and try again with that new counter.

How to resolve conflicts between the local copy and the upstream data is dependent on the
actual data saved and SHOULD be defined in the specification of these events. This MSC doesn't
define how these must be resolved, just that this left with the client.

## API Update

The MSC proposes to deprecate the current account data API
(under `/_matrix/client/v3/user/{userId}/account_data/[...]`) in favor of the versioned one under
the new path `/_matrix/client/v4/user/{userId}/account_data/`.
The new version only differs in that the `PUT` request MUST include an `If-Match` header with
the current version counter of the entry to be updated and that the `GET` request MUST include the
`ETag` header from the server.

On the initial push request to create a new entry, the `If-Match` header MUST be `0`.

If the `If-Match` header does not match the server's current version for the entry, the request
is rejected with the HTTP response of `412 Precondition Failed` and the json body 

```JSON
{
    "": "M_VERSION_MISMATCH",
    "error": "The account data version doesn't match"
}
```

Additionally the sync response value for `account_data` entries will include the `version` field
for each entry.

Note: while the version is a strictly atomically increasing u64 counter, the HTTP specification
defines the ETag header to be a string in quotes. Thus for the header value itself the counter
must be represented as such on the wire.

### Upgrade path

Depending on how strongly we want this to be enforced, there are three possible options for
the upgrade path:

1. Still allow the old API to be used as is, just assuming that the version always matches. (weak)
2. Reject requests to the old API for any item that has been updated via the new API (strong)
3. Allow fetching over the old API for a while, but reject any updates unless they are done with the new API

## Alternative approaches

- *Using If-Modified-Since*-headers: While semantically cleaner with our counter, the HTTP spec
  defines these as Dates. The Etag system fits cleaner into our model though also using opaque
  strings.
- *Keeping the current API Path*: this could alternatively be done but makes it a bit harder to
  properly enforce the API update over. Because you'd either have to hard break and require the
  the new headers immediately or accept an awkward in between state where you accept technically
  invalid requests and make some shaky assumptions about them (either accepting or rejecting the
  the request), which make debugging harder.
- *Revision as Request parameter managed by the client*, e.g. [MSC4547](https://github.com/matrix-org/matrix-spec-proposals/pull/4547): instead of having the server handle the tagging, this approach
  takes an otherwise similar approach but have the client define the revision tag itself and include
  that in the request as a query parameter. On its merits this is a pretty close resemblance with
  the difference that here a semantic increased tagging enforcement by the server is proposed and
  the practical mechanisms to communicate them use existing and established HTTP mechanisms and thus
  feels "cleaner" to this author.
``
