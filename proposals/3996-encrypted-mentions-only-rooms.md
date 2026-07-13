# MSC3996: Encrypted mentions-only rooms

It is currently not possible for mobile clients to properly implement a mentions-only
room.

Currently, every new event in an encrypted room might be pushed to mobile clients
due to the [`.m.rule.encrypted` default underride rule](https://spec.matrix.org/v1.6/client-server-api/#default-underride-rules).

However, a room can be configured to be mentions-only by creating a
[room-specific push rule](https://spec.matrix.org/v1.6/client-server-api/#push-rules)
with the `id` property set to the room ID & `actions` set to do nothing.[^1] Since
this is evaluated *before* the `.m.rule.encrypted` rule (almost)
**no events get pushed for a mentions-only room**.

Additionally, a room can be configured to be muted by creating the earliest
[override push rule](https://spec.matrix.org/v1.6/client-server-api/#push-rules)
possible which matches the room ID & has `actions` set to do nothing[^2], e.g.:

```json
{
    "rule_id" : "!abcdef:example.com",
    "conditions" : [
       {
          "key" : "room_id",
          "kind" : "event_match",
          "pattern" : "!abcdef:example.com"
       }
    ],
    "default" : false,
    "enabled" : true,
    "actions" : []
}
```

## Proposal

A new top-level property (`m.has_mentions`) is defined which contains a boolean
value. It is sent in cleartext (i.e. it is not encrypted) and is set to `true` if
the event mentions another user or the room per
[MSC3952](https://github.com/matrix-org/matrix-spec-proposals/pull/3952).[^3]

A new push rule is added after the `.m.rule.is_room_mention` push rule to match
encrypted mentions:

```json
{
    "rule_id": ".m.rule.is_encrypted_mention",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "event_property_is",
            "key": "content.m\\.has_mentions",
            "value": true
        },
        {
            "kind": "event_property_is",
            "key": "type",
            "value": "m.room.encrypted"
        }
    ],
    "actions": ["notify"]
}
```

(Note: `\\.` would become a single logical backslash followed by a dot since the
above is in JSON-representation. See
[MSC3873](https://github.com/matrix-org/matrix-spec-proposals/pull/3873).)

When this push rule matches then it would push the event to all users, similar to
how the [`.m.rule.encrypted` default underride rule](https://spec.matrix.org/v1.6/client-server-api/#default-underride-rules)
push rule works, but with the added context that *some clients will probably care*.
Clients would [decrypt the event and re-run push rules](https://spec.matrix.org/unstable/client-server-api/#receiving-notifications)
as normal. This would result in:

1. No push notification for muted rooms as their push rule has a higher priority,
   as mentioned [above](#encrypted-mentions-only-rooms).
2. A push notification which the client would discard if the room is set to
   mentions-only and the user/room was not mentioned in the event.[^4]
3. No change in behavior if the user has no special rules for the room and is not
   mentioned (i.e. the event would generate a push notification via the
   [`.m.rule.encrypted` default underride rule](https://spec.matrix.org/v1.6/client-server-api/#default-underride-rules).
4. A push notification which the client would "upgrade" to a highlight notification
   if the (decrypted) event mentions the user.

The overall tradeoff is that clients will receive extra pushes some of the time
(which won't matter), but help hide the metadata of who, in particular, is being
mentioned.

If the decrypted ciphertext contains a `m.has_mentions` property it should be ignored.

## Potential issues

If the mentioned user has muted the room then the above logic breaks down since the
event will get pushed to all *other* users unnecessarily. This could be considered
a good thing (see [security consideration](#security-considerations)) to protect
who was mentioned in the message.

## Alternatives

[MSC1796](https://github.com/matrix-org/matrix-spec-proposals/pull/1796) to keep
mentions information in cleartext was rejected.

The previously discusssed alternative[^5] is for clients to download all encrypted
messages, decrypt them locally and evaluate push rules. This is a costly process
in terms of bandwidth, CPU, and battery since the client must either receive every
message via push notifications or backpaginate every room fully via a polling loop,
in case of a gappy sync.

Both of the above solutions are sub-optimal however:

* Some platforms don't allow a polling loop,
  [e.g. iOS](https://github.com/matrix-org/matrix-spec-proposals/pull/3952#discussion_r1065004790),
  so Matrix homeservers are forced to push every (encrypted) message.
* Some platforms, e.g. Android without Firebase Cloud Messaging support, it is known to be
  [expensive to run a polling loop](https://github.com/vector-im/element-android/issues/2055)
  to download all messages and search them for notifications.

This MSC proposes a middle ground, which should help with platforms which support
push notifications. (Although it isn't as directly able to help with platforms
without push unless an easier API to find these events is created.)

It is also asserted[^5] that clients want to download all data for search (and
keyword matching) in encrypted rooms. It is unclear if there is actually a need
to do this on mobile devices (and it could use excessive storage and bandwidth,
as mentioned above).

[MSC3575: Sliding Sync](https://github.com/matrix-org/matrix-spec-proposals/blob/kegan/sync-v3/proposals/3575-sync.md#e2ee-handling)
discusses the trade-off of choosing which rooms to sync based on whether the rooms
are encrypted and whether they have notifications. This proposal may help slightly
to give more confidence that an event is notification or not, but does not help
solve the issue of which rooms to sync first.

## Security considerations

[MSC1796](https://github.com/matrix-org/matrix-spec-proposals/pull/1796) and an
[earlier version of MSC3952](https://github.com/matrix-org/matrix-spec-proposals/blob/86bf972c2c8ef04dc849ada5bbcb986ac990a7a3/proposals/3952-intentional-mentions.md)[^6]
proposed sending the mentioned users (or room) in cleartext to allow for more
fine grained control of which events are pushed, but this was deemed to be too
much of a metadata leak.

This proposal significantly reduces the metadata leak by only including *if* there
is a mentioned user or room. This helps reduce metadata leakage by:

1. Not including the mentioned users in cleartext. 🙃
2. Treating a room mention and an individual user mention identically (it is
   likely that some or most users will discard the message on the client device
   once decrypted).

This seems like a reasonable trade-off, but needs vetting.

## Future extensions

This proposal does not attempt to solve the issue of keyword notifications,
although it has been [suggested](https://github.com/matrix-org/matrix-spec-proposals/blob/matthew/msc1796/proposals/1796-e2e-notifications.md#better-handling-of-custom-keyword-notifications)
that custom keywords are uncommon and a sufficiently different problem. Regardless,
it is recommended that client authors explain this limitation to users or provide
a way for users to enable keywords in a subset of rooms.

## Unstable prefix

During development the new push rule shall use `org.matrix.mscxxxx.is_encrypted_mention`
instead of `.m.rule.is_encrypted_mention`.

## Dependencies

This proposal depends on the following MSCs which, at the time of writing, have
not yet been accepted into the Matrix spec:

* [MSC3952](https://github.com/matrix-org/matrix-spec-proposals/pull/3952): Intentional Mentions


[^1]: Via either an explicit `"dont_notify"` action or an empty array. These are
equivalent, see [issue #643](https://github.com/matrix-org/matrix-spec/issues/643).

[^2]: The [`.m.rule.master`](https://spec.matrix.org/v1.6/client-server-api/#default-override-rules)
is *always* first, so this rule gets created right after it.

[^3]: Strictly speaking this does not require MSC3952, but it simplifies the text
to assume it will be accepted.

[^4]: In the past it was not possible to discard notifications on iOS: if a push
notification was received it *had to be displayed*. This is [no longer the case](https://developer.apple.com/documentation/bundleresources/entitlements/com_apple_developer_usernotifications_filtering).

[^5]: [From MSC3952 comments](https://github.com/matrix-org/matrix-spec-proposals/pull/3952#discussion_r1113525021):
"we already are committed to downloading all contents in E2EE rooms in order to
calculate unread state (given the server doesn't know if a msg is visible until
it's decrypted), notifying for keyword mentions, updating full-text indexes for
E2EE content, etc."

[^6]: In particular see [this thread](https://github.com/matrix-org/matrix-spec-proposals/pull/3952#discussion_r1112154200)
on MSC3952 and the [subsequent](https://github.com/matrix-org/matrix-spec-proposals/commit/f0a1f6ad184788814c45d58370248b8052142171)
reversal of the cleartext mentions information.
