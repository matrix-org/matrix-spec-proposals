# MSC 4080: Cryptographic Identities (Client-Owned Identities)
**THIS MSC IS IN PROGRESS AND WILL CHANGE AS IMPLEMENTATIONS LAND**

Today’s Matrix does not allow users to move their account between homeservers. It would be beneficial to be able 
to move a user account from one homeserver to another while allowing that user to maintain their existing room 
memberships, power levels in those rooms, message history, account data and end-to-end encrypted sessions.

With Pseudonymous Identities (pseudoIDs) we have decoupled a user’s mxid from the identity used to track room 
membership. The new pseudoIDs (also known as user_room_keys/senderids) are both created and managed 
entirely by the homeserver. PseudoIDs was the first step towards having portable accounts in Matrix.

With Cryptographic Identities we aim to take portable accounts one step further by moving the Pseudonymous 
Identities off the server and onto the client in order for the client to have full ownership over their identity.
Clients are then responsible for performing full event signing on a per-event basis. This step brings us closer to
portable accounts primarily in two ways.

1.  Users now fully own their identity in the Matrix ecosystem and have the control to move their identity.
2.  It improves the security of the Matrix ecosystem by making it more difficult for a homeserver to act maliciously
on a client’s behalf. This is particularly important once accounts are portable in order to prevent a homeserver from
being able to continue operating on a user’s behalf after that user has moved their account off the homeserver.

Cryptographic Identities does not get us all the way to having account portability. Further MSC/s will be required to
create the appropriate endpoints and other changes in order to successfully port a user’s account from one homeserver
to another.

## Proposal

PseudoIDs are generated and stored by the client. When joining a room for the first time, a pseudoID should be
generated for that room. All events are signed by the client using their pseudoID and are no longer signed by the
user’s homeserver with the exception of the mxid_mapping in the m.room.member event.

### Event Signing

Events are required to be signed by the pseudoID. In order for this to work with client-owned keys, clients need to
obtain the full version of events before they can be signed. This proposal introduces a few changes to the C-S API
endpoints used to send events between the client and the server. Any C-S API endpoint which previously was used to
send events, now returns the fully formed version of those event/s to the client (minus the signatures block). The
event/s are no longer processed by the server while handling these endpoints. The client then signs the event/s and
forwards them to the server via a new `/send_pdus` endpoint. When handling events sent to this new endpoint the server
should process the event/s like normal by adding them to their respective rooms.

A homeserver should avoid processing room events from the client until they have been sent via the `/send_pdus`
endpoint to ensure the client actually signs the event so it can be successfully sent into the room.

### Endpoint Additions

##### POST /_matrix/client/v1/send_pdus/{txnId}

**Rate-limited**: Yes
**Requires authentication**: Yes

Fully formed PDUs are sent to this endpoint to be committed to a room DAG. Clients are expected to have signed the
events sent to this endpoint. Homeservers should reject any event which isn’t properly signed by the client.

Events sent to this endpoint are processed in the order they are received. A homeserver should check the validity of
each event before sending it to the room. This includes verifying the signature of the event matches the pseudoID
found in the `sender` field of the event. If the event is for a `remote` invite or join, the relevant `/send_invite`
or `/send_join` over federation should be performed prior to adding the event to the room.

