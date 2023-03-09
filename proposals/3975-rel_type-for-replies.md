# MSC3975: rel_type for Replies

Aggregation of child events ([Aggregations](https://spec.matrix.org/v1.6/client-server-api/#aggregations), 
[Relationships API](https://spec.matrix.org/v1.6/client-server-api/#aggregations)) 
has proven itself useful for features such as Threads and Reactions. Clients are unable to access Rich Replies via the Relationships API,
complicating that task of finding replies to an event. This proposal seeks to
solve this problem by including Rich Replies among the relationship types that use rel_type.

This proposal is related to the merged [MSC2675](https://github.com/matrix-org/matrix-spec-proposals/pull/2675) which defines APIs to let the server calculate
aggregations on behalf of the client.


## Proposal

Rich Reply events should include a `rel_type` field with a new value specific to replies.

For example, a reply might look like:

```json
{
  "content": {
    "body": "> <@imbev:matrix.org> Original Message\n\nReply Message",
    "format": "org.matrix.custom.html",
    "formatted_body": "<mx-reply><blockquote><a href=\"https://matrix.to/#/!OAWeIkjdeYXEnQPoWC:matrix.org/$ju0-ipo32h_2eaD1JBVUmwayiAHKcu2eq21PX15E1Zg?via=matrix.org\">In reply to</a> <a href=\"https://matrix.to/#/@imbev:matrix.org\">@imbev:matrix.org</a><br>Original Message</blockquote></mx-reply>Reply Message",
    "m.relates_to": {
      "m.in_reply_to": {
        "event_id": "$ju0-ipo32h_2eaD1JBVUmwayiAHKcu2eq21PX15E1Zg"
      },
      "event_id": "$ju0-ipo32h_2eaD1JBVUmwayiAHKcu2eq21PX15E1Zg", // Proposed additions to reply event
      "rel_type": "m.reply" //
    },
    "msgtype": "m.text"
  },
  "origin_server_ts": 1678300521134,
  "sender": "@imbev:matrix.org",
  "type": "m.room.message",
  "unsigned": {
    "age": 434,
    "transaction_id": "m1678300520742.91"
  },
  "event_id": "$DplZPaY06i_BcWs0I_8jRxWhVoFvhMFlrBj5q41GVvk",
  "room_id": "!OAWeIkjdeYXEnQPoWC:matrix.org"
}
```

For compatibility, the `m.in_reply_to` field should be remain, and 
a new `event_id` field added for consistency with other relationship types.


## Potential issues

There is a possible conflict with threads, as a messages in threads use `m.thread`
as the `rel_type`.


## Alternatives

An alternative solution would be to add a new endpoint specifically finding an 
event's replies. This would avoid conflicts with `m.thread`, however may be more
confusing due to the presence of the current Relationships API.



