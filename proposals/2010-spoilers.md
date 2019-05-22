# MSC 2010: Proposal to add client-side spoilers
Sometimes you are talking about e.g. a new movie and want to discuss the plot without spoiling others. Or you are talking in e.g. some mental health community where, due to triggers, some content shouldn't be immediately visible to everybody. For this the content is hidden and then revealed once interacted somehow (e.g. a click / hover).

## Proposal
This proposal adds a new attribute, `data-mx-spoiler`, to the `<span>` tag. If the attribute is present the contents of the span tag should be rendered as a spoiler. Optionally, you can specify a reason for the spoiler by setting the attribute string.

For example:  
`Hello there, the movie was <span data-mx-spoiler>awesome</span>` for a spoiler without reason and `Hey <span data-mx-spoiler="movie">the movie was awesome</span>` for a spoiler with the reason "movie".

The plain-text fallback could be rendered as `(Spoiler: <content>)` and `(Spoiler for <reason>: <content>)` respectively.

For example:  
`Hi <span data-mx-spoiler>there</span>` would have as fallback `Hi (Spoiler: there)`  
`Hi <span data-mx-spoiler="greeting">there</span>` would have as fallback `Hi (Spoiler for greeting: there)`

## Tradeoffs
Instead of making this an attribute, an entirely new tag could be introduced (e.g. `<mx-spoiler>`), however that wouldn't be HTML-compliant.

Instead of limiting the proposed `data-mx-spoiler` attribute only to the `<span>`-tag it could be added to all tags, however it might make implementations for clients more complicated.

## Potential issues
Depending on context it might make sense to put other events, such as `m.image`, into spoilers, too. This MSC doesn't address that at all. Using `<span data-mx-spoiler><img src="mxc://server/media"></span>` seems rather sub-optimal for that.

## Security considerations
The spoiler reason needs to be properly escaped when rendered.
