## Motivation
When an account with an offensive profile (profile picture, username...) is removed from a room,
many clients will render the profile with a message such as "<offensive name> was banned".
This essentially cements the string in the room history.

## Proposal
Add a top-level `m.moderation_hidden` key to the content of an event. The format is as follows:
```
{
  "level": <level:string>,
  "tags": <tags:[string]>
}
```

`<level:string>` is a string referring to the *level* of perceived need to hide the event. Valid keys are:

##### `"spoiler"`
Show the event's presence, but hide its user-contents with a [spoiler](https://spec.matrix.org/latest/client-server-api/#spoiler-messages).
Example HTML
```html
<span data-mx-spoiler>@AVeryOffensiveUsername:example.com</span> was banned
```

##### `"hidden"`
Hide it by default, display for moderators and client debug views.

Tags is a list of strings representing content warnings that ought to be applied to the event.
Clients can choose to match on the tag list when deciding how to interpret the event.

Example:
```json
{
    "level": "spoiler",
    "tags": ["nsfw"]
}
```

This key should be retroactively editable.  
Since this is intended primarily for state events, this also means allowing the modification of this part of a state event.
Thankfully, this is only metadata, and it does not change the actual protocoal-critical parts of the stat event, so there should be no problem,
but it's important to mention it nonetheless. 

## Client implementation
A client should offer a three-state option in its settings about the interpretation of the hints
- Respect the hints
- Treat `hidden` as `spoiler`
- Ignore the hints

Plus a toggle option to
- Redact `spoiler` contents

Where an event such as `<span data-mx-spoiler>AVeryOffensiveUsername</span> was banned` would be rendered as `[redacted] was banned`

## Unstable prefix
Use `org.itycodes.msc4179.moderation_hidden` in place of `m.moderation_hidden`.

## Comparison with #3531
##### Motivation 
#3531 is primarily for hiding message events pending moderation, while #4179 is for hiding state events that have already happened but include content that one might not wish to be visible 
(such as a user with an offensive MXID getting banned). 
#3531 is likely to have the hidden status of an event retracted and the message deleted, while #4179 is unlikely to have the hidden status modified after the event has been sent 
##### Granularity
#3531 is less granular. Its `visibility: hidden` corresponds to the `hidden` level in #4179, but there is no equivalent of the `spoiler` level. 
Additionally, #3531 uses a free-form string, which cannot be automatically matched on by a client, while #4179 uses a tag list
(allowing someone to customize what events they are okay with seeing, and allowing optional fine-grained control over the completeness vs safety of room history per-client)
##### Race condition
#3531 requires the sending of a separate event, while #4179 has no such race condition, plus piggy-backs off of edit events for changing the content.

## Further work
Standardizing the list of tags

## Security implications
None known
