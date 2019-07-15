# MSC 2010: Proposal to add client-side spoilers
Sometimes, while you want to put text into a spoiler to not have people accidentally read things that they don't want to see.

For example, when discussing a new movie or a TV series, not everyone might have watched it yet.
In such cases it would make sense to add a spoiler so that only those who have seen the movie or
don't mind spoilers read the content.  
Another example would be e.g. in mental health communities where certain people have certain
triggers. People could put talking about abuse or the like into a spoiler, to not accidentally
trigger anyone just reading along the conversation.  
Furthermore this is helpful for bridging to other networks that already have a spoiler feature.

To render the spoiler the content is hidden and then revealed once interacted somehow
(e.g. a click / hover).

## Proposal
This proposal is about adding a new attribute to the `formatted_body` of messages with type
`m.room.message` and msgtype `m.text`.

It adds a new attribute, `data-mx-spoiler`, to the `<span>` tag. If the attribute is present the
contents of the span tag should be rendered as a spoiler. Optionally, you can specify a reason for
the spoiler by setting the attribute string. It could be rendered, for example, similar to this:

![Spoiler rendering idea](images/2010-spoiler-example.gif)

To preserve the semantics of a spoiler in the plaintext fallback it is recommended to upload the contents of the spoiler
as a text file and then link this: `[Spoiler](mxc://someserver/somefile)` and
`[Spoiler for reason](mxc://someserver/somefile)` respectively.

### Example
Without reason:
```
{
    "msgtype": "m.text",
    "format": "org.matrix.custom.html",
    "body": "Hello there, the movie was [spoiler](mxc://someserver/somefile)",
    "formatted_body": "Hello there, the movie was <span data-mx-spoiler>awesome</span>"
}
```
With reason:
```
{
    "msgtype": "m.text",
    "format": "org.matrix.custom.html",
    "body": "Hey [Spoiler for movie](mxc://someserver/somefile)",
    "formatted_body": "Hey <span data-mx-spoiler="movie">the movie was awesome</span>"
}
```

## Tradeoffs
Instead of making this an attribute, an entirely new tag could be introduced (e.g. `<mx-spoiler>`),
however that wouldn't be HTML-compliant.

Instead of limiting the proposed `data-mx-spoiler` attribute only to the `<span>`-tag it could be
added to all tags, however it might make implementations for clients more complicated.

## Potential issues
Depending on context it might make sense to put other events, such as `m.image`, into spoilers,
too. This MSC doesn't address that at all. Using
`<span data-mx-spoiler><img src="mxc://server/media"></span>` seems rather sub-optimal for that.

This MSC doesn't take HTML block elements into account.

Clients would have to come up with a way how to input spoilers. This could be done, for example,
by adding a custom markdown tag (like discord does), so that you do `Text ||spoiler||`, however
that doesn't take a spoiler reason into account.

## Security considerations
The spoiler reason needs to be properly escaped when rendered.
