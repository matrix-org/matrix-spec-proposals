# Proposal for aggregations via relations

## Problem

It's common to want to send events in Matrix which relate to existing events -
for instance, reactions, edits and even replies/threads.

Clients typically need to track the related events alongside the original
event they relate to, in order to correctly display them.  For instance,
reaction events need to be aggregated together by summing and be shown next to
the event they react to; edits need to be aggregated together by replacing the
original event and subsequent edits; replies need to be indented after the
message they respond to, etc.

It is possible to treat relations as normal events and aggregate them
clientside, but to do so comprehensively could be very resource intensive, as
the client would need to spider all possible events in a room to find
relationships and maintain an correct view.

Instead, this proposal seeks to solve this problem by:
 * Defining a standard shape for defining events which relate to other events
 * Defining APIs to let the server calculate the aggregations on behalf of the
   client, and so bundle the related events with the original event where
   appropriate.

## Proposal

This proposal introduces the concept of relations, which can be used to
associate new information with an existing event.

Relations are any event which have an `m.relationship` field in their
contents. The `m.relationship` field must include a `rel_type` field that
gives the type of relationship being defined, and the `event_id` field that
gives the event which is the target of the relation.  All the information about
the relationship lives under the `m.relationship` key.

  FIXME: in practice, clients have ended up using `m.relates_to` rather than
  `m.relationship`, based on an earlier version of this MSC.  It's unclear
  whether to migrate the clients to `m.relationship` or give up and stick with
  `m.relates_to`.

If it helps, you can think of relations as a "subject verb object" triple,
where the subject is the relation event itself; the verb is the `rel_type`
field of the `m.relationship` and the object is the `event_id` field.

We consciously do not support multiple different relations within a single event,
in order to keep the API simple, and in the absence of identifiable use cases.
Instead, one would send multiple events, each with its own `m.relationship`
defined.

### Relation types

This proposal defines three `rel_type`s, each of which provide different behaviour
when aggregated:

 * `m.annotation` - Intended primarily for handling emoji reactions, these let
   you define an event which annotates an existing event. The annotations are
   typically presented alongside the event in the timeline. When aggregated,
   it groups events together based on their `key`  and `type` and returns a `count`.
   Another usage of an annotation is e.g. for bots, who could use annotations
   to report the success/failure or progress of a command.

For example, an `m.reaction` event which annotates an existing event with a 👍
looks like:

```json
{
    "type": "m.reaction",
    "content": {
        "m.relationship": {
            "rel_type": "m.annotation",
            "event_id": "$some_event_id",
            "key": "👍"
        }
    }
}
```

 * `m.replace` - Intended primarily for handling edits, these let you define
   an event which replaces an existing event.  When aggregated, returns the
   most recent replacement event (as determined by `origin_server_ts`). The
   replacement event must contain an `m.new_content` which defines the
   replacement content (allowing the normal `body` fields to be used for a
   fallback for clients who do not understand replacement events).

For instance, an `m.room.message` which replaces an existing event looks like:

```json
{
    "type": "m.room.message",
    "content": {
        "body": "s/foo/bar/",
        "msgtype": "m.text",
        "m.new_content": {
            "body": "Hello! My name is bar",
            "msgtype": "m.text",
        },
        "m.relationship": {
            "rel_type": "m.replace",
            "event_id": "$some_event_id",
        }
    }
}
```

  Permalinks to edited events should capture the event ID that the sender is viewing
  at that point (which might be an edit ID).  The client viewing the permalink
  should resolve this ID to the source event ID, and then display the most recent
  version of that event.

  XXX: in future we may wish to consider ordering replacements (or relations
  in general) via a DAG rather than using `origin_server_ts` to determine
  ordering - particularly to mitigate potential abuse of edits applied by
  moderators.  Whatever, Care must be taken by the server to ensure that if
  there are multiple replacement events, the server must consistently choose
  the same one as all other servers.

 * `m.reference` - Intended in future for handling replies and threading,
   these let you define an event which references an existing event. When
   aggregated, currently doesn't do anything special, but in future could
   bundle chains of references (i.e. threads). These do not yet replace
   `m.relates_to`-style replies however.

