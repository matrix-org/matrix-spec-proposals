# MSC3868: Room Contribution

Many projects and communities have a room on Matrix nowadays and many may wish to show their friends how to support 
them.  
The goal, would be to have something only visible to room & space members and to provide something easier to manage &
display than putting links into the room topic or announcing them periodically.

## Proposal

This proposal implements a new `m.room.contribute` state event. This state event contains a "uri" parameter that may
link to a git repo or any kind of URI and a "text" parameter that may contain the text of the button directing to the
support link. There may be multiple "uri" and "text" parameters, each adding a different button containing a different
link. Alternatively to the "uri" parameter, a "copy" one can be specified and will tell clients to copy the value in
the clipboard.
An example of this event would look like this:

```json
{
  "links": [
    {
      "uri": "https://git.me/contribute",
      "text": "Contribute code!"
    },
    {
      "uri": "https://translate.me/contribute",
      "text": "Translate the project!"
    },
    {
      "uri": "mailto:team@verygoodproje.ct",
      "text": "Get in touch!"
    },
    {
      "text": "Donation IBAN",
      "copy": "CH5604835012345678009"
    }
  ]
}
```

## Potential issues

// To be determined

## Alternatives

Historically, that sort of advertisement is either taken care of by adding the said URIs to the room topic or 
periodically sending an announcement in the channel.

## Security considerations

State events are currently not encrypted which could leak some data.

## Dependencies

None.
