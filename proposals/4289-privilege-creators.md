## MSC4289: Explicitly privilege room creators

**NOTE**: This MSC is part of the security update to Matrix announced at https://matrix.org/blog/2025/07/security-predisclosure/.
This is a lightly edited version of the final MSC, released ahead of the disclosure in order to aid
client implementors with implementation, and will be updated with full security context upon disclosure.

### Problem

Matrix has a longstanding problem that creators can lose control of rooms, either by promoting other
admins who they can then no longer demote or by demoting themselves (https://github.com/matrix-org/matrix-spec/issues/165).
Despite warnings from clients about these limitations, it is still surprising to users.

This MSC gives the room creator(s) an ability to demote those admins (or promote themselves).

This MSC also addresses other forthcoming security considerations.

### Proposal

In short:
 - Formally define the ‘room creator’ as the user who sent the `m.room.create` event for a given room.
   By definition, this is immutable per room.
 - Update auth rules so that the ‘room creator’ and `additional_creators` (see below) are always
   considered to have infinite power level.
   This means when sorting this user by PL, they always sort last ascending and first descending. Users
   with [MAX_INT](https://spec.matrix.org/v1.14/appendices/#canonical-json) power level are still less than creators.
 - Clients may guide creators who try to demote themselves to get someone else to upgrade the room instead.
 - Clients no longer need to warn creators that if they promote someone to admin they won’t be able to undo it. They
   may need to highlight that any additional creators cannot be removed.
 - Given the changes to auth rules need to be executed consistently across all servers, this requires a new room version.

It is important to note that this does NOT centralise the room on the creator’s server. The room
remains fully functional if the creator’s server is unreachable, as nothing in the protocol requires
communicating exclusively with the creator’s server. Indeed, the room remains fully functional in
the face of arbitrary network partitions. Conversation history is still replicated equally over all
participating servers, and the access control hierarchy can be shared equally across multiple servers,
and is enforced independently by all participating servers.  However, access control, by definition,
specifies how some users are privileged over other users in a given context - and in such a hierarchy,
some entity always ends up on top.

This fixes [Should room creators always be able to give themselves power?](https://github.com/matrix-org/matrix-spec/issues/165)
once and for all (previous attempts being [MSC3915](https://github.com/matrix-org/matrix-spec-proposals/pull/3915)
“owner power level” and [MSC3510](https://github.com/matrix-org/matrix-spec-proposals/pull/3510) “let the same PL kick/ban/deop each other”).

>[!NOTE]
> Clients which show a user's power level SHOULD indicate ‘creatorship’ in a similar way to help
> manage expectations on access control to users (i.e. to remind users who created the room, and so
> who can override access controls).

#### Create event changes

To support fully multilateral decentralisation, the create event `content` MAY include a new field `additional_creators`
which is a list of user IDs. All the user IDs specified have the same permissions as the original creator.
The [auth rules](https://spec.matrix.org/v1.14/rooms/v11/#authorization-rules) are updated to include additional validation on the create event:

> - If type is m.room.create:
>   * 3: [...]
>   * 4: ~~Otherwise, allow.~~
>   * 4: **NEW: If the `additional_creators` field is present and is not an array of strings where each string
>     passes the same [user ID validation](https://spec.matrix.org/v1.14/appendices/#user-identifiers) that
>     is applied to the `sender`, reject.**
>   * 5: Otherwise, allow.

User IDs in `additional_creators` are NOT bound to the creator server: any valid user ID may be provided.

Earlier versions of this proposal explicitly stated that `additional_creators` must be a [valid user ID](https://spec.matrix.org/v1.14/appendices/#user-identifiers)
but due to ambiguity between allowed/historical/invalid user IDs that exist on the public network, this proposal
merely states that the same validation applied on the `sender` key should be applied on the `additional_creators` field.
If this proposal is too strict, it would prevent historical user IDs from joining rooms with this MSC.
The intention of this wording is to allow the validation to be changed as and when the validation of the `sender` key changes.
See [MSC2828](https://github.com/matrix-org/matrix-spec-proposals/pull/2828) and [this clarification](https://github.com/matrix-org/matrix-spec/pull/1506)
for more information.

This new field is especially useful when creating DMs, as both parties retain equal control of the room.

#### `/createRoom` changes

In order to ensure Direct Message rooms have both the creator and recipient as joint creators,
[`/createRoom`](https://spec.matrix.org/v1.15/client-server-api/#post_matrixclientv3createroom)
requests with BOTH `preset: trusted_private_chat` and users in the `invite` field have additional meaning
server-side. The server SHOULD copy any users in the `invite` field into the `creation_content.additional_creators` field
in the **request body** and de-duplicate them. The net result is that the union of `invite` and `creation_content.additional_creators`
in the request body form the `additional_creators` in the `m.room.create` event.

#### Power levels event changes

This change affects the `m.room.power_levels` event which will no longer have the creator user ID with
`100` by default. Instead, the `users` map will be empty, and clients/servers must infer that the creator
has infinite power level based on the `m.room.create` event's `sender` (and `content.additional_creators` if present).

The auth rules for `m.room.power_levels` events are adjusted to say:

> 9. If type is `m.room.power_levels`:
>   - 1). If any of the properties `users_default`, `events_default`, `state_default`, `ban`, `redact`, `kick`, or `invite` in content are present and not an integer, reject.
>   - 2). If either of the properties `events` or `notifications` in `content` are present and not an object with values that are integers, reject.
>   - 3). If the `users` property in `content` is not an object with keys that are valid user IDs with values that are integers, reject.
>   - 4). **NEW: If the `users` property in `content` contains the `sender` of the `m.room.create` event or any of the user IDs in the create event's `additional_creators` array within `content`, reject.**
>   - 5). ...rest of rules...


This ensures that there can be no confusion among clients or servers if the creator were to have a PL entry
in the `users` map.

>[!NOTE]
> We could add a compatibility shim which would inject the creators into the PL event for clients.
> Naively, this would set the creators to be `max(users)+1`. This naive solution is wrong though, as
> some PL events may have "the level required to send event X" to be higher than any other user, so the shim
> would also need to be `max(PL_to_send_anything)+1` in addition  to `max(users)+1`.
>
> However, this would introduce new problems for client implementations:
>  * This shim would break any client which asserts [MAX_INT](https://spec.matrix.org/v1.14/appendices/#canonical-json)
>    in power levels, as the creator PL would have to be 1 greater than the actual max a real user could have.
>  * Creators would appear to break PL transition rules, as they would be seen to give themselves more power
>    (e.g if the max PL of non-creators was 100, then they increased a non-creator to 150, the same event would also
>    transition all creators to PL151). This would also be confusing to render, as there would appear to be
>    two changes (creator->PL151 and target user->PL150), when it practice only one change was made.
>  * This logic makes it harder to transition to pure P2P systems in the future, where
>    [clients sign federation events](https://github.com/matrix-org/matrix-spec-proposals/pull/4080), as clients
>    would have to assert that the PL transitions are valid before committing a signature to authorise it.
>  * The lack of any new role descriptor (e.g "Creator") means in practice major clients would simply list
>    the creators as "Admin" (any PL>=100). This could cause confusion among users if a creator were to
>    demote an admin, as this should not be possible.


This change does not add significantly more complexity to the calculation of PLs for users
in a room because both clients and servers have always needed BOTH the `m.room.power_levels` and `m.room.create`
events in order to display PLs correctly (as in previous room versions the absence of a PL event means the creator
has PL100). For this reason and the ones listed above, no compatibility shim is proposed with this proposal.

#### Tombstone changes

The _initial power levels event in the room_ MUST have the level required to send `m.room.tombstone` events
be higher than the level required to send state events. This is to ensure only creators are able to upgrade
the room _by default_, but allowing them to transfer ownership by increasing the PL of any user to PL150 (for example)
to allow them to send the tombstone event. Note: this may still be overridden by `power_level_content_override`.

The rationale for this is as follows: Matrix does not allow users with the same PL to demote each other.
Upgrading a room breaks this because the non-creator doing the upgrade will now gain unlimited PL, potentially
demoting the original creator ("potentially" because they could be set via `additional_creators` during the upgrade process).
As such, more protections need to be in place to guard against unauthorised privilege escalation by admins,
hence the introduced of a new PL150 tier for tombstoning the room. If we kept the ability to tombstone to be PL100,
then by default it would be impossible to allow someone to A) change the server ACLs, B) update history visibility,
without also C) giving them the ability to privilege escalate.

#### Room upgrades

A new `additional_creators` key is added to the [`/upgrade`](https://spec.matrix.org/v1.14/client-server-api/#post_matrixclientv3roomsroomidupgrade) endpoint. This has the same validation rules applied as the
`additional_creators` field in the `m.room.create` event, and serves as a way to transfer ownership of a room (remove a creator).
This key behaves in the same way as if it were specified in the `creation_content` in `/createRoom`:
the _entire set_ of additional creators are specified up-front. For example, consider the following scenario:
 - Alice created a room and put Bob as an additional creator.
 - Charlie has PL150 and wants to upgrade the room so Alice is no longer a creator. He wants to keep Bob as an additional creator.
 - Charlie can `/upgrade` the room and specify Bob as an additional creator.
 - The new room does not have Alice as a creator or additional creator.

This allows the creator status to move between users.

### Potential Issues

Any update to the set of creators in a room requires a room upgrade. This means room upgrades will occur
more often than today. Forming a complete timeline history across several rooms may make a number of things
harder for implementations. For instance, it increases the pressure to implement seamless merging of timelines
across a tombstone rather than the currently widespread "click to jump to the old room" UX.

Clients which don't already implement the [default power level for creators](https://spec.matrix.org/v1.15/client-server-api/#mroompower_levels)
may experience bugs where users who just created a room cannot (visually) change details of that room,
such as adding admins or setting the room's topic. A server-side backwards-compatibility shim to append
the room creators to the power levels event over the Client-Server API as `2**53-1` (JavaScript's `Number.MAX_SAFE_INTEGER`)
was considered, however with the expectation that most communities will upgrade their rooms when they're
ready rather than immediately upon availability of this MSC, clients in particular will have opportunity
to be updated accordingly.

Similarly, clients which attempt to set an explicit PL for the creator(s) will fail. A backwards-compatibility
shim was considered to ignore PLs set for creator(s) but rejected, on the basis of causing avoidable
confusion and technical debt, given clients are already making breaking changes for this room version.

### Alternatives

(Embargoed until Aug 14, 2025)

### Security Considerations

(Embargoed until Aug 14, 2025)

### Credits

Thanks to Timo Kösters for initiating discussion around this MSC.

### Unstable prefix

During development this room version is referred to as `org.matrix.hydra.11` alongside MSC4291 and MSC4297 (embargoed until Aug 14, 2025).

### Dependencies

This MSC depends on ["MSC4291: Room IDs as hashes of the create event"](https://github.com/matrix-org/matrix-spec-proposals/pull/4291).
