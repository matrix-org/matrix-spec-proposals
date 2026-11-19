# MSC4582: Require the `m.room_versions` capability

[`GET /_matrix/client/v3/capabilities`][capabilities] lets a homeserver tell clients which room
versions it supports and which one it uses for new rooms, through the
[`m.room_versions`][room-versions-cap] capability. Clients use this to decide which features to
offer when creating a room and when to prompt users to upgrade a room.

The capability is currently optional, which causes problems for clients trying to determine
valid values for creating rooms and suggesting room upgrades. For example, matrix-js-sdk [assumes][js-sdk-fallback] version 10 with versions 1 to 10 available, while Element Web [assumes][element-web-fallback] version 1 when creating a room.

Every homeserver implementation surveyed for this proposal already sends the capability (see [Homeserver survey](#homeserver-survey)), and both [Complement][complement-test] and [Sytest][sytest-test] already fail a server which omits it.

This proposal makes `m.room_versions` a required part of the capabilities response.

## Proposal

Homeservers MUST include the `m.room_versions` capability in the `capabilities` object returned by
[`GET /_matrix/client/v3/capabilities`][capabilities].

If `/capabilities` fails to respond or the field is missing, clients MUST not
try to guess the room version support and instead fail whatever operation they
are attempting.

### Homeserver survey

The capabilities handler of each of the following homeservers was read to
determine whether `m.room_versions` is always sent.

| Homeserver | Always sent? | Notes |
|---|---|---|
| [Synapse][synapse-src] | Yes | Built unconditionally from the configured default and all known room versions. |
| [Dendrite][dendrite-src] | Yes | Built unconditionally from the roomserver's default and supported room versions. |
| [Palpo][palpo-src] | Yes | Built unconditionally from configuration. |
| [Continuwuity][continuwuity-src] | Yes, in practice | Always set by the handler. Serialised by Ruma, see below. |
| [Tuwunel][tuwunel-src] | Yes, in practice | Always set by the handler. Serialised by Ruma, see below. |
| [Grapevine][grapevine-src] | Yes, in practice | Always set by the handler. Serialised by Ruma, see below. |

The homeservers built on [Ruma][ruma-src] always populate the capability, but Ruma skips the field
when serialising if it is equal to its default value: a `default` of `"1"` with `available` equal
to `{"1": "stable"}`. None of these servers ship with such a configuration, so the capability is
always sent in practice.

## Potential issues

None. This is a change to the spec to require a field that is always sent in practice.

## Alternatives

The fallback that clients assume could be updated to a newer room version instead. This would
need revisiting every time the recommended default room version changes, and would still be wrong
for any server which is configured differently.

The capability could be left optional, with clients continuing to choose their own fallback. This
leaves clients behaving inconsistently for a case that does not appear to occur in practice.

## Security considerations

None.

## Unstable prefix

None required. This simply makes an existing field required.

## Dependencies

None.

[capabilities]: https://spec.matrix.org/v1.19/client-server-api/#get_matrixclientv3capabilities
[room-versions-cap]: https://spec.matrix.org/v1.19/client-server-api/#mroom_versions-capability
[room-versions-schema]: https://spec.matrix.org/v1.19/client-server-api/#get_matrixclientv3capabilities_response-200_roomversionscapability
[js-sdk-fallback]: https://github.com/matrix-org/matrix-js-sdk/blob/develop/src/models/room.ts
[element-web-fallback]: https://github.com/element-hq/element-web/blob/develop/apps/web/src/createRoom.ts
[complement-test]: https://github.com/matrix-org/complement/blob/main/tests/csapi/apidoc_server_capabilities_test.go
[sytest-test]: https://github.com/matrix-org/sytest/blob/develop/tests/10apidoc/45server-capabilities.pl
[synapse-src]: https://github.com/element-hq/synapse/blob/develop/synapse/rest/client/capabilities.py
[dendrite-src]: https://github.com/element-hq/dendrite/blob/main/clientapi/routing/capabilities.go
[palpo-src]: https://github.com/palpo-im/palpo/blob/main/crates/server/src/routing/client.rs
[continuwuity-src]: https://forgejo.ellis.link/continuwuation/continuwuity/src/branch/main/src/api/client/capabilities.rs
[tuwunel-src]: https://github.com/matrix-construct/tuwunel/blob/main/src/api/client/capabilities.rs
[grapevine-src]: https://gitlab.computer.surgery/matrix/grapevine/-/blob/main/src/api/client_server/capabilities.rs
[ruma-src]: https://github.com/ruma/ruma/blob/main/crates/ruma-client-api/src/discovery/get_capabilities.rs
