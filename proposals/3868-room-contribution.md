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
the clipboard. Another, optional, "badge_uri" parameter may be specified and only may contain a MXC URI to a image
media. When specified, the image, or badge, is displayed in place of the text, the text becoming the `alt` property
of said image.
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
    },
    {
      "uri": "https://liberapay.com/foo",
      "text": "Support us on LiberaPay",
      "badge_uri": "mxc://jae.fi/5d718eb34d05c8b6b1304e2a106aa800400476a6"
    }
  ]
}
```

## Potential issues

The authors aren't aware of any potential issues being raised.

## Alternatives

Historically, that sort of advertisement is either taken care of by adding the said URIs to the room topic or
periodically sending an announcement in the channel. However room topic is public information when the room
has `m.room.join_rules` other than `invite`.

## Security considerations

State events are currently not encrypted which could leak some data.

## Unstable prefix

Unstable implementations should use the state event type of `eu.dn0.msc3868.rev1.room.contribute`

## Dependencies

The authors believe this MSC could benefit from
[MSC3414: Encrypted State Events](https://github.com/matrix-org/matrix-spec-proposals/pull/3414)
while not considering it as a blocker.
Given the use of MXC URIs to display badges, the implementation of
[MSC3468: MXC to Hashes](https://github.com/matrix-org/matrix-spec-proposals/pull/3468)
would benefit the current MSC while, again, not blocking its implementation.
