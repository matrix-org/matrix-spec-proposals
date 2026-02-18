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
key+value store for each of a user's devices.
- The store is deleted when the device is deleted (upon logout).
- Reads from this store can occur by any device and the server.
- Write-access is specified on a per-type basis; unless otherwise
specified, default write-access is permitted only by the device with a
matching `device_id`.
- Updates to the store are echoed via sync or sliding-sync, in a location
to be determined. Updates are found in an object keyed by `device_id`.
This allows updates to be visible across devices by default, but per-type
specifications may restrict visibility as desired.

It is in fact the server's read-access which is the motivator for this
proposal. Without it there is little reason to burden the server with
storing anything on behalf of a device with its own local storage.

### Client-server endpoints

- `GET /_matrix/client/v3/user/{userId}/devices/{deviceId}/account_data/{type}`

- `PUT /_matrix/client/v3/user/{userId}/devices/{deviceId}/account_data/{type}`

### Unstable prefix

`/_matrix/client/v3/user/{userId}/devices/{deviceId}/net.zemos.account_data/{type}`

## Discussion

### Stabilization

Such communication to the server via Account Data can certainly occur
via other components with well-specified types and contents but no
other use case for Device Account Data have been committed to. This
proposal is therefore to remain dormant (but not draft) until another
proposal invokes it as a dependency. At that time this proposal is to
be stabilized concurrently with its first dependent.

### Potential Uses

Future-specified event types and contents communicate per-device
information to the server. Examples of such information for further
specifications include:
- Supported room versions (replaces
[MSC4292](https://github.com/matrix-org/matrix-spec-proposals/pull/4292)).
- [MSC3890](https://github.com/matrix-org/matrix-spec-proposals/pull/3890)
suggests [per-device account data](https://github.com/matrix-org/matrix-spec-proposals/pull/3890/files#diff-b32a4af9b74efc2c7a6af62a1ce0b53ec4f12f9d92349b75f5682f4ebb16cce7R71-R76).
- Client capabilities and preferences.
	- e.g. Format for `redacts` in
	[MSC2244 Mass Redactions](https://github.com/matrix-org/matrix-spec-proposals/pull/2244)
- Client software version identifier.
- Encryption metadatas.

## Alternatives

Some form of [device metadata already exists](https://spec.matrix.org/v1.15/client-server-api/#put_matrixclientv3devicesdeviceid).
The existing system is easier to work with at small scale; if only one or a
few uses are ever contemplated it may be sufficient. This proposal instead
offers a more general abstraction, matching the approach of other account
data, available over sync. If this proposal is considered, deprecating and
consolidating the existing metadata should also be taken into consideration.

## Security Considerations

Lost, stolen or compromised devices should be considered with regard to any
cross-device information sharing, which this proposal makes default for read
access and updates.

## Potential Issues
