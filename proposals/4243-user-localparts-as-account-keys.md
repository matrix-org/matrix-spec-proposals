## MSC4243: User ID localparts as Account Keys

User IDs should be public keys because:
 - User IDs as they are today are direct personal data. For [GDPR](https://github.com/matrix-org/matrix-spec/issues/342)
   reasons we would like to be able to remove direct personal data from the immutable append-only DAG. This proposal
   replaces user IDs with indirect personal data.
 - As user IDs are user controlled, spammers set their localpart to abusive messages in order to harass and intimidate others. Redactions
   do not remove the user ID so these messages persist in the room.

Furthermore, we would like to remove the need for servers to sign events with their federation signing
key to:
 - improve the security of the federation API by reducing split-brain opportunities,
 - [improve the robustness](https://github.com/matrix-org/synapse/issues/3121) of the client-server API.

This follows the wider pattern of IDs becoming cryptographic primitives:
 - Event IDs were converted to SHA-256 hashes of the event JSON in [MSC1659](https://github.com/matrix-org/matrix-spec-proposals/pull/1659)
 - Room IDs were converted to SHA-256 hashes of the create event in [MSC4291](https://github.com/matrix-org/matrix-spec-proposals/blob/matthew/msc4291/proposals/4291-room-ids-as-hashes.md)

Several proposals already exist to do this, notably [MSC4014: Pseudonymous Identities](https://github.com/matrix-org/matrix-spec-proposals/pull/4014)
and its parent [MSC1228: Removing mxids from events](https://github.com/matrix-org/matrix-spec-proposals/pull/1228).
However, these proposals drastically alter one of the fundamental data types in Matrix. This has a
negative effect on the (particularly client) ecosystem as they need to update their code to handle the changes.
This was seen in [MSC4291: Room IDs as hashes of the create event](https://github.com/matrix-org/matrix-spec-proposals/pull/4291)
which removed the `:domain` part of the room ID. Furthermore, both of those MSCs suffer from scope creep: MSC4014 had per-room per-user keys, and MSC1228 had room keys complete with new `^` and `~` sigils. 

Instead, this proposal solely addresses the problem with allowing direct personal data in the user ID and using the server signing key
to sign events, taking care to keep the user ID format compatible with the existing ecosystem. This makes the proposal very light, and
easier to implement incrementally on top of the existing Matrix ecosystem, whilst leaving room for per-room per-user keys or
client-controlled cryptographic keys in the future.

### Proposal

Starting in room version `vNext`:
 - Each user is identified using an ed25519 key: an "Account Key". A user SHOULD[^perroom] have exactly 1 immutable _account key_ for all rooms they are a part of.
 - User ID _localparts_ in rooms are replaced with the unpadded urlsafe[^urlsafe] base64 encoded public part of the _account key_.
   Leaving and rejoining the same room MUST NOT change the _account key_.
   An example _user ID_ is: `@l8Hft5qXKn1vfHrg3p4-W8gELQVo8N13JkluMfmn2sQ:matrix.org`.
 - The private key for the `sender`'s _account key_ signs the event JSON over federation. Servers no longer
   sign events with their [server signing key](https://spec.matrix.org/v1.14/server-server-api/#retrieving-server-keys).[^signing]
   Co-signed events (e.g invites) are still co-signed, but with _account keys_ not server signing keys.
 - The domain part of the user ID is kept for compatibility and to provide _routing information_ to other servers.
   Servers still determine which servers are in the room based on the domain of the user ID.
   
Signatures on an event follow the same format as today for backwards compatibility with existing server code, but:
 - the [entity](https://spec.matrix.org/v1.14/appendices/#checking-for-a-signature) signing the event is now public part of the account key.
 - the [signing key identifier](https://spec.matrix.org/v1.14/appendices/#checking-for-a-signature) is now the constant `ed25519:1`[^keyid].
```json
{
  "type": "m.room.member",
  "state_key": "@l8Hft5qXKn1vfHrg3p4-W8gELQVo8N13JkluMfmn2sQ:matrix.org",
  "content": {
    "membership": "join",
    "displayname": "Alice",
  }
  "room_id": "!K3DOWWLmkHLl52yJ-vT8J5jX5wuYZati_KvC6PliIPE",
  "sender": "@l8Hft5qXKn1vfHrg3p4-W8gELQVo8N13JkluMfmn2sQ:matrix.org",
  "signatures": {
    "l8Hft5qXKn1vfHrg3p4-W8gELQVo8N13JkluMfmn2sQ": {
      "ed25519:1": "these86bytesofbase64signaturecoveressentialfieldsincludinghashessocancheckredactedpdus"
    }
  }
}
```

Terminology for the rest of this proposal:
 - Account Key: the ed25519 public key for the user's account, e.g. `l8Hft5qXKn1vfHrg3p4-W8gELQVo8N13JkluMfmn2sQ`.
 - Account Name: The human-readable localpart today e.g `alice`.
 - Account Name User ID: user IDs as they exist today, formed of an account name and domain e.g `@alice:example.com`
 - Account Key User ID: user IDs of the form `@l8Hft5qXKn1vfHrg3p4-W8gELQVo8N13JkluMfmn2sQ:matrix.org`, formed of an account key and domain.
 - Localpart / Domain: segments of a user ID as they are defined today. 'Localpart' is ambiguous and should be qualified as 'account name' or 'account key'.
   'Domain' may be _unverified_ or _verified_.

>[!NOTE]
> Naming is a famously hard problem. The term "Account Key" was chosen for a few reasons:
> - Accounts are heavily implied to live server-side which matches the storage location of this key.
> - It implies the key is user ID scoped, which it is (as opposed to room / device scoped).
> - It isn't a term used in Matrix today (unlike Master Key, User-Signing Key, Self-Signing Key which are all cross-signing keys, or Sender Key which is used in E2EE)
> - As the key is per-user, it doesn't imply unlinkability of the key between rooms (unlike Pseudonymous Identities).
> - It provides reasonable flexibility for extensions to the key e.g if they become per-room, a 'Pseudonymous Account Key' works well.
>   If the key moves client-side, a 'Local Account Key' also works as a descriptor, even combined as a 'Pseudonymous Local Account Key'.

In order to map the account key to a user, servers will ask the domain-part of the user ID for information about the
account key via a new bulk federation endpoint:
```js
POST /_matrix/federation/v1/query/accounts
{
    "account_keys": [
        "l8Hft5qXKn1vfHrg3p4-W8gELQVo8N13JkluMfmn2sQ",
        "EgdGx+0oy/9IX5k7tCobr0JoiwMvmmQ8sDOVlZODh/o",
        "cWm64pdXOGz1DbIXTuH+24szY/+9HjPP7jZwbDjn12s"
    ]
}
```
Returns:
```js
200 OK
{
    "account_keys": {
        "l8Hft5qXKn1vfHrg3p4-W8gELQVo8N13JkluMfmn2sQ": {
            "account_name": "kegan",   // The account name. The 'localpart' of a user ID today.
            "domain": "matrix.org", // The 'domain' of a user ID today.
            "signatures": { ... }   // This JSON object is signed with the account key to allow changes in the account name/domain to be detected.
            // This JSON object is extensible. In the future we could add:
            //  - Profile info e.g displayname, avatar_url
            //  - Per-room keys info e.g room_id
            //  - 3PID info e.g email_address (could this replace 3PID invites?)
        },
        "EgdGx+0oy/9IX5k7tCobr0JoiwMvmmQ8sDOVlZODh/o": {
            "account_name": "matthew",
            "domain": "matrix.org",
            "signatures": { ... }
        },
        "cWm64pdXOGz1DbIXTuH+24szY/+9HjPP7jZwbDjn12s": {
            // alternatively this can be another error code to indicate why this key is unknown
            "errcode": "M_UNKNOWN"
        }
    }
}
```
Unknown account keys are explicitly marked as unknown. If an account key is missing, then the sending server should try again later with that key
to resolve it. This creates a bidirectional link:
 - By signing event JSON, the account key claims to belong to a particular domain. This is embedded into the DAG.
 - By responding to the endpoint[^tls] with that account key, the domain claims to own that particular account key. This is not embedded into the DAG so it is possible that not all servers will agree on this[^cas].
 - Taken together, the two claims prove that the domain owns the key.

>[!NOTE]
> Earlier versions of this proposal just omitted unknown account keys rather than returned an explicit `errcode` for them. This was changed
> in order to A) provide a mechanism to provide context on the unknown account and B) protect against stale caches / reverse proxies accidentally
> causing account keys to be unknown by omission.

The server receiving this response SHOULD persist the mapping in persistent storage. The `account_name` MUST NOT change upon subsequent
requests for the same account key.[^1] When a user is created on a server, the account key SHOULD[^2] be created and SHOULD be kept immutable
for the lifetime of that user. There is a chicken/egg problem for some federation operations e.g invites,
as clients will invite the `account_name` to a room, and will not know the account key yet. Specifically, any federation operation which acts
on another server's user needs to talk to that server to discover the account key mapping. To aid this, the following adjustments are made:
 - `/_matrix/federation/v2/invite`: The sender sets the `state_key` of the invite `event` to the account name user ID (as we do today),
   which the receiver then replaces with an account key user ID when signing the invite event. The sender then signs this JSON, creating the double-signed event.
 - A new endpoint `/_matrix/federation/v1/ban` is created, which is identical to `/invite` but for pre-emptive bans when the account key is not known. Omits the `invite_room_state` field.

>[!NOTE]
> A few designs were considered here, including having a generic bulk lookup function to map **from account name** to account key.
> A generic bulk lookup function would be prone to abuse as malicious servers could enumerate the relatively small namespace of account
> names to discover all the accounts on any server.
>
> Considering the chicken/egg problem only exists for invites and pre-emptive bans, it feels acceptable to keep the scope small and
> only add a generic lookup function as and when the use cases present themselves. This allows servers to rate-limit these requests to
> prevent enumeration of accounts e.g. unsolicited federated ban operations should be infrequent and so can have aggressive rate limits,
> whereas it's not clear what a sensible limit is for a generic single account lookup operation.
>
> An alternative design would be to exclude the `/ban` endpoint entirely, making it impossible to do pre-emptive bans in room version `vNext`.
> In practice this works well with moderation tooling (e.g Mjolnir, Draupnir) which instead reactively ban the user if they join a moderated room, rather
> than flooding the DAG with thousands of potentially unnecessary ban events. This would mean the chicken/egg problem would exist solely for invites,
> which would then mean a simple modification to the `/invite` API is enough.

#### Handling GDPR erasure

The account keys for erased users MUST return an `errcode` of `M_ERASED` to indicate that the key was valid but is now deleted.
In addition, the JSON object MUST include the domain and signatures keys to confirm the erasure e.g:
```json
{
    "account_keys": {
        "cWm64pdXOGz1DbIXTuH+24szY/+9HjPP7jZwbDjn12s": {
            "errcode": "M_ERASED",
            "domain": "matrix.org",
            "signatures": { ... }
        }
}
```

>[!NOTE]
> The object is signed to prevent DNS takeover attacks erasing users, where DNS is compromised to point to an unauthorised server who then responds
> with erased users. By including the signature, it forces the attacker to also have access to the private key for the account key.
>
> The `domain` is included to ensure that the signature for `{ "errcode": "M_ERASED" }` isn't enough to confirm the erasure, else the signature could
> be reused for different unauthorised domains.
>
> Further work could improve the temporality of these signatures e.g including a timestamp for when this attestation was made, but this is out-of-scope
> for this proposal.


#### Server behaviour

When a server joins a room, it will receive a list of account keys that are joined to the room. No external requests need to be made in order to verify
the event signatures of the DAG or to apply auth rules, thus ensuring that all servers will converge on the same room state.

The server SHOULD group each key according to its claimed domain and perform a single `/accounts` query to fetch the account name for each
account key. Requests SHOULD be batched to ensure that the HTTP request/response size doesn't become too large for reverse proxies to handle: this proposal
recommends that keys for the same domain SHOULD be batched into groups of 2048 keys[^reqsize]. This SHOULD be done prior to sending the room information to clients.
Based on the result of the query, the server should then group account keys into two categories:
 - Verified: the domain is aware of the account key because it was contained in the response. The JSON in the response has been correctly signed by the account key.
 - Unverified: the domain is unaware of the account key because it was not contained in the response or the domain is unreachable[^unreach], returned a non 2xx status,
   or the server cannot decode the response body.

This proposal tries to avoid clients needing to know or care about these account keys. As such, it takes steps to replace the account key
with the account name in the user ID where possible in event JSON sent to clients/bots/bridges/appservices. For a given account key `@l8Hft5qXKn1vfHrg3p4-W8gELQVo8N13JkluMfmn2sQ:matrix.org`:
 - The server should replace the account key with the account name in the user ID for verified keys. E.g `@kegan:matrix.org`.
 - The server should _filter out_ both state and message events from unverified users from being sent down the Client-Server API.

The act of filtering out unverified user IDs means clients will potentially see different events in the same room. However, _servers_ will always see
the same events, and be able to perform state resolution / apply event auth rules consistently. Clients that do not want to have these events filtered out
can specify this by **TODO: we need something that works across ALL CSAPI endpoints so no sync filter, on a per device basis.**

>[!NOTE]
> We could _alternatively_ replace the `domain` of the user ID with "invalid" for unverified keys e.g. `@l8Hft5qXKn1vfHrg3p4-W8gELQVo8N13JkluMfmn2sQ:invalid`.
> We replace the domain with 'invalid' for unverified keys because otherwise it implies that user ID is an
> account on that server. The domain part of the user ID is
> not verified with this proposal. If we did not replace the domain with 'invalid', abusive or illegal activity
> may be incorrectly tied back to a particular victim server. The word "invalid" is specifically
> [reserved](https://www.rfc-editor.org/rfc/rfc2606.html#section-2) so it cannot become a valid TLD in the future.
> Conversely, by doing this we enable domainless accounts
> because malicious servers may purposefully omit their own users from the response, thus causing all their users
> to appear with an "invalid" domain. [Moderation tooling](https://github.com/matrix-org/matrix-spec-proposals/pull/4284)
> may decide to automatically soft-fail events sent from unverified domains to protect against abuse. On the flip side,
> this is exactly what we want for peer-to-peer applications, where the identity and routing information is solely the
> public key (e.g used in a distributed hash table). If we chose to inform clients about unverified users, it would make
> the MSC depend on [MSC4284: Policy Servers](https://github.com/matrix-org/matrix-spec-proposals/pull/4284) to ensure that
> events sent by invalid domains can be moderated safely.
>
> However, we would need to handle the case where the user ID eventually becomes verified. This is error-prone and complex because
> servers would need to issue synthetic leave events for the old user ID and synthetic join events for the new user ID and keep track of
> those interactions across lazy-loading, sync filters, etc.
>
> Embedding the account name into the event JSON would not resolve the problem
> as malicious servers could lie about their domain, creating impersonation attacks. For example,
> Eve on `evil.com` could generate an account key with the name 'alice' then claim the domain part as `example.com`.
> A third server might then fail to query `example.com` (e.g because it is temporarily unavailable), and could incorrectly
> assume that the account key _is_ for `alice` on `example.com`, which it isn't. To avoid this, we rely on `/accounts` to
> know the account name, and must handle the cases where we cannot perform that operation. As an aside,
> if we forced all messages to be cryptographically signed (not necessarily encrypted) _by the client_, we would avoid this
> impersonation attack, but that is orthogonal to this proposal.

Once a mapping has been verified, it can be permanently cached. Servers MAY retry unverified mappings in the future,
prioritising servers which have never responded over servers which have responded with the absence of the key.
Servers should time out requests after a reasonable amount of time in order to ensure they do not delay new rooms appearing on clients.
If an unverified user later becomes verified:
 - the _current state events_ for that user (e.g their `m.room.member` event and any current state they are the `sender` of) SHOULD be
   sent down client's sync streams. For [Simplified Sliding Sync](https://github.com/matrix-org/matrix-spec-proposals/pull/4186),
   this is via `required_state` if those state tuples are being tracked. For [the current sync API](https://spec.matrix.org/v1.14/client-server-api/#get_matrixclientv3sync),
   this is the `state` block if and only if [`use_state_after`](https://github.com/matrix-org/matrix-spec-proposals/pull/4222) is enabled.
   If that option is disabled, then the events for that user SHOULD NOT be sent.[^stateafter]
 - historical messages for that user SHOULD NOT be sent down client's sync streams. This avoids creating confusion that the user actively
   sent those messages. The messages MAY be returned via [`/messages`](https://spec.matrix.org/v1.14/client-server-api/#get_matrixclientv3roomsroomidmessages),
   [`/context`](https://spec.matrix.org/v1.14/client-server-api/#get_matrixclientv3roomsroomidcontexteventid) and
   [`/event`](https://spec.matrix.org/v1.14/client-server-api/#get_matrixclientv3roomsroomideventeventid).

#### Gradual compatibility

To enable clients to gradually become aware of account keys, servers MUST set the `unsigned.sender_account.key` property of the event JSON to be the account key
and the `unsigned.sender_account.user_id` property of the event JSON to be the account name + verified domain returned from `/accounts` e.g:

```js
{
    // .. event fields
    "unsigned": {
        "sender_account": {
            "key": "l8Hft5qXKn1vfHrg3p4-W8gELQVo8N13JkluMfmn2sQ",
            "user_id": "@kegan:matrix.org",
        }
    }
}
```
If the user is unverified then the `user_id` field MUST be omitted.

Clients can then use the `unsigned.sender_account.key` field as an unchanging identifier[^idunchange] for the sender of the event, akin to how they use the `sender` field today.
Clients can render the `unsigned.sender_account.user_id` field (if it exists) as a human-readable displayable identifier for the user. When the user is deleted, the key can be
rendered instead. This is slightly more wasteful on bandwidth, but provides much more convenience for clients as the data they need is in the same struct.

A later room version or version of the CSAPI can then:
 - Transform the `sender` of the event to be of the form `@l8Hft5qXKn1vfHrg3p4-W8gELQVo8N13JkluMfmn2sQ:invalid`. By using the `invalid` top-level domain we ensure this cannot be a
   valid account name user ID. By universally replacing the domain with `invalid` we ensure that we do not send unverified domains to clients, who may otherwise think that e.g.
   `@l8Hft5qXKn1vfHrg3p4-W8gELQVo8N13JkluMfmn2sQ:matrix.org` resides on matrix.org.
 - Tell clients to form the user ID by using `unsigned.sender_account.user_id` if it exists, falling back to `unsigned.sender_account.key`. Abusive user IDs can be redacted which will
   remove the `user_id` property from the event.

#### Impacts on end-to-end encryption

Device lists are fetched based on the user ID over federation via [`GET /_matrix/federation/v1/user/devices/{userId}`](https://spec.matrix.org/v1.15/server-server-api/#get_matrixfederationv1userdevicesuserid).
This MUST continue to use
the human-readable account name form of the user ID. This means if a server is unable to map an account key to an account name, it will be unable
to fetch device lists for that user and E2EE will break. This is reasonable because servers are in general only unable to perform the mapping if
the remote server is unavailable, in which case E2EE will break anyway.

>[!NOTE]
> This is done in order to not break cross-signing keys, which sign the `user_id`. This will be signed with the Account Name User ID.

#### Impacts on restricted rooms

Rooms with the `restricted` join rule are impacted because we no longer want to check that the server domain signed the event.
Thankfully, the `join_authorised_via_users_server` field is a _user ID_, so we can simply extract the account key from the localpart of the
user ID and verify that there is a signature with that key. For clarity, auth rules are modified like so:

> If type is `m.room.member`:
> - [...]
> - If `content` has a `join_authorised_via_users_server` key: 
>    * If the event is not validly signed by the ~~homeserver of the user ID denoted by the key~~ account key denoted by the user ID, reject.

#### Impacts on key validity

It is critical that all servers agree on which events have valid signatures and which do not. As a result, key validity as a concept is untenable
if we wish for all servers to converge because the key validity time can be modified inconsistently for different servers. As a result, this
MSC _removes_ the [Signing key validity period](https://spec.matrix.org/v1.15/rooms/v5/#signing-key-validity-period) introduced in room version 5.

The impact of this is that a compromised private key cannot be cycled by setting an expiry time for it. Instead, the server should:
 - Generate a new account key for this user.
 - For each room that user is joined to, invite the new account key to the room.
 - Join the room with the new account key.
 - Transfer any power level rights (NB: creatorship cannot be transferred, so this will be imperfect).
 - Leave the room with the compromised key.

This is best-effort and there are numerous limitations to this approach: predominantly the compromised key may be able to backdate themselves back into the room due to the self-revocation.

TODO: if we are serious about this, we should probably introduce some kind of recovery key semantics instead of a validity period, but this feels like massive scope creep.

### Potential Issues

Servers may lie about their domain e.g `foo.com` may join the room as `@l8Hft5qXKn1vfHrg3p4-W8gELQVo8N13JkluMfmn2sQ:bar.com`.
This means `foo.com` will not get events in the room routed to them, but a victim server `bar.com` will instead be pushed events as a form of amplification attack.
Servers MUST have a global backoff timer per-domain to ensure that attackers cannot repeatedly join users with fake domains to popular rooms to cause amplification attacks.

### Security Considerations

- Servers can equivocate and tell some servers that account key A has the account name "alice" and tell other servers
  that account key A has the account name "bob". This doesn't affect the security of the protocol _from a server perspective_
  as the account name is simply a user alias at this point for clients. However, _from a client perspective_ this makes it
  harder e.g to establish pre-emptive ban lists as you cannot be guaranteed that banning the account name "alice" will actually
  prevent alice from joining the room. This requires dishonest servers to achieve however, so can be addressed with server ACLs
  (banning the dishonest server from participating in the room).
- Servers can masequarade as users on their server, but they could _already_ do this due to the lack of any end-to-end
  cryptographic signing of events.
- If another domain gets hold of the private key to an identity, they can manufacture valid events with that key
  e.g `@l8Hft5qXKn1vfHrg3p4-W8gELQVo8N13JkluMfmn2sQ:matrix.org` => `@l8Hft5qXKn1vfHrg3p4-W8gELQVo8N13JkluMfmn2sQ:evil.com`.
  As the domain is not checked when verifying events, this will pass event signature checks. However, this is a new identity at
  a protocol level since the domains are different and as such the user must be allowed to join the room before their events will
  pass event authorisation checks. Alternatively, a stolen identity could manufacture valid events with that key _and domain_.
  At this point, the event will be indistinguishable from a non-stolen identity. However, the attacker will not be sent events in
  the room due to their domain not being present in the domain part of the user ID. The attacker would need to additionally
  compromise DNS in order for events to be sent to them, or have an existing stooge server joined to the room.
- Servers could ignore the requirement to keep the account key constant for each user. This would allow ban evasion,
  but this is also possible today with server collusion.


### Alternatives

We could move to per-room per-user keys like MSC4014 does. Unfortunately, that makes several things harder. Performance is worse
because every key needs to be queried with the remote server, scaling O(nm) where n=number of users, m=number of rooms rather than
O(n) like this proposal does. Extra protocol complexity is required in order to pre-emptively resolve the mappings without requiring additional
network requests _for authorised servers_ (e.g [key blinding](https://cfrg.github.io/draft-irtf-cfrg-signature-key-blinding/draft-irtf-cfrg-signature-key-blinding.html)).
This has knock-on effects because the inability to retrieve the underlying user identity can break E2EE and cause the end-user
to see ugly user IDs which can't be mapped to any human-readable identifier. Assuming these problems could be addressed, this proposal
would require no extra changes to support per-room per-user keys as it would just result in more `/accounts` requests to servers. 
It is technically possible with this proposal alone for some servers to use per-room per-user keys and some servers to use per-user keys.
Care must be taken to ensure that any "aggregate" operations which intend to operate on a user across all rooms use the account name and
not the account key (e.g like fetching device lists for a user).

We could have the server co-sign events sent by their accounts, such that they are now signed by the account key and the server key.
The reason for this would be to provide information of the origin of the event. However, failed server key signatures
can't result in events getting dropped or rejected if they are not signed correctly by the server because of the aforementioned split brain
scenarios. As a result, there seems to be little benefit to having the server cosign since you can't take any action without diverging
from other servers who may or may not be able to get the server key.

Another alternative would be to have some dedicated server which everyone in the room agrees on to co-sign events e.g the creator server,
a policy server or a per-room notary server. The problem with this approach is that:
 - server keys are not per-room, so you can't really enforce any domain wide rules using it.
 - all rooms would be required to communicate with this dedicated server in order to get their events signed, centralising writes in the protocol
  and breaking partition tolerance.
 - the dedicated server would need to remain forever accessible. If the dedicated server dies, the
   room becomes read-only.

Alternative MSCs which implement the same level of indirection and have much the same benefits as this MSC whilst making different trade-offs include:
 - [MSC1228: Removing MXIDs from events](https://github.com/matrix-org/matrix-spec-proposals/pull/1228)
 - [MSC2787: Portable Identities](https://github.com/matrix-org/matrix-spec-proposals/pull/2787)
 - [MSC4014: Pseudonymous Identities](https://github.com/matrix-org/matrix-spec-proposals/pull/4014)
 - [MSC4348: Portable and serverless accounts in rooms](https://github.com/matrix-org/matrix-spec-proposals/pull/4348) and [MSC4345: Server key identity and room membership](https://github.com/matrix-org/matrix-spec-proposals/pull/4345)

### Future work

We want to eventually support portable accounts, where a user can migrate seamlessly to a different server. This would require the
_client_ to store the account key, not the server. The underlying identity string would need to drop the domain to support this e.g
the `sender` of the event would have to just be the key, without the domain. It has to do this otherwise when you migrate to a different
server, the domain of the `sender` will be wrong and critically will never be able to be updated without creating a new identity from a
room protocol perspective, and thus will have the wrong permissions. Alternatively, we could keep the domain and adjust the auth rules to
only use the public key to determine identity, meaning `@l8Hft5qXKn1vfHrg3p4-W8gELQVo8N13JkluMfmn2sQ:foo.com` and
`@l8Hft5qXKn1vfHrg3p4-W8gELQVo8N13JkluMfmn2sQ:bar.com` would be treated as the same user from a room permissions perspective. Both options
are invasive: one changes the user ID format and the other subverts the existing room permission model that clients have been coded to expect
(which can be particularly painful to change, see [MSC4289](https://github.com/matrix-org/matrix-spec-proposals/pull/4289) as an example).





### Unstable prefix

- The room version is `org.matrix.12.4243` based on room version 12.
- The `/invite` and `unsigned` properties do not need prefixes as they are already room-scoped, and the room is prefixed.
- The endpoint `/_matrix/federation/v2/ban` is `/_matrix/federation/unstable/org.matrix.msc4243/ban`.
- The endpoint `/_matrix/federation/v1/query/accounts` is `/_matrix/federation/unstable/org.matrix.msc4243/query/accounts`

### Dependencies

None.

[^1]: Because the JSON with the `account_name` and `domain` is signed, we could use transparency logs to detect when a server
tells some people one account name and other people a different account name. In addition, it opens up the possibility of having
trusted notary servers provide the JSON in the event that the server is unavailable. Notary servers would be trusted to perform
the federation requests honestly, and only return the JSON for account keys which have a correct `domain`.
[^2]: Servers are allowed to lazily create account keys on usage.
[^perroom]: By using 'SHOULD' we informally bless servers that wish to add additional privacy protections for their users via
per-room per-user keys, in which case there will be multiple account keys for the same underlying account.
[^signing]: This means servers do not need to make any network requests to verify the signature on inbound events.
Currently servers need to ask for the server keys of the domain directly or via a notary server. If they cannot get the server keys,
the event is dropped, causing a split-brain. This is why this proposal improves the security of the federation protocol.
NB: The private key still lives on the server, not clients.
[^urlsafe]: We want the public account key to be url-safe because it frequently appears in URL paths in the client-server API e.g account data,
profile data, user reporting and the Federation API e.g `/make_knock|join|leave/{roomID}/{userID}` and `/users/devices/{userID}`. This aligns
with other base64 data like event IDs and room IDs which are also urlsafe but notably is in conflict with _signatures_ which are not urlsafe.
[^keyid]: This format accurately encodes the fact that the public key is not at all related to the claimed domain name. It may allow flexibility
later on should we want to introduce portable accounts, as the signatures on these events will remain valid.
[^unreach]: Earlier versions of this proposal treated unreachable servers as a third category: "unknown" instead of "unverified". The intention
was that _unverified_ keys were explicit negative ACKs stating that the server is unaware of the given key, and therefore indicated malice on
the part of the sender of the event. This contrasted with "unknown" keys which were simply network problems. Clients were told of the difference
due to munging the user ID in a slightly different way. However, there is no guarantee that a server responding negatively to the existence of a
key is actually malicious (recreating your database would do this for example). Therefore, the distinction isn't important, meaning they can be
combined into one category.
[^idunchange]: TODO: This isn't actually unchanging, as a key K known to two servers S1 and S2 can map the 'same' event to the same underlying key.
For now, this is just a peculiarity and isn't a problem. But, we can't really consider the full account key user ID to be the principal; only the account key
itself is the principal. This _matters_ for portable accounts, so perhaps we should be defining the account key as the unchanging identifier to anticipate
this?
[^tls]: Specifically, the bidirectional link is created only when the requesting server verifies the TLS certificate of the responding server and confirms
it is valid. The TLS certificate confirms ownership over the domain, and is subsequently used to send back the HTTP response claiming the account key.
[^cas]: Further disagreements could happen if two servers don't have the same set of trusted certificate authorities or if the certificate has been revoked.
[^reqsize]: The length of a public key with `"` and `,` is 45 bytes. For 2048 keys, this results in ~90KB requests and ~1MB responses (assuming maximum user ID length).
[^stateafter]: We allow servers to opt-out simply because the current sync API, in absence of `use_state_after`, is not actually tracking the current state, thus
it isn't safe to just inject the events randomly.
