# MSC4046: Make & send PDU endpoints

Though extremely uncommon, there are cases where a client wants to send a fully-formed
PDU to a room instead of just the fields exposed by [`/send`](https://spec.matrix.org/v1.7/client-server-api/#put_matrixclientv3roomsroomidsendeventtypetxnid).

This proposal introduces both Client-Server API endpoints and Server-Server API endpoints
for creating and sending PDUs into rooms.

## Proposal

Two new Client-Server API endpoints are introduced:

* `GET /_matrix/client/v1/room/:roomId/make_pdu/:eventType`
* `PUT /_matrix/client/v1/room/:roomId/send_pdu/:txnId`

These endpoints are inspired by the [federation join sequence](https://spec.matrix.org/v1.7/server-server-api/#joining-rooms). Both require authentication and can be rate limited. Both endpoints also accept
any number of `server_name` query parameters for federation routing, similar to
[`POST /join/:idOrAlias`](https://spec.matrix.org/v1.7/client-server-api/#post_matrixclientv3joinroomidoralias).

`GET /make_pdu` returns a PDU (minus some fields) the client can populate and the room version
of the room. After the client has added useful `content` and other fields, it populates `hashes`
and `signatures` (if relevant/possible) before sending the event with `PUT /send_pdu`.

`GET /make_pdu`'s 200 response looks as follows:

```json
{
  "room_version": "11",
  "pdu": {
    // event goes here
  }
}
```

Servers MUST pre-populate the following fields of the `pdu`:

* `sender` as the authenticated user ID.
* If `:eventType` is a known state event type, `state_key` must be present.
  * For `m.room.member` events, `state_key` is the authenticated user ID.
  * For all other event types, an empty string is used.
* All other fields required by a PDU in the room's version, except for `content`, `hashes`, and `signatures`.

`GET /make_pdu` returns the following error codes as applicable:

* `403 M_FORBIDDEN` - The user won't be able to send an event in the room at all. Note that this
  make-and-send sequence can be used by users to join public rooms if they wish.
* `404 M_NOT_FOUND` - The room is unknown to the server, and can't be located over federation (see
  later in this proposal).
* `400 M_INCOMPATIBLE_ROOM_VERSION` - The server doesn't support the room version. The room's version
  is populated as `room_version` on the returned error.

`PUT /send_pdu` takes a request body of the PDU to be sent. The
[`:txnId`](https://spec.matrix.org/v1.7/client-server-api/#transaction-identifiers) can be
anything, though callers are encouraged to use the event ID as it's always consistent. The server
appends `signatures` which are missing and [validates](https://spec.matrix.org/v1.7/server-server-api/#checks-performed-on-receipt-of-a-pdu)
the resulting event.

`PUT /send_pdu`'s 200 response is an empty JSON object. No event ID is returned because in room versions
1 and 2 the event ID is part of the content hash, which the server validates upon receipt. For all other
room versions (as of writing), the event ID is a calculated reference hash where calculating the wrong
reference hash would manifest as a content hash issue as well. Therefore, since the client is *always*
aware of the event ID it is sending, it is not returned.

`PUT /send_pdu` returns the following error codes as applicable:

* `403 M_FORBIDDEN` - The PDU was rejected.
* `400 M_BAD_STATE` - The PDU was [soft-failed](https://spec.matrix.org/v1.7/server-server-api/#soft-failure),
  or the event ID is already in use (applies to room versions 1 and 2).
  * Blocking on soft failure is to prevent clients from sending events which reference ancient parts of
    the DAG, for example.
* `404 M_NOT_FOUND` - The room is unknown to the server, and can't be located over federation (see
  later in this proposal).
* `400 M_INCOMPATIBLE_ROOM_VERSION` - The server doesn't support the room version. The room's version
  is populated as `room_version` on the returned error.

For both endpoints, if the server is not aware of the room then it can use the caller-supplied `server_name`
query parameters to make federation requests instead. Two new Server-Server API endpoints are introduced
to mirror the Client-Server API ones:

* `GET /_matrix/federation/v1/make_pdu/:roomId`
* `PUT /_matrix/federation/v1/send_pdu/:roomId`

Like the Client-Server API endpoints, both are inspired by `GET /make_join` and `PUT /send_join`. Both
require authentication, and both can be rate limited.

`GET /make_pdu/:roomId` has the same request and response shape as the Client-Server API with the notable
difference that instead of `server_name` query parameters the sender SHOULD supply `ver` parameters. `ver`
is exactly as defined by [`GET /make_join`](https://spec.matrix.org/v1.7/server-server-api/#get_matrixfederationv1make_joinroomiduserid).

`PUT /send_pdu/:roomId` also shares its request and response shape with the Client-Server API, notably
missing `server_name` query parameters. `ver` is not required on this endpoint, so is not included.

In both endpoints, the server SHOULD proxy the error through to the client. Servers might also prefer to
call each `server_name` in parallel for `GET /make_pdu` and use the first to respond (and use the first
200 OK as a successful response).

Both endpoints are additionally affected by [Server ACLs](https://spec.matrix.org/v1.7/server-server-api/#server-access-control-lists-acls).

## Potential issues

The client APIs described by this MSC are likely to be used very often. Future MSCs might make better use
of them.

The federation APIs described by this MSC are slightly scary: they allow servers to potentially send *through*
them instead of using the normal [`PUT /send`](https://spec.matrix.org/v1.7/server-server-api/#put_matrixfederationv1sendtxnid)
API. Servers SHOULD reject `PUT /_matrix/federation/v1/send_pdu/:roomId` requests with `400 M_UNAUTHORIZED`
when the calling server (or `sender`) is able to send the event themselves. For example, them being joined
to the room.

This MSC does not deprecate the existing federation `/make_*` and `/send_*` APIs. This might be considered a
bug in the proposal, however.

## Alternatives

### Give clients context for the auth chain

If a client was given enough information for useful `prev_events` and `auth_events`, it could likely skip
the "make" step and jump to "send". `prev_events` is easy because the client can just use the end of its known
timeline, but `auth_events` is harder: clients don't traditionally become aware of state resets and similar,
and so can become desynced from reality. If "current state" was highly reliable for the client then it could
calculate `auth_events` trivially - the server already fully resolves and linearizes the DAG for the client.

Assuming infrequent use of this MSC's APIs, a workaround might be for a client to call
[`GET /state`](https://spec.matrix.org/v1.7/client-server-api/#get_matrixclientv3roomsroomidstate), cache the
response for a short while, generate its events, and send them. The client should be sure to mutate its cache
with any events it generates to keep it as up to date as possible. The client can also refresh the cache from
time to time.

## Security considerations

See "Potential issues" section.

**TODO**: Other security details.

## Unstable prefix

While this proposal is not considered stable, the `org.matrix.msc4046` unstable prefix should be used on
all new endpoints.

| Stable | Unstable |
|-|-|
| `GET /_matrix/client/v1/room/:roomId/make_pdu/:eventType` | `GET /_matrix/client/unstable/org.matrix.msc4046/room/:roomId/make_pdu/:eventType` |
| `PUT /_matrix/client/v1/room/:roomId/send_pdu/:txnId` | `PUT /_matrix/client/unstable/org.matrix.msc4046/room/:roomId/send_pdu/:txnId` |
| `GET /_matrix/federation/v1/make_pdu/:roomId` | `GET /_matrix/federation/unstable/org.matrix.msc4046/make_pdu/:roomId` |
| `PUT /_matrix/federation/v1/send_pdu/:roomId` | `PUT /_matrix/federation/unstable/org.matrix.msc4046/send_pdu/:roomId` |
