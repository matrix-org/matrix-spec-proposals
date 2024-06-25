# MSC3051: Scalable relations

Edits, reactions, replies, threads, message annotations and other MSCs have
shown, that relations between events are very powerful and useful. Currently the
format from [MSC2674](https://github.com/matrix-org/matrix-doc/pull/2674) is
used. That format however limits each event to exactly one relation. As a result
events rely on other ways to represent secondary relations. For example edits
keep the relation from the previous event. Their support to change or delete
that relation is limited. In theory you could pass that in `m.new_content`, but
clients don't seem to support that and the actual deletion of a relation is
unexplored as well.

There are many cases where 2 or more relations on an event would be useful. This
MSC proposes a simple way to do that and replace the currently proposed format.

## Proposal

To support multiple relations per file this MSC proposes the following format:

```json
{
  "content": {
    "m.relations": [
      {
        "event_id": "$some-other-event",
        "rel_type": "m.in_reply_to"
      },
      {
        "event_id": "$some-third-event",
        "rel_type": "m.replaces"
      },
      {
        "event_id": "$event-four",
        "rel_type": "org.example.custom_relation",
        "key": "some_aggregation_key"
      }
    ]
  },
  "event_id": "$something",
  "type": "m.room.message"
}
```

This has a few benefits:

- You can relate to multiple events at the same time. (I.e. you have a
    description for multiple files you sent.)
- You can have multiple different relation types at once. (I.e. an edit, that
    is also a reply, or a reaction inside a thread.)
- You don't need to look up reply relations in multiple events for edits. The
  edited event is canonical and can be used standalone, without having to look
  up the original event to figure out, what was replied to. You can also remove
  a relation with an edit now. (Useful if you replied to the wrong message or
  didn't mean to reply to anyone.)
- This format is conceptually a lot simpler, if an event has multiple relations.
    You don't run into issues with packing relations into `m.new_content`,
    especially for encrypted events, etc. You just have a list of relations.

If clients want to stay backwards compatible (for a while at least), in many
instances it is possible to generate an `m.relates_to` object from the relations
list. This can be done by picking a primary relation, i.e. the edit relation,
and then packaging up the remaining relations in `m.new_content` or simply
throwing them away. Since this proposal uses `m.relations`, this does not
conflict with the current relations from the other MSCs. One can also generate
the relations object from this MSC from the old relations, since the new
relations are a strict superset, which may be useful to make handling inside of
a client easier.

## Potential issues

### Ordering

The list of relations is not hierarchical. As such there is no order like where
you have a top level relation and a lower level relation like an edit having
priority over a reply.

I don't believe that is an issue in practice. If you edit a message with a
reply, there is a natural meaning to the combination of both relations. You can
even apply them in any order, imo. But there may be other relations, where this
causes more issues. An MSC introducing such a relation should specify how to
handle conflicts then.

### Conflicting relations

Some relation types should probably not be combined. For example you may
disallow editing a reaction, because clients probably won't be handling that
correctly. This MSC however does not disallow that. Specifications that define relations should specify,
how clients should handle that and clients sending such combinations should be
aware, that those probably won't get handled. I don't think just allowing 1
relation is the solution to handling such conflicts and I don't think they will
happen much in practice.

There are some examples of conflict resolution in Appendix B.

## Alternatives

- We could just stick with the existing proposal to only have 1 relation per
    event. This is obviously limiting, but works well enough for a lot of
    relation types.
- There are a few other ways to structure relations like using an object instead
    of an array, etc. I believe this is the most usable one.

## Security considerations

Multiple releations may increase load on the server and the client and provide
more opportunities to introduce bad data. Servers and clients should take
additional care and validate accordingly. It should not be considerably worse
than single relations though and servers may limit relations to a reasonable
amount (like they do for devices already).

## Unstable prefix

Clients should use `im.nheko.relations.v1.relations` instead of `m.relations`
and `im.nheko.relations.v1.in_reply_to` as the relation type for replies in the
mean time.

## Appendix

### Appendix A: Extended motivation

There are a few use cases, where I find a single relation limiting. A few of
those are listed below.

#### Replies + Edit

One common mistake when sending a message is, that I reply to the wrong message.
Currently in most clients the only way to fix that is to send a new message and
delete the old one. This was what we had to do with all messages before edits,
but edits only support changing the content, but not the relations of a message.

One obvious way to edit a reply with the single relation format is sending an
event like this:

```json
{
    "type": "m.room.message",
    "content": {
        "body": "I <3 shelties (now replying to the right parent)",
        "msgtype": "m.text",
        "m.new_content": {
            "body": "I <3 shelties",
            "msgtype": "m.text",
            "m.relationship": {
                "rel_type": "m.reply",
                "event_id": "$the_right_event_id"
            }
        },
        "m.relationship": {
            "rel_type": "m.replace",
            "event_id": "$some_event_id"
        }
    }
}
```

In practice, almost no client supports this. One reason could be, that this is
not very obvious. Another could be, that clients remove the fallback and merge
the `m.new_content` into the top level, but explicitly try to preserve the edit
relation, so the reply relation gets lost.

This format also has some theoretical drawbacks though. It is very irregular. So
for a server to understand this format, it needs to know about edits. Otherwise
it can't list all events with a reply relation to a specific event. This makes
single relations not very generic or extensible, which makes client side
experiments much harder without server support.

It is also beneficial to always send the current reply relation in an edit
event. That way the edit can be somewhat rendered standalone without needing to
lookup the reply relation in the edited event.

If we support edits in the protocol, there is little reason to only be able to
edit specific user visible parts of an event instead of all of them. It is a
wart.

With multiple relations the behaviour is obvious. The following event is a reply
and an edit. If no reply relation is given in an edit, the reply relation is
removed (if there was any):

```json
{
    "type": "m.room.message",
    "content": {
        "body": "I <3 shelties (now replying to the right parent)",
        "msgtype": "m.text",
        "m.new_content": {
            "body": "I <3 shelties",
            "msgtype": "m.text"
        },
        "m.relationships": {
            "m.replace": {
                "event_id": "$some_event_id"
            },
            "m.reply": {
                "event_id": "$the_right_event_id"
            }
        }
    }
}
```

#### Galleries ([MSC2881](https://github.com/matrix-org/matrix-doc/pull/2881))

Context:
https://github.com/matrix-org/matrix-doc/pull/2881#issuecomment-905905261

MSC2881 proposes to be able to send an event like this:

```json
{
  "type": "m.room.message",
  "content": {
    "msgtype": "m.text",
    "body": "Here is my photos and videos from yesterday event",
    "m.relates_to": [
      {
        "rel_type": "m.attachment",
        "event_id": "$id_of_previosly_send_media_event_1"
      },
      {
        "rel_type": "m.attachment",
        "event_id": "$id_of_previosly_send_media_event_2"
      }
    ]
  }
}
```

This is a description, that groups 2 media events together and gives them a
common description (similar to how some other chat apps automatically group a
large batch of pictures). You should be able to reply with that and edit the
description. Because the media is sent are sent as single events first, this
automatically works on clients not implementing this and gives you a rough
progress report, but still allows the timeline to stay clean, if someone opens
the room later. This simply is not possible in this form without multiple
relations.

#### Threads ([MSC3440](https://github.com/matrix-org/matrix-doc/pull/3440))

Threads are a much requested feature. MSC3440 proposes a thread relation in the
following format:

```json
"m.relates_to": {
  "rel_type": "m.thread",
  "event_id": "$thread_root"
}
```

This is a very simple relation, but pretty powerful. However, this again
interacts with all other relation features, that currently make Matrix great.

You can somewhat reply in a thread, because replies still use a different
format:

```json
"m.relates_to": {
    "rel_type": "m.thread",
    "event_id": "$thread_root",
    "m.in_reply_to": {
        "event_id": "$event_target"
    }
}
```

This however prevents us from ever making replies a normal relation, if we only
allow a single relation.

Alternatively, reactions and edits do work in threads, but their behaviour is
not obvious. If a reaction or edit relates to an event in a thread, it is then
shown in the thread. This however means, that a server can't just allow clients
to filter by thread without explicitly supporting threads. It needs to always
query if the original event is in a thread instead of just returning all events
with a specific `rel_type` and `event_id`.

There is also no way to edit an event into a thread. Assuming you replied into
the wrong thread or none at all, there is no way to retroactively fix that,
because you can't easily add a thread relation by editing an event. The first
example in this Appendix describes the obvious way to do this with multiple
relations. In theory it would also be a very powerful tool, if moderators could
"move" messages into threads too by editing them. (Currently only the sender can
edit an event, but there are usecases, where you might want to also allow mods
to do this.)

I would argue threads would be a much richer experience, if we allowed users to
combine them with any kind of relation! You could even weave threads together
and make a conversation "fabric"!

#### Replies to multiple events

Often times people ask similar questions in a conversation. One way to focus the
conversation would be threads. Alternatively it could be very useful to just
reply to multiple people, so that everyone knows, that they are adressed. The
current solution is to just mention everyone by username, but sometimes that is
confusing, especially if one of the questions was asked further back in the
timeline.

### Appendix B: How would this work for existing relation types

This sections gives some examples of how multiple relations could interact on
different events. These are not actually part of the proposal, but just
suggestions to understand the format better.

#### Replies

If your client can't handle it, just pick the first reply from the relations
list. In the future this might be extended to reply to multiple messages at the
same time.

#### Edits

Having one edit apply to multiple events should probably be illegal. In this
case the first edit of the event is picked and the others are ignored.

#### Edits + Replies

Having an edit and a reply relation is well formed. In this case the new reply
relation replaces the reply relation of the original event.

#### Edits + Reactions

Having an edit and a reaction relation is illegal. You are not allowed to edit
reactions currently and this MSC would not change that.

#### Threads + Edits/Replies

Having a thread and an edit relation makes obviously sense. This is an edit in a
thread. Same applies to replies in threads. Clients may choose not to render
those replies to provide a simpler (Slack style) view for threads, but often
that has been voiced as negative feedback on threads. There are a few vocal
users that want replies in threads.

#### Threads

Having multiple thread relations could be interesting. It would allow you to
"join" or "cross" threads. Whether clients want to actually render that or not I
have no opinion on, but the idea sounds interesting.

#### Threads + Reactions

This would make it easier to filter a room by a thread relation, but still have
reactions visible on the `/message` pagination.

#### Annotation + Replies

This probably makes no sense. If it is a reaction event, you probably want to
render it as such, otherwise render it as a reply. Alternatively, just pick the
first relation.

This provides a way for a malicious client to make events render differently on
clients. But it just adds one more way to send invalid relation data. The client
could also just send invalid event ids, combine `m.room.message` with an
annotation relation and similar nonsense variants. While this adds one more way
to do that, I don't think it matters all too much.

#### Attachement (MSC2881)

Attachements are one of the motivating usecases for this proposal. They allow a
client to pull multiple media events together into a gallery with a description.
Obviously you want to be able to edit that description or reply with such a
"Gallery". You might want to do that in a thread. But sending one as a reaction
probably makes very little sense.

#### Conclusion

Most combinations are very simple and somewhat orthogonal. Clients can decide,
which combinations they want to support. In some cases they might want to
validate a minimal sensible set of supported combinations on parsing, but even
if they don't, UI restrictions will in most cases lead to a sensible solution.
There are a few edge cases, that can be abused, but the impact of that is
minimally bigger of just combining invalid event type and `rel_type` or sending
otherwise invalid data.
