# Standardised federation response formats

Some responses formats in the federation API specifications use the form `[200,
res]` in which `res` is the JSON object containing the actual response for the
affected endpoints. This was due to a mishap while building synapse's federation
features, and has been left as is because fixing it would induce backward
incompatibility. With r0 approaching, and already including features with
backward compatibility issues (e.g.
[MSC1711](https://github.com/matrix-org/matrix-doc/pull/1711)), this is likely
the right timing to address this issue.

## Proposal

Change the responses with a 200 status code for the following federation
endpoints:

* `PUT /_matrix/federation/v1/send/{txnId}`
* `PUT /_matrix/federation/v1/send_join/{roomId}/{eventId}`
* `PUT /_matrix/federation/v1/invite/{roomId}/{eventId}`
* `PUT /_matrix/federation/v1/send_leave/{roomId}/{eventId}`

From a response using this format:

```
[
    200,
    res
]
```

To a response using this format:

```
res
```

Where `res` is the JSON object containing the response to a request directed at
one of the affected endpoints.

## Potential issues

As it's already been mentioned in the proposal's introduction, this would induce
backward compatibility issues. However, proposals that have already been merged
at the time this one is being written already induce similar issues.

As a mitigation solution, we could have a transition period during which both
response formats would be accepted on the affected endpoints. This would give
people time to update their homeservers to a version supporting the new one
without breaking federation entirely.

## Conclusion

Such a change would make the federation API specifications more standardised,
but would induce backward incompatible changes. However, with r0 coming up soon,
this is likely the best timing to address this issue.
