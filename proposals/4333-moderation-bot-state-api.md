# MSC4333: Room state API for moderation bots

Moderation bots such as [Draupnir](https://github.com/the-draupnir-project/Draupnir), [Meowlnir](https://github.com/maunium/meowlnir),
and [Mjolnir](https://github.com/matrix-org/mjolnir) typically have the same basic functions relevant
to this MSC's interests:

* When a ban recommendation is published to a watched [policy room](https://spec.matrix.org/v1.15/client-server-api/#moderation-policy-lists),
  the bot bans that user/server.
* Publishing to policy rooms, hiding the original moderator which added the recommendation (a feature).
* Redacting events sent by users either as part of a ban or as a once-off action.
* Kicking users from rooms.

Other functionality is common among these bots, such as an ability to add "protections" which monitor
for certain classifications of spam and taking appropriate action, but are generally out of scope for
the first cut of this proposal. A future proposal may build upon this MSC to add more functionality
as needed.

To exercise the above functionality, a moderator typically needs to encounter problematic content,
record/copy some details of the user or permalink, find their bot's "management room", formulate the
command (complete with typos), and send it. Instead, a desirable workflow would be to have the moderator's
ban, redact, and kick buttons already present in their client's UI actually route to the bot's management
room, reducing the need for context switching and typos in commands.

This proposal achieves that button rewiring by leveraging [MSC4332](https://github.com/matrix-org/matrix-spec-proposals/pull/4332)
bot commands and a new state event published in the moderation bot's management room.


## Proposal

A new state event is added: `m.bot.moderation_config`. Like and for the same reasons in MSC4332, the
`state_key` is the bot's user ID. If the user ID referenced by the state key is not present in the
room where the moderation config event is sent, that event does not apply.

The `content` for the new event fits the following implied schema:

```jsonc
{
  // The room IDs the moderation bot "protects". Typically, these are the rooms where policy recommendations
  // are automatically applied.
  "protected_room_ids": [
    "!room:example.org"
  ],
  "commands": {
    // These are the MSC4332 commands the client UI can use instead of the normal Client-Server API,
    // discussed later in this proposal. If the bot doesn't support a command listed below, it elides
    // the field.

    "ban": {
      // MSC4332 command syntax to use. Must be a known command for the same bot in the management room.
      // Required field.
      "use": "modbot ban {userId} {list} {reason}", // This is an example! A bot may require a user permalink instead.

      // Defaults for variables the client probably won't be aware of, but should specify.
      "prefill_variables": {
        "list": "code_of_conduct"

        // Note: it's expected that clients understand `reason` in addition to the predefined variables
        // in MSC4332.
      }
    },
    "kick": {
      "use": "modbot kick {userId} {reason}" // This is an example! A bot may ask for a {roomId} too.
      // if `prefill_variables` isn't supplied, it's assumed to be `{}`.
    },
    "redact_event": { // redact a specific event
      "use": "modbot redact {permalink}" // This is an example! A bot may also accept {roomId} {eventId}.
    },
    "redact_user": { // redacts most/all of the user's past messages in the room
      "use": "modbot redact {userId} {roomId} {limit}", // This is an example! The {roomId} may not be present.
      "prefill_variables": {
        "limit": "1000" // if the client knows better, it may populate this differently.
      }
    }
  }
}
```

**Note**: The syntaxes shown are examples, not requirements. Bots may use a variety of different command
variables, though the above are roughly common to moderation bots. For example, a bot's `kick` command
may require a `{roomId}` or `{permalink}` or another custom (prefilled) variable too. Clients MUST NOT
assume that the example commands are the only variables they need to support.

Clients SHOULD look for the `m.bot.moderation_config` state event, and when the user attempts to perform
one of the actions described by `commands` in one of the `protected_room_ids`, it asks if the user would
prefer to use the bot's management room (where the client found the moderation config) instead. If the
user chooses to use the management room, the client sends the command specified (if it can) to the
management room, using the existing context it already has.

For example, if the user is trying to ban another user from a protected room, the client might show
a checkbox saying "Use 'Moderation Internal' to ban this user". If checked when the user submits the
dialog, the `reason` and user ID the user is trying to ban will be converted to a command which is
then sent to the management room (instead of calling the `/ban` API, for example).


## Potential issues

* *Technically* reasons are optional command variables for moderation bots, but MSC4332 can't express
  that. It's assumed that bots are tolerable to `reason` being an empty string.

* This setup implies that the moderation bot will hide the user's identity as best it can, but this
  is not guaranteed. It may be desirable to have an explicit `actions_performed_as: "caller"` field
  in the config event to clarify when the bot won't be anonymizing the caller. Clients can then use
  this to reassure users that the ban will appear as issued by the bot rather than themselves.

* The Community Moderation Effort (CME) folks have access to moderation bots and policy lists which
  the human operators know ultimately protect a given room, but the bots/list can't reasonably say
  they do in fact protect the room ID. Though not formally part of this proposal (**TODO**: Yet?),
  it's suggested that clients maintain an `m.bot.moderation_config` account data event with `content`
  of `{"management_room": "!manage:example.org"}`. The choice of management room would then instruct
  the client to use that room's `m.bot.moderation_config` state event, ignoring the `protected_rooms`
  array (instead, treating *all* rooms the client sees as "protected" by that management room).


## Alternatives

Instead of a state event within the bot's management room, the bot could be asked to maintain a space
with the same moderation config (minus `protected_rooms` - the space's children would be assumed as
protected). When the user is viewing rooms "inside" that space, their buttons would be (optionally?)
rewired to use the bot's management room, as described by this proposal. This solution is currently
discounted as it's unclear that the current implementation of spaces within the client ecosystem fits
this kind of use case.

MSC4332's event templates idea could additionally be used to send policy-like events to either the
management room or to the policy list itself (if state events become allowed).


## Security considerations

Clients SHOULD clearly show which room is going to be used to send the command. A malicious room may
try to redirect ban commands away from the user's actual management room. Clients SHOULD additionally
consider the case where multiple rooms advertise themselves as management rooms for a specific protected
room, possibly by showing multiple checkboxes on an action's confirmation dialog.

In addition to clearly showing the room where commands will be sent, clients SHOULD clearly show the
bot's user ID to further confirm that they are using the expected bot.


## Unstable prefix

While this proposal is not considered stable, implementations should use `org.matrix.msc4333.moderation_config`
in place of `m.bot.moderation_config` throughout this proposal.


## Dependencies

This proposal depends on [MSC4332: In-room bot commands](https://github.com/matrix-org/matrix-spec-proposals/pull/4332).
