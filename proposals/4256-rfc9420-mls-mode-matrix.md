# MSC4256: MLS mode Matrix

Messaging Layer Security ([RFC 9420][RFC9420], MLS) is a modern
layer for end-to-end encrypted group messaging providing Forward Secrecy (PFS) and Post-Compromise
Security (PCS). MLS further provides performance that’s logarithmic in the group size, an easy
migration to post-quantum security, and is a rigorously analyzed protocol.

The primary goal of MLS is to define a common view of the group, which is then used to derive keys
from. Group members share a common key if and only if they share the same view of the group, which
includes who is in the group as well as important metadata about how the group functions.
MLS embeds the membership "tree" in the group state, which results in one coherent view of the
current membership in a group. For users this has the benefit of giving a stronger guarantee about
which "ends" the group is communicating with and who has access to a specific message. By design MLS
requires a "delivery service" to order "handshake" messages that affect the state of the group. This
delivery service is a conceptually single service, delivering all state change messages in a group,
and in control of ordering these messages.

Matrix on the other hand is a decentralised messaging protocol. It allows multiple servers and their
users to participate in a shared room without being reliant on a single server to be highly
available. Matrix allows any server (including the creator of a room) to be unavailable or
disconnected from the other servers in the room for an arbitrary extent of time and the room will
recover once the connection is restored. This is achieved by using a DAG of messages, that allows
temporary splits to merge together using state resolution once a connection is restored including
arbitrary state modifications.

Previous proposals have tried to unify those aspects of MLS and Matrix, but often this has come at
the expense of some of the security benefits of MLS. At its core having a coherent set of members in
a room and the ability to change membership at any time without the ability to broadcast these
changes to other servers in the room are at conflict. If any server can modify historical membership
of a room, this compromises security. In an earlier proposal, decentralised
MLS (dMLS), each participant will need to keep private keys at every possible fork point of the DAG
around for a possibly unlimited amount of time as Matrix places no upper bound on how far back
history can have diverged but ultimately still be allowed to merge together in the future.
Furthermore, dMLS did not use the state  synchronization mechanisms, which are core to MLS and its
security guarantees.

Another weakness of end-to-end encryption on Matrix currently is found in the validation of
membership in a room. Matrix has membership events which are resolved on the server side. These
don’t reflect a verified set of users. With olm and megolm each sender has to decide which senders
to send the keys for a message to and it can’t trust the membership events received from the server.
This is in conflict with how Matrix usually works, where a lot of the operations are delegated to
the homeserver, while the clients tend to do less work and trust the server instead. In an E2EE
context the sender only selects the members it can currently see as the recipients for the Megolm
decryption keys. Meanwhile state resolution calculates history visibility using a different set of
rules.

This proposal aims to address both of these aspects. Using MLS, this proposal introduces a
cryptographically guaranteed common view on the group by all members. This provides much stronger
security guarantees compared to the encryption currently used in Matrix. It combines the group
membership of a room and the end-to-end encrypted group without compromising on PCS and forward
secrecy in the common case, but it does so by reducing the decentralisation promises of Matrix by a
(in our opinion hopefully negligible) amount. Additionally this proposal aims to reduce unencrypted
metadata of Matrix rooms encrypted with MLS to the minimal set of data necessary for federation and
message delivery to function.

In some aspects this proposal is a big departure from how Matrix works currently, but we tried to
keep the most beneficial aspects of Matrix around and only change aspects which we understood more
as technical limitations without apparent beneficial impact on users. In some areas we weren’t
always quite successful at achieving this goal, but this is something that can be remedied by future
MSCs.

## Proposal

To shift primary responsibility over membership to the MLS state of a group, this proposal
introduces a new room version with significant changes to the authorization rules and some smaller
changes to state resolution and the event format.

Additionally, and this is the biggest departure from Matrix today, the proposal removes most
existing state events and allows only encrypted messages in a room. This will significantly impact
clients and servers, but also allows for encrypted state events using the shared group state.

Apart from these changes the existing key distribution endpoints are reused as they are with only
new algorithms and keys for MLS.

Federation and client APIs only have minor changes where necessary to adapt to the changes in
membership handling as well as event format.

### Room version

A new room version is introduced, which may live in parallel to other room versions, but is used for
MLS encrypted rooms: `m.mls.1`

### Membership

Membership is split into 2 categories:

- MLS membership
- Network membership

Users get added to the MLS group state using MLS proposals and commits. This process is not visible
to the homeserver apart from the encrypted commit event changing. Instead clients send invites using
the existing invite API, which the homeservers track out of band instead of in the room state. For
inviting remote users those invites have to always be sent over federation. Current room versions
can instead send an `m.room.member` in the room if the homeserver is already participating, but
those events don’t exist in MLS rooms.

Users can then call the join API to join the room if they are currently invited to it. This action
gives them "network membership" and they will receive messages until they leave the room.