If any event is invalid all events are rejected by the homeserver. Invalid events include those that are not correctly
signed, whose event fields are invalid (such as a state event missing a `state_key` field), or the homeserver deems
the event invalid for some other reason. This approach is taken because this failure mode is most likely due to a
programming error. Failures of this nature result in a HTTP status 400. A [standard error response](https://spec.matrix.org/v1.8/client-server-api/#standard-error-response)
will be returned. As well as the normal common error codes, other reasons for rejection include:

-   M_DUPLICATE_ANNOTATION: The request is an attempt to send a [duplicate annotation](https://spec.matrix.org/v1.8/client-server-api/#avoiding-duplicate-annotations).

A `txn_id` is added to the request parameters. Clients should generate an ID unique across requests with the same
access token; it will be used by the server to ensure idempotency of requests.

Request:
```
{
    pdus:  [
        PDUInfo    
    ]
}
```

PDUInfo:
```
{
    room_version:  string,
    via_server:  string,  //  optional
    pdu: PDU  //  signed  PDU
}
```

### Endpoint Changes

Effected endpoint versions all need to be bumped since the underlying behaviour is changed with this proposal. When
hitting any of these endpoints the resulting events are no longer immediately added to the room. Instead the client
is required to send the returned event/s to the `/send_pdus` endpoint after signing them in order for the event/s to
be added to the room DAG.

##### POST /_matrix/client/v4/createRoom

Room creation adds a new `sender_id` field to the request body. The `sender_id` must be valid [Unpadded Base64](https://spec.matrix.org/v1.8/appendices/#unpadded-base64)
and 32 bytes in size in order to be a valid ed25519 public key. This field is used for the homeserver to be able to
fully create all the necessary room creation events on behalf of the client. Since this is a new room the homeserver
needs to be told which pseudoID to correlate to this room for this user.

The response includes the new fields: `room_version` and `pdus`.

Request:
```
{
    ...,
    sender_id: string
}
```

200 OK Response:
```
{
    room_id: string,
    room_version: string,
    pdus:  [  PDU ]
}
```

##### POST /_matrix/client/v4/rooms/{roomId}/invite

Inviting users to a room has a number of changes in order to make it work. First, since the pseudoID for a given user
and room needs to be created by the client, we cannot rely on the existing invite sequence which relies on the invited
user’s homeserver to fully populate the invite event. Instead we need a way for the invited user to be part of the
loop and provide a pseudoID in order to finalize the event. It would not be acceptable to require the invited client
to be available at all times in order to respond to an invite request in real time. Matrix does not currently have a
requirement that client communications be synchronous and this proposal seeks to preserve asynchronous communications
when participants are unreachable. Instead, this proposal introduces the concept of one-time pseudoIDs.

One-time pseudoIDs are uploaded to the user’s homeserver so that they can be claimed and used whenever that user
receives a room invite. In order for a user to be available for invite, one-time pseudoIDs should be created and
uploaded to a user’s current homeserver. This should take the same shape as one-time keys for encryption do today.
The one-time pseudoIDs should be signed by the device’s ed25519 key to verify they were created by that device.

When a client wants to invite a new user to a room for the first time, they need to query the invited user’s
homeserver for one of the invited user’s one-time pseudoIDs. They can then use that pseudoID to create an invite
event for the user.

The invite response includes a new `pdu` field.

Two new endpoints are also added to the S-S API: `/make_invite` & `/send_invite`. These endpoints are required in
order to split out generating an invite event, and having the inviting client sign that event, from actually sending
the event to the invited user’s homeserver.

**TODO**: document /make_invite & /send_invite endpoints

200 OK Response:
```
{
    pdu:  PDU
}
```

##### POST /_matrix/client/v4/join/{roomIdOrAlias} && POST /_matrix/client/v4/rooms/{roomId}/join

A number of fields are added to the response of the `/join` endpoints: `room_version`, `via_server`, and `pdu`.
These are added to help the client when sending the join event to the `/send_pdus` endpoint. The `via_server` is the
server chosen by the homeserver to perform the join via.

200 OK Response:
```
{
    room_id: string,
    room_version: string,
    via_server: string,
    pdu:  PDU
}
```

##### POST /_matrix/client/v4/rooms/{roomId}/leave

The leave endpoint is extended to return a `pdu` for the client to sign.

200 OK Response:
```
{
    pdu:  PDU 
}
```

##### PUT /_matrix/client/v4/rooms/{roomId}/send/{eventType}/{txnId} && PUT /_matrix/client/v4/rooms/{roomId}/state/{eventType}/{stateKey}

The `/send` & `/state` endpoints are extended to return the `pdu` in the response for the client to sign.

200 OK Response:
```
{
    event_id: string,
    pdu:  PDU
}
```

##### POST /_matrix/client/v4/keys/upload

A `one_time_pseudoids` field is added to the `/keys/upload` endpoint in order to upload new `one_time_pseudoids` for
the purposes of inviting the user to new rooms.

Request:
```
{
    ...,
    one_time_pseudoids: map[string]OneTimePseudoID
}
```

200 OK Response:
```
{
    ...,
    one_time_pseudoid_counts: map[string]int
}
```

OneTimePseudoID: 
```
“algorithm:KeyID”: {
    “key”: ”base64_bytes”
}
```

##### GET /_matrix/client/v4/sync

The `/sync` endpoint will need to be extended to report the one-time pseudoID count. In the response, a
`one_time_pseudoids_count` field is added. This is a mapping of pseudoID algorithm (ie. ed25519) to the count of
`one_time_pseudoids` for that algorithm.

200 OK Response:
```
{
    ...,
    one_time_pseudoids_count: map[string]int
}
```

The `/sync` endpoint also requires an extension of the `InvitedRoom` parameter to include a `one_time_pseudoid` field
which is the pseudoID that was selected by the user’s homeserver when creating the invite event. This field is
necessary in order to inform the client which pseudoID was used to create the invite event since homeservers translate
all pseudoIDs to regular mxids when sending events to the client. Then the client can track this association
internally in order to correctly sign future events sent to the room.

200 OK Response (InvitedRoom JSON Object):
```
{
    invite_state:  InviteState,
    one_time_pseudoid: string
}
```

##### POST /_matrix/client/v4/rooms/{roomId}/kick

**TODO**

##### POST /_matrix/client/v4/rooms/{roomId}/ban

**TODO**

##### POST /_matrix/client/v4/rooms/{roomId}/unban

**TODO**

##### PUT /_matrix/client/v4/rooms/{roomId}/redact/{eventId}/{txnId}

**TODO**

##### POST /_matrix/client/v4/rooms/{roomId}/upgrade

**TODO**

  

**TODO**: look into the following:
-   Room directory
-   Peek & unpeek
-   sendToDevice
-   What to do with EDUs?
	-   Read_markers
	-   Presence
	-   VOIP stuff
	-   Typing
	-   Locations? EDU/State?
    

### Auth Rules

A new room version will be required to account for the modifications to the auth rules.

The check to validate the signature on the `m.room.member` field `mxid_mapping` should be modified to allow the case
where no `mxid_mapping` is present. This is done to allow redacting `m.room.member` events without causing those
events to be rejected. In the case of a redacted `m.room.member` event, the user will need to send a new
`m.room.member` event into the room with their `mxid_mapping` in order to continue receiving events from other room
members over federation. Clients should be updated to alert the user if this ever happens in order for the user to
take appropriate action and avoid silently missing events.

Invite events no longer require a signature from the invited user’s homeserver. This signature requirement does not
appear to have an obvious benefit and would make invite events overly onerous with the new room invite process.

### Redaction Rules

Redacting an `m.room.member` event will also remove the `mxid_mapping` field which results in that user being
unroutable since that field contains the user’s homeserver information.

### User Attestation (Optional)

To attest that a pseudoID belongs to a specific user, the client `master_signing_key` could sign the join event
containing their generated  pseudoID, verifying they are that identity, to prevent a server from spoofing a user
joining a new room by having the malicious server generate a pseudoID themselves to create & sign events with.

Linking the pseudoID with the `master_signing_key` will remove the deniability aspect of messages since you are now
cryptographically linking your `master_signing_key` which is synonymous with a user’s identity, with each pseudoID.

This extension is effectively what is proposed in [MSC3917 - Cryptographic Room Memberships](https://github.com/matrix-org/matrix-spec-proposals/pull/3917).

An alternative to using the `master_signing_key` would be to use some other client generated key & include that in
the attestation of the pseudoID. A client could choose whether to use different room signing keys per room (the
benefit of doing this would be to ensure that knowing a user’s identity in one room did not lead to knowing that
same user’s identity in another room), or use the same room signing key for all rooms. Then at a later time clients
could use some out of band attestation mechanism to “cross-sign” in order to verify the user/s are who they say they
are. This has the additional benefit of not needing to enter the user’s recovery passphrase to provide the attestation
as clients could store these room signing keys.

### Pseudonymous Identity Sharing Between Devices

The pseudoIDs of a user are shared between devices using secret storage similar to the way encryption keys are shared.
This leverages server-side key backups for key recovery. 

#### Server-Side Key Backups

**TODO**: detail this section

## Potential Issues

### Recovery Passphrase Entry

Requiring the `master_signing_key` to sign a join event in order to attest a user is who they claim to be would
typically require the user to enter their recovery passphrase every time they join a room. This is because clients
do not usually store this key. This would lead to a large burden on users and would be best to avoid if at all 
possible.

### Additional Attack Vectors

Clients can modify events prior to signing them and sending them to the server for processing. This can lead to
issues if the client were to change something such as the `prev_events` which could lead to further problems. 
In order to mitigate this, a server should perform validation of each event being received from the `/send_pdus`
endpoint. A homeserver could do this by storing the hash of an event prior to sending it to a client, then ensure
any event received by the `/send_pdus` endpoint has a matching hash to one stored previously.

A homeserver can run out of one-time pseudoIDs used during invites. Homeservers should protect against this by
attempting to detect malicious activity which seeks to deplete the one-time pseudoID reserves for a user. An
alternative would be to have a fallback one-time pseudoID. The issue with relying on this mitigation is that it
could quickly become the case that a client ends up with the same pseudoID in many rooms. This is not necessarily an
issue unless that user wants to keep their pseudoIDs separate in order to maintain the pseudonymity they provide.

## Alternatives

### Clients delegate event signing on a per-event basis

In this alternative, events would add a field to event content specifying the event signing delegate (such as the
user's homeserver). All events would be expected to be signed by this delegate.

This has the advantage of avoiding a second round trip.

This has the disadvantage of the added complexity of trying to protect event content such that only a client is
allowed to specify a signing delegate. This ends up leading to a number of issues where homeservers could be able
to replay events on a client's behalf, thus minimizing the benefits of cryptographic identities.

### Clients sign full events via room extremity tracking

In this model the client would be responsible for creating a full event (including `prev_events` and `auth_events`) 
by tracking and resolving the room’s state.

This has the advantage of events being fully signed by the pseudoID and avoiding a second round trip.

This has the disadvantage of requiring clients to do state resolution.

### Clients delegate event signing in their m.room.member event

In this model the client would add a `allowed_signing_keys` field to their `m.room.member event` in order to delegate 
event signing to another party. Homeservers still have full authority over a client’s events in this scenario since 
the client doesn’t sign any part of each event to verify they are the sender.

This has the advantage of not adding additional size to each event.

This has the disadvantage of giving over full event control to the delegated homeserver. It also has the disadvantage 
of trying to resolve `allowed_signing_keys` if a client wants to remove authority from a homeserver or there are 
conflicts in the room DAG. Revocation of a delegated key is known to be extremely problematic.

## Unstable prefix

While this proposal is not considered stable, the `org.matrix.msc4080` unstable prefix should be used on
all new or changed endpoints.

| Stable | Unstable |
|-|-|
| `POST /_matrix/client/v1/send_pdus/{txnId}` | `POST /_matrix/client/unstable/org.matrix.msc4080/send_pdus/{txnId}` |
| `POST /_matrix/client/v4/createRoom` | `POST /_matrix/client/unstable/org.matrix.msc4080/createRoom` |
| `POST /_matrix/client/v4/rooms/{roomId}/invite` | `POST /_matrix/client/unstable/org.matrix.msc4080/rooms/{roomId}/invite` |
| `POST /_matrix/client/v4/join/{roomIdOrAlias}` | `POST /_matrix/client/unstable/org.matrix.msc4080/join/{roomIdOrAlias}` |
| `POST /_matrix/client/v4/rooms/{roomId}/join` | `POST /_matrix/client/unstable/org.matrix.msc4080/rooms/{roomId}/join` |
| `POST /_matrix/client/v4/rooms/{roomId}/leave` | `POST /_matrix/client/unstable/org.matrix.msc4080/rooms/{roomId}/leave` |
| `PUT /_matrix/client/v4/rooms/{roomId}/send/{eventType}/{txnId}` | `PUT /_matrix/client/unstable/org.matrix.msc4080/rooms/{roomId}/send/{eventType}/{txnId}` |
| `PUT /_matrix/client/v4/rooms/{roomId}/state/{eventType}/{stateKey}` | `PUT /_matrix/client/unstable/org.matrix.msc4080/rooms/{roomId}/state/{eventType}/{stateKey}` |
| `POST /_matrix/client/v4/keys/upload` | `POST /_matrix/client/unstable/org.matrix.msc4080/keys/upload` |
| `GET /_matrix/client/v4/sync` | `GET /_matrix/client/unstable/org.matrix.msc4080/sync` |
| `POST /_matrix/client/v4/rooms/{roomId}/kick` | `POST /_matrix/client/unstable/org.matrix.msc4080/rooms/{roomId}/kick` |
| `POST /_matrix/client/v4/rooms/{roomId}/ban` | `POST /_matrix/client/unstable/org.matrix.msc4080/rooms/{roomId}/ban` |
| `POST /_matrix/client/v4/rooms/{roomId}/unban` | `POST /_matrix/client/unstable/org.matrix.msc4080/rooms/{roomId}/unban` |
| `PUT /_matrix/client/v4/rooms/{roomId}/redact/{eventId}/{txnId}` | `PUT /_matrix/client/unstable/org.matrix.msc4080/rooms/{roomId}/redact/{eventId}/{txnId}` |
| `POST /_matrix/client/v4/rooms/{roomId}/upgrade` | `POST /_matrix/client/unstable/org.matrix.msc4080/rooms/{roomId}/upgrade` |


## Dependencies

[MSC4014 - Pseudonymous Identities](https://github.com/matrix-org/matrix-spec-proposals/pull/4014)

