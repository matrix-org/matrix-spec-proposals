MSC4306: Thread Subscriptions
=====

## Background and Summary

Threads were introduced in [version 1.4 of the Matrix Specification](https://spec.matrix.org/v1.13/changelog/v1.4/) as a way to isolate conversations in a room, making it easier for users to track specific conversations that they care about (and ignore those that they do not).

Thus far, there has been no good way for users to ensure that they see new messages in only the threads that they care about. The current rules only allow expressing one of two choices: users and their clients can either watch all threads, or ignore all threads.
As a result, the user is either being presented with unwanted information (misusing their attention), or they risk missing important messages.

This proposal introduces a new mechanism, Thread Subscriptions, as a first-class way for users to signal which threads they care about.

We then add a new push rule so that users can receive push notifications only for threads that they care about.


## Proposal

This proposal consists of four main parts:
- 3 simple endpoints for subscribing to and unsubscribing from threads;
- new prescribed client behaviour when the user sends a message in a thread;
- new prescribed client behaviour when the user is mentioned in a thread; and
- a new push rule (including a new push rule condition) that prevents notifying about threads that the user has not subscribed to.


### Terminology

This proposal introduces the concept of being 'subscribed' to and 'unsubscribed' from a thread.

The default state is unsubscribed.


### New Endpoints

#### Subscribing to a thread

```
PUT /_matrix/client/v1/rooms/{roomId}/thread/{eventId}/subscription
```

with request body:

```jsonc
{
  // If the subscription was made automatically
  // by a client, this is the ID of the latest event that caused
  // the automatic subscription.
  //
  // If the subscription was made manually,
  // this field is omitted.
  "automatic": "$abcdef"
}
```

In the general case, returns 200 with empty body `{}`.

If an automatic subscription was requested but the provided cause event ID is not within the thread, returns 400/`M_NOT_IN_THREAD`.

If an automatic subscription was requested but the automatic subscription is skipped by the server, returns 409 (Conflict) with `M_CONFLICTING_UNSUBSCRIPTION`. See the section below on *'Server-side automatic subscription ordering'*.

If the thread does not exist, or if the user does not have access to it, returns 404/`M_NOT_FOUND`.

If the thread is already subscribed, then the subscription remains and:

- if `automatic` is `false`, the thread is marked as manually-subscribed, even if the existing subscription has it marked as automatically subscribed. (In other words, manual subscriptions take precedence over automatic subscriptions.)


#### Unsubscribing from a thread
```
DELETE /_matrix/client/v1/rooms/{roomId}/thread/{eventId}/subscription
```

Returns 200 with empty body `{}`.

If the thread was not subscribed, returns 200 with empty body `{}` for idempotence.

If the thread does not exist, or is inaccessible, returns 404/`M_NOT_FOUND`.


#### Retrieving thread subscription

```
GET /_matrix/client/v1/rooms/{roomId}/thread/{eventId}/subscription

{"automatic": true}
```

Retrieves the thread subscription for a given thread.

On success (200), returns:

```jsonc
{
  // Whether the subscription was automatically made or not
  "automatic": true
}
```

If there is no subscription to that thread, or the thread does not exist, or the thread is inaccessible, returns 404/`M_NOT_FOUND`.

#### Server-side automatic subscription ordering

It would be undesirable if a user was automatically re-subscribed to a thread, after having already unsubscribed, because they opened a dormant device which was not aware of the automatic subscription having already taken place.

To this end, we must prevent automatic subscriptions being re-applied when an unsubscription occurred *after* receipt of the event causing a subscription.

As clients are currently not privy to the ordering of events, we propose that the server is left in charge of making the ordering decision.

For this to work, when a client requests an automatic subscription, it presents the event ID of the latest event it has seen that would give rise to this automatic subscription (**the 'cause event'**).

The server will skip the subscription if it determines that the automatic subscription is for an event that was already acknowledged at the time a manual unsubscription was requested.

To determine this ordering, the server can consider either:

- physical timestamps (comparing the time of the manual unsubscription to the time of receipt of the cause event); or
- logical timestamps (for example, position of the events within an event stream and/or topological ordering position within the room event DAG)

In either case, servers must ensure that an automatic subscription cannot keep getting retriggered by clients.


### New Client Behaviour: subscribe when sending in a thread

When a user is sending a message in a thread, the user's client SHOULD simultaneously perform a manual subscription to that thread using `PUT /subscription`.
The subscription is not considered automamtic, because it was initiated by a user action (sending a message). Further, it'd be best for latency to perform the subscription concurrently with sending the message, so the client doesn't yet have an event ID to attach a hypothetical automatic subscription to anyway.

Clients MUST only perform these subscriptions for messages sent by the same client and at the time of the messages being sent. In other words, client MUST NOT apply them for existing messages or messages sent by other devices.

Clients MAY offer the user the ability to disable this feature, or disable it by default depending on use case.


### New Client Behaviour: subscribe on mention

When a user is mentioned in a thread (by another user — the *mentioning user*), the user's client should perform an automatic subscription to that thread using `PUT /subscription` with `{"automatic": "$eventId"}`.

The server does not perform this action on the client's behalf, principally because the server is not able to detect mentions in encrypted rooms.

If the client is already aware of the user being subscribed to the thread, then making a `PUT /subscription` request is not necessary.

If the mentioning user is banned in the room or ignored by the user, the automatic thread subscription should not occur.

#### What counts as a mention

To determine whether an event within a thread is considered as 'mentioning' the user,
for the sake of the 'subscribe on mention' behaviour,
clients evaluate the push rules against that event.

If the evaluation of the push rules results in a `notify` action as the outcome, then
that event is considered to be 'mentioning' the user.

As a result, along with automatically supporting future notification rules,
this definition includes, by default, all of the following circumstances:

- `@room` — both intentional and fallback;
- intentional user mentions;
- fallback plaintext mentions when intentional mentions are not in use; and
- keyword mentions, if the user has configured some.


#### Reversal of automatic subscriptions

*This section is an optional aspect. Clients can choose not to implement it, particularly in scenarios where it doesn't make sense.*

If an automatic thread subscription occurs and the mentioning user is subsequently banned (or ignored by the user, but without loss of generality we refer to the user as banned hereinafter), then:

- the thread subscription should be reversed,
- provided that there aren't any other mentions by other, non-banned, users that would have caused the same automatic subscription.

When a client becomes aware of a banned user in a room, it may need to backpaginate thread history to determine whether there are any threads whose automatic subscriptions should be reversed, or to determine if there are any other qualifying mentions that would obviate the need to reverse automatic subscriptions.

For efficiency reasons, clients may limit the depth of this backpagination with an implementation-defined recency limit, owing to the observation that abuse is usually cleaned up shortly after it occurs.

### New Push Rules

As motivation, we want threads to have the following notification semantics:

- Messages in unsubscribed threads should not count as activity at all; as a user, I do not want to see the room as unread because there are new messages in an unsubscribed thread.
    - Exceptions: if the user is mentioned, this should generate a notification as usual. (The push notification thus generated is also useful for the client to realise it needs to create an automatic thread subscription.)
- Messages in subscribed threads should always count as a notification, and the (effective) room notification settings should not matter at all. E.g. the room can be muted, but if I, as a user, am subscribed to a thread, I still want to get a notification for new messages in that thread. If I do not want that, then I will unsubscribe.

To achieve this, we propose the addition of two new push rules, both added to a new push rule `kind` called `postcontent`, which is ordered between `content` and `room` but which can contain general-purpose rules:

1. `.m.rule.unsubscribed_thread`, at the beginning of the underride list. This rule causes events in unsubscribed threads to skip notification processing without generating a notification.
   The rule occurs after mention-specific rules and keyword mention rules, meaning that mentions continue to generate notifications.
   ```jsonc
   {
       "rule_id": ".m.rule.unsubscribed_thread",
       "default": true,
       "enabled": true,
       "conditions": [
           {
               "kind": "thread_subscription",
               "subscribed": false
           }
       ],
       "actions": []
   }
   ```
2. `.m.rule.subscribed_thread`, at the beginning of the underride list (following `.m.rule.unsubscribed_thread`). This rule causes events in subscribed threads to generate notifications.
   ```jsonc
   {
       "rule_id": ".m.rule.subscribed_thread",
       "default": true,
       "enabled": true,
       "conditions": [
           {
               "kind": "thread_subscription",
               "subscribed": true
           }
       ],
       "actions": [
           "notify",
           {
               "set_tweak": "sound",
               "value": "default"
           }
       ]
   }
   ```

These push rules use a new push condition `thread_subscription`, which takes an argument `subscribed` (boolean).
The `thread_subscription` push condition is satisfied if and only if all the following hold:
1. the event, which we are running push rules for, is part of a thread.
2. the user is subscribed to the thread (`subscribed` = `true`) or is not subscribed to the thread (`subscribed` = `false`).

### Explanation of the rationale behind the `postcontent` push rule kind

We need a new push rule kind ordered between `content` and `room` because:

**For `.m.rule.unsubscribed_thread`**
- this rule must come after any keyword mentions the user has configured (which would be configured in `content`)
  as those should still trigger mentions (and thus automatic thread subscriptions).
- the rule must come before any room settings the user has configured, such as notifying on all messages in a room,
  as that would cause automatic subscriptions to every thread in the room and it would cause inconsistencies
  between the default 'notified for all messages' behaviour and 'notified for all messages in this room'.

**For `.m.rule.subscribed_thread`**
- it seems inappropriate for an `override` rule to produce notifications, given the `override` rules generally
  are intended to suppress them.
  - more concretely, we should allow rules in the `override` and `content` block the opportunity to produce
    notifications with specific tweaks, e.g. `content` rules to match mentions might highlight the messages
    rather than simply notifying.
      - `.m.rule.contains_user_name` and user-specified keyword mention rules must therefore execute first
        so they can make use of `"set_tweak": "highlight"`.
- this rule should come after `content` in case any users perform negative filtering (i.e. suppressing
  notifications for messages containing certain keywords), although the author is not aware of clients with
  such functionality.
- this rule must come before `room` to avoid thread subscriptions being defeated by user rules such as
  the ones underlying 'Mentions only' or 'Mentions & Keywords' settings available in common clients.

For the time being, servers MUST ensure that clients MUST NOT be able to create custom rules with this push rule kind.
If a client attempts to do this, a 400 / `M_INVALID_PARAM` error response MUST be produced by the server.

## Limitations and Potential Future Expansions

- Users will not have enough granularity to subscribe to threads in a way that lets them keep track of threads (being able to 'catch up' through some mechanism in their client) without also getting notifications for them, except by disabling ALL thread subscription notifications altogether.
  - There is precedent for this granularity in the popular forum software *Discourse*, but the author is not aware of Instant Messaging software with this granularity.
  - With that said, this could be feasibly extended by a later MSC with no apparent issues.
- Users will not be given any functionality allowing them to permanently 'mute' a thread, preventing future automatic subscriptions.
  - This could, however, be introduced in the future as an extension to MSC.

## Alternatives

- Clients could maintain thread subscription settings in Room Account Data, as a map from event ID to the subscription settings.
    - This would be inefficient by requiring the entire subscription set for an entire room to be transferred at once, for example in Sliding Sync.
    - This would make subscriptions vulnerable to Read-Modify-Write race conditions (though this could be addressed with extensions to the Room Account Data APIs).
- Clients could maintain their thread subscription settings in their global Account Data, but this seems to be strictly worse than doing so in Room Account Data.

## Security considerations

- Abuse of 'subscribe on mention', particularly in public rooms
    - Malicious users can be ignored by the user, to stop the subscribe on mention behaviour.
    - Users can disable notifications entirely for rooms.
    - Room moderators can take action against malicious users abusing the feature.
    - If no room moderators are protecting the user, the user can of course also leave the room.

## Notes to Client Implementors

## Notes to Server Implementors

- Since clients will be automatically updating the Thread Subscription Settings when their user is mentioned, server implementations should be ready to handle concurrent updates by multiple of the user's devices/clients when they are online at the same time.

## Unstable amendments

Whilst this proposal is unstable, the following changes should be noted:

- the endpoint is renamed to `/_matrix/client/unstable/io.element.msc4306/rooms/{roomId}/thread/{eventId}/subscription`
- the push rules' IDs are renamed to:
  - `.io.element.msc4306.rule.unsubscribed_thread`
  - `.io.element.msc4306.rule.subscribed_thread`
- the push rule condition `kind` is renamed to:
  - `io.element.msc4306.thread_subscription`
- the error codes are renamed to:
  - `IO.ELEMENT.MSC4306.M_CONFLICTING_UNSUBSCRIPTION`
  - `IO.ELEMENT.MSC4306.M_NOT_IN_THREAD`

For servers implementing this MSC, the `org.matrix.msc4306` feature should be advertised through `/_matrix/clients/versions`.

## Dependencies

- no dependencies on other pending MSCs

## Dependents

This proposal is known to be depended upon by the following MSCs:

- [MSC4308: Thread Subscriptions extension to Sliding Sync](https://github.com/matrix-org/matrix-spec-proposals/blob/rei/msc_ssext_threadsubs/proposals/4308-sliding-sync-ext-thread-subscriptions.md)
