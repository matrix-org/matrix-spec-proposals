# MSC3743: Standardized error response for unknown endpoints

Matrix does not define how a server should treat unknown endpoints. This makes it
more difficult than necessary to determine whether an endpoint is responding with
a legitimate error (e.g. a 404 for an object not being found) or because it does
not support the endpoint.

This has impacted clients [wishing to support stable features](https://github.com/vector-im/element-web/issues/19738),
as well as requiring servers to [implement workarounds](https://github.com/matrix-org/synapse/blob/a711ae78a8f8ba406ff122035c8bf096fac9a26c/synapse/federation/federation_client.py#L602-L622)
based on heuristics.


## Proposal

The Client-Server API, Server-Server API, Application Service API, Identity Service API,
and Push Gateway shall respond with a 400 HTTP error response with an error code
of `M_UNKNOWN_ENDPOINT`. This is required for all endpoints under the `/_matrix`
prefix.

This applies if a server receives a request to an unknown URL or if an invalid method is
used for a known URL, i.e. whenever the request cannot be routed to business logic.

## Potential issues

Servers and clients may still need to rely on heuristics until this is widely
available, but this proposal should not cause any additional issues.


## Alternatives

[MSC3723](https://github.com/matrix-org/matrix-doc/pull/3723) could be an alternative
to this, but it has the downside of servers needing to track the version state
of each other server it is interacting with.

It is seen as being more narrowly applicable (only to the Server-Server API),
while also being more complicated to implement.

A new error code was chosen since the `M_UNRECOGNIZED` error code has more specific
definitions in the Identity Server API:

> The request contained an unrecognised value, such as an unknown token or medium.

It could be left to the status quo of being unspecified (or as being implied
by the HTTP specification), but this has already shown to not work, as Synapse,
Conduit, and Dendrite return different errors for unknown endpoints.


## Security considerations

None.

## Unstable prefix

None (as this is about unknown endpoints!)

## Current status

[Issue #1492](https://github.com/matrix-org/matrix-doc/issues/1492) discusses this
problem a bit, but does not propose a concrete solution.

### Client-Server API

Tested by querying for `GET /_matrix/client/v4/login`

* Synapse:
  * < 1.53.0: 404 error with an HTML body
  * \>= 1.53.0: 400 error with a JSON body
    ```json
    {"errcode": "M_UNRECOGNIZED", "error": "Unrecognized request"}
    ```
* Dendrite: 404 error with body of `404 page not found`
* Conduit: 404 error with no body

### Server-Server API

Tested by querying for `GET /_matrix/federation/unknown`.

* Synapse: 400 error with a JSON body
  ```json
  {"errcode": "M_UNRECOGNIZED", "error": "Unrecognized request"}
  ```
* Dendrite: 404 error with body of `404 page not found`
* Conduit: 404 error with no body

### Application Service API

Untested

### Identity Service API,

* Sydent: 404 with an HTML body

### Push Gateway

* Sygnal: 404 with an HTML body

## Dependencies

None.
