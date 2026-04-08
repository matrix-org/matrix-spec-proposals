# MSC4295: Bot bounce limit - a better loop prevention mechanism

## Background

Matrix is an open platform that welcomes bots and bridges. Unlike other platforms (e.g., Telegram), Matrix allows multiple bots to interact with each other, creating a unique and useful experience. However, this feature is a double-edged sword due to the risk of infinite loops between bots. A bot loop can cause an exponentially growing flood, damaging the reputation of the source homeserver and potentially leading to unintentional or intentional Denial-of-Service attacks.

Here are some examples of multi-bot interactions and their needs for loop prevention:

1. The room operator can run a "CAPTCHA bot" that screens every new member joining the room, but doesn't want these CAPTCHAs to be bridged to other platforms [[1]](https://github.com/mautrix/telegram/issues/918).
2. The room operator can run a "GitHub CI bot" that sends CI task reports, and another "URL previewer bot" that generates URL previews from the former bot's output. (It is a separate debate whether a centrally-managed URL previewer bot is more privacy-preserving than the URL preview feature provided by each member's homeserver.)
3. For a room purposed for technical support, the operator can run an AI-powered bot to automatically answer common questions. Such an AI bot is allowed to trigger other bots for certain helpful tasks.
4. The room operator can run a "UTD notification bot" that notifies room members that their messages can't be decrypted by others. However, it is very important to prevent it from replying to another bot's message.
5. When bridging rooms across three or more platforms (e.g., Matrix ⇌ Telegram ⇌ IRC ⇌ Matrix), it is necessary to make sure each bridge doesn't pick up another bridge's messages.
6. If the same bot provides native versions for multiple platforms, the room operator may want to let the bot itself provide native experiences on different platforms (e.g., `!bot help` on Matrix and IRC, `/help@bot` on Telegram, `/help` on Discord, etc.). This bot needs to bridge its outputs by itself to make command palettes work, thus it needs to inform any existing bridges to ignore its output to prevent double bridging.

Currently, it is usually a room operator's responsibility to prevent bot loops, for example, by carefully configuring each bot's ignore list, ensuring all possible outputs of one bot don't contain trigger words of another bot, and removing unauthorized bots invited by some random member. Nonetheless, a well-maintained configuration can be very fragile, and the room operator may not be able to monitor the room at all times.

The goal of this proposal is to:

1. Reduce the burden on room operators — they still carry the responsibility to prevent loops, but less effort is needed.
2. Allow bot developers to follow a standardized guideline for their bots not to cause trouble in a multi-bot environment.
3. In the event of a bot loop due to misconfiguration, ensure "specification-compliant" bots will eventually stop, giving the room operator time to react.
4. In rooms with no moderators, or even no human presence, reduce the risk that remaining bots generate an infinite amount of traffic without being noticed.
5. Promote a healthier Matrix ecosystem where multiple bots can collaborate better.
6. Be compatible with the existing `m.notice` mechanism.

The goal of this proposal is **NOT** to:
1. Prevent any malicious bot from flooding a room.
2. Prevent a bot loop from happening at all.
3. Prevent a bot loop if the bot isn't yet updated to support this new proposal.

## Existing solutions

There are four existing solutions to prevent bot loops:

1. The `m.notice` message type:

   By specification, `m.notice` messages must never be automatically responded to.

   However, there are a few disadvantages of `m.notice`:

   1. It is analogous to `m.text`, which doesn't support attached files or encrypted images.
   2. It is designed for automated messages, not bridged messages sent originally by a human.
   3. The current Matrix specification doesn't define whether bridges should forward `m.notice` to different platforms.
   4. It prevents multiple bots from collaborating. As shown above, bot collaboration can be helpful.
   5. It is difficult to decide whether an AI-powered bot should use `m.notice` or `m.text`. —Should we give it the ability to interact with other bots?
   6. `m.notice` is often displayed in a distinct manner, such as with a different text color, which, depending on the semantics of the message, may not always be ideal.