Currently "restricted join", "knock", "ban" and "kick" are not supported membership transitions.
However, there’s no reason they can not be supported with this MSC, and they may be added with
subsequent MSCs. The homeserver has no visibility on join rules or power levels of users and
therefore can’t validate if a "ban" would be valid or not. Instead rooms currently rely on the MLS
membership for forcing removal of a user. A user, who is removed against their will, will still
receive encrypted messages, but will be unable to decrypt them. If the user is the last user on
their server in the room, the server can be removed completely and the server will not receive any
messages for the room, but this doesn’t work when some users still need to receive messages. To
resolve this hole a future MSC could introduce signature keys, which will be exposed to the server
to allow authenticating membership transitions. But to limit the size of this MSC that hole is left
open for now.

### Event format

The MLS room version removes the `sender` and `depth` fields. The sender field is removed to
reduce metadata at the server level. The server can’t verify if a specific sender is allowed to send
a specific event anymore, so this field provides no value anymore. The `depth` field is an
artifact of older room versions and should nowadays not be relied upon anymore. Some servers still
use that field to calculate topological order of events, but the authorization rules don’t validate
that the `depth` field is incremented in a trustworthy manner and therefore relying on the
`depth` field is more problematic than beneficial. MLS based rooms have an epoch field as part of
the MLS state and this field provides a similar function to the `depth` field, but it is
cryptographically validated by all group members as well as validated as part of the authorization
rules, which gives it stronger guarantees.

The `origin` field is used instead of the `sender` field. This field only contains the sending
homeserver and is used to validate participating homeservers and signatures on events. This field
already exists in older versions of the Matrix specification, but this room version assigns it a new
meaning (without changing the value, so there is no breaking change).

### State events

This room version removes all existing state events apart from the `m.room.create` event from the
unencrypted room state. Some state events like `m.room.name` can still be sent inside of the MLS
encryption layer, but they are not visible to the server. This section focuses on the server visible
state events, see "Encrypted state events" for state events inside of the MLS layer.

Every valid state event in this room version is required to have an empty state key.

The `m.room.create` event has a mandatory `encryption_algorithm` field now to set the encryption algorithm
for the room. This would be the MLS ciphersuite prefixed with `m.mls.v1.` for example
"m.mls.v1.MLS_128_DHKEMX25519_AES128GCM_SHA256_Ed25519". All future events in the room need to
have the same algorithm set. To change the algorithm a new room needs to be created possibly via the
room upgrade endpoint.

A new state event is introduced to track the current MLS commit. This event follows the format for
encrypted events with only an `algorithm` and `ciphertext` field. It contains the current MLS
commit as a MLS private message encoded as urlsafe base64 without padding.

The MLS commit contains a CBOR encoded field in its unencrypted authenticated data of the MLS
private message. The object follows the following format (here illustrated as JSON):

```json
{
   "federation": {
      "powers": ["example.net", "example.org"],
      "servers": ["example.com", "example.net", "example.org"],
      "can_propose": ["example.com", "example.net", "example.org"]
  },
   "security": {
      "window": 0,
      "required_verification": "m.cross"
  }
}
```

`federation.powers` represents an ordered list of servers allowed to send new MLS commits.
`federation.servers` represents all servers that are allowed to participate in this room and will
receive messages. Each "power" has to be present in "servers". The order of servers in the powers is
used for state resolution. This replaces the existing approach of ordering by power level and
provides a reliable tie break, since no server can have the same index as another server. There are
specific rules around promotions in the powers list to provide similar guarantees about demoting
more powerful users/servers as the power levels event did. Neither of those lists can be empty.
`security.window` specifies the seconds of how long old private keys might be kept to recover from
mls commit conflicts. Optional, defaults to 0\. Clients should not allow values larger than 7 days
and should clamp any larger values to that maximum.
`security.required_verification` specifies the verification required to add new users or clients
to the MLS state. The sender of such a commit needs to have at least this level of verification with
the other participant to add them. Possible values are:

- `m.direct`: Direct verified (without cross-signing)
- `m.cross`: Verified via cross-signing
- `m.tofu`: Trust on first use, so pinning the first master key the user has seens for that user
- `m.none`

Optional, defaults to `m.cross`.

The MLS commit should use the event type "m.mls.commit".

Additionally the MLS commit can be sent by clients not in the "powers" list. This
"m.mls.pending_commit" has the same format as the "m.mls.commit", but is not a state event. Such an
event contains a full MLS commit event, not an MLS proposal, but it isn’t accepted as a commit yet.
Instead a different server will apply it and convert it to a state event, if the origin is listed in
the "can_propose" list and some additional rules that are lined out later in this proposal.

All other events in the room should be `m.room.encrypted` events and encrypted using the currently
specified MLS algorithm.

### Authorization Rules

Most state events from other room versions are now invalid. This requires major changes to the
authorization rules. The mls commit event now defines what servers are allowed to send events into a
room as well as who is allowed to modify the commit event. Additionally unencrypted content is
generally disallowed in this room version and the create event defines the encryption algorithm now.
The below rules describe such behaviour and if there is the option to decide between stricter and
less strict validation, those rules tend to favour stricter validation. Some of those rules could be
made more lenient to allow more extensibility if such a need is expected.

