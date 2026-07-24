# MSC4512: Delegating parts of the C-S and S-S API to application services

With the Matrix spec growing, there is an increased burden on homeserver maintainers to implement
new functionality[^1]. In some cases, this burden could be reduced by sharing common code as
libraries among server implementations. Differences between tech stacks can make this difficult,
however.

Another, less tightly integrated, alternative is to delegate certain parts of the API to a sidecar
component that runs alongside but separately from the homeserver. An example use case where this
would be beneficial is [lk-jwt-service], originally introduced in [MSC4195]. Reusing this service
spares server maintainers having to integrate LiveKit SDKs and converse with the LiveKit SFU.
Instead they could just run lk-jwt-service as a sidecar and proxy the respective endpoints to it.

This proposal aims to formalise this delegation process in a generic way by enabling app services to
claim parts of the Client-Server and Server-Server API.

## Proposal

Two new properties `proxy_prefix` and `proxy_url` are added to the top level of the [registration
file] for application services. `proxy_prefix` is a string and defines the path prefix that the
service is claiming. `proxy_url` is a string that determines the `url` to send proxied requests to.
`proxy_prefix` and `proxy_url` are optional but if used, MUST always be specified together.

```yaml
id: "My app service"
url: null
as_token: "30c05ae90a248a4188e620216fa72e349803310ec83e2a77b34fe90be6081f46"
hs_token: "312df522183efd404ec1cd22d2ffa4bbc76a8c1ccf541dd692eef281356bb74e"
sender_localpart: "_my_service"
namespaces:
proxy_prefix: "foo/bar"
proxy_url: "http://127.0.0.1:1234"
```

When both `proxy_prefix` and `proxy_url` are set, the server proxies matching C-S and S-S requests
to the application service and allows the service to trigger S-S requests under its own prefix.

### Proxying client-server requests

For any authenticated C-S request under `/_matrix/client/(unstable/[^/]+|v[^/]+)/{proxy_prefix}/.*`,
the server first authorises the request as usual. If authorization succeeds, the server proxies the
request to the same path anchored on `proxy_url` and streams the response back to the requesting
client.

Any "hop-by-hop" headers as defined by [RFC 2616] MUST be stripped both before forwarding the request
to the service and before streaming the response back to the requesting client.

Additionally, the `Authorization` header MUST be stripped on the forwarded request. Instead, the
server supplies the MXID of the requesting client to the application service in a new request header
`X-Matrix-User-Identifier`.

### Proxying server-server requests

The process for proxying server-server requests is analogous.

For any authenticated S-S request under
`/_matrix/federation/(unstable/[^/]+|v[^/]+)/{proxy_prefix}/.*`, the server first authorises the
request as usual. If authorization succeeds, the server proxies the request to the same path
anchored on `proxy_url` and streams the response back to the requesting server.

Any "hop-by-hop" headers as defined by [RFC2616] MUST be stripped both before forwarding the request
to the service and before streaming the response back to the requesting server.

Additionally, the `Authorization` header MUST be stripped on the forwarded request. Instead, the
server supplies the server name of the requesting server to the application service in a new request
header `X-Matrix-Origin`.

### Sending server-server requests

Application services that provide both C-S and S-S endpoints may need to call their S-S endpoint(s)
on a different server when processing C-S requests. To enable this, a new Client-Server endpoint
`POST /_matrix/client/v1/appservice/fed_proxy` is introduced.

``` http
POST /_matrix/client/v1/appservice/fed_proxy HTTP/1.1

{
  "destination": "example.org",
  "method": "POST",
  "path": "/_matrix/federation/v1/{proxy}/foo/bar/",
  "query": { ... },
  "body": { ... }
}
```

- `destination` (required, string): The [server name] of the target server.
- `method` (required, string): The HTTP method to use for the request. MUST be one of `GET`, `POST`,
  `PUT`, `DELETE`.
