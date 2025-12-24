# MSC0000: Simplified in-room bot commands

> [!NOTE]
>
> This proposal is a simplification of
> [MSC4332: In-room bot commands](https://github.com/matrix-org/matrix-spec-proposals/pull/4332)
> that specifies only an object format for bot commands, and keeps syntax and
> command interaction implementation dependant.

Many bots on Matrix have a command interface consisting of `!botname <command>`,
and have a pretty long help menus which can make it difficult to find the right
command. Many clients already have a concept of "slash commands" which are
[desirable to reuse](https://github.com/matrix-org/matrix-spec/issues/93) and
[come up occasionally](https://github.com/matrix-org/matrix-spec/issues/2170) -
finding a way to populate this feature with bot-specific details is beneficial.

This proposal suggests that bots maintain a state event in the rooms it joins to
advertise available commands. This does require that bots need power levels to
maintain their state event though, so bots without such power level (or are
looking to maintain backwards compatibility with clients which don't support
this MSC) will need to rely on the existing `!botname help` convention.

## Proposal

### Command description

A new state event type is introduced: `m.bot.commands`. The state key is the
bot's own user ID to prevent other users/bots from changing it (this is a
feature of rooms: see
[`state_key`](https://spec.matrix.org/v1.15/client-server-api/#room-event-format)).

When presenting command options to users, clients SHOULD use this event to
suggest per-bot commands too, unless the user ID implied by the `state_key` is
not joined to the room. (Note that this means "invalid" state keys get treated
as unjoined users: an empty string, "not_a_user_id", etc can't join rooms, but
`@bot:example.org` can.)

The `content` for such an event fits the following implied schema:

TODO: A single event for all commands is bad and we will probably easily exhaust
that with Draupnir.

TODO: Variadic arguments should be replaced with an array schema.

TODO: Enum should be replaced with union and literal types.

TODO: number instead of integer type

```jsonc
{
  "sigil": "!", // Defaults to `!` if not specified. Clients can use this to show the user a consistent
  // experience in the form of slash commands, but ultimately send the command as a
  // sigil-prefixed string to the room. Eg: the UI might say `/botname`, but the command
  // becomes `!botname` upon sending.
  "commands": [
    {
      "designator": ["ban"],
      "parameters": [
        {
          "key": "target_room",
          "type": "room_id",
          "description": {
            // Descriptions use m.text from MSC1767 Extensible Events to later support MSC3554-style translations.
            // See https://spec.matrix.org/v1.15/client-server-api/#mroomtopic_topiccontentblock
            // See https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/1767-extensible-events.md
            // See https://github.com/matrix-org/matrix-spec-proposals/pull/3554
            "m.text": [{ "body": "The room ID" }],
          },
        },

        {
          "key": "timeout_seconds",
          "type": "integer",
          "description": { "m.text": [{ "body": "The timeout in seconds" }] },
        },

        {
          "key": "apply_to_policy",
          "type": "boolean",
          "description": {
            "m.text": [{ "body": "Whether to apply this to the policy" }],
          },
          // This argument is not required
          "required": false,
        },

        // The final argument is variadic in this case, but doesn't need to be.
        {
          "key": "target_users",
          "type": "user_id",
          "description": { "m.text": [{ "body": "The user ID(s)" }] },
          "variadic": true, // can only apply to the last argument. Default false when not supplied.
        },
      ],
      "description": {
        // We also use m.text here for the same reason as the argument descriptions above.
        "m.text": [{ "body": "An example command with arguments" }],
      },
    },
  ],
}
```

A client may show the arguments and commands similar to Discord:

![](./images/4332-discord-example.png)

#### Invariants of command descriptions

- A command description with parameters that have duplicate keys is invalid and
  the command SHOULD be hidden by clients.

- The position of parameter descriptions in the _parameters_ property that are
  _required_ is significant and clients SHOULD use the same order when prompting
  for arguments.

- The position of parameter descriptions that are not _required_ is not
  significant.

### Command invocation

When the user sends the command, the client creates either an `m.room.message`
or an `m.room.bot.command` event with the following `content` shape:

```jsonc
{
  // body is client supplied and may not match at all with the bot's fallback syntax.
  // body may be omitted entirely in an `m.room.bot.command`.
  "body": "@bot:example.org ban !room:example.org 42 true @alice:example.org @bob:example.org",
  "msgtype": "m.text",

  // Mentions should always be added, to lower the chances of command conflicts.
  // Bots SHOULD look for mentions where possible to avoid accidental activations.
  "m.mentions": {
    "user_ids": ["@bot:example.org"], // should be a single element array, containing the bot's user ID
    // from the `m.bot.commands` state event's `state_key` (or `sender`).
    // Note: doesn't include other users which may be referenced by the
    // command being sent, such as via `user_id` arguments.
  },

  // This is a new content block so bots don't *need* to do string unpacking when
  // commands are sent this way. Bots may still need to unpack `body` when users
  // send commands manually or without client support.
  "m.bot.command": {
    "designator": ["ban"],
    "arguments": {
      // These are just the arguments and their user-supplied values.
      "room_id": {
        // Room IDs are special because they can carry routing information too.
        // Object types have a type specifier.
        "id": "!room:example.org",
        "via": ["second.example.org"], // Optional, but recommended.
        "type": "room_id",
      },
      "timeout_seconds": 42, // integers and booleans use appropriate value types (converted from (probably) strings)
      "apply_to_policy": true, // tip: clients can convert user input like "yes" to booleans
      "users": ["@alice:example.org", "@bob:example.org"],
    },
  },
}
```

Bots can then respond however they normally would to the command input.

TODO: I don't know if this text below about conflicting commands is even
relevant. Especially if we are going to make the descriptions go in one event
each and have a `state_key` of `hmac_sha256(mxid, ...designator_parts)`

Clients SHOULD be aware that some bots may attempt to create conflicts with
built-in commands or other bots. Where conflicts with built-in events exist,
clients SHOULD NOT show the bot's option to the user. Where conflicts with other
bots exist, clients SHOULD show the bot's name/user ID in the autocomplete text.
For example, "@Giphy /gif {search}". Clients MAY wish to always disambiguate
commands like this to avoid future conflicts with built-in commands. From an
implementation perspective, clients might cause their built-in commands to
always take precedence over any bot's commands to avoid users becoming confused.

### Type schema

TODO: distinction of room_id, alias, event AND permalink seems like a disaster,
each of these should be permalinks. And permalinks should be provided in object
format like the room_id was.

The following are the predefined `types` for an argument:

- `string` - An arbitrary string.
- `integer` - An arbitrary whole number. May be negative or zero.
- `boolean` - `true` or `false` literal.
- `user_id` - Must be a valid
  [user ID](https://spec.matrix.org/v1.15/appendices/#user-identifiers) for the
  room version.
- `room_id` - Must be a valid
  [room ID](https://spec.matrix.org/v1.15/appendices/#room-ids).
- `room_alias` - Must be a valid
  [room alias](https://spec.matrix.org/v1.15/appendices/#room-aliases).
- `event_id` - Must be a valid
  [event ID](https://spec.matrix.org/v1.15/appendices/#event-ids).
- `server_name` - Must be a valid
  [server name](https://spec.matrix.org/v1.15/appendices/#server-name).
- `permalink` - Must be a valid
  [permalink URI](https://spec.matrix.org/v1.15/appendices/#uris) (either
  `matrix.to` or `matrix:`) for an event ID.

**Tip**: Clients can accept a wider variety of inputs for some types, provided
they reduce them down to the expected value types when sending the command. For
example, accepting a room permalink for a `room_id` type, or "yes" in place of
`true` for a `boolean`.

## Extensions

The following extensions/features are best considered by future MSCs:

- Specifying a minimum power level required to send a command, to hint to users
  that a command may be unavailable to them. This wouldn't be enforced by auth
  rules, but clients can stop a lot of the accidental usage if they know the
  power level the caller must have.

- Specifying a non-`m.room.message` event template to send instead. This could
  be useful if the bot wants to minimize "visible" traffic in the room or has
  custom event types it wants to use. In future, being able to specify
  extensible event content blocks which should be added to the resulting event
  may be a better option. In either case, bots should not be able to cause users
  to send state events to prevent bots from tricking users into changing power
  levels, join rules, etc.

- Support for non-text-like arguments like images, files, etc.

- Some predefined validation on arguments, like a range for integers or
  maximum/minimum length of strings.

## Potential issues

- Using state events limits a bot's ability to advertise commands if it isn't
  given power to do so.

## Alternatives

- Not using state events would work, but can be tricky to manage. This proposal
  fills a gap until proposals which solve the problem space more completely are
  written and proven by implementation. Sticky events maybe?

## Security considerations

Mentioned in the proposal, clients should be explicitly aware that bots may try
to create confusion for users and override built-in commands or another bot's
commands. For example, a bot may advertise a `myroomnick` command which leads to
the client's functionality not working as expected. Clients should be taking
measures to minimize this confusion from happening.

## Unstable prefix

While this proposal is not considered stable, implementations should use
`org.matrix.msc0000.commands` in place of `m.bot.commands` and
`org.matrix.msc0000.command` in place of `m.bot.command`.

## Dependencies

This proposal has no direct dependencies, but benefits more strongly from the
following Extensible Events MSCs:

- [MSC1767 (accepted)](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/1767-extensible-events.md)
- [MSC3554: Translatable Text](https://github.com/matrix-org/matrix-spec-proposals/pull/3554)
