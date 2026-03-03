# MSC0000: Stable identifiers for Room Members

Currently Matrix events hardcode the [User ID](https://spec.matrix.org/v1.17/appendices/#user-identifiers) under the `sender` field, and sometimes the `state_key` field for some event types e.g. [`m.room.member`](https://spec.matrix.org/v1.17/client-server-api/#mroommember) events. This is problematic for the following reasons:

- we can't erase it for GDPR purposes  
- we can't erase it for moderation purposes (abusive localparts)  
- the domain can't be changed to support portable accounts as the field cannot be modified.

This is also problematic if we want to verify event signatures as that expects the `sender`’s domain to have signed the event. Not all servers are guaranteed to see the same server signing keys for a given domain. This leads to events getting dropped by some servers and not others, which can cause room state to diverge. Every MSC which attempts to address this ends up converting the `sender` into a public key of some kind. The public key often does not have the same `@localpart:domain` format as User IDs, and is not intended to be human-readable. It also doesn't make the same guarantees: a valid event signature from the public key does not mean the event originated from that domain. This means every MSC which attempts to tackle this problem has the notion of "verified" and "unverified" user IDs. This represents whether the domain claims to have the public key provided in the event.

The purpose of this MSC is primarily to introduce a Client-Server mechanism to communicate these subtleties, with the expectation that one of the MSCs which convert users to public keys will eventually be merged into the specification. A secondary motivation is that it allows erasure to be more fully communicated to *local* clients by setting the user ID to `null`.

## Proposal

An additional map is provided alongside Client-Server API operations *which track room member information*, which provides *current* information on that room member. It looks like this:

```javascript
"member_info": {
    "$stable_id": {
        "user_id": "@alice:example.com" // string | null if erased
    }
}
```

It is always present under a room-scoped JSON object or room-scoped HTTP endpoint. When used as part of a sync response, only incremental deltas are expressed (the entire map is sent only on initial syncs). The following endpoints which track room member information are affected:

```javascript

// /sync
{
  "rooms": {
    "join": {
      "!roomid": {
        "account_data": {...},
        "ephemeral": {...},
        "timeline": {...},
        "state": {...},
        "member_info": {...}, // <-- NEW
        "unread_notifications": {...}
      }
    }
  }
}

// Simplified Sliding Sync
{
  "rooms": {
    "!roomid": {
      "name": "Room Name",
      "required_state": [...],
      "timeline": [...],
      "prev_batch": "s1_2_3_4",
      "member_info": {...}, // <-- NEW
    }
  }
}

// GET /_matrix/client/v3/rooms/{roomId}/members 
{
  "chunk": [...],
  "member_info": {...} // <-- NEW
}

// GET /_matrix/client/v3/rooms/{roomId}/joined_members
{
  "joined": {
    "$stable_id": { // <-- CHANGED, was user_id
      "avatar_url": "mxc://riot.ovh/printErCATzZijQsSDWorRaK",
      "display_name": "Bar",
      "user_id": "@bar:example.com" // <-- NEW
    }
  }
}
```

The `$stable_id` can be obtained from events via a new `stable_id` field in `unsigned`.

Today, the `$stable_id` will always be the user ID of the room member. However, clients MUST treat the `$stable_id` as an opaque identifier which uniquely identifies that *room member*, and so map the stable ID to a user ID, **which may not exist or may change**.

In the future, this map may be expanded to include `displayname` and `avatar_url`, which would support more efficient profile changes (see [MSC4218](https://github.com/matrix-org/matrix-spec-proposals/pull/4218)). NB: This would then match the shape that already exists in `/joined_members`.

When a user is [erased](https://spec.matrix.org/v1.17/client-server-api/#post_matrixclientv3accountdeactivate), servers MUST set the `user_id` to `null` for all rooms that user was joined to. Clients SHOULD display a placeholder indicating that the user ID is unknown e.g. "An unknown user", "Anonymous User".

Clients MUST use the new `unsigned.stable_id` field as the stable ID.  
Clients MUST NOT use the `sender` field of events as the stable ID.  
A later room version may remove the `sender` field entirely on events, which would break any client relying on the `sender` field for the stable ID.

## Potential issues

The stable ID currently includes the user ID of an erased user, which is antithetical to erasure. This is a temporary issue whilst the stable ID continues to be the user ID.

In encrypted rooms, clients verify that the `sender` (user ID) matches that of the encrypted session. This check will fail for erased users because the user ID will map to `null`. This check is done to help higher levels of the stack use the `sender` field without needing to know or care if the event is encrypted.

By expecting stable ID aware clients to read the `unsigned.stable_id` field to extract the stable ID, we lock in that field name for any future MSC which converts user IDs to public keys.

This proposal duplicates data in every single event for everyone by adding `unsigned.stable_id` to all events going forwards. This is slightly mitigated by the field’s locality to the `sender`, meaning the user ID will likely be in the same compression window and therefore be compressed down.

## Alternatives

Rather than add `unsigned.stable_id`, we could remove the `sender` and replace it with a `stable_id` field. We would do this so clients which do not implement stable IDs would crash due to the \`sender\` field not existing, rather than parsing the \`sender\` as a user ID when it is in fact a stable ID. This is backwards incompatible so clients would need to opt-in e.g. via a query parameter `?stable_ids=1`. The problem is that this opt-in then needs to be specified in every Client-Server endpoint which can return events, including stripped events. This includes `/messages`, `/context`, `/state`, `/threads`, `/hierarchy`, `/relations/{eventId}`, `/event/{eventId}`.

We could repurpose the `sender` field as the stable ID. This is backwards compatible. However, this changes the data type depending on the room version (the `sender` is either a User ID *or* a Stable ID (public key). This is particularly concerning for stable ID aware clients, as in order for them to know how to parse the `sender` field they either need to figure out the room version (which is fragile as it needs to be kept updated) or they need to conditionally parse based on `if sender[0] == “@”`. This data type confusion is risky, as it would never be valid for a user ID to appear in room versions which use public keys, but clients may accept them anyway based on conditional parsing. This can result in security issues as it’s a form of [CWE-843](https://cwe.mitre.org/data/definitions/843.html).

An alternative would be to not have a `member_info` at all, and rely solely on the `unsigned.stable_id` field in conjunction with `sender` to provide the mapping information. However, this assumes the mapping can only change in response to events, when this is not true e.g. user deactivation does not send events into every room, and in MSCs which verify domains there is similarly no event sent upon verification. This means mappings could change but other users/servers would be completely unaware until the affected user sent an event, which may never happen in the case of erasure.

To provide that notification mechanism, we could resend (in room state) the most recent `m.room.member` event when the mapping information changes, and put the new mapping in `unsigned`. However, this breaks the contract between client and server because the event will have the same event ID but with different data. This means most clients will de-duplicate the event and ignore it. To fix this, we could massage the `event_id` and create a fake "synthetic" event, similar to how [MSC4218](https://github.com/matrix-org/matrix-spec-proposals/pull/4218) proposes to do it, but this adds significant complexity:

- What happens when a client tries to redact / pin the synthetic event? We would need to persist linking information to work out the original member event.  
- What happens when a client adds a reaction or thread reply to the synthetic event? We would need to modify the client request to be routed to the original event, but this would created inconsistencies as encrypted content would refer to the synthetic event still.  
- What happens when a client shared a permalink to the synthetic event to a different user on a different server? The permalink will not work as not all servers will agree on the same synthetic events.

We could alternatively keep the event ID the same and add a special flag to indicate that the event should be re-processed e.g. `unsigned: { reprocess: true }`.

All of these options attempt to bundle the mapping change in the context of an event, which doesn't always work if the client/bot/application service retrieves information which does not have an event context e.g. `/_matrix/client/v3/rooms/{roomId}/joined_members`. All these options also use more bandwidth compared to sending a separate `member_info` because the same erased user saying N messages in the timeline will have N-1 redundant mapping entries in `unsigned`.

We could mutate the `sender` to try to match the current user ID by mapping erased users to a special sentinel value like `@_:matrix.invalid`. However, `m.room.member` events are very sensitive to the values of `sender` and `state_key`. For example, if `membership` is `leave` and the `sender` and `state_key` match, then the user left the room. If they don’t match, then the user was kicked. By modifying the `sender` we need to also modify the `state_key` or else these membership transitions will be displayed incorrectly e.g. a leave event would turn into `@_:matrix.invalid` *kicked `@alice:example.com`.* However, by modifying the target of membership operations it means invite/kicking/banning erased users will be re-mapped to *`@_`*`:matrix.invalid`. Furthermore, power level events include user IDs in `content.users`. These values will also need to be modified in order to scrub erased user IDs from all events in the Client-Server API. This could cause confusing behaviour though because these user IDs are not the `sender` of an event. For example, explicitly promoting an erased user ID to PL100 would constantly be re-mapped to `@_:matrix.invalid`. 

## Security considerations

In encrypted rooms, clients MUST NOT trust the `member_info` or `unsigned.stable_id` for the purposes of determining who sent an event. This is not a new constraint: clients must not trust the `sender` field in encrypted rooms today because it is unencrypted and hence can be modified by the server.

## Unstable prefix

- `member_info` is `org.matrix.mscXXXX.member_info`.  
- `stable_id` in `unsigned` is `org.matrix.mscXXXX.stable_id`.

## Dependencies

None.  
