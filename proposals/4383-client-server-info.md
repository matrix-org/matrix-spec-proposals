# MSC4383: Client-Server Discovery of Server Version

### Introduction

The Matrix client-server API does not advertise which homeserver implementation a client is
connected to. In its absence, client applications have settled on querying the server-server
endpoint `GET /_matrix/federation/v1/version`[^2] from the client side, where the homeserver
identifies itself by name and version. The result is embedded in crash reports and diagnostic
submissions so that defect triage can route a report to the appropriate implementation team. This
proposal offers the same information over the client-server interface, allowing the cross-interface
workaround to be retired.

The observed use is logging only. The identification is included in rageshakes and similar
diagnostic submissions so that recipients can recognise the server vendor and version; the field
is not consulted to determine application behaviour. The query is to the user's own homeserver
only; remote-server identification is out of scope, and a client has no general means to resolve
a remote server name in any case.

Cross-interface requests are problematic. The partition in the `/_matrix` URL hierarchy is
understood by site administrators to permit distinct middleware configurations, and sites commonly
apply WAF rules to the client and federation hierarchies under differing source and destination
assumptions. Some sites disable the federation portion entirely, rendering the status quo
unreliable. Client applications utilising the Matrix SDK[^6], a client-server library, have been
observed[^3] making this cross-interface request. element-web exhibits a related workaround in its
rageshake collector[^11]: a primary call to the Synapse-specific administrative endpoint
`GET /_synapse/admin/v1/server_version`, falling back to the same federation `/version` call when
the administrative endpoint is unavailable. The administrative-endpoint path substitutes a
vendor-specific dependency for the partition violation; neither workaround functions under
deployments that restrict the corresponding interface.

This proposal reestablishes the partition between the client-server and server-server interfaces
by exposing the same version data over both. With its adoption, no need for cross-interface
requests is known to remain.

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

### Backwards Compatibility

The `server` object is additive. Clients that do not recognise it
ignore it per the existing client-server forward-compatibility rules.
No existing field is renamed or removed, and the response shape on
`GET /_matrix/client/versions`[^1] is otherwise unchanged.

Implementations populating the field advertise `net.zemos.msc4383: true`
in `unstable_features`, so clients can detect support without inspecting
the object. Clients that have existing fallback paths to
`GET /_matrix/federation/v1/version`[^2] may keep those paths conditional
on the flag's absence; once servers in the deployment universe advertise
the flag, the fallback may be retired.

SDKs that already expose a method fetching this data from the federation
endpoint can transparently prefer the client-server source under this
proposal and retain the federation call as a fallback, so application
consumers receive the partition correction without code change. The
matrix-rust-sdk implementation (see Implementations) demonstrates this
pattern: the existing `Client::server_vendor_info` API preserves its
return-type contract while switching its primary source to
`GET /_matrix/client/versions`, and applications consuming the FFI
binding inherit the new behaviour on rebuild without an application-side
opt-in.

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

[^11]: https://github.com/element-hq/element-web/blob/220f68935e1700f3bd6e0786aac049bf6803badb/apps/web/src/rageshake/submit-rageshake.ts#L153-L189
