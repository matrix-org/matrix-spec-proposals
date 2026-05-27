# MSC4383: Client-Server Discovery of Server Version

### Motivation

Client applications utilizing the Matrix SDK[^6], a Client-Server[^7] library, have been observed
making requests to `GET /_matrix/federation/v1/version`[^2]. It is the only known example of a
cross-interface request made by an implementation[^3]. The purpose is valid: informing logs
used for crash reports of the server specifics; often essential for efficient triage and robust
patching of client software. This proposal reestablises the proper partition between client and
federation interfaces while retaining the value added by the de facto misuse.

Such cross-interface requests are problematic: the partition in the `/_matrix` URL hierarchy is
understood by site-administrators to allow for distinct middleware configurations. Sites commonly
employ WAF rules covering the client and federation hierarchies with source and destination
assumptions. Some sites disable the entire federation portion, rendering the status quo as unreliable.

This proposal reestablishes the partition between client-server and server-server by simply offering
the same version data over both. With the adoption of this proposal, no need for cross-interface
requests will be known to remain.

### Proposal

An object is added to the top-level of `GET /_matrix/client/versions`[^1] named `server` with
parity to the eponymous object returned by `GET /_matrix/federation/v1/version`[^2].

Example of the `server` object:

```json
  "server": {
    "name": "My_Homeserver_Implementation",
    "version": "ArbitraryVersionNumber"
  }
```

Example of a full response:
```json
{
  "server": {
    "name": "My_Homeserver_Implementation",
    "version": "ArbitraryVersionNumber"
  },
  "unstable_features": {
    "org.example.my_feature": true
  },
  "versions": [
    "r0.0.1",
    "v1.1"
  ]
}
```

The endpoint specification is otherwise unchanged.
`GET /_matrix/client/versions`[^1] remains unauthenticated, is not
rate-limited, and guest-access restrictions are not applicable. No new
error responses are introduced; the field is purely additive on the
existing response body.

##### Unstable prefix

| Stable identifier | Purpose | Unstable identifier |
| --- | --- | ---|
| `server` | Server information | `net.zemos.msc4383.server` |

### Alternatives

MSC2301[^4] enriches the discovery information, including some identifying information about the
server, though specific formal vendor and semantic version information appears avoided
(see: potential issues).

### Potential Issues

Server vendor and version information has been considered counter-productive to the motivations
of Matrix as a unifying communication standard. Matrix believes any use of implementation
knowledge as a condition in its applications always represents an accidental failure of its
implementations or the standard binding them; the solution to such problems is thus found in
cooperation, community and conformity, precluding the need for bug-for-bug conditions and
workarounds. This MSC has the option of including a normative statement which inhibits the use
of vendor information to determine functionality.

### Security Considerations

The federation endpoint is the only location which presently reveals this information.
Site-administrators which have taken some measure to hide, or obscure, or modify it (i.e. with a
proxy) will have to note their implementation's new exposure of it when upgrading.

### Implementations

- Server: Tuwunel[^8] (shipped in v1.6.2), populating the `server` object on
  `GET /_matrix/client/versions` and advertising `net.zemos.msc4383` in
  `unstable_features`.
- Protocol types: a Ruma[^9] pull request adds the `Server` struct and the
  `Response.server` field behind the `unstable-msc4383` Cargo feature.
- Client SDK: a matrix-rust-sdk[^10] pull request rewrites
  `Client::server_vendor_info` to prefer the client-server source, falling
  back to `GET /_matrix/federation/v1/version` only when the object is
  absent. The feature is enabled by default in `matrix-sdk-ffi`, so
  applications consuming the FFI binding acquire the client-server path
  on rebuild without an app-side flag.


[^1]: https://spec.matrix.org/v1.16/client-server-api/#api-versions

[^2]: https://spec.matrix.org/v1.16/server-server-api/#server-implementation

[^3]:
    https://github.com/matrix-org/matrix-rust-sdk/blob/d228bde8ef51a98da10a6b7d4b9f3e5b8f49ad3c/crates/matrix-sdk/src/client/mod.rs#L581-L616

[^4]: https://github.com/matrix-org/matrix-spec-proposals/pull/2301

[^6]: https://github.com/matrix-org/matrix-rust-sdk

[^7]: https://spec.matrix.org/v1.16/client-server-api/

[^8]: https://github.com/matrix-construct/tuwunel

[^9]: https://github.com/ruma/ruma/pull/2495

[^10]: https://github.com/matrix-org/matrix-rust-sdk/pull/6622