2. [MSC3955](https://github.com/matrix-org/matrix-spec-proposals/pull/3955): Extensible Events - Automated event mixin

   It is similar to `m.notice` but it supports multimedia messages. This solution still bears the same five remaining disadvantages of `m.notice`.

3. Vendor-specific tags:

   For example, Mautrix attaches the `fi.mau.double_puppet_source` tag to messages sent by a reverse puppet account. This tag is not visible to humans, but can be inspected through "View JSON Source." Mautrix won't forward a message if the sender is a reverse puppet account managed by the same Mautrix instance and the message has such a tag [[2]](https://github.com/mautrix/python/blob/8eac9db01e2b5fd9a30620bcbc8ebbaa36c71ecb/mautrix/bridge/matrix.py#L960-L964).

   There are two concerns of vendor-specific tags:

   1. One bot developer cannot expect all other bot developers to support their custom tag unless it's standardized.
   2. Vendor-specific tags exist for a reason: they sometimes serve a different purpose than this proposal and can't replace each other. For example, `fi.mau.double_puppet_source` prevents intra-bot loops — double puppeting's unique challenge, instead of inter-bot loops.

4. An ignore list:

   In the configuration file of a Matrix bot with such a feature, the operator can specify a list of users whose messages are ignored by the bot.

   However, a valid ignore list that allows multi-bot collaboration without bot loops is fragile. Adding new bots to the room, or adding new features to an existing bot, may lead to new bot loops.

   The new proposal won't replace ignore lists. Instead, it aims to complement the mechanism, enabling new creative use cases of Matrix bots.

## Proposal: `m.bounce_limit`

I propose a new tag `m.bounce_limit` inside the **unencrypted** `content` subobject of any message-like JSON objects, including `m.room.message`, `m.sticker`, and `m.room.encrypted`. (The debate on whether it should reside in the **encrypted** `content` will be discussed in the [Alternatives](#alternatives) section below.)

A valid `m.bounce_limit` value can be in either of the following forms:

1. Missing.
2. The number 1.
3. An integer between and including 2 and 2^53-1.

These are invalid forms, and their normalization rules upon receiving:

1. The number 0, which should be treated as missing. (This design is to simplify the development of bots in certain programming languages, such as Go.)
2. Floating-point numbers, which are not permitted by the Matrix protocol.
3. Any other values, including but not limited to negative numbers, strings, etc., which should be treated as the number 1.

Here are two example events:

```json
{
  "content": {
    "body": "It works!",
    "m.bounce_limit": 3,
    "m.mentions": {},
    "m.relates_to": {
      "m.in_reply_to": {
        "event_id": "$BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"
      }
    },
    "msgtype": "m.notice",
  },
  "sender": "@bot:example.com",
  "type": "m.room.message",
  "event_id": "$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
  "room_id": "!AAAAAAAAAAAAAAAAAA:example.com"
}
```

```json
{
  "content": {
    "algorithm": "m.megolm.v1.aes-sha2",
    "ciphertext": "11Y45j14S19n19P81i0",
    "device_id": "AAAAAAAAAA",
    "m.bounce_limit": 3,
    "m.relates_to": {
      "m.in_reply_to": {
        "event_id": "$BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"
      }
    },
    "sender_key": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "session_id": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
  },
  "sender": "@bot:example.com",
  "type": "m.room.encrypted",
  "event_id": "$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
  "room_id": "!AAAAAAAAAAAAAAAAAA:example.com"
}
```

The behavior of a client:

1. If a message is sent by a human, `m.bounce_limit` is RECOMMENDED to be missing. In the case when the definition of "sent by a human" is ambiguous in certain applications, a message is considered equivalently "sent by a human" only if there is absolutely no risk of bot loops except for software malfunctions. In other words, bridged messages MUST NOT be considered "sent by human."
2. A bot supporting `m.bounce_limit` MUST define its own `max_outgoing_bounce_limit` value, which does not need to be shared.
   1. It MUST be an integer between and including 1 and 2^53-1.
   2. We RECOMMENDED that a bot allows its operator to configure the `max_outgoing_bounce_limit` to suit their needs.
   3. We also RECOMMEND `max_outgoing_bounce_limit` default to 1, or in case of a special reason (e.g., due to the bot's job), no more than 3.
3. A bot is allowed to process any incoming messages, but MUST NOT send response messages (including stickers) to any incoming messages:
   1. with an `m.bounce_limit` of 1 after normalization, or
   2. whose `m.bounce_limit` is missing after normalization AND with a `msgtype` of `m.notice`, or
   3. whose `m.bounce_limit` is missing after normalization AND the bot is unable to decrypt the message.
4. When the bot sends a response message (including stickers), it MUST set its outgoing `m.bounce_limit` to `min(incoming_bounce_limit - 1, max_outgoing_bounce_limit)`, where `incoming_bounce_limit` is the `m.bounce_limit` value of the incoming message, or `max_outgoing_bounce_limit` if the `m.bounce_limit` value of the incoming message is missing.
5. When a bot sends an outgoing message (including stickers) that is not a response to any incoming message, it MUST set its outgoing `m.bounce_limit` to `max_outgoing_bounce_limit`.
6. The bot SHOULD use `m.notice` unless there is a reason not to. Examples of such reasons are listed in the [Existing solutions](#existing-solutions) section.
7. Bridges consume one bounce similar to bots. In other words, if a message MUST NOT be responded by a bot, it MUST NOT be forwarded by a bridge either.
8. If the sole purpose of an SDK or library is to develop bots or bridges, and if it is convenient to do so, it SHOULD make `m.bounce_limit` support on by default.

Compatibility advantages of this design:

1. Most clients don't need to be aware of `m.bounce_limit`, thus requiring no modifications.
2. The semantics of `m.notice` is preserved.

## Potential issues

There are a few issues to consider:

1. If the response of a bot is relevant to multiple incoming messages, it is not defined which message determines `incoming_bounce_limit`.

   Potential definitions could be the minimum value, the maximum value, or the last message's value. The bot developer also needs to pay special attention if some, but not all, of the relevant incoming messages have an `m.bounce_limit` of 1.

2. If the response of a bot is not a message (or a sticker), the behavior is not defined.

   For example, if the bot's job is to change the room name, room topic, or pinned messages, this proposal does not define its loop prevention behavior.

   Two bots racing with each other changing room states would surely cause greater havoc, but we can't analyze such a hypothetical problem until it is observed in practice.

3. How `m.bounce_limit` propagates across bridges is undefined.

   Some platforms, such as Telegram, already prevent bot loops by forbidding bots from seeing each other's messages.

   Some other platforms, such as IRC, have bot loops as a long-standing problem. We don't aim to solve other people's problems.

   If a platform has a similar bounce limit mechanism, the bridge developer SHOULD try to pass the bounce limit value across the bridge as `m.bounce_limit - 1`.

   Or, if a platform has an equivalent of `m.notice`, the bridge developer SHOULD try to map messages with `m.bounce_limit` of 2 to the `m.notice` equivalent of that platform.

4. A probable implementation pitfall of unconditionally ignoring messages with an `m.bounce_limit` of 1.

   If a bot's job is to prevent flooding or remove spam messages, it MUST NOT ignore messages based on their `m.bounce_limit` values.

   If the incoming relevant message has an `m.bounce_limit` of 1, the bot developer MUST judge wisely whether to let the bot perform its work quietly, but MUST NOT allow the bot to respond with a message.

## Alternatives

There are three alternative considerations:

1. Whether to put `m.bounce_limit` into the **encrypted** `content`.

   Regarding this question, here are my reasons:

   1. `sender` and `m.relates_to` are unencrypted. The information that can be inferred from `m.bounce_limit` is the same as what can be inferred from analyzing `sender` and `m.relates_to`.
   2. `m.bounce_limit` is similar to TTL in IPv4 or Hop Limit in IPv6, which are unencrypted even under IPsec encryption.
   3. The occurrence of bot loops does not require messages to be decrypted successfully.
   4. Putting `m.bounce_limit` in the cleartext allows a useful application of "UTD notification bot," described in the [Background](#background) section.

   In my personal experience, I set all my rooms to end-to-end encrypted. Such a "UTD notification bot" reduces the friction of this switch, as members can be notified of a potentially misconfigured client or an E2EE-incompatible homeserver almost immediately. My room members were skeptical before the E2EE switch but became satisfied afterward. By allowing more large-scale rooms to be encrypted, I believe the overall privacy of the Matrix ecosystem increases.

   However, the design of `m.bounce_limit` being in the cleartext relies on the fact that `m.bounce_limit` does not leak new information other than what can be inferred from `sender` and `m.relates_to`. Feel free to comment your opinions if I missed anything!

2. Whether to introduce a structure for data exchange between bots, for example `m.bot_data_exchange`, and make `bounce_limit` a part of it.

   Regarding this question, here are my reasons:

   1. It is impossible to standardize `m.bot_data_exchange`, because it has to be flexible enough to accept any valid JSON. Vendor-prefixed tags should be a better choice for inter-bot data exchange.
   2. Obviously, `m.bot_data_exchange` has to be encrypted, while I propose that the bounce limit be unencrypted.

3. Whether we should simply ban inter-bot interaction.

   As Matrix is an open platform, this is impossible. Additionally, the ability to perform bot-to-bot interaction sets Matrix bots apart from bots on other platforms, such as Telegram bots.

   Inter-bot interaction even enables some creative use cases, for example, allowing bots that primarily serve users on other platforms to use a bot-only Matrix room as an out-of-band communication channel.

## Security considerations

1. Denial-of-Service

   Bot loops can cause intentional or unintentional Denial-of-Service attacks. If among two bots, one supports `m.bounce_limit` and the other doesn't, there could be a risk of causing bot loops, which leads to a Denial-of-Service. However, this proposal doesn't increase the severity from its previous level. A room operator's typical responsibility of keeping an eye on the bots hasn't changed, therefore, the room operator should be aware which bots don't support `m.bounce_limit` and configure accordingly.

2. Information leakage from the cleartext `m.bounce_limit`.

   This is discussed in the [Alternatives](#alternatives) section.

3. Bypassing room moderation bots due to implementation pitfalls.

   This is discussed in the [Potential issues](#potential-issues) section.

## Unstable prefix

When implementing this proposal, the unstable tag `io.github.m13253.bounce_limit` MUST be used.

| Proposed stable tag name | Unstable tag name               |
|--------------------------|---------------------------------|
| `m.bounce_limit`         | `io.github.m13253.bounce_limit` |

## Unstable Implementations

This proposal requires no client modification.

However, SDKs, bots, or bot frameworks can implement an unstable version of the proposal prior to its official acceptance.

## Dependencies

This MSC does not depend on any other MSCs that are yet to be accepted.
