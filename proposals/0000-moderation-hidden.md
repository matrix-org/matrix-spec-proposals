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

`<level:string>` is a string referring to the *level* of percieved need to hide the event. Valid keys are:

##### `"spoiler"`
Show the event's presence, but hide its contents.

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

## Unstable prefix
Use `org.itycodes.msc0000.moderation_hidden` in place of `m.moderation_hidden`.

## Further work
Standardizing the list of tags

## Security implications
None known
