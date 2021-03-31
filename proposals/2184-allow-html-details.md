# Allow the HTML `<details>` tag in messages

Currently, there's no available method for bot developers - among others - to provide larger informative
messages in a room without disrupting the conversation for all other users. This often causes bots
to appear needlessly "spammy".

## Proposal

This proposal suggests adding the existing HTML tags for `<details>` and `<summary>` to the list of
allowed tags in formatted Matrix messages. Which would allow for larger messages to be shown simply
as smaller - and less intrusive - summaries for the users who are not interested in their full contents.

## Tradeoffs

An alternative method to provide a summary/details split could possibly be done through [MSC1767],
with the details and summaries being specified through repeated bodies with added metadata. This could
then also allow clients better autonomy in deciding what to display - or how to structure the information.

However, allowing the use of the `<details>` and `<summary>` tags would still offer richer formatting
capabilities even in such messages, especially as more than one detail/summary block could be included
in a single message.

## Potential issues

Allowing more HTML tags in formatted messages could cause more work for client developers, as they would
have to fit a larger and more diverse corpus of input into their designs and user experience.
However, these are both well documented - and implemented - HTML tags, so there is plenty of prior work
available to take example from in how to incorporate them.

Additionally, as the addition of these tags will make it possible to fit even more information into
a single message without worry of overflowing the room, any client that doesn't render the formatting
of the body might end up with a lessened user experience - from either an under- or overflow of information.

The onus on ensuring that the unformatted body is a reasonable representation of the message has always
been on the user or bot writing the formatted message though, so providing an improved ability for
formatting should not negatively affect the experience for any clients that simply render unformatted
text.

## Security considerations

Allowing more HTML tags in client rendering could lead to a wider attack surface for DOM-based exploits.
However, these tags are very simple in both function and design, so any possible attack surface they
would offer would be minimal at best.

[MSC1767]: https://github.com/matrix-org/matrix-doc/blob/matthew/msc1767/proposals/1767-extensible-events.md