In the following section the “epoch” field refers to the epoch of the MLS message
([RFC9420 Sec. 6.3][RFC9420Sec6.3]), which is available as part of the ciphertext, but not encrypted.

1. Only allow empty state keys or events without state keys. If the state key is present and not empty, reject
2. if state_key is present and event type is not `m.mls.commit` or `m.room.create`, reject
3. if the event is `m.room.create`:
   1. If it has no state_key, reject
   1. If it has any `prev_events` or `auth_events`, reject
   1. If the room version is not an mls version, reject (or it should have been a different
algorithm for that room version!)
   1. If `origin` does not match the domain of the `room_id`, reject
   1. If the `algorithm` is not present or empty, reject
   1. Otherwise, allow
4. Considering the events auth events:
   1. If there is not exactly one `m.room.create` event (with implicitly an empty state key), reject
   2. If the event is not the `m.room.create` event (we never get here) or an `m.mls.commit` event
with epoch == 0 (we do get here), then if there is no `m.mls.commit` event in the auth events,
reject (could move this check to a different section)
   3. If any additional auth events are present, reject
   4. If any auth event did not pass the checks done on PDU receipt, reject
5. If the `content` of the `m.room.create` event in the room state has the property `m.federate` set
to `false`, and the `origin` of the event does not match the `origin` domain of the create event,
reject.
6. If the `origin` is not listed in the `servers` of the previous `m.mls.commit` event (unless it is
the first commit), reject. Previous in this case refers to the m.mls.commit from the auth events
representing the current state of the room.
7. If the room_id or the MLS group_id do not match the room_id of the create event, reject
8. If the algorithm of the event does not match the create event, reject
9. If the event type is `m.mls.commit`:
   1. If it has no state_key, reject
   1. If the epoch is 0, the origin has to match the room id
   1. If the epoch of this event is not exactly the epoch of the previous `m.mls.commit` event + 1,
reject
   1. If the MLS content is not a commit, reject
   1. If `servers` is empty or any of the entries are not a valid servername, reject
   1. If `powers` is empty or any of the entries are not a valid servername, reject
   1. If the `origin` is not listed in `powers` (of the previous `m.mls.commit` event), reject
   1. If the `powers` has entries not in `servers`, reject
   1. If the `powers` start not with exactly the same entries in the same order as the subset of
entries in the previous `powers` above the `origin` , reject
   1. If the `can_propose` has entries not in `servers`, reject
   1. Otherwise, allow
10. If the event type is `m.mls.pending_commit`:
    1. If the epoch of this event is not exactly the epoch of the current `m.mls.commit` event + 1, reject
    2. If the MLS content is not a commit, reject
    3. If `servers` is empty or any of the entries are not a valid servername, reject
    4. If `powers` is not the same as the current `m.mls.commit`, reject
    5. If `origin` is not listed in `can_propose` of the current `m.mls.commit`event, reject
    6. If the `powers` has entries not in `servers`, reject
    7. If the `can_propose` has entries not in `servers`, reject
    8. Otherwise, allow
11. If the epoch of the `ciphertext` is not the epoch of the current `m.mls.commit` event + 1,
reject
12. Otherwise, allow

These rules currently also don’t account for redactions.

### State resolution

State resolution only has to resolve conflicts between mls commits now, but we will still describe
it as a generic algorithm. This algorithm ensures that only a single commit is accepted for each MLS
epoch.
This MLS version of state resolution is very similar to the existing state resolution. Only small
changes are applied to replace the power level events with MLS commit events. The core of Matrix,
where a higher power level implies a more trustworthy homeserver, is encoded directly in the mls
commit events as part of the "federation.powers" list. Commit events are also used in the auth chain
similar to how power levels are used in state resolution v2. As such the necessary changes can be
described as follows:

During topological power ordering events are now ordered by the index of the origin server in the
"federation.powers" list instead of the power level of the sender. A lower index implies a higher
power. Events sent by an origin with a lower index should therefore be ordered before events of an
origin with a higher index. The other rules regarding the origin_server_ts and the eventid stay
the same and exist as tie breakers.

Mainline ordering is similarly redefined in terms of mls commits now. Every event needs to reference
an MLS commit in its auth events (excluding the first commit and the create event) and because of
this, events can be ordered by the commit events they reference.

### Commit handling with multiple servers

MLS requires the delivery service to resolve conflicting commits. This requires some form of global
synchronization of the system, which is difficult in a decentralised setting.

The MLS protocol always requires server-side approval of a commit before it can be applied by
clients. Therefore clients need to wait for a commit to appear in the sync response before applying
it.

There are several options for how a client can send a new commit into a room.

