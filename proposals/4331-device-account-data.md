# MSC4331: Device Account Data

Specification version 1.15 § 
[10.21.2](https://spec.matrix.org/v1.15/client-server-api/#client-behaviour-17) 
features key+value storage allocated on the server for a user's
"Account Data." It also features similar storage for a user's "Room 
Account Data" like Account Data but with a `room_id` division. These 
form the two components of Account Data which have existed prior to the 
1.0 specification through the present release.

## Proposal

We specify a third Account Data component: "Device Account Data" with 
similar characteristics as the other two but with a `device_id` 
division. Device Account Data acts as an arbitrary server-side 
key+value store for each of a user's devices. Writes to this store are 
only permitted by the device with a matching `device_id`. Reads from 
this store can occur by any device and the server.

It is in fact the server's read-access which is the motivator for this 
proposal. Without it there is little reason to burden the server with 
storing anything on behalf of a device with its own local storage.

Future-specified event types and contents communicate per-device 
information to the server. Examples of such information for further 
specifications include:
- Supported room versions (replaces 
[MSC4292](https://github.com/matrix-org/matrix-spec-proposals/pull/4292)).
- Client software version identifier.
- Client capabilities and preferences.
	- e.g. Format for `redacts` in
	[MSC2244 Mass Redactions](https://github.com/matrix-org/matrix-spec-proposals/pull/2244)
- Encryption metadatas.

## Client-server endpoints

- `GET /_matrix/client/v3/user/{userId}/devices/{deviceId}/account_data/{type}`

- `PUT /_matrix/client/v3/user/{userId}/devices/{deviceId}/account_data/{type}`

## Stabilization

Such communication to the server via Account Data can certainly occur 
via other components with well-specified types and contents but no 
other use case for Device Account Data has been proffered. This 
proposal is therefore to remain dormant (but not draft) until another
proposal invokes it as a dependency. At that time this proposal is to 
be stabilized concurrently with its first dependent.

## Enhancements

It is possible to add an `account_data` field to the v1.15 § 
[10.11.1](https://spec.matrix.org/v1.15/client-server-api/#get_matrixclientv3devices) 
response's `Device` object as a convenience, but that will not be
mandated by this proposal without feedback.

## Unstable prefix

`/_matrix/client/v3/user/{userId}/devices/{deviceId}/net.zemos.account_data/{type}`
