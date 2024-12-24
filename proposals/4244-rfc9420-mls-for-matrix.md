# MSC4244: RFC 9420 MLS for Matrix

[RFC 9420](https://datatracker.ietf.org/doc/rfc9420/) defines the Messaging Layer Security (MLS)
protocol for secure, end-to-end encrypted, group conversations. Matrix in its current design is capable
of supporting multiple different types of encryption, including custom crypto, through the
[`m.room.encryption`](https://spec.matrix.org/v1.13/client-server-api/#mroomencryption) state event.
Much of the existing architecture is built around a Double Ratchet algorithm at its core (like Olm),
which MLS is sufficiently different from. Therefore, architectural additions are needed to support
MLS in an everyday Matrix room.

Critically, MLS requires group changes ("Commits") to be strictly ordered across all participating
servers, and must be append-only. This eliminates using traditional eventual consistency mechanisms
as the key material will have already rolled forward by the time a server attempts to resolve a conflict.

Meanwhile, the SCT has experimented with approaches such as
[Decentralised MLS (DMLS)](https://gitlab.matrix.org/matrix-org/mls-ts/-/blob/decentralised2/decentralised.org)
([MSC](https://github.com/matrix-org/matrix-spec-proposals/pull/2883))
and Linearized Matrix ([I-D](https://datatracker.ietf.org/doc/draft-ralston-mimi-linearized-matrix/),
[MSC](https://github.com/matrix-org/matrix-spec-proposals/pull/3995)). These are valid approaches
which come with different architectural tradeoffs. In the case of DMLS, forward secrecy is reduced
(as key material must be retained in case of network partitions) and higher complexity is needed on
the client-side to resolve conflicts. With Linearized Matrix, rooms become uncomfortably centralized
on a server in the room.

Continuing that work, we circulated some untested theories about how to restore those valuable
properties in [these slides](https://conference.matrix.org/documents/talk_slides/LAB3%202024-09-20%2016_15%20Travis%20Ralston%20-%20DMLS,%20MIMI,%20etc.pdf)
at Matrix Conference 2024. At the time, the idea was to lean a little less on Linearized Matrix, but
still retain relative centrality in the room (participants could only continue using the room if they
were on the 'good' side of a network partition).

This still leaves some centralization, with a 'hub' server required per room in order to sequence and
authenticate MLS commits, synchronizing them with Matrix membership state. This centralization could
be mitigated by server elections, which would help to bifurcate the room with hubs on each side of a
network partition, leading to those branches needing conflict resolution upon the partition being
(partially) healed. Consensus mechanisms are thought to be the best approach to healing those conflicts,
particularly when considering MLS's append-only requirement - the servers, in healing their connection,
would reach a conclusion on what the MLS and room state is, and that result would become fact. This
is notably different from the [existing state resolution algorithm](https://spec.matrix.org/v1.13/rooms/v11/#state-resolution)
where participating servers are instructed on how to reach a factual representation of the room.
Consensus mechanisms and leader election are deliberately left as concepts for a future MSC to discuss,
though some non-normative ideas are discussed here to kickstart those future MSCs. The remainder of
federation traffic (power level changes, message events, topic changes, etc) is sent over the normal
full mesh federation in Matrix today, unaffected by the hub server.

This proposal's changes, namely the partial centralization, are designed to be an opt-in feature at
room creation time. It is therefore left to the room creators to decide what is best for their
communities, particularly when it comes to encryption and the room model that it imposes.

By using RFC 9420 MLS, this proposal also naturally brings cryptographically-constrained room membership
to Matrix: users may only participate in the room if their devices are legally added to the MLS group
state, rather than if their `m.room.member` event is successfully accepted to the room. This proposal
still retains `m.room.member` for primarily communicating which users are "in" the room, even when
they have no devices, but ties this state to the MLS group state to ensure authenticity.


## Background

In MLS, there is a concept of a Delivery Service (DS) which is responsible for tracking MLS group
changes and membership. This DS can be a physical or logical server, and can have its role (theoretically)
spread over multiple other servers. In Matrix, we'd ideally call the set of participating servers in
a room the DS, however because of the linear append-only group state requirements, we assign this
role to a single Matrix homeserver.

Note that the group state is independent of the Matrix room state: room state tracks room configuration,
as it always has, while group state tracks which devices are participating in that room. Which *users*
are joined is tracked in room state, while their *devices* (if any) are tracked in group state. Group
state is otherwise an encrypted binary blob passed around between devices, and stored on the DS. The
DS has configurable visibility on the group state, up to and including zero visibility.


## Proposal

MLS can be enabled in a room only at creation time due to the room's underlying algorithms, like the
authorization rules, changing behaviour depending on whether MLS is enabled. This is achieved using
[MSC4245](https://github.com/matrix-org/matrix-spec-proposals/pull/4245)'s `encryption_algorithm` in
the create event for the room. The initial Matrix-namespaced MLS encryption algorithm is `m.mls.10`
to mirror the `mls10` `ProtocolVersion` defined by RFC 9420. `m.mls.*` encryption algorithms are
*illegal* in `m.room.encryption` events, and clients MUST treat such configurations as though the
room has an unknown encryption algorithm (unless of course `encryption_algorithm` is set, in which
case `m.room.encryption`'s `algorithm` is meaningless under MSC4245).

**Note:** The `m.mls.10` algorithm does not define primitives, against the specification's
[request](https://spec.matrix.org/v1.13/client-server-api/#messaging-algorithm-names). This is because
MLS is capable of changing its underlying ciphersuite and therefore primitives. Which ciphersuite is
recommended, and how to figure out which one is in use, is discussed later in this proposal.

**Note:** A new room version will be required due to the conditional behaviour of the underlying room
algorithms. This is discussed in more detail later in this proposal.

The device which calls [`/createRoom`](https://spec.matrix.org/v1.13/client-server-api/#post_matrixclientv3createroom)
also creates the initial MLS Group using the returned room ID as the group ID (**TODO**: we may wish
to decouple room ID from group ID to make ReInit easier later in the group lifecycle). That creating
device then can add the user's other devices to the MLS group through commits and proposals.

MLS Commits (and technically Proposals) run through a designated DS homeserver in the room. By default,
this is the server which created the room. All other operations, like power level changes, messages,
etc, transit the normal full mesh of Matrix. Transferring this role to another server is an unsolved
problem in this version of the MSC (**TODO:** solve this).

When a client wishes to Commit, Proposal, or other update to the MLS group state, it uses the
to-device semantics defined by [MSC4246](https://github.com/matrix-org/matrix-spec-proposals/pull/4246),
sending an `m.mls.message` event with the following respective contents:

```jsonc
{
    "message": "<unpadded base64 MLSMessage>", // unpadded base64 per Matrix, MLSMessage per RFC 9420

    // If a commit...
    "commit_info": {
        "welcome": "<unpadded base64 Welcome>", // optional
    }
}
```

**TODO:** It may be worth considering a GroupInfoOption similar to the MIMI concept at https://datatracker.ietf.org/doc/html/draft-ietf-mimi-protocol-02#name-update-room-state

If the DS *rejects* the update, the client is informed of that with an `m.mls.rejected` to-device
message, sent by the DS. Accepted updates are communicated to all joined devices in the MLS group
over to-device from the DS as `m.mls.commit` events.

**TODO:** Event/message shapes for `m.mls.rejected` and `m.mls.commit`.

Providing deltas in this way prevents having to transfer large blobs of binary around servers and
clients. Later in this proposal is a description of how a client (or server) can restore its MLS
state if it were to lose it.

**TODO:** Update/add auth rules to designate the DS server, including transfers. Implementations
should meanwhile note it's the room creator, for experimentation purposes.

MLS has its own notions of "membership", consisting of the *devices* in the room, which belong to
users. This is different from Olm/Megolm which rely on the existing user-level membership denoted by
`m.room.member` events - the devices simply belong to the room at the point in time an encrypted
message is sent. Maintaining the concept of user-level membership is important to match the expected,
and established, user experience where Alice joins a room, not Alice's laptop, and to keep as much
compatibility with existing clients as possible - clients already show member lists as `m.room.member`
events, and a large number of Matrix APIs do the same.

Maintaining the `m.room.member` events structure also allows Matrix rooms to have a concept of being
a member of the room with zero devices. A pure MLS room would consider the user to have left in this
case, making recovery of the user's room list a feat. Instead, by keeping the user joined through
`m.room.member`, the user can restore their room list when they go from zero to one (or more) devices,
and use MLS to participate in the encrypted conversation again. Most notably however, the default
operation mode of MLS prevents the user and their new devices from decrypting messages sent while
they had zero devices. Clients SHOULD help their users understand this through explainer text or
similar instead of showing a bunch of "unable to decrypt" errors. Alternatively, clients can make
use of [MSC3814](https://github.com/matrix-org/matrix-spec-proposals/pull/3814)-style dehydrated
devices to always consider the user as having 1 usable device.

With those considerations, it's still important to have cryptographically-constrained membership,
where the crypto layer (in this case, RFC 9420 MLS) has authority over the membership of the room,
and proofs exist so other participants can verify that membership changes are legitimate. This is
achieved by including the auth events which allow a user to perform a given action in the Additional
Authenticated Data (AAD) of the MLS commit, and having the DS produce an `m.room.member` event which
references that commit. Together, these layers allow downstream servers to authorize the event (and
thus the commit), and clients SHOULD further verify the event by requesting the auth events individually
and performing the subset of the [auth rules](https://spec.matrix.org/v1.13/rooms/v11/#authorization-rules)
which apply to them (namely rule 4 and onwards, minus any server signature verification).

After the user's initial device is added through MLS commits, their other devices may be added with
minimal overhead. Likewise for device removals (as they get logged out, lost, etc). These still must
be coordinated with the DS, but don't cause `m.room.member` events to be generated.

The [membership transitions](https://spec.matrix.org/v1.13/client-server-api/#room-membership) change
slightly to account for the changes actually happening within the MLS layer, though only in rooms
where MLS is used. In other (possibly encrypted) rooms, the [existing auth rules](https://spec.matrix.org/v1.13/rooms/v11/#authorization-rules)
and related algorithms apply unchanged.

**Note**: The KeyPackage infrastructure needed to actually add/remove other devices is described later
in this proposal.


### Knocks

Sending a knock does not exchange key material, and requires no changes. The knocking server coordinates
with an already-joined server, which may be the DS, to send an `m.room.member` state event with
`membership: knock` to the room, provided the auth rules permit such an action.

If the knock is rejected, it's rejected using an MLS-independent `leave` event. If it's accepted,
the invite sequence described below takes effect.


### Invites

From a cryptography point of view, an invite is essentially just adding the user to the room. In some
cases this could appear as a force-join, especially when the sending user intends for the receiving
user to see history immediately after the invitation. In other cases, the invite is more notional,
like knocks above. To determine which case we're operating under, we rely on the [history visibility](https://spec.matrix.org/v1.13/client-server-api/#mroomhistory_visibility)
for the room.

If the room's history visibility is `joined`, the invite is notional and has no particular meaning to
the MLS group state. The invite is sent as a regular `m.room.member` state event to the room, using
the existing invite mechanisms.

Otherwise, when the history visibility is `shared`, `world_readable`, or (critically) `invited`, the
sending device must first retrieve a KeyPackage from one of the target user's devices. The first to
respond with a suitable KeyPackage is the device which will act as the 'invited' device, and can add
the user's other devices once fully added to the MLS group state. The sending device then prepares a
Welcome message for the invited device, and asks their server for the `m.room.power_levels` and
`m.room.history_visibility` event IDs. The sending device prepares an Add commit with the event IDs
in the AAD (**TODO:** CSV?), and sends the combination of Add commit and Welcome message to the DS
for inclusion in the MLS group state.

The DS takes the Add and Welcome, runs the normal MLS-required checks, and further verifies that the
auth events in the AAD are representative of current state for the room, and that they permit such an
invite to happen. If any of these checks fail, the commit is rejected (and the client is informed of
that). If they all pass, the DS forwards the Welcome message to the invited device (**TODO:** Define
to-device message shape), sends the Add commit to all other joined devices (from the MLS group state
perspective), and sends an `m.room.member` state event with `membership: invite` for the invited user.
This event is signed by the target and sending servers (**TODO:** Using the existing /invite API, or
a new one?), and includes a copy of the Add commit under a new top-level `mls_commit` field as
[unpadded base64](https://spec.matrix.org/v1.13/appendices/#unpadded-base64).

When a server receives the `m.room.member` event, the normal [auth rules](https://spec.matrix.org/v1.13/rooms/v11/#authorization-rules)
apply with an added condition that the `mls_commit` MUST have AAD which references the same auth
events as the membership event. Otherwise, the event is rejected.

Servers MUST NOT inspect to-device messages, particularly those sent between the DS and local users.
This is to ensure that the client receives the Add commit even if their server rejects the
`m.room.member` event with `mls_commit`. A server which does intercept to-device messages would
corrupt the encryption state for its users, making the room unusable for those devices. (**TODO:**
Can we encrypt to-device messages between DS and users, to prevent inspection in the general case?)

If a client receives the commit but no membership event, the client should assume the event was
rejected by the server for some reason. The client can use the AAD to request the events and further
verify if the membership event was supposed to be rejected, and choose to apply the Add commit
accordingly. Clients SHOULD perform this check regardless of the membership event being accepted by
their server.

**Security consideration:** A server *could* lie about the `content` for an event when the client
requests it by ID only. Perhaps the AAD should include the full federation-formatted (PDU) event JSON,
because then the client can compare `content` because event IDs are hashes of the event, which covers
the content hash, which (naturally) covers `content`. This would all be verifiable by the client
without needing to know the intricacies of DAGs or state resolution - they can verify the event ID
is correct, and compare `content` against what their server gave them for that same event ID.

Clients receiving invites would receive key material for events they haven't seen yet, until they
accept the invite and join the room (see below). If they reject the invite, they SHOULD discard key
material they've collected.


### Joins

**TODO:** Similar to invites and knocks. Where the user is accepting an invite, just a normal
membership change. Where joining from scratch, use external joins assisted by the DS.


### Leaves

**TODO:** DS or parting user spams Remove proposals, DS requires removal before it'll accept any
other changes.


### Kicks/Bans

**TODO:** Similar to leaves, but with some added "you really need to remove these devices".


### Adding/removing devices while joined to the room

**TODO:** Happens purely in MLS, no Matrix state events required.

### KeyPackages

Similar to Matrix's [one-time keys (OTKs)](https://spec.matrix.org/v1.13/client-server-api/#one-time-and-fallback-keys),
KeyPackages are provided by a device to enable other devices to add them to the MLS group. They are
still uploaded ahead of time by the device for reliability purposes, and are single-use. Their format
and contents are, however, very different.

Uploading KeyPackages is done through the [`/_matrix/client/v3/keys/upload`](https://spec.matrix.org/v1.13/client-server-api/#post_matrixclientv3keysupload)
endpoint with the following request shape:

```jsonc
{
  "one_time_keys": {
    "mls:<key_id>": {
      "key": "<unpadded base64 MLS KeyPackage object>" // KeyPackage per RFC 9420, unpadded base64 per Matrix
    }
  }
}
```

The `key_id` is generated by the device, and is an [opaque string](https://spec.matrix.org/v1.13/appendices/#opaque-identifiers).

**TODO**: Use existing grammar for `key_id`, if present.

The `key` contains all the needed information for a server to index the KeyPackage for a later claim,
such as protocol version (MLS_10), ciphersuite, extensions/capabilities, and whether it is a "last resort"
key (similar to Matrix's [fallback keys](https://spec.matrix.org/v1.13/client-server-api/#one-time-and-fallback-keys)).

Claiming a key is slightly more involved, as the requesting device needs to indicate multiple required
capabilities to get a useful key from a device. The request shape for [`/_matrix/client/v3/keys/claim`](https://spec.matrix.org/v1.13/client-server-api/#post_matrixclientv3keysclaim)
is thus changed slightly:

```jsonc
{
  "timeout": 10000, // unchanged
  "one_time_keys": { // unchanged (at all levels)
    "@alice:example.com": {
      "DEVICEID": "mls"
    }
  },
  "mls": { // new! describes what "mls" means to the caller
    "protocol_version": "m.mls_10", // maps to ProtocolVersion.mls10 in RFC 9420
    "acceptable_ciphersuites": [ // by name, not value
      "MLS_128_DHKEMX25519_AES128GCM_SHA256_Ed25519",
      "MLS_128_DHKEMP256_AES128GCM_SHA256_P256",
      // etc
    ],
    "required_capabilities": "<unpadded base64 RequiredCapabilities>" // RequiredCapabilities per RFC 9420, unpadded base64 per Matrix
  }
}
```

**TODO**: Should we include the room ID, like [MIMI does](https://datatracker.ietf.org/doc/html/draft-ietf-mimi-protocol-02#name-fetch-key-material)?

The same effective change is made to [`/_matrix/federation/v1/user/keys/claim`](https://spec.matrix.org/v1.13/server-server-api/#post_matrixfederationv1userkeysclaim),
sans `timeout` of course.

For both endpoints, a successful response looks as follows:

```jsonc
{
  "one_time_keys": {
    "@alice:example.com": {
      "DEVICEID": {
        "mls:<key_id>": {
          "key": "<unpadded base64 KeyPackage>" // per upload
        }
      }
    }
  }
}
```

Clients continue discovering other devices through [device lists](https://spec.matrix.org/v1.13/client-server-api/#tracking-the-device-list-for-a-user),
which are unchanged by using RFC 9420 MLS.

## Potential issues

Unresolved:
* What happens if the DS no longer has any users in the room?
* What if the DS doesn't transfer its role to another server?
* The DS is effectively required to fully resolve the room state, and state res will need to be
  modified to rely on MLS group state (or its effects) as definitive truth.
* How to actually specify ciphersuite and etc in the room? (probably just copy LM)
* How to determine if your local server can behave as a DS? (try to create room with encryption_algorithm?)
* Credentials (what makes a "device" a device, what makes a "user" the owner of that device)
* How does the DS find out what the MLS Group even is? (we may need to add it to `/createRoom`)

This proposal centralizes room membership operations onto a single server within the room (not across
the federation), which may be undesirable to room operators. Rooms which want to retain full
decentralization should not use this proposal's mechanism for encryption, instead relying on the
existing Megolm standard. In future, it may be possible to retain the security properties of MLS in
a fully decentralized environment.

Adoption of off-the-shelf MLS also limits the ability to decrypt history from before the MLS Add
Commit. Room operators should be aware of this limitation when deciding what encryption algorithm to
use when creating the room.


## Security considerations

**TODO:** Improve this section.

Keeping centralization to the absolute bare essentials is a strong consideration for this proposal.


## Dependencies

This proposal is dependent on [MSC4245](https://github.com/matrix-org/matrix-spec-proposals/pull/4245)
and [MSC4246](https://github.com/matrix-org/matrix-spec-proposals/pull/4246).


## Future considerations

**TODO:** Discuss consensus from MXCONF2024


## Unstable prefix

**TODO**


## Credits

Many thanks to Franziskus Kiefer and Karthikeyan Bhargavan at Cryspen for their thoughtful feedback
on how best to integrate RFC 9420-standard MLS into Matrix.
