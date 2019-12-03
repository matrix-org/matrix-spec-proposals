# MSC 2376: Disable URL Previews
Currently URLs posted in chat give a URL preview. Sometimes, for example with bots, this can be
unwanted. For instance if a bot is posting a message with a lot of links, or the content of the link
is already obvious from the message itself.

## Proposal
This proposal adds a new attribute to the `formatted_body` key of messages with type
`m.room.message` and msgtype `m.text`.

It adds a new attribute, `data-mx-nopreview` to the `<a>` HTML tag. The presence of the attribute
can be used as a hint by clients to indicate that a URL preview for the link is not necessary, and
clients may skip the link when displaying previews.

### Example
```json
{
	"msgtype": "m.text",
	"format": "org.matrix.custom.html",
	"body": "Hey, look at what I did! MSC2376: Disable URL Previews",
	"formatted_body": "Hey, look at what I did! <a data-mx-nopreview src=\"https://github.com/matrix-org/matrix-doc/pull/2376\">MSC2376: Disable URL Previews</a>"
}
```

## Potential issues
HTML tags are usually meant for formatting. Disabling URL previews isn't strictly formatting.

Additionally, clients may currently only gather the URL previews only from the `body`, forcing them
to parse the `formatted_body` as well.

## Alternatives
A flag could be set for the entire message to disable URL previews, however that doesn't allow for
having within a message one URL with preview and one without.

Alternatively, a new, optional, key `url_previews` with an array of the URLs to preview for could be
introduced.

## Security considerations
You could get tricked more easily into being Rickroll'd.
