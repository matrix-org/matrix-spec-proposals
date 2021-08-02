# MSC0000: How to count unread messages

## Preface

It all started when the author of this MSC tried to count unread messages on
the client side so that the result matches the `notification_count` number
returned by `/sync`. After a couple of unsuccessful attempts to match it
it occured to me that, aside from the generic guidance in The Spec that
the unread notifications are counted from the read receipt and only include,
well, messages(?) there's some extensive sacred knowledge regarding which
messages should be counted. I went asking around and looking into the Synapse
code, finding a particular function, the contents of which I suggest enshrining
in a canonical text for reasons described in the normative part of this MSC,
as follows.


## Introduction

The Client-Server API (CS API) and the Push Gateway API (PG API) employ
a certain counter called "the number of unread notifications". In CS API it
comes in the `/sync` response, placed under
`rooms.*.unread_notifications.notification_count`; PG API places a similar
counter but spanning all rooms in the `/notify` request body under
`notification.counts.unread`. The way this number is calculated is obscure:
you have to look at the homeserver's source code to figure out how it is
produced, bearing in mind that, despite the `notification_count` name in
CS API, it is different from the number of messages for which there's
a [Push Rule](https://spec.matrix.org/unstable/client-server-api/#push-rules)
with `action` set to `notify`. There's merit therefore providing a common
"notable events" criterion, both for homeservers to calculate the unread count
uniformly but also for clients so that they could provide more accurate numbers
when it's possible and/or even customise the calculation algorithm to
users' liking.


## Proposal

It is proposed to use the following algorithm (slightly extending
[the _should_count_as_unread function in Synapse](https://github.com/matrix-org/synapse/blob/bdfde6dca11a9468372b3c9b327ad3327cbdbe4a/synapse/push/bulk_push_rule_evaluator.py#L65)
that provides a reasonable baseline) to determine whether a given event should
be included in an unread counter:

1. return false if the event is never going to come to clients, i.e., it is
   rejected or soft-failed
2. return false if the event is a room message event with
   `msgtype == "m.notice"`
3. return false if the event is redacted (only for clients)
4. return false if the event is an edit, as per the algorithm proposed by
   [MSC1849](https://github.com/matrix-org/matrix-doc/pull/1849), i.e. with
   `rel_type == "m.replace"` in its content (see below)
5. return true if the event content has a non-empty `body` value (see below)
6. return true if the event is a state event with one of the following types:
   `m.room.topic`, `m.room.name`, `m.room.avatar`, `m.room.tombstone`
7. return true if the event is encrypted and is not a state event (see below)
8. otherwise, return false

Homeservers can only check criteria 4 and 5 in unencrypted rooms while clients
and bridges supporting E2B can apply them in any room; rule 7 is only
applicable to cases when decryption is impossible or impractical.

Homeservers SHOULD implement the above algorithm; clients MAY implement it, in
order to report more accurate figures to the users, but are not required to,
given that the numbers produced by homeservers are in many cases good enough.


## Potential issues

In some cases counting messages on the server side may yield different results
for encrypted and non-encrypted rooms, as homeservers cannot inspect
the content to determine whether a given event should be counted. This proposal
does not try to align unread counting on client side and server side, deeming
the divergence acceptable. Shifting calculation entirely to the client side is
not friendly to mobile clients that rely heavily on push notifications; on
the other hand, mandating calculation to occur on the server side means that
clients (and bridges) won't be able to take advantage from looking into
messages.


## Alternatives

The obvious alternative is to do nothing and stay with the current unspecified
way to count unread messages. The obvious drawback of this alternative is that,
as the number of homeserver codebases grows, counting events will be done in
increasingly diverse ways, confusing users who happen to deal with several
homeservers.


## Security considerations

None that I know of.


## Unstable prefix

Since impact on the network operation from a possible change in calculation logic
in non-Synapse homeservers is negligible, no unstable prefix is suggested for
counters calculated in a new way. Just start using a common algorithm.