* Users on the first server listed in the "powers" list can send commit state events directly. They
still have to wait for the commit to sync back to them, before they can consider the commit
accepted.
* Other servers in the "powers" list could in theory send commits directly (from an auth rule
perspective), but should not do so.
* Servers not listed as the first entry in the "powers" list should send a "m.mls.pending_commit"
as a normal message. This will then be applied according to the sorting rules of that server, or
according to the rules in the following section, and a commit state event will be sent by one of the
homeservers listed in the "powers" list. Only users on servers in the "can_propose" list can send
"m.mls.pending_commit". Note that proposed commits are regular MLS commits for the MLS protocol,
but are communicated as "proposed commits" in the Matrix infrastructure.
* Servers not listed in the "can_propose" list can not modify the MLS group directly and require
other users on other servers to do the modifications for them. However, clients on any server can
send MLS proposals.

If only one server is listed in the powers of a room, no commits can result in a conflicting set
during state resolution even if multiple servers are participating in the room.

![Pending commit flow][pending-flow]

### Commit Conflict Handling

A more decentralized version of commit conflict resolution with committing clients on different home
servers can be implemented with eventual consistency when accepting the resulting reduction in
security.

If a room decides to allow this, conflicts between multiple servers applying the same
`m.mls.proposed_commit` will be resolved by state resolution, but as long as the same commit was
applied, they have no impact on clients. In this case there is no synchronous communication between
servers. Instead the commit is optimistically applied by one homeserver and forwarded to other
homeservers via federation. If there is a conflict, this is resolved by state resolution. Clients
are then notified via the sync API about changes in the state they expect.

Only the highest power server may send `m.mls.commit` events directly. Clients on other servers
should send `m.mls.proposed_commit` events instead. These may then be replayed by servers in the
"powers" list.

Servers have a 5 minute conflict window to apply `m.mls.proposed_commit` they receive. The
highest power server can apply the commit in the first 3 minutes after the `origin_server_ts` of
the `m.mls.proposed_commit` event. After this a 2 minute grace period follows to allow for some
clock desynchronization latencies as well as message transfer. The next 5 minutes are for the second
server listed in "powers" and so on. If the commit referenced by the auth events of a
`m.mls.proposed_commit` is not the current commit, a commit has already been applied and servers
should ignore the `m.mls.proposed_commit`.

Clients can know their `m.mls.proposed_commit` failed to be applied if they haven’t received a
`m.mls.commit` event matching their `m.mls.proposed_commit` after "len(powers)*5" minutes.

State resolution might result in some clients losing access to messages as they threw their private
state away immediately to provide PCS and forward secrecy. In that case the clients dropped by the
state event will have to be sent another welcome to rejoin them into the room.

The duration of this temporary compromise is specified in the security.window in seconds. If this
value is not 0, a client is allowed to keep the old private keys required to apply a different
commit around for up to this many seconds. This allows a client to recover automatically from state
conflicts happening during a very small period.

Having conflicting commits will lead to some undecryptable messages. For short durations that can be
mitigated by keeping the old state around for seconds to minutes. This is the common case when
people invite new users at the same time or do otherwise racing modifications on different servers.
For long durations no automatic recovery is possible and manual communication is necessary. We
expect those cases to be rare even in larger federations. Long term server outages usually don’t
include membership modifications at the same time as usually one server is completely offline. Even
if there is just a network split between 2 "power" servers, membership modifications on both sides
of the split tend to be rare and can be resolved after the network outage with some manual
communication. Not allowing the other side to recover encrypted messages in that case might even be
a positive to some extent, where one side abused the outage to add a malicious actor. And such
behaviour matches other end to end encrypted messaging systems, where key material can’t be
retrieved or exchanged.

For the common case of small to medium sized encrypted groups with only a few "power" servers a
short pcs window should provide a reasonable user experience. Further improvements could be done in
the future by allowing for rejoins using preshared keys or external joins. State conflicts can be
avoided by only listing one homeserver in the "powers" list or using the hub server approach.

This approach of handling conflicting commits is compatible with the eventual consistent MLS
architecture. The main drawback here is that it requires a careful evaluation of the window in which
a previous state is kept. Further, two different state resolution mechanisms, one from the
end-to-end encryption layer in MLS, and one from the application layer in Matrix, makes the state
resolution much more fragile and difficult. Additional mechanisms for solving them will most likely
be necessary and an increased number of undecryptable messages are expected. Allowing a copy MLS
state opens the door for illegitimate use of old state and potentially breaking security guarantees.
This approach should therefore only be implemented and used after carefully designing the acceptable
compromise window as well as a misuse resistant implementation.

### MLS encrypted events

Events are encrypted using plain MLS and sent into a room as m.room.encrypted events. The sender can
be retrieved using MLS, which allows mapping a decrypted MLS message to a credential.

The encrypted payload should be:

```json
{
   "type": "m.room.encrypted",
   "content": {
      "algorithm": "m.mls.v1.MLS_128_DHKEMX25519_AES128GCM_SHA256_Ed25519",
      "ciphertext": "<encrypted_payload_unpadded_base_64>"
   }
}
```