For instance, an `m.room.message` which references an existing event
would look like:

```json
{
    "type": "m.room.message",
    "content": {
        "body": "i <3 shelties",
        "m.relationship": {
            "rel_type": "m.reference",
            "event_id": "$another_event_id"
        }
    }
}
```

Different subtypes of references could be defined through additional fields on
the `m.relationship` object, to distinguish between replies, threads, etc.
This MSC doesn't attempt to define these subtypes.

  XXX: do we want to support multiple parents for a m.reference event, if a
  given event references different parents in different ways?

### Sending relations

Related events are normal Matrix events, and can be sent by the normal /send
API.

The server should postprocess relations if needed before sending
them into a room, for instance, if we ever use a DAG to define the ordering of
`m.replace` relations, the server would be responsible for specifying the
parent pointers on the DAG.

If the user tries to send the same annotation multiple times for the same
event `type` (e.g. `m.reaction`) and aggregation `key` (e.g. 👍) then the
server should respond with 400 and error M_INVALID_REL_TYPE.

    XXX: currently synapse returns 400 and `{"errcode":"M_UNKNOWN","error":"Can't send same reaction twice"}`

Similar to membership events, a convenience API is also provided to highlight
that the server may post-process the event, and whose URL structures the
semantics of the relation being sent more clearly:

```
PUT /_matrix/client/r0/rooms/{roomId}/send_relation/{parent_id}/{relation_type}/{event_type}/{txn_id}[?key=%F0%9F%91%8D]
{
    // event contents
}
```

The `parent_id` is:

  * For annotations the event being displayed (which may be an edit)
  * For replaces/edits the original event (not previous edits)
  * For references should be the event being referenced

Any trailing slashes on the endpoint should be ignored.

### Receiving relations

#### Unbundled relation events

Relations are received during non-gappy incremental syncs as normal discrete
Matrix events.  These are called "unbundled relation events".

There is one special case: `unsigned.annotation_count` is provided on annotation events,
calculated by the server to provide the current absolute count of the given
annotation key as of that point of the event, to avoid the client having to
accurately track the absolute value itself.

  XXX: this special case isn't implemented in Synapse yet

For instance, an incremental sync might include the following:

```json
{
    "type": "m.reaction",
    "sender": "@matthew:matrix.org",
    "content": {
        "m.relationship": {
            "rel_type": "m.annotation",
            "event_id": "$some_event_id",
            "key": "👍"
        }
    },
    "unsigned": {
        "annotation_count": 1234,
    }
}
```

...to indicate that Matthew just thumbsupped a given event, bringing the current
total to 1234 thumbsups.

#### Bundled relations

Other than during non-gappy incremental syncs, an aggregate view of relation
events should be bundled into the unsigned data of the event they relate to,
rather than sending un-bundled individual relation events.  This is called a
bundled relation (or bundled aggregation), and by sending a summary of the
aggregations, avoids us having to always send lots of individual unbundled
relation events individually to the client.

Any API which receives events should bundle relations (apart from non-gappy
incremental syncs), for instance: initial sync, gappy incremental sync,
/messages and /context.

The bundled relations are grouped according to their `rel_type`, and then
paginated within each group using Matrix's defined pagination idiom of `count`,
`limited` and `chunk` fields - respectively giving the total number of
elements in the list, whether that list has been truncated, and an array of
elements in the list.

