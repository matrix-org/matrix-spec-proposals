# MSC4340: Prompts and partial commands for in room commands.

When composing a command, a user may not know what to provide for as an argument to a command. In
this situation, it is desirable for the client to be able to prompt the user with suggestions for
the argument. 

## Proposal

### The promptable property on parameters

Within the parameter description for a command argument, we specify a new property `promptable`
which when given the value `true` signals to clients that they may send a _partial command_ to the
bot to receive suggestions for the argument.

### The `m.bot.command_prompt` event

Consider the following command description under the context of MSC4332 and MSC4333.

```jsonc
{
  "sigil": "!",
  "commands": [
    {
      "syntax": "draupnir takedown {entity} {list} {reason}",
      "arguments": {
        "entity": {
          "m.text": [{"body": "The entity to ban"}],
        },
        "reason": {
          "m.text": [{"body": "The reason for the ban"}],
        },
        "list": {
          "m.text": [{"body": "The policy list to ban the user on"}],
          "promptable": true,
        },
      },
      "description": {
        "m.text": [{"body": "Ban a user in all protected rooms"}],
      },
    },
  ]
}
```

When a client is composing the argument for `list`, if the user is unable to make a decision for the
policy list, the client can send the following `m.bot.command`:

```jsonc
{
  "m.bot.command": {
    "syntax": "draupnir takedown {entity} {list} {reason}",
    "arguments": {
      "entity": {
        "id": "!room:example.org",
        "via": ["second.example.org"]
      },
    }
  }
}
```

The bot will then respond with an event containing an `m.bot.command_prompt` mixin:


```jsonc
{
  "body": "Please select a policy room",
  "m.bot.command_prompt": {
    "syntax": "draupnir takedown {entity} {list} {reason}",
    "arguments": {
      "entity": {
        "id": "!room:example.org",
        "via": ["second.example.org"]
      },
    },
    "suggested_arguments": {
      "list": {
        "suggested": [
          {
            "id": "!policyroom:example.com",
            "via": ["second.example.com"]
          },
          {
            "id": "!fTjMjIzNKEsFlUIiru:neko.dev",
            "via": ["neko.dev"]
          }
        ],
        "default": {
          "id": "!policyroom:example.com",
          "via": ["second.example.com"]
        }
      }
    }
  }
}
```

It is desirable that a bot can send a prompt without any prior command, so that it is possible to
create notices which prompt action.

### Client considerations

Clients should allow prompts to be cancellable.

## Potential issues

None considered.

## Alternatives

### Reaction based prompts

[Draupnir](https://github.com/the-draupnir-project/Draupnir) currently manages prompts manually by
embedding a mixin in a reply to a command event with suggestsions that can be selected by sending
a reaction that references the event.

## Security considerations

### Unsolicited prompt

Clients need to take care to make sure that the sender of the prompt matches the bot for which the
command is intended to be sent to. Otherwise clients could be tricked into sending commands by other
users.

## Unstable prefix

`m.bot.command_prompt` -> `org.matrix.msc4340.command_prompt`

## Dependencies

This MSC builds on MSC4332 (which at the time of writing have not yet been accepted into the spec).
