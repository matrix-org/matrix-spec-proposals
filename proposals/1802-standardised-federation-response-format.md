# Remove the '200' value from some federation responses

Some responses formats in the federation API specifications use the form `[200,
res]` in which `res` is the JSON object containing the actual response for the
affected endpoints. This was due to a mishap while building synapse's federation
features, and has been left as is because fixing it would induce backward
incompatibility.

This proposal proposes a backward compatible alternative

## Proposal

Add a new version of the following endpoints under the prefix
`/_matrix/federation/v2`:

* `PUT /_matrix/federation/v2/send_join/{roomId}/{eventId}`
* `PUT /_matrix/federation/v2/send_leave/{roomId}/{eventId}`

Which are the exact same endpoints as their equivalents under the `v1` prefix,
except for the response format, which changes from:

```
[
    200,
    res
]
```

To:

```
res
```

Where `res` is the JSON object containing the response to a request directed at
one of the affected endpoints.

This proposal doesn't address the `PUT
/_matrix/federation/v1/invite/{roomId}/{eventId}` endpoint since
[MSC1794](https://github.com/matrix-org/matrix-doc/pull/1794) already takes care
of it.

If a call to any of the `v2` endpoints described in this proposal results in an
unrecognised request exception (i.e. in a response with a 400 or a 404 status
code), then the sending server should retry the request with the `v1` API.

## Alternative solutions

An alternative solution would be to make the change in the `v1` federation API,
but would break backward compatibility, thus would be harder to manage.
