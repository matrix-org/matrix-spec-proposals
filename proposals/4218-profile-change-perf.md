# MSC4218: Improving performance of profile changes

Many users in the Matrix ecosystem have seen how slow it is to change either their display name or their avatar. It is slow because it causes O(n) updates, one for each room the user is joined to. This MSC details a mechanism to improve performance by not sending O(n) updates. It does this by introducing a new concept called "Synthetic Events". This new concept can also be conveniently applied to [communicate state resolution deltas accurately to clients](https://github.com/matrix-org/matrix-spec/issues/1209). Also conveniently, decoupling profile changes from the membership of the user decreases the length of the auth chain for that user, which decreases the amount of data that is required to be fetched in order to join a room, thus improving performance on room joins as well.

## Proposal

This MSC borrows and expands upon the ideas in MSC3883, specifically:

> Displayname/Avatar updates should be EDUs that trigger a /profile query. 

For unfederated rooms, no EDUs need to be sent. So how do users see profile changes in rooms? The server creates a "synthetic event" which is effectively a fake member event based on the real member event, decorated with the latest profile data at the time the EDU is received / the profile was updated. As an example, if a user has no profile then sets one, the new profile fields will appear in the synthetic event e.g `content: { membership: join }` becomes `content: { membership, join, displayname: Alice }`. The synthesised event MUST have a unique event ID as clients often deduplicate data based on the event ID. This proposal proposes a format of `{original_member_event_id}_{iteration}` e.g `$A5z9GLL8ABCYg4SKujf_ehtW52yGoGhZuQGc0nspEeU_2`.

As a result, clients will see no differences except:
 - profile change `m.room.member` events are synthetic so they don't exist in the room DAG, so the event ID isn't real. This can break clients which ask for events in federation format as this event won't have `prev_events`, etc. The response to `GET /state/m.room.member/@user:id` would also return the _synthetic event content_, not the federation form (as would `/members`), on the basis that we care about profiles more than accurate DAG reproducibility. This could be configured in another MSC.
 - `/myroomnick` (per-room nicks) isn't possible anymore without modifications.

### Per-room nicks

To support per-room nicks, there exists a new endpoint: `POST /rooms/{roomID}/user_profile` which sends a new state event type `m.room.user_profile` into the room, with the `state_key` matching the logged in user's ID. This new event has the relevant `displayname` and `avatar_url` fields.

We don't want to send `m.room.member` events because then they would form part of the auth chain. We don't want to put per-room nicks in global profile data (in a room ID to profile info map) because it would leak the rooms the user is joined to. We want a new endpoint and not `PUT /state/m.room.user_profile/{userID}` because that event is never sent to the client, so the lack of symmetry would be confusing. See below.

On receipt of `m.room.user_profile`, the contents of this event _overrides_ the global profile info for that user in that room only, _even if the global profile is updated after this point_. Servers should treat this event _as if_ it were the global profile response for this room, meaning the way the data is delivered to clients should remain the same. This implies the new event type is NOT sent to clients, which is intentional as we do not wish to introduce needless breaking API changes to all clients, AND we want to preserve the existing property of seeing a new `m.room.member` join the room and immediately knowing that member's name/avatar: this atomicity requirement was why they were coupled in the first place. Because of these reasons, we do not go "all in" on the new event type and synthesise fake versions of this event to communicate profile updates, even though this may initially seem like a more consistent alternative.

### Redactions

`m.room.member` events can be redacted to remove abusive display names and avatars. This proposal changes how profile information is stored so it has implications on the redaction logic. It is more complex now because there is an impedance mismatch between clients and federation: clients will redact _synthetic events_ which have no representation over federation, so how is this redaction communicated to other servers?
 - As today, moderators will redact the `m.room.member` event, however the semantics server-side changes.
 - Redacting a member event automatically redacts any corresponding `m.room.user_profile` event if they exist **now OR in the future**.
 - Redacted member events are communicated to other servers as they are today.
 - Receiving a redacted member event will cause servers to create a new synthetic event with just `content: {membership: join}`, with no profile fields. This synthetic event will then be sent to clients.
 - After this point, global profile updates have no effect for this user in this room: the state is terminal. This means that if your member event is redacted and then you send an `m.room.user_profile` event, it is ignored and immediately redacted by the receiving server. This immediate redaction is required in order to prevent servers from storing abusive profile fields, even if they aren't communicated to the clients.
 - Due to synthetic events, redacting a member event will cause both the redaction event _and the new synthetic event_ to come down /sync. The synthetic event should be decorated to indicate they the fields were removed via redaction e.g via `unsigned.redacted_because`. This allows clients to differentiate between redactions and genuinely unsetting the display name / avatar.

 Effectively, this mechanism means we are using the redaction of the `m.room.member `event as a signal to redact all profile info for that user in that room. This has tradeoffs, notably that if a profile is redacted, it cannot be set again unless that user changes their membership e.g by leaving and rejoining the room. Typically, spammers will have their display names redacted then they will be kicked from the room, so this wouldn't change the behaviour for this use case at all.

 The entire flow chart looks like:

 <img width="994" alt="Screenshot 2024-10-20 at 15 17 46" src="https://github.com/user-attachments/assets/ac227603-b635-4ecc-bd60-d3446074facf">


 ### Synthetic Events

 These are events created by a server which aren't sent to any other server, but _are sent to clients_. Clients treat them as real events but they aren't real over federation and do not form part of the room DAG. The purpose of this is to help state synchronisation between clients and server. They can be detected because all synthetic events MUST have `synthetic: true` at the top-level of the event JSON. Other uses for synthetic events include communicating state deltas to clients when state resolution needs to back out some state it had previously told clients, see https://github.com/matrix-org/matrix-spec/issues/1209 

## Potential issues

If the receiving server cannot get the profile info for a user due to network issues, it must retry periodically. This can introduce a delay between when the user actually changed their name and it taking effect.

## Alternatives

- Do nothing, and deal with slow performance and longer auth chains.
- Don't send synthetic events on profile updates. We could pass the EDU directly to clients and expect them to re-query, but this would then break the ability to have historical display names, and it would cause much more traffic to get the profile as every client would ask for the profile rather than every server. In addition, client uptime isn't as good as servers, and the lag time between the EDU being sent and the profile being retrieved would be much higher than this proposal.
- Remove support for per-room nicks. This would remove the need for `m.room.user_profile` events and arguably simplify this MSC.


## Security considerations

Profile changes are no longer part of the room DAG. This means malicious servers can split-brain the room for a user's profile: users on different servers may see different profile info for the same user. This can be done by accident due to network partitions or maliciously, by only sending innocuous display names to servers with admins but abusive names to servers without admins. Users in a room typically ping admins to remove bad users, so this could cause confusion if the admin doesn't see the abusive name/avatar. Given this relies on global profile data which is public, we could do transparency logs to ensure a server responds with the same data to all servers, but this is likely overkill so it doesn't form part of this MSC. It is worth noting per-room nicks ARE part of the room DAG and as such are not vulnerable to this.

Denial of Service: when users receive a real `m.room.member` event, the receiving server should request profile info to decorate the event BEFORE delivering the event to the client, in order to preserve atomicity. Malicious servers can tarpit this request and purposefully take ages before responding with an error, thus introducing a denial of service. This happens because profile lookups are now on the hot path of message delivery. To fix this, servers should set sensibly low timeout values to this request, and cache profile data wherever possible.

## Unstable prefix

- Room version is `org.matrix.msc4218` based off room version 11.
- `m.room.user_profile` events are `org.matrix.msc4218.room.user_profile`.
- `synthetic` flag is `org.matrix.msc4218.synthetic`.
- `POST /rooms/{roomID}/user_profile` is `POST /rooms/{roomID}/org.matrix.msc4218.user_profile`

## Dependencies

This MSC has no dependencies.