This differs from the encrypted payload in megolm by not having sender_key, device_id or
session_id in the framing. This data is already part of the MLS layer and sender_key as well as
device_id are also deprecated for megolm messages. MLS encrypts the sender, but authenticates the
sender for people who can decrypt the message. MLS does have indirect equivalents to the session id
in megolm as part of the epoch and key tracking. Those are not directly comparable, but serve a
similar purpose.

The plain text payload should be:

```json
{
   "type": "<event_type>",
   "content": "<event_content>"
}
```

This is different from megolm encrypted events as the room_id is already part of the MLS message
and doesn’t need to exist in the inner payload.

This does not currently allow for online key backup. Any key backup breaks Forward Secrecy as it
allows an attacker to access possibly all past messages. There are various ways message
synchronization and backup could be supported by introducing an additional layer of indirection.
This can be based on exporters from the MLS key schedule. But this will require a new protocol with
a separate security analysis and is left out of this proposal.

### Encrypted state events

This proposal provides no support for generic state events outside of the MLS layer. State events
inside the MLS layer are agreed upon using a GroupContext extension. The extension id for the group
state should be 0xF6D0. 0xF000 to 0xFFFF is reserved for private extensions, 6D is a lowercase "m" in
ASCII and 0 is just a placeholder.

The extension is a required extension and has to be supported by all group members.

This extension should be a JSON encoded map of state event type to state key to state event content.
This could for example look like this:

```json
{
   "m.room.name": {
      "": { "name": "Dinner party" }
   },
   "m.room.topic": {
      "": { "topic": "What will we have for dinner?" }
   },
   "net.example.custom.event" {
      "somestatekey": { "custom": "field"},
      "someotherstatekey": { "custom": "field2"}
  }
}
```

Clients should validate the length and character set of event types and state keys. The mapping
should also be canonically encoded.