- `path` (required, string): The request path.
- `query` {object}: A flat JSON object denoting the query parameter pairs to supply on the request,
  if any. All values in `query` MUST be strings.
- `body` {object}: A JSON object defining the request body, if any. MUST NOT be specified when
  `method` is `GET` or `DELETE`.

This endpoint can only be called by application services. If the requesting client is not an
application service, the server MUST respond with HTTP 403 / `M_FORBIDDEN`.

If any of the required parameters are missing, the server MUST reject the request with HTTP 400 /
`M_MISSING_PARAM`. If any of the parameters contain invalid values, the server MUST reject the
request with HTTP 400 / `M_INVALID_PARAM`.

If `destination` points to a remote server that the server generally denies federating with or if
`destination` is the server's own server name, the server MUST reject the request with HTTP 403 /
`M_FEDPROXY_DESTINATION_DENIED`.

If `path` does not have a prefix of `/_matrix/federation/{proxy_prefix}/` (where `proxy_prefix` is
the identically named property from the application service's registration file), the server MUST
reject the request with HTTP 403 / `M_FEDPROXY_PATH_NOT_ALLOWED`. The same MUST happen if `path`
contains any segments of `.` or `..`.

Otherwise, the server signs and sends the respective federation request.

If the server is unable to deliver the request to the destination, it MUST fail with HTTP 502 /
`M_FEDPROXY_CONNECTION_FAILED`. If the server can deliver the request, it relays the response status
code and body back to the application service.

``` http
HTTP 200 OK

{
  "status": 200,
  "content": { ... }
}
```

- `status` (required, number): The HTTP status of the federation response.
- `content` (object): A JSON object representing the body of the federation response.

## Potential issues

Running sidecar services reduces implementation work but complicates deployment of the homeserver.
This is a tradeoff that server maintainers need to consider on a case by case basis.

This proposal doesn't permit application services to proxy unauthenticated endpoints. This is by
design as no associated use cases are known yet.

## Alternatives

The existing `url` property could be reused to avoid having to specify a separate `proxy_url`. This
would disallow using proxying while disabling namespace-related traffic from the server by setting
`url` to `null`, however.

## Security considerations

External services triggering federation requests on behalf of the server could be used abusively.
The impact is limited though because requests are limited to the service's proxy prefix which the
homeserver needs to explicitly allow-list.

## Unstable prefix

| Stable identifier | Purpose | Unstable identifier |
|----|----|----|
| `proxy_prefix` | Registration file property | `io.element.msc4512.proxy_prefix` |
| `proxy_url` | Registration file property | `io.element.msc4512.proxy_url` |
| `/_matrix/client/v1/appservice/fed_proxy` | Endpoint | `/_matrix/client/unstable/io.element.msc4512/appservice/fed_proxy` |
| `M_FEDPROXY_DESTINATION_DENIED` | Error code | `IO.ELEMENT.MSC4512.M_FEDPROXY_DESTINATION_DENIED` |
| `M_FEDPROXY_PATH_NOT_ALLOWED` | Error code | `IO.ELEMENT.MSC4512.M_FEDPROXY_PATH_NOT_ALLOWED` |
| `M_FEDPROXY_CONNECTION_FAILED` | Error code | `IO.ELEMENT.MSC4512.M_FEDPROXY_CONNECTION_FAILED` |

## Dependencies

None.

[^1]: Some statistics on what spec versions homeservers support and how long it took them to declare
    support may be found on <https://patrick.cloke.us/homeserver-spec-versions/>.

  [lk-jwt-service]: https://github.com/element-hq/lk-jwt-service
  [MSC4195]: https://github.com/matrix-org/matrix-spec-proposals/pull/4195
  [registration file]: https://spec.matrix.org/v1.19/application-service-api/#registration
  [RFC 2616]: https://datatracker.ietf.org/doc/html/rfc2616#section-13.5.1
  [server name]: https://spec.matrix.org/v1.19/appendices/#server-name
