# MSC4565: Share additional invite state

When a Matrix client receives an invitation, it gets access to `InviteState` containing a list of specified
`StrippedStateEvent`s. The minimal set of events that should be included are currently part of the spec.

As the inviter, I want to be able to share additional (stripped) state events to the invitee. As an example, a user
wants to send some calendar event information, so the invitee can decide to accept or decline it based on the upcoming
event
data.

## Proposal

This proposal adds a new optional request body parameter `shared_state` to
`POST /_matrix/client/v3/rooms/{roomId}/invite`. This parameter is a map of event types to a list of `state_key`
strings.

This parameter defines what state should be shared with the invitee and overrides the current behavior of sharing only
the default set of events defined by the spec. If the `shared_state` parameter is omitted, the current specified
behavior applies.

It is possible to share all `state_key`s for a specific event type by using the wildcard `*`.

Example:

```json
{
  "reason": "Welcome to the daily!",
  "user_id": "@dino:connect2x.de",
  "shared_state": {
    "m.room.create": [
      ""
    ],
    "m.room.name": [
      ""
    ],
    "m.room.avatar": [
      ""
    ],
    "de.connect2x.custom": [
      "dino",
      "unicorn"
    ],
    "de.connect2x.m.jscalendar.event": [
      "*"
    ]
  }
}
```

To ensure backward compatibility with the current specification, the `shared_state` object MUST contain the
`m.room.create` event type (with an empty string key as per current specification).

## Potential issues

## Alternatives

## Security considerations

## Information Leakage

Because this proposal allows for a much broader range of state to be attached to an invitation, there is an increased
risk that an inviter may accidentally include sensitive metadata or share them with the wrong invitee. While similar
risks exist with the current specification, the increased flexibility of this proposal expands the potential scope of
such accidental disclosures.

## Denial of Service (DoS)

Including a large amount of state in an invitation increases the size of the invitation object. While these are
"stripped" events, a malicious or poorly configured client could attempt to send a massive amount of data, increasing
the overhead for the server and the receiving client during the initial sync/room loading process. Clients should use
sync filters to only receive events they are interested to. Servers should implement validation to ensure that the
`shared_state` provided is within reasonable bounds of size and complexity to prevent resource exhaustion.

## Unstable prefix

- `shared_state` -> `de.connect2x.msc4565.shared_state`

## Dependencies