Having all state events in one extension forces severe size limits on the combination of all events.
For this reason this is just a transitionary solution. In the future this solution should be
replaced with an MLS extension, which allows for delta updates. One such option could be appsync:
[https://datatracker.ietf.org/doc/html/draft-barnes-mls-appsync-01](https://datatracker.ietf.org/doc/html/draft-barnes-mls-appsync-01)

Allowing only encrypted state events vastly reduces the metadata available for a room. Currently
even in megolm encrypted rooms, the room name and topic are not encrypted (as well as all other
state events). This is often surprising to users who tend to store confidential information in the
room topic and sometimes the room name and people often criticize Matrix for leaking such metadata.
In rooms based on this proposal that information is encrypted.

### Credentials & KeyPackages

In the long term a Matrix specific credential should be registered with IANA. Until then Matrix
should use a basic credential with a specific payload. This payload should contain the TLS encoded
user_id and device_id in utf-8 as well as the public signing key of the MLS client. These
credentials should then be uploaded as another key under the users device keys. The algorithm for
the credential should be the plain text algorithm from the MLS specification prefixed with
"m.mls.v1".

These credentials should be cross-signed. They should list the above GroupContext extension as one
of the supported extension types. Additionally the device keys should be signed using the signing
key of the credential. The signature should use the credential type as the key id.

No extensions are done to the key distribution APIs at this point. In the future those APIs may have
to support filtering by extension types.

Clients will upload key packages to /keys/upload. Key packages should use the respective algorithm
(prefixed with m.mls.v1) as well as the reference hash of the key package as their identifier,
separated by a colon. As key packages already include a signature, they should be uploaded as a
base64 encoded string instead of an object.

Clients can upload last resort key packages as a fallback key. Clients should be notified about key
counts and usage over sync as they do for olm.

Key packages can be claimed remotely. Such claims should happen in order to allow synchronizing
client and server state.

Additionally the following API should be exposed by homeservers to allow a user to query their
current onetime keys:

```
GET /_matrix/client/v3/keys/list
{
    "one_time_keys": ["m.mls.v1.MLS_128_DHKEMX25519_AES128GCM_SHA256_Ed25519:AAAAAAAAAAAA"],
    "fallback_keys": ["m.mls.v1.MLS_128_DHKEMX25519_AES128GCM_SHA256_Ed25519:AAAAAAAAAAAB"]
}
```

### Adding users to a room

To invite user's devices into a room the client should first fetch the key packages for that user and add the
user to the MLS group. The key packages should be validated and should be cross-signed as configured
in the additional authenticated data of the current MLS commit.
After this the commit in the room is updated. Once this commit is accepted by the delivery service,
the inviting user should send out the welcome message as a to_device message and send an invite
using the /invite endpoint. To distribute the ratchet tree the ratchet tree MLS extension is
currently required.

The invited user will then receive the invite and welcome message. If the user wants to join the
room, the client can send a request to the /join endpoint.

As no member events are used in this room version, the direct /state endpoint can not be used to
change membership in a room

![Invite flow][invite-flow]

## Potential issues

Some of these issues are already explained in the proposal sections. The following list provides
them and other issues together to allow an easier overview.

## Displayname & Avatars

Currently this proposal does not support per room avatars. Instead clients have to fall back to
the global user profile to query display name and avatar for users. In the future per room profiles
could be supported by making them part of the group context. As this has storage overhead and
possible abuse aspects, this feature is left up to an future MSC to implement.

Falling back to the global profile for users could cause moderation problems as room moderators
can’t redact problematic display names. As a result we currently recommend not showing the
display name for users not part of the room.

Querying a number of profiles could also potentially leak room membership to the server. Storing
profile information as part of the MLS group context could be one way to mitigate this in the future.

### Redactions

Currently redactions are not supported in the outer protocol layer. This has the benefit of making
redactions invisible to the server, but also prevents any server side aggregation. This also means
content can’t be deleted. As we require all events to be encrypted, this might not be a major
problem, but policy makers might disagree. Redactions could be supported in various ways and we
haven’t decided on a solution yet.

### Decryption errors

Every time the commit graph diverges, some branch of messages will become undecryptable. This is
explicitly tracked using the auth events for each event, which identifies which epoch was used to
encrypt an event. In this case, the group needs to be reset, using mechanisms from MLS such as
re-init, and potentially manual, social interaction. Additional protocols are needed to recover from
such a state. Designing such protocols is left open to future MSCs.

One benefit of MLS is that commit events clearly mark transitions in key material. This should
reduce the amount of individual clients having no access to messages as well as be more
introspectable by having the current access to events spelled out every commit in the ratchet
tree/group context.

Reducing the security of the room, it is possible to use the security.window of previous epochs to
decrypt old messages. Note however that using the security.window breaks some MLS security
guarantees and as such  should only be used and implemented after a rigorous security analysis on
the exact impact.

### Verification chains

This proposal relies on cross-signing to add new members and devices. Such a structure might not
provide sufficient security guarantees. In megolm each sender can decide who can decrypt a message.
In MLS this is a shared state and relies much more heavily on each individual to provide the same
trust guarantees. For this reason the minimum requirement is spelled out in the authenticated data
of the commit events, but any client can in theory violate this requirement. Stricter rules around
adding members could resolve this in the future.

A more comprehensive authentication mechanism and application level policies can be added in future
to allow clients to validate more (authentication) policies with more granularity.

### Permissions

The current proposal gets rid of power levels. It doesn’t provide any replacement for per user
permission management. This might be fine for smaller encrypted groups, but larger groups may want
to restrict state and member modifications to only specific users, beyond what is implemented on the
client. If additional permissions that the server should enforce are desired, additional information
may be exposed from the client to the server.  One possible direction could be by exposing signature
keys for specific transitions, that are only accessible to specific users, that a server could then
validate without understanding the content of events. For example specific signatures to be able to
send invites and allow other users to gain access to the encrypted messages of a room. Other
approaches might be possible by leveraging some features of MLS more directly.

This feature is left for future MSCs to resolve.

### Room state

Currently all state is stored in one GroupContext extension. This has obvious size limitations.
There are proposals to enable delta updates for MLS extensions, but those are not finished yet. We
hope that such MLS extensions will be finished in the near future and an MSC should then be able to
replace the state synchronization mechanism in Matrix with such an extension.

As member events don’t exist anymore, we expect MLS state to be significantly smaller.

Putting all state into the GroupContext also requires atomic updates. As such multiple clients won’t
be able to modify different state events in parallel. This will impact some applications. For now we
recommend using application messages instead of using Matrix as a distributed database. Frequently
updated state causes a lot of load for federation and increases the hosting cost for Matrix. Instead
Matrix should be used for exchanging messages and state should be stored out of band.

Some applications might also benefit from MLS and won’t need to store state in Matrix anymore. For
example a MatrixRTC application could validate room membership directly by relying on MLS keys and
signatures.

### Key Backup

This proposal does not support any form of key backup. Key backups break the security guarantees of
the end-to-end encryption in MLS.

However, key backups are not necessary. The reason Matrix uses key backups nowadays is because of
the lack of a message history synchronization and backup protocol. These features can be implemented
with secure protocols without breaking the security of the end-to-end encryption. Specification of
such protocols is left open for future MSCs.

### Size of Welcome Messages

Welcome messages can become pretty big when they contain the ratchet tree. To reduce the message
size of welcome messages, MLS allows distributing the ratchet tree (which is the largest part in
the message) in other ways. Future MSCs can define other delivery mechanisms for ratchet trees
when the size of the welcome messages becomes an issue.

## Alternatives

### MSC2883: Matrix-flavoured MLS

[MSC2883][MSC2883] provides MLS support over Matrix by making extensive changes to MLS (dMLS). Those changes
compromise Forward Secrecy by making it impossible to delete past private keys. Such a change does
not provide the security guarantees we are looking for and is incompatible with MLS. If state
resolution allows an arbitrary long amount of time between one server changing membership and other
servers being made aware of that change, secret keys to resolve those commits have to be kept around
for the same amount of time.

This proposal instead doesn’t modify MLS. It can be used with existing MLS implementations. The only
changes done are safe extensions using additional data in fields supporting such extensions. As such
this MSC can build on the existing reviews of MLS and only requires additional review for the parts
not covered by MLS like credential signatures and rules around member additions in MLS (which MLS
only defines under an abstract authentication service).

### MSC4244: RFC 9420 MLS for Matrix

This proposal shares a lot of similarities with [MSC4244][MSC4244]:

- Both proposals move to more of a hub approach in how they handle commits. In the default mode only
one server is responsible for forwarding and ordering MLS commits. This is basically required by
MLS, although this proposal includes some optional parts to allow using MLS in a more decentralized
setting with reduced security compared to [MSC4244][MSC4244].
- Both proposals put the encryption algorithm into the create event ([MSC4244][MSC4244] technically uses
[MSC4245][MSC4245]), but this proposal uses "algorithm", while [MSC4245][MSC4245] uses "encryption_algorithm". This is
not a functional difference.
- Both proposals reuse the existing key infrastructure to distribute key packages. [MSC4244][MSC4244] includes
some additional filtering based on key package capabilities that this proposal explicitly left for a
future MSC.

In other areas the proposals have some significant differences. Detailed comparison is difficult at
this time as both proposals are still in progress and [MSC4244][MSC4244] includes a lot of open "TODOs":

#### Membership handling

This proposal does not use membership events and gets rid of the "sender" field in events. This
essentially makes membership opaque to the homeserver (apart from its own local users for distributing
messages to clients) and gets Matrix a lot closer to portable
identities as well as provides a lot less metadata to the homeservers as well as anyone else being
able to intercept HTTPS traffic. [MSC4244][MSC4244] instead uses traditional membership events with some
additional rules on how to make them match the MLS membership list.

The approach from [MSC4244][MSC4244] has benefits regarding API compatibility. A lot of clients and servers
today expect the sender field on events. Clients also usually expect being able to query the member
list from the homeserver and use membership events to set custom, per-room names.

This proposal on the other hand provides vastly less metadata to parties outside of the MLS group.
This also has performance benefits. Today membership events are one of the biggest sources of
storage and CPU requirements on Matrix. Outside of the MLS state shared between clients, rooms are
expected to be a lot smaller and more performant using this proposal. It is also less likely for
users to confuse network membership in a room with the cryptographic group membership based on MLS
if the traditional server side APIs for membership queries don’t work for MLS encrypted rooms. And
because this proposal removes most state events it should also make lazy loading of room members as
well as fast joins for remote rooms redundant.

This does come at the cost of not having all the different membership states available anymore.
Currently only "invite", "join" and "leave" are supported by this proposal. Restricted joins and
knocks could be supported in the future however by relying on MLS native features like "external
commits" or similar.

#### Message framing

This proposal explicitly supports MLS private messages. While some membership information is still
exposed to homeservers, only the local homeserver knows the membership of its users. Homeservers
don’t know what members are part of a room on remote homeservers. By leveraging the federation
aspects of Matrix we actually manage to achieve better metadata protection than some centralized
protocols in this specific aspect.

[MSC4244][MSC4244] doesn’t spell out if it uses private or public message framing. We assume it can only work
with public message framing. This exposes a lot of data to the homeserver, which this proposal
instead manages to protect.

#### Key backup and encryption without devices

This proposal does not support online key backup or dehydrated devices. In theory those could be
supported, but a major motivating factor behind this proposal is better security. Both key backup
and dehydrated devices allow an attacker to possibly read an unbounded amount of past messages.
While that is convenient, it removes the fundamental security aspects of MLS.

[MSC4244][MSC4244] mentions support for dehydrated devices, but not online key backup. But even supporting
dehydrated devices in the proposal is a significant compromise on security and requires thorough
security analysis.

#### Support for decentralization

MSC4244 currently does not support changing which homeserver is responsible for ordering MLS
commits. This effectively makes rooms centralized and reliant on a single homeserver. That is fine
for many use cases and simplifies many aspects of Matrix, but also loses one of the main selling
points of Matrix.

This proposal instead optionally supports decentralization. By changing the "powers" entries,
responsibility for a room can be transferred. Optionally multiple servers can also be responsible
for a room at the same time, which provides transparent fallback semantics in case a homeserver is
"lost" temporarily or permanently, but comes at the cost of security or undecryptable messages. In
this proposal that choice is left to the user as different user groups have different needs.
Existing Matrix enthusiasts are very decentralized and often run single user homeservers with no
uptime guarantees. Government style deployments on the other hand often have highly available
homeservers and don’t necessarily need the more decentralized aspects of Matrix, but tighter
security guarantees instead.

#### State events and permission handling

This proposal removes most state events and instead puts them inside the shared MLS group context.
As a result there is no state resolution run on those state events. Only the current MLS commit
defines what the current room state events are. As a side effect all state events are encrypted now.

[MSC4244][MSC4244] relies on traditional state events and does not provide a solution to encrypt state events
yet. This allows it to enforce normal power levels and have the traditional permission handling. But
it has significantly worse metadata protection. We don’t want users to accidentally leak
confidential information using the `m.room.name` or `m.room.topic` events.

Once we moved state events into the MLS state, the existing power level permissions provided little
value and we removed them to simplify the protocol. This does not mean that permissions would not be
needed, but they would likely have to be enforced by clients if we don’t want to expose additional
metadata to the homeserver and having the homeserver enforce permissions can conflict with MLS
internal rules.

#### Welcome messages

In our proposal welcome messages are sent between devices directly. They are only necessary to be
received by new members of the group and can become quite large. [MSC4244][MSC4244] sends them to the delivery
service first, which then forwards the welcome to the user, if the commit is accepted. In our
proposal a client would have to wait for the commit to be accepted before sending out the welcome
and invite to a new client. Doing this server side has benefits in cases where the user goes offline
before the commit is accepted, but also requires more bandwidth.

If [MSC4244][MSC4244] supported private MLS messages a lot of its server side validation would become redundant
and would likely obsolete the need for the additional complexity of server side welcome forwarding.

Apart from that, [MSC4244][MSC4244] is heavily reliant on to_device messages. to_device messages have
historically not been very reliable. In this proposal instead they are only used when inviting new
members, but otherwise normal room federation is used. Invites are already point-to-point and
therefore should succeed in the same cases where the welcome message can also be sent.

### Keeping membership events

MLS could also be done while keeping membership events and the sender key on events around. This
would however require more extensive state resolution and such member events are likely to diverge
from the MLS state. It also leaks metadata to servers.

Alternatively MLS commits could be sent as MLS PublicMessages. This would expose the group
membership to the server and the server could generate membership events to send to clients, but
this would also expose the whole group state to the server.

In our proposal we instead handle this membership outside of the room. While this makes it harder to
model bans and other membership transitions, it vastly reduces metadata sent over federation. It
also prevents clients from querying the room membership using the server. We view this as a benefit
as now the only complete membership list a client could have is from decrypting the MLS state. This
provides, to users, a single source of truth about the current room membership.

## Security Considerations

This proposal changes almost all aspects of end-to-end encryption on Matrix. For obvious reasons
this includes a lot of security considerations. But we claim to reduce the necessary considerations
a lot by not doing any changes to MLS itself.

First, it is worth noting that this MSC introduces a much stronger notion of end-to-end security.
MLS cryptographically enforces a global view of the group. Only the members that share a common view
of the group can exchange messages. Further, this end-to-end security implies that only the clients
may be capable of validating the common group state. Any application level operation must be
performed by clients, rather than servers. For example, moderation policies on who is allowed to add
another user to the group are enforced by the clients who commit the changes to the group.

User verification is left unchanged in this proposal and hence should be updated in future proposals
to achieve a higher level of trust in the identities of users and clients in a group.

Since MLS is used as defined in the RFC, the security in the case of a single home server that is
enforcing commit ordering is guaranteed by MLS and its analysis. As long as the federation ensures
that the home server performs ordering of commit messages, as described in this proposal when using
owning home servers, this does not change in the federated setting.

When MLS state is copied however, as described in the scenario where commits are applied
optimistically and a security window is used, the security degrades. While generally allowed in the
eventual consistency MLS architecture, this scenario is not covered by existing security analyses of
MLS and is incompatible with the deletion schedule required in [RFC 9420][RFC9420].

One security concern may be the "Network membership" of users. Currently users can’t be removed from
a room, just from the MLS state. However, this is not a security issue as the security depends
solely on MLS. But it may be a privacy issue.

## Unstable prefixes

Keys, credentials, signatures, room version and event types from this proposal should use the prefix
"de.bwi".

As such credentials, key packages and signatures should be prefixed with "de.bwi.mls.v1" instead of
"m.mls.v1".

The room version should be "de.bwi.mls.v1".

The mls commit event should be "de.bwi.mls.pending_commit".

## Credits

Many thanks to [Cryspen (Franziskus Kiefer, Jan Winkelmann, and Karthikeyan Bhargavan)](https://cryspen.com/)
and [famedly (Niklas Zender and Nicolas Werner)](https://www.famedly.com/) both from Berlin 🧸
for their ideas, feedback and work on that...you guys rock!

[RFC9420]: <https://datatracker.ietf.org/doc/rfc9420/>
[RFC9420Sec6.3]: <https://datatracker.ietf.org/doc/html/rfc9420#name-encoding-and-decoding-a-pri>
[MSC2883]: <https://github.com/matrix-org/matrix-spec-proposals/pull/2883>
[MSC4244]: <https://github.com/matrix-org/matrix-spec-proposals/pull/4244>
[MSC4245]: <https://github.com/matrix-org/matrix-spec-proposals/pull/4245>

[invite-flow]: <./images/4256-invite-flow.png>
[pending-flow]: <./images/4256-pending-commit-flow.png>
