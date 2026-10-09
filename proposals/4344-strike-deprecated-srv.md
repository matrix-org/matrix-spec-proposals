# MSC4344: Strike deprecated SRV service name

The SRV service name `matrix` was deprecated by 
[MSC4040](https://github.com/matrix-org/matrix-spec-proposals/pull/4040) 
due to adverse possession. The replacement service name `matrix-fed`
became active on the same date of August 19, 2023. After an elapsed 
grace-period of two years, the deprecated service name is to be stricken 
from the specification.

Upon activation of this change by the appropriate release-version of the 
specification, implementations MUST NOT query for records using the 
deprecated service name. Implementations MAY perform a Server Name 
Resolution seeking their own domain for the purpose of alerting 
administrators to the stricken record's use, and encourage removal.

### Potential Issues

Deployments which have not updated their name service records during the 
grace-period will no longer be reachable over the federation.

### Alternatives

The service name retains its deprecated-but-active status quo: this
maintains a considerable amount of wasteful overhead within the Server 
Name Resolution process. Due to the lack of necessity for this method of 
indirection after the introduction of 
[MSC1708](https://github.com/matrix-org/matrix-spec-proposals/pull/1708), 
both the replacement and deprecated service names are often queried with
negative results, potentially doubling the load on the name service.

### Security Considerations

Deployments which are made unreachable by this proposal (see: Potential 
Issues) will no longer have their federation public keys directly 
obtainable, introducing non-zero exposure to matrix-spec/#383 during the 
window of domain record replacement.
