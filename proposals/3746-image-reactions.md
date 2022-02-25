# MSC3746: Render Images in Reactions

Many messaging services such as Slack and Discord allow for custom images for reacts, rather than only standard emoji. Currently Element will only show the plain text of the reaction key.  In order to achieve parity with other messaging services and satisfy customer needs, we must implement a way to have reactions which can be any image, rather than one of the unicode emojis.

This proposal is concerned only with providing an event format which can describe image reactions.  Any way for users to compose and send these reactions such as pickers and image packs is out of scope.

## Proposal

Currently, reactions are implemented as room events which have a relationship with the event they are reacting to.  Identical reactions by different users are grouped together by the reaction key, and the reaction key (text/emoji) is displayed under the related message.

An example of a reaction, which displays 😀
```json
{
  "type": "m.reaction",
  "sender": "@testme:localhost:8008",
  "content": {
    "m.relates_to": {
      "rel_type": "m.annotation",
      "event_id": "$hPRRsFL03pNRE2tnmzzqyP6OXofz-bbsrQbRWJDA4p0",
      "key": "😀"
    }
  },
  "origin_server_ts": 1645830754708,
  "unsigned": {
    "age": 28,
    "transaction_id": "m1645830754585.0"
  },
  "event_id": "$8dZO0nnIoz-uWyDfevNcaGcg5p6e7oK7CoKOwe-aWTM",
  "room_id": "!uLFjhtpHuebWoCiyvz:localhost:8008"
}
```

In order to describe a reaction with an image, we simply include an mxc url and optionally [ImageInfo](https://github.com/matrix-org/matrix-doc/blob/f8b83b7fb1194ab48ee3461185c4764ebbfecc68/data/event-schemas/schema/core-event-schema/msgtype_infos/image_info.yaml) in the event content

content of an image reaction:
```json
  "content": {
    "m.relates_to": {
      "rel_type": "m.annotation",
      "event_id": "$hPRRsFL03pNRE2tnmzzqyP6OXofz-bbsrQbRWJDA4p0",
      "key": "😀"
    },
    "url": "mxc://matrix.org/VOczFYqjdGaUKNwkKsTjDwUa",
    "info": {
      "w": 256,
      "h": 256,
      "size": 214537,
      "mimetype": "image/png",
      "thumbnail_url": "mxc://matrix.org/VOczFYqjdGaUKNwkKsTjDwUa",
      "thumbnail_info": {
        "w": 256,
        "h": 256,
        "size": 214537,
        "mimetype": "image/png"
      }
    }
  }
```

### Server side aggregation
Server side aggregation will remain unchanged, where only the keys and counts of those keys are aggregated.  In the case where the client is unable to use client-side aggregation and must display reactions based on the server-side aggregation, then it will fallback to displaying only the key for reactions.

Element web and desktop do not make use of server-side aggregation for reactions, so they are currently unaffected by this.

### Fallback
Older clients will simply display the reaction emoji or plaintext.  If an older client also clicks the reaction, it will send a reaction event without the image content.  Other clients must check all aggregated events to find which ones include the image.  If all newer clients unreact, then the image will be lost and the reaction will revert to plaintext/emoji.

## Potential issues

It's possible that different users will send reactions with different images under the same reaction key, either due to malicious action or collisions.  Reaction senders must take this into account and use a key that will not collide with previously existing reactions.

This would remove the chance of mismatches between key and image, but would not give an experience to older clients.

## Alternatives

Instead of including the image information in the event content, we could include everything necessary in the relation key.  For example the key could be an mxc url, json, markdown, or reference to an external data source (such as an image set-as-room).

