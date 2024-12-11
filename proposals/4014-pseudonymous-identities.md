## MSC4014: Pseudonymous Identities

This MSC aims to remove MXIDs from events in almost exactly the same was as proposed in [MSC1228](https://github.com/matrix-org/matrix-spec-proposals/blob/rav/proposal/remove_mxids_from_events/proposals/1228-removing-mxids-from-events.md), with a few minor tweaks.

This assumes *good knowledge* of how MSC1228 works, and should be read thoroughly prior to reading this proposal.


**THIS MSC IS MASSIVELY WIP AND WILL CHANGE RAPIDLY AS IMPLEMENTATIONS LAND**.

### Background from MSC1228

We would like to be able to break the association between a user's ID (such as `@richvdh:sw1v.org`) and their activity in a room.

The stretch goal is to also remove the association with server names, since for many users, they are the only user on a server and it is reasonable to be able to ask for the removal of any history of `sw1v.org`'s involvement with a room.

The general idea presented here is to use a pseudomym in many places where we currently use user IDs. The current `@user:server` then becomes a user alias; the mapping between alias and the **pseudonymous ID** is public but can be removed in the future.

#### Additional Background

In addition to the background mentioned in MSC1228, converting `sender` fields to public keys provides a way to enable portable accounts, because the `sender` field is no longer fixed to a certain domain name. This MSC alone is insufficient for portable accounts, but is a concrete stepping stone on the way towards it.

### Hard requirements
 - Clients MUST work without any changes to their code.
 - Clients MUST have enough data sent to them to be able to migrate to being key-aware.

### Proposal

Please read MSC1228 first, as it is extremely similar to this proposal.

This proposal creates a new room version where the following changes are made:
- Events no longer have a `sender` field. Events now have a `sender_key` field, which is a base-64 encoded ed25519 public key (encoded the same way as other binary event data in Matrix).
    * By using a new field it ensures that everyone knows that the value of a `sender` field is ALWAYS a user ID, and not _sometimes_ a public key. Likewise, the value of a `sender_key` is _always_ a public key. No new sigil e.g `@ # !` is introduced.
    * The private part of this key resides on the server of the sender, in the same way that server keys are today.
- Events are signed by the `sender_key`. This bundles the signature and key together in the event, ensuring it is always possible to verify event signatures, without requiring external network requests.
    * This removes the need for server keys to verify the room DAG, making them much more reliable when remote servers are dead.
- The `sender_key` is scoped to a specific per-room, per-user identity.
    * Per-user only keys (1 sender key for each user, globally across the network) are undesirable as it leaks that "some user" is in rooms "a,b,c,d", which doesn't require too much deduction to figure out the identity of the underlying user, if they happen to join a massive public room like Matrix HQ.
    * The per-room per-user key SHOULD NOT change for that underlying user, otherwise it enables ban evasion. This is not "MUST" because there are legitimate reasons for cycling keys e.g if the key is compromised.
- There is a new field in the `content` of `m.room.member` events called `mxid_mapping` which contains the `sender_key`, the `user_id` and critically a signature from the domain part of the `user_id` which signs the `mxid_mapping`.
    * The purpose of this is to link together some random public key with a user ID, and ensure it cannot be spoofed by any random server.
    * To verify this signature, server keys are needed. This may be impossible if the server is no longer running and there are no perspective servers hosting keys for that server. In this case, the user ID is unverified. How this is handled on clients _who are unaware of such a concept_ is a major outstanding question.
    * TODO: We probably need to mux the room ID into the signature or else a malicious server can just yank the `mxid_mapping` from one room and put it in another room. 

#### Changes from MSC1228

- There is no `user_key`. As a result, there is no `user_mapping` field.
- There is no `room_key`.
- The `user_room_key` is now `sender_key` and has no new sigil.
- The `sender` key is no longer used over federation (to avoid implementation confusion), using the `sender_key` instead.
- There is no `verified_sender_mxid` field. Instead, the `sender` field is used in the CSAPI to allow clients to transparently work in pseudo ID rooms. The `sender_key` field is also sent to clients to allow clients to slowly migrate to be pseudo ID aware.
- If a `sender` cannot be verified by server `example.com`, the user ID `@localhost:domain` in question is transformed into a fake user ID `@_unverified_localhost_domain:example.com`.
    * Currently, these events would be ignored _entirely_ by homeservers as the server keys are required to verify event signatures. With this MSC, those events would now be accepted by the server. To ensure we keep a consistent view between clients and servers, we need to ensure clients also accept this event. To do that in a safe way is hard. The main options are A) use an empty/malformed user ID, B) use a fake user ID, C) use the claimed user ID despite not being able to verify it. A) would break many clients. C) would allow malicious servers to pretend that Alice is in a room when they are not. B) seems like the only reasonable workaround. By using the same domain as the client, all requests involving the unverified user ID will go through the homeserver, providing a mechanism for client-initiated retries.
    * If the server successfully verifies the user ID at a later date, it should resend the `m.room.member` event for that user ID in that room, with the correct verified user ID instead of the fake user ID. [MSC3575: Sliding Sync](https://github.com/matrix-org/matrix-doc/blob/kegan/sync-v3/proposals/3575-sync.md) clients should have the room invalidated and room state resent to the client. Events sent prior to this will show ugly `@_unverified_localhost_domain:example.com` senders. Events sent after this will show the correct displayname and avatar. E2EE will be broken until the user ID is verified, due to `@_unverified_localhost_domain:example.com` not having the same devices as the verified user. These seem like reasonable tradeoffs. Remember, the current UX is that these messages are _entirely dropped by the protocol_ if we fail to get server keys.

##### Addressing the "Problems" section in MSC1228
 - The state keys in the room aliases event is unimportant since v6 rooms removed them from the specification.
 - matrix.to links remain as they are, with the `via=` params formed using verified mxid mappings.
 - Redacting an `m.room.member` event should not remove the `mxid_mapping` field in the case where the `displayname` or `avatar_url` is malicious. In order to remove the `mxid_mapping` field (e.g for PII removal), the account in question should be deactivated or the room in question should be "purged", which would cause the mapping to be removed. This more severe form of redaction has side-effects as deleting the `mxid_mapping` potentially alters routing information as that user may be the last user in the room for that server, and hence should not be triggered by a CSAPI `/redact` call. How this functions at a protocol level is undetermined at this point. The redaction algorithm will remain the same for the purposes of signing events / hashes (so the `mxid_mapping` is removed in this case). This implies 2 kinds of redaction for `m.room.member` events.


#### Key-aware clients

Clients can inspect the `sender_key` on events and use that as a fixed ID representing the sender of the event. This isn't particularly important _right now_, but can be useful for pairing up senders from an unverified mxid and a verified mxid. In the future when portable accounts are introduced, this key will be critical as the mxid will regularly change as the user migrates accounts.

#### Additional notes

- `join_authorised_via_users_server` is currently a user ID, which will now be a `sender_key`. The clause:
   > the event must be signed by the server which owns the user ID in the field.

  would change to:
  
   > the event must be signed by the same key as this field.

