# MSC2929: Interaction events

Interaction events are intended to create a standardised way for bots or other third party applications
to interact with other users. IRC, Telegram, Discord solve this using slash commands in the user side.

## Proposal

There are many possibilble subtypes of interaction events that could be used, under `m.room.interaction`
umbrella type. Precise subtypes and response flows are left implementation defined in the client side.
Servers are not expected to aggregate multiple interaction events into a single interaction event.

There are three basic fields, however, implementations are allowed to arbitrarily add more fields:
* itype, modelled after msgtype of `m.room.message`, but exact types are implementation defined
* body, where the request body would be contained
* target, the expected responding user

An interaction initiation example:
```json
{
  "type": "m.room.interaction",
  "content": {
    "itype": "m.command",
    "body": "help",
    "target": "@example:example.com"
  }
}
```

Although the example contains a text command, a menu or some other means of sending interactions
are also allowed.

Redacting an interaction event shall not undo the effect caused by event that has been redacted.
This is intentional as interactions are allowed to create irreversible side effects outside Matrix.
Interactions should be responded by `target` users if and only if they understand the interaction
body. 

Presentation of interactions to users are left implementation defined.

## Potential issues

No known issues at the time of writing.

## Alternatives

Having each bot create own event type for interactions: Which is entirely possible given the extensible
nature of Matrix, however, this will constrain the support of such events to event.

## Security considerations

No issues foreseen.

## Unstable prefix

No implementations yet.