The format of the aggregated value in the bundle depends on the relation type:

 * `m.annotation` aggregations provide the `type` of the relation event, the
   aggregation `key`, the `origin_server_ts` of the first reaction to that event,
   and the `count` of the number of annotations of that `type` and `key` which
   reference that event.
 * `m.replace` aggregations provide the most recent edited version of the event
   in the main event contents, but with the metadata (sender & ts) of the
   original event. Then in the bundle itself there are keys for  `event_id`
   (the ID of the original event at the root of the sequence of edits).
   `origin_server_ts` (for when it was edited) and `sender` for who did the
   edit. This allows the client to identify the message as an edit, and easily
   tell who authored the edit and when (given the event itself tracks the
   original message's metadata).
 * `m.reference` list the `event_id` and event `type` of the events which
   reference that event.

  XXX: An alternative approach could be to (also?) use a filter to
  specify/override how to aggregate custom relation types, which would then
  also be used to inform /sync how we want to receive our bundled relations.
  However, we really need to be better understand how to do custom relation
  types first...

For instance, the below example shows an event with five bundled relations;
three thumbsup reaction annotations, one replace, and one reference.

```json
{
    ...,
    "unsigned": {
        "m.relations": {
            "m.annotation": {
                "chunk": [
                  {
                      "type": "m.reaction",
                      "key": "👍",
                      "origin_server_ts": 1562763768320,
                      "count": 3
                  }
                ],
                "limited": false,
                "count": 1
            },
            "m.reference": {
                "chunk": [
                    {
                        "type": "m.room.message",
                        "event_id": "$some_event_id"
                    }
                ],
                "limited": false,
                "count": 1
            },
            "m.replace": {
                "event_id": "$original_event_id",
                "origin_server_ts": 1562763768320,
                "sender": "@bruno1:localhost"
            }
        }
    }
}
```

  FIXME: the server needs to generate the `origin_server_ts` of the first
  reaction in a given group, to allow clients which want to do chronological
  ordering to do so.

#### Handling limited (gappy) syncs

For the special case of a gappy incremental sync, many relations (particularly
reactions) may have occurred during the gap.  It would be inefficient to send
each one individually to the client, but it would also be inefficient to send
all possible bundled aggregations to the client.

The simplest thing a client can do is to just throw away its history for a
room on seeing a gappy incremental sync, and then re-paginate the history of
the room using /messages in order to get a consistent view of the relations
which may have changed during the gap.  However, this is quite inefficient,
and prohibits the client from persisting multiple sections of timeline for a
given room.

Alternatively, the server tells the client the event IDs of events which
predate the gap which received relations during the gap.  This means that the
client can invalidate its copy of those events (if any) and then requery them
(including their bundled relations) from the server if/when needed.

The server does this with the new `stale_events` field of each room object
in the sync response.  The `stale_events` field lists all the event IDs
prior to the gap which had updated relations during the gap.  The event IDs
are grouped by relation type, and limited to N entries for efficiency.  N
should be 100.  If the number of events with stale relations exceeds N, the
list is marked as `limited` as per the normal Matrix pagination model.  We do
not include events referenced by `m.reference` as stale, in favour of more
sophisticated pagination techniques in future. For instance:

```json
"!roomid:matrix.org": {
  "account_data": {},
  "ephemeral": {},
  "state": {},
  "summary": {},
  "timeline": {},
  "unread_notifications": {},
  "stale_events": {
    "m.annotations": {
      "chunk": [
        "$12345676321:matrix.org",
        "$12345321432:matrix.org"
      ],
      "limited": false
    }
  }
}
```

This shows that in the gappy sync response, a given room has two events prior
to the gap which received new annotations during the gap. Therefore if the
client has cached a local copy of those events, it should invalidate them, and
subsequently refresh them as needed.

To refresh events, we need an API to load arbitrary events from the room in
bulk, which the CS API doesn't currently provide.  We propose extending GET
`{roomId}/event/{eventId}` to accept a list of event IDs on the URL, e.g:

`POST /_matrix/client/r0/rooms/{roomId}/event`
```json
{
    "event_ids": [
        "$12345676321:matrix.org",
        "$12345321432:matrix.org"
    ]
}
```

...which returns an array of events with the given IDs.

  XXX: Synapse hasn't implemented any of this section yet.

#### Paginating relations and aggregations

A single event can have lots of associated relations, and we do not want to
overload the client by including them all in a bundle. Instead, we provide two
new APIs in order to paginate over the relations, which behave in a similar
way to `/messages`, except using `next_batch` and `prev_batch` names (in line
with `/sync` API). Clients can start paginating either from the earliest or
latest events using the `dir` param.

The `/relations` API lets you iterate over all the **unbundled** relations
associated with an event in standard topological order.  You can optionally
filter by a given type of relation and event type:

```
GET /_matrix/client/r0/rooms/{roomID}/relations/{eventID}[/{relationType}[/{eventType}]]
```

```json
{
  "chunk": [
    {
      "type": "m.reaction",
      "sender": "...",
      "content": { }
    }
  ],
  "next_batch": "some_token",
  "prev_batch": "some_token"
}
```

Any trailing slashes on the endpoint should be ignored.

  FIXME: we need to spell out that this API should return the original message
  when paginating over `m.replace` relations for a given message.  Synapse currently
  looks to include this as an `original_event` field alongside `chunk` on all relations,
  which feels very redundant when we only need it for edits.  Either we specialcase it
  for edits, or we just have the client go call /event to grab the contents of the original?

The `/aggregations` API lets you iterate over **bundled** relations, and within them.

To iterate over the bundled relations for an event (optionally filtering by
relation type and target event type):

```
GET /_matrix/client/r0/rooms/{roomID}/aggregations/{eventID}[/{relationType}][/{eventType}][?filter=id]
```

```json
{
  "chunk": [
    {
      "type": "m.reaction",
      "key": "👍",
      "origin_server_ts": 1562763768320,
      "count": 5,
    }
  ],
  "next_batch": "some_token",
  "prev_batch": "some_token"
}
```

Any trailing slashes on the endpoint should be ignored.

  FIXME: what should we expect to see for bundled `m.replace` if anything?
  Synapse currently returns an empty chunk for an event with subsequent edits,
  while you might expect to receive the most recent bundled aggregation data
  for an edit. Similarly, what do you get for `m.reference`?  Should it be an
  array of event_ids for replies to this msg?  Alternatively, should we just
  ignore anything other than annotations, given the API is only meaningful for
  annotations?

To iterate over the unbundled relations within a specific bundled relation, you
use the following API form, identifying the bundle based on its `key`
(therefore this only applies to `m.annotation`, as it is the only current
`rel_type` which groups relations via `key`).

```
GET /_matrix/client/r0/rooms/{roomID}/aggregations/{eventID}/${relationType}/{eventType}/{key}
```

e.g.

```
GET /_matrix/client/r0/rooms/!asd:matrix.org/aggregations/$1cd23476/m.annotation/m.reaction/👍
```

```json
{
  "chunk": [
    {
      "type": "m.reaction",
      "sender": "...",
      "content": { }
    },
  ],
  "next_batch": "some_token",
  "prev_batch": "some_token"
}
```

## End to end encryption

Since the server has to be able to bundle related events, structural
information about relations cannot be encrypted end-to-end, and so the
`m.relationship` field should not be included in the ciphertext.

For instance, an encrypted `m.replace` looks like this:

```json
{
  "content": {
    "algorithm": "m.megolm.v1.aes-sha2",
    "ciphertext": "AwgBErA....",
    "device_id": "NBHOQUBWME",
    "m.relationship": {
      "event_id": "$15632219072753999gNDqf:matrix.org",
      "rel_type": "m.replace"
    },
    "sender_key": "rt/7v+UV9cw9PzXEVk7gjLe8kLxuu/e3075PgPi9XVU",
    "session_id": "q9Okpk4fK+SqSPvTBbhWPZt39LrTEj8vuQdcIK/iYa4"
  },
  "sender": "@matthew:matrix.org",
  "type": "m.room.encrypted",
}
```

For `m.annotation` relations, the annotation SHOULD be encrypted, encrypting
the `key` field using the same message key as the original message as per the
following section.  However, while transitioning to this system, reactions may
be sent entirely unencrypted in an E2E room.

### Thoughts on encrypting the aggregation key

XXX: this hasn't been locked down yet, and at this rate will form a different
MSC entirely, for E2E-safe reactions.  But until that point, let's gather it
here:

@jryans said:

We have agreed IRL that encrypted aggregations should include additional
metadata so that clients can clearly distinguish unencrypted and encrypted
aggregation keys for presentation. In addition, the proposal might want to
clarify that e2e rooms might have both unencrypted and encrypted aggregation
keys (just like it's currently possible to send unencrypted regular messages
to an e2e room).

@ara4n said:

How about "alg": "A256CTR" which then matches how we encrypt attachments for
E2E. Given the aggregation keys are kindasorta mini encrypted attachments,
this doesn't seem unreasonable. Someone needs to doublecheck whether CTR is
the right mode, however, and if so what we do about IVs and hashes etc.

@jryans said:

The core idea is that the aggregation key will be encrypted with the same
message key as the original message. Maybe copying encryption metadata from
the original message is the right way to indicate that on the key? For
example:

```json
{
    "type": "m.reaction",
    "content": {
        "m.relationship": {
            "algorithm": "m.megolm.v1.aes-sha2",
            "session_id": "<id from original message>",
            "rel_type": "m.annotation",
            "event_id": "$some_event_id",
            "key": "<encrypted key>"
        }
    }
}
```

We likely also want to define that reaction should be left as `m.reaction` in
an encrypted room (rather than becoming `m.room.encrypted` as least Riot Web
does at the moment) because:

* `m.room.encrypted` triggers default push rules for DM rooms
* `m.room.encrypted` is a bit silly for reactions since the relation data (the
  interesting bit of the event) is already lifted out to clear text anyhow
* `m.room.encrypted` prevents server-side bundling for reactions which
  currently checks for the `m.reaction` type

@uhoreg said:

I don't think the encryption mode matters too much.  Megolm encrypts using
CBC, which is probably fine for short data like this.  The main advantage of
CTR over CBC is that CTR can encrypt in parallel, which shouldn't be a huge
deal in this case.  So I think the main question for whether we use CTR or CBC
is whether we want to be consistent with Megolm or with encrypted attachments.
 I'd suggest that it's better to be consistent with Megolm in this case,
especially if the encryption/decryption will be handled in libolm (see below).

As far as reusing the same encryption key from the original message for
encrypting the reaction, I think it's going to be a bit complicated.

First of all, the session ID is somewhat tied to the sending user.  At least
in matrix-js-sdk, looking up an incoming session ID requires the sender's
curve25519 key, which in this case would mean the sender of the original
message, and not the sender of the reaction.  This can be figured out in one
of two ways: either you add the original sender's key to the `m.relationship`
data, or else get the client to look it up from the original event.  (And if
you're looking up the sender's key from the original event, you could also
look up the session ID as well.)

Secondly, if we just follow the megolm format, the encrypted result includes a
signature from the sender's ed25519 key.  Again, this would be the sender of
the original event, and not the reaction, and obviously the sender of the
reaction will not be able to form a correct signature (unless they're also the
sender of the original event, or manage to crack the sender's key).  We could
instead replace it with a signature from the reaction sender's ed25519 key,
but then of course the reaction keys won't be the same between senders.  We
could drop the signature entirely, but that means that ((unless I'm missing
something) a homeserver admin who can read the original message could forge a
reaction from one of their users.  So we may need to add a signature somewhere
else.

Third, using the exact same key for encrypting the reaction as the original
message opens up a potential known-plaintext attack.  AES (and any other
modern cipher) should be immune to known-plaintext, but if we can easily use a
different key, then we may want to do that anyways.  One way that this can be
done is by deriving the aes key/hmac key/aes IV using HKDF(0, R_i, rel_type,
80), rather than HKDF(0, R_i, "MEGOLM_KEYS", 80).

The main thing on the olm side is that, no matter what we do, we we'll need to
add some functions to libolm in order to do this.  We could:

1. add an olm function to get the decryption key for a particular message, and
let the client author handle the encryption/decryption themselves.  This would
also include
[formatting](https://gitlab.matrix.org/matrix-org/olm/blob/master/docs/megolm.md#message-format)
the encrypted reaction key themselves.  The advantage to this is that it would
be a fairly generic function, not specific to reactions, but overall, I think
this would probably be too annoying for a lot of client authors, and probably
wouldn't be used outside of reaction anyways.

2. add olm functions to handle the encryption and decryption entirely.  This
would probably end up being functions that are very specific to reactions,
which would be :( , but would probably result in client authors not hating us
(more).

This, of course, is all going to be a load of fun to spec. :P 

## Redactions

Relations may be redacted like any other event.  In the case of `m.annotation`
this removes the annotation from the message.  In the case of `m.replace` it
removes that edit revision.  In the case of `m.reference` it removes the
referencing event.

Trying to call `/relations` or `/aggregations` on a redacted message must return
a 404.

In the UI, the act of redacting an edited message in the timeline should
remove the message entirely from the timeline.  It can do this by redacting the
original msg, while ensuring that clients locally discard any edits to a
redacted message on receiving a redaction.

  XXX: does Riot actually do this?

The `m.relationship`.`rel_type` and `m.relationship`.`event_id` fields should
be preserved over redactions, so that clients can distinguish redacted edits
from normal redacted messages, and maintain reply ordering.

  FIXME: synapse doesn't do this yet

When a specific revision of an event is redacted, the client should manually
refresh the parent event via `/events` to grab whatever the replacement
revision is.

## Local echo

XXX: do we need to spell out how to handle local echo considerations?

Remember to let users edit unsent messages (as this is a common case for
rapidly fixing a typo in a msg which is still in flight!)

## Edge cases

How do you stop people reacting more than once with the same key?
 1. You error with 400 (M_INVALID_REL_TYPE) if they try to react twice with the same key, locally
 2. You flatten duplicate reactions received over federation from the same user
    when calculating your local aggregations
 3. You don't pass duplicate reactions received over federation to your local user.
 4. XXX: does synapse do 2 & 3 yet?

Can you edit a reaction?
 * It feels reasonable to say "if you want to edit a reaction, redact it and resend".
   `rel_type` is immutable, much like `type`.

Can you react to a reaction?
 * Yes, at the protocol level.  But you shouldn't expect clients to do anything
   useful with it.

Can you reply (via m.references) to a reaction/edit?
 * Yes, at the protocol level.  But you shouldn't expect clients to do anything
   useful with it.
 * Replying to a reaction should be treated like a normal message and have the
   reply behaviour ignored.
 * Replying to an edit should be treated in the UI as if you had replied to
   the original message.

How do you handle ignored users?
 * Information about relations sent from ignored users must never be sent to
   the client, either in bundled or unbundled form.  This is to let you block
   someone from harassing you with emoji reactions (or using edits as a
   side-channel to harass you).

What happens when you react to an edit?
 * You should be able to, but the reaction should be attributed to the edit (or
   its contents) rather than the message as a whole.
 * Edits gather their own reactions, and the clients should display
   the reactions on the most recent edit.
   * This provides a social pressure to get your edits in quickly before there
     are many reactions, otherwise the reactions will get lost.
   * And it avoids us randomly aggregating reactions to potentially very
     different contents of messages.

How do you handle racing edits?
 * The edits could form a DAG of relations for robustness.
    * Tie-break between forward DAG extremities based on origin_ts
    * this should be different from the target event_id in the relations, to
      make it easier to know what is being replaced.
    * hard to see who is responsible for linearising the DAG when receiving.
      Nasty for the client to do it, but the server would have to buffer,
      meaning relations could get stuck if an event in the DAG is unavailable.
 * ...or do we just always order by on origin_ts, and rely on a social problem
   for it not to be abused?
    * problem is that other relation types might well need a more robust way of
      ordering. XXX: can we think of any?
    * could add the DAG in later if it's really needed?
    * the abuse vector is for a malicious moderator to edit a message with origin_ts
      of MAX_INT. the mitigation is to redact such malicious messages, although this
      does mean the original message ends up being vandalised... :/
 * Conclusion: let's do it for origin_ts as a first cut, but use event shapes which
   could be switched to DAG in future is/as needed.  Good news is that it only
   affects the server implementation; the clients can trust the server to linearise
   correctly.

Which message types are reactable?
 * Any. But perhaps we should provide some UI best practice guidelines:
  * `m.room.message` must be reactable
  * `m.sticker` too
  * ...but anything else may not be rendered.

What does it mean to call /context on a relation?
 * We should probably just return the root event for now, and then refine it in
   future for threading?
 * XXX: what does synapse do here?

What can we edit?
 * Only non-state events for now.
 * We can't change event types, or anything else which is in an E2E payload
 * We can't change relation types either.

How do diffs work on edits if you are missing intermediary edits?
 * We just have to ensure that the UI for visualising diffs makes it clear
   that diffs could span multiple edits rather than strictly be per-edit-event.

What happens when we edit a reply?
 * We just send an m.replace which refers to the m.reference target; nothing
   special is needed.  i.e. you cannot change who the event is replying to.
 * The edited reply should ditch the fallback representation of the reply itself
   however from `m.new_content` (specifically the `<mx-reply>` tag in the
   HTML, and the chevron prefixed text in the plaintext which we don't know
   whether to parse as we don't know whether this is a reply or not), as we
   can assume that any client which can handle edits can also display replies
   natively.

   XXX: make Riot do this

Do we need to support retrospective references?
 * For something like "m.duplicate" to retrospectively declare that one event
   dupes another, we might need to bundle two-levels deep (subject+ref and then
   ref+target).  We can cross this bridge when we get there though, as a 4th
   aggregation type

What power level do you need to be able to edit other people's messages, and how
does it fit in with fedeation event auth rules?
 * 50, by default?

    XXX: Synapse doesn't impose this currently - it lets anyone send an edit,
    but then filters them out of bundled data.

"Editing other people's messages is evil; we shouldn't allow it"
 * Sorry, we have to bridge with systems which support cross-user edits.
 * When it happens, we should make it super clear in the timeline that a message
   was edited by a specific user.
 * We do not recommend that native Matrix clients expose this as a feature.

## Federation considerations

In general, no special considerations are needed for federation; relational
events are just sent as needed over federation same as any other event type -
aggregated onto the original event if needed.

We have a problem with resynchronising relations after a gap in federation:
We have no way of knowing that an edit happened in the gap to one of the events
we already have.  So, we'll show inconsistent data until we backfill the gap.
 * We could write this off as a limitation.
 * Or we could make *ALL* relations a DAG, so we can spot holes at the next
   relation, and go walk the DAG to pull in the missing relations?  Then, the
   next relation for an event could pull in any of the missing relations.
   Socially this probably doesn't work as reactions will likely drop off over
   time, so by the time your server comes back there won't be any more reactions
   pulling the missing ones in.
 * Could we also ask the server, after a gap, to provide all the relations which
   happened during the gap to events whose root preceeded the gap.
   * "Give me all relations which happened between this set of
     forward-extremities when I lost sync, and the point i've rejoined the DAG,
     for events which preceeded the gap"?
   * Would be hard to auth all the relations which this api coughed up.
     * We could auth them based only the auth events of the relation, except we
       lose the context of the nearby DAG which we'd have if it was a normal
       backfilled event.
     * As a result it would be easier for a server to retrospectively lie about
       events on behalf of its users.
     * This probably isn't the end of the world, plus it's more likely to be
       consistent than if we leave a gap.
       * i.e. it's better to consistent with a small chance of being maliciously
         wrong, than inconsistent with a guaranteed chance of being innocently
         wrong.
   * We'd need to worry about pagination.
   * This is probably the best solution, but can also be added as a v2.

## Security considerations

If using reactions for upvoting/downvoting purposes we would almost certainly want to anonymise the
reactor, at least from other users if not server admins, to avoid retribution problems.
This gives an unfair advantage to people who run their own servers however and
can cheat and deanonymise (and publish) reactor details.  In practice, reactions may
not be best used for upvote/downvote as at the unbundled level they are intrinsically
private data.

Or in a MSC1228 world... we could let users join the room under an anonymous
persona from a big public server in order to vote?  However, such anonymous personae
would lack any reputation data.

## Extended annotation use case

In future it might be useful to be able to annotate events with more
information, some examples include:

  * Annotate commit/PR notification messages with their associated CI state, e.g.
    pending/passed/failed.
  * If a user issues a command to a bot, e.g. `!deploy-site` the bot could
    annotate that event with current state, like "acknowledged",
    "redeploying...", "success", "failed", etc.
  * Other use cases...?

However, this doesn't really work with the proposed grouping, as the aggregation
key wouldn't contain the right information needed to display it (unlike for
reactions).

One way to potentially support this is to include the events (or a subset of the
event) when grouping, so that clients have enough information to render them.
However this dramatically inceases the size of the parent event if we bundle the
full events inside, even if limit the number we bundle in. To reduce the
overhead the annotation event could include a `m.result` field which gets
included.

This would look something like the following, where the annotation is:

```json
{
  "type": "m.bot_command_response",
  "content": {
    "m.result": {
      "state": "success",
    },
    "m.relationship": {
      "type": "m.annotation",
      "key": ""
    }
  }
}
```

and gets bundled into an event like:

```json
{
  "unsigned": {
    "m.relations": {
      "m.annotation": [
        {
          "type": "m.bot_command_response",
          "key": "",
          "count": 1,
          "chunk": [
            {
              "m.result": {
                "state": "success",
              },
            }
          ],
          "limited": false,
        }
      ]
    }
  }
}
```

This is something that could be added later on. A few issues with this are:

  * How does this work with E2EE? How do we encrypt the `m.result`?
  * We would end up including old annotations that had been superceded, should
    these be done via edits instead?

## Tradeoffs

### Event shape

Shape of

```json
"content": {
    "m.relationship": {
        "m.reference": {
            "event_id": "$another:event.com"
        }
    }
}
```
versus

```json
"content": {
    "m.relationship": {
        "rel_type": "m.reference",
        "event_id": "$another:event.com"
    }
}
```

The reasons to go with `rel_type` is:
 * we don't need the extra indirection to let multiple relations apply to a given pair of
   events, as that should be expressed as separate relation events.
 * if we want 'adverbs' to apply to 'verbs' in the subject-verb-object triples which
   relations form, then we apply it as mixins to the relation data itself rather than trying
   to construct subject-verb-verb-object sentences.
 * so, we should pick a simpler shape rather than inheriting the mistakes of m.in_reply_to
   and we have to keep ugly backwards compatibility around for m.in_reply_to
   but we can entirely separately worry about migrating replies to new-style-aggregations in future
   perhaps at the same time as doing threads.

## Historical context

pik's MSC441 has:

Define the JSON schema for the aggregation event, so the server can work out
which fields should be aggregated.

```json
"type": "m.room._aggregation.emoticon",
"content": {
    "emoticon": "::smile::",
    "msgtype": "?",
    "target_id": "$another:event.com"
}
```

These would then aggregated, based on target_id, and returned as annotations on
the source event in an `aggregation_data` field:

```json
"content": {
    ...
    "aggregation_data": {
        "m.room._aggregation.emoticon": {
            "aggregation_data": [
                {
                    "emoticon": "::smile::",
                    "event_id": "$14796538949JTYis:pik-test",
                    "sender": "@pik:pik-test"
                }
            ],
            "latest_event_id": "$14796538949JTYis:pik-test"
        }
    }
}
```
