# MSC 2376: Disable URL Previews
Currently URLs posted in chat give a URL preview. Sometimes, for example with bots, this can be
unwanted, as the user is already basically aware what the link the bot is posting is following to.

## Proposal
This proposal is about adding a new attribute to the `formatted_body` of messages with type
`m.room.member` and msgtype `m.text`.

It adds a new attribute, `data-mx-nopreview` to the `<a>` tag. If this attribute is present the
client is expected **not** to display a URL preview.

### Example
```json
{
	"msgtype": "m.text",
	"format": "org.matrix.custom.html",
	"body": "Hey, look at this awesome MSC!",
	"formatted_body": "Hey, look at <a data-mx-nopreview src=\"https://github.com/matrix-org/matrix-doc/pull/2379\">this</a> awesome MSC!"
}
```

## Potential issues
HTML tags are usually meant to be for formatting. Disabling URL previews isn't strictly formatting.
However, as the client will already have parsed the tag in order to generate a URL preview the place
seems appropriate.

## Alternatives
A flag could be set for the entire message to disable URL previews, however that doesn't allow for
having within a message one URL with preview and one without.

## Security considerations
You could get tricked more easily into being Rickroll'd.
