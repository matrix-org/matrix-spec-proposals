# MSC3550: Add HTTP 403 to possible profile lookup responses

# Background
In the current spec, the only response codes listed for [GET /_matrix/client/v3/profile/{userId}](https://spec.matrix.org/v1.1/client-server-api/#get_matrixclientv3profileuserid)
are `200` and `404`. However, some servers may not allow profile lookup over federation, and thus
respond to [GET /_matrix/client/v3/profile/{userId}](https://spec.matrix.org/v1.1/client-server-api/#get_matrixclientv3profileuserid) with an HTTP 403.

For example, Synapse can be configured to behave in this way by setting:

```
allow_profile_lookup_over_federation=false
```

Thus, this behavior already exists in Synapse, and may cause issues for
clients such as [vector-im/element-web#17269](https://github.com/vector-im/element-web/issues/17269).

# Proposal
The proposal is to allow HTTP 403 as an option for responding to [GET /_matrix/client/v3/profile/{userId}](https://spec.matrix.org/v1.1/client-server-api/#get_matrixclientv3profileuserid)
requests. Allowing HTTP 403 gives clients more specific information as to why a request has 
failed, thus enabling more precise error handling. The 403 would be accompanied by an
`M_FORBIDDEN` error code. 

# Potential Issues
The change to the spec may conflict with other existing server implementations.

# Alternatives
The spec could remain as-is and Synapse could alter its current behavior and return an HTTP 
404 rather than 403 in this case. 

# Security Considerations
None at this time. 
