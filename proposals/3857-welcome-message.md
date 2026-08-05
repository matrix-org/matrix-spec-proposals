# MSC3857: Welcome messages/screening

Many communities are interested in ways to show a README-style message to new users, giving further
context for how the community works, what sort of rules there may be, etc. Discord takes this a step
further by [requiring users to accept](https://support.discord.com/hc/en-us/articles/1538570466882-Rules-Screening-FAQ)
the dialog - while it is *possible* for Matrix to enforce this, this MSC deliberately leaves this as
an implementation detail or for a future MSC to consider. Some ideas are covered in the Future
Considerations section of this proposal, however.

## Proposal

We introduce a new state event, `m.room.welcome`, which uses [MSC1767 - Extensible Events](https://github.com/matrix-org/matrix-spec-proposals/pull/1767)
to create a renderable `m.message`-like event, similar to [MSC3765 - Rich text topics](https://github.com/matrix-org/matrix-spec-proposals/pull/3765).

Such an event would look like:

```json5
{
  "type": "m.room.welcome",
  "state_key": "",
  "content": {
    "m.room.welcome": {
      // we use an object to support future extensions like a theoretical "must_accept: true" flag

      "m.message": [ // exactly what it looks like: an m.message schema goes here
        { "mimetype": "text/html", "body": "<h1>Welcome!</h1> Here are some rules before you get going..." },
        { "mimetype": "text/plain", "body": "Welcome!\nHere are some rules before you get going..." },
      ]

      // if desired, shorthand m.message also would work here:
      //"m.text": "Welcome!\nHere are some rules before you get going...",
      //"m.html": "<h1>Welcome!</h1> Here are some rules before you get going..."
    }
  }
}
```

When a user first joins the room (which may be a [space](https://spec.matrix.org/v1.3/client-server-api/#spaces)),
the welcome message is shown (if set). It is left as an implementation detail if this appears as a timeline
message or as a dialog, though a dialog is suggested. Clients can show the welcome message more or less often
as needed for their specific use-case.

A user can be identified as first joining a room with a `membership` of `join`, and either a lack of
`prev_content` ([ref](https://spec.matrix.org/v1.3/client-server-api/#mroommember)) or with a previous
membership of `invite`. Clients might also wish to validate the `invite`'s `prev_content` to see if the
user would have already been presented with the welcome message, however this is not suggested due to
added complexity with minimal gain.

Clients can further simplify the check to be just when the user joins the room, regardless of previous
membership state. Clients might also track whether a specific edition of the welcome message was shown
to only show new welcome messages on join rather than repeated ones. Tracking of which ones the user has
seen are specifically left as an implementation detail.

## Potential issues

Having lack of overly-strict rules for when to show a welcome message could lead to inconsistencies
between clients interacting with the same room, as could clients not implementing this feature at all.
This is considered low risk for the time being until a future MSC handles considerations for preventing
interaction before acceptance of the dialog.

## Alternatives

There's a thousand different ways to represent a README/welcome/rules/topic message - Extensible Events
seems the most reasonable given it solves this sort of problem and re-uses the message rendering functions
clients would already have.

## Security considerations

No major considerations need to be made with the scope of this MSC. Clients should be aware of event size
limits being large, and thus seeing large welcome messages, however.

## Future considerations

In a later MSC, it would be desirable to support a way to prevent the user from interacting with the room
until they've accepted/agreed to the welcome message, akin to Discord's Rules Screening feature mentioned
in the introduction.

This could be achieved by adding the user's acceptance to their membership event (or as a new event), linking
acceptance into the event authorization rules. This would enforce at a federation level that the acceptance
must be given in order to send messages, which avoid polluting power levels (promoting a user from -1 to 0
would mean a potentially lengthy list of users in a power levels event).

A consideration for that future MSC is whether restricting users in this way is effective: unlike Discord,
bots and Matrix clients are easily able to just automate acceptance, making the measure ineffective against
spam. There may be solutions in this area which can provide the anti-spam value without too much technical
work, however.

## Unstable prefix

While this MSC is not considered stable, implementations should use `org.matrix.msc3857.welcome` as the
event type instead, including in `content`:

```json5
{
  "type": "org.matrix.msc3857.welcome",
  "state_key": "",
  "content": {
    "org.matrix.msc3857.welcome": {
      "org.matrix.msc1767.message": [ // note unstable prefix for extensible events
        { "mimetype": "text/html", "body": "<h1>Welcome!</h1> Here are some rules before you get going..." },
        { "mimetype": "text/plain", "body": "Welcome!\nHere are some rules before you get going..." },
      ]
    }
  }
}
```

## Dependencies

This MSC requires [MSC1767 - Extensible Events](https://github.com/matrix-org/matrix-spec-proposals/pull/1767).
