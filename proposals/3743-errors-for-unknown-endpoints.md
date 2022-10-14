# MSC3743: Standardized error response for unknown endpoints

Matrix does not define how a server should treat unknown endpoints. This makes it
difficult to determine whether an endpoint is responding with a legitimate error
(e.g. a `404` for an object not being found) or because it does not support the
endpoint.

This has impacted clients [wishing to support stable features](https://github.com/vector-im/element-web/issues/19738),
as well as requiring servers to [implement workarounds](https://github.com/matrix-org/synapse/blob/a711ae78a8f8ba406ff122035c8bf096fac9a26c/synapse/federation/federation_client.py#L602-L622)
based on heuristics.


## Proposal

The Client-Server API, Server-Server API, Application Service API, Identity Service API,
and Push Gateway shall respond with a `404` HTTP error response with an error code
of `M_UNRECOGNIZED`. This is required for all paths under the `/_matrix` prefix.

This applies if a server receives a request to an unknown path or if an invalid method is
used for a known path, i.e. whenever the request cannot be routed to business logic.

The major homeserver implementations have recently settled on using `M_UNRECOGNIZED`,
so it seems reasonable to specify this formally.

## Potential issues

Servers and clients may still need to rely on heuristics until this is widely
available, but this proposal should not cause any additional issues.

A `M_UNRECOGNIZED` error code with a status of `400` has more specific definition
in the Identity Server API:

> The request contained an unrecognised value, such as an unknown token or medium.

## Alternatives

[MSC3723](https://github.com/matrix-org/matrix-doc/pull/3723) could be an alternative
to this, but it has the downside of servers needing to track the version state
of each other server it is interacting with.

It is seen as being more narrowly applicable (only to the Server-Server API),
while also being more complicated to implement.

## Security considerations

None.

## Unstable prefix

None (as this is about unknown endpoints!)

## Current status

[Issue #1492](https://github.com/matrix-org/matrix-doc/issues/1492) discusses this
problem a bit, but does not propose a concrete solution. [^0]

### Homeserver API

Tested by querying for `GET /_matrix/client/v4/login` and `GET /_matrix/federation/unknown`.

* Synapse:
  * Client-Server:
    * < 1.53.0: 404 error with an HTML body
    * \>= 1.53.0: 400 error with a JSON body [^1]
      ```json
      {"errcode": "M_UNRECOGNIZED", "error": "Unrecognized request"}
      ```
  * Server-Server: 400 error with a JSON body
    ```json
    {"errcode": "M_UNRECOGNIZED", "error": "Unrecognized request"}
    ```
* Dendrite:
  * Client-Server:
    * < 0.10.0: 404 error with a text body of `404 page not found`
    * \>= 0.10.0: 404 error with a JSON body [^2]
      ```json
      {"errcode": "M_UNRECOGNIZED", "error": "Unrecognized request"}
      ```
  * Server-Server: 404 error with a text body of `404 page not found`
* Conduit (both Client-Server and Server-Server):
  * < 0.4.0: 404 error with no body
  * == 0.4.0: 404 error with a JSON body [^3]
    ```json
    {"errcode": "M_NOT_FOUND", "error": "M_NOT_FOUND: Unknown or unimplemented route"}
    ```
  * > 0.4.0: 404 error with a JSON body [^4]
    ```json
    {"errcode": "M_UNRECOGNIZED", "error": "M_UNRECOGNIZED: Unrecognized request"}
    ```

### Application Service API

Untested

### Identity Service API,

Tested by querying for `GET /_matrix/identity/unknown`

* Sydent: 404 with an HTML body

### Push Gateway

Tested by querying for `GET /_matrix/push/unknown`

* Sygnal: 404 with an HTML body

## Dependencies

None.

[^0]: Tests were run against matrix.org (1.69.0rc3 (b=matrix-org-hotfixes,aca3a117a9));
dendrite.matrix.org (0.10.2); and conduit.rs (0.4.0-next).
[^1]: https://github.com/matrix-org/synapse/issues/11600
[^2]: https://github.com/matrix-org/dendrite/issues/2739
[^3]: https://gitlab.com/famedly/conduit/-/merge_requests/306
[^4]: https://gitlab.com/famedly/conduit/-/merge_requests/388
