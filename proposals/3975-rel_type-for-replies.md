# MSC3975: rel_type for Replies

Aggregation of child events (MSC2675) has proven itself useful for features such as Threads
and Reactions. Clients are unable to access Rich Replies via the Relationships API,
complicating that task of finding replies to an event. This proposal seeks to
solve this problem by including Rich Replies among the relationship types that use rel_type.

This proposal is related to MSC2675 which defines APIs to let the server calculate
aggregations on behalf of the client.


## Proposal

Rich Reply events should include a `rel_type` field with a new value specific to replies.

For example, a reply might look like:

```json
{
  "content": {
    "body": "> <@imbev:matrix.org> Original Message\n\nReply Message",
    "format": "org.matrix.custom.html",
    "formatted_body": "<mx-reply><blockquote><a href=\"https://matrix.to/#/!OAWeIkjdeYXEnQPoWC:matrix.org/$ju0-ipo32h_2eaD1JBVUmwayiAHKcu2eq21PX15E1Zg?via=matrix.org\">In reply to</a> <a href=\"https://matrix.to/#/@imbev:matrix.org\">@imbev:matrix.org</a><br>Original Message</blockquote></mx-reply>Reply Message",
    "m.relates_to": {
      "m.in_reply_to": {
        "event_id": "$ju0-ipo32h_2eaD1JBVUmwayiAHKcu2eq21PX15E1Zg"
      },
      "rel_type": "org.example.reply" // Proposed addition to reply event
    },
    "msgtype": "m.text"
  },
  "origin_server_ts": 1678300521134,
  "sender": "@imbev:matrix.org",
  "type": "m.room.message",
  "unsigned": {
    "age": 434,
    "transaction_id": "m1678300520742.91"
  },
  "event_id": "$DplZPaY06i_BcWs0I_8jRxWhVoFvhMFlrBj5q41GVvk",
  "room_id": "!OAWeIkjdeYXEnQPoWC:matrix.org"
}
```


## Potential issues

*Not all proposals are perfect. Sometimes there's a known disadvantage to implementing the proposal,
and they should be documented here. There should be some explanation for why the disadvantage is
acceptable, however - just like in this example.*

Someone is going to have to spend the time to figure out what the template should actually have in it.
It could be a document with just a few headers or a supplementary document to the process explanation,
however more detail should be included. A template that actually proposes something should be considered
because it not only gives an opportunity to show what a basic proposal looks like, it also means that
explanations for each section can be described. Spending the time to work out the content of the template
is beneficial and not considered a significant problem because it will lead to a document that everyone
can follow.


## Alternatives

*This is where alternative solutions could be listed. There's almost always another way to do things
and this section gives you the opportunity to highlight why those ways are not as desirable. The
argument made in this example is that all of the text provided by the template could be integrated
into the proposals introduction, although with some risk of losing clarity.*

Instead of adding a template to the repository, the assistance it provides could be integrated into
the proposal process itself. There is an argument to be had that the proposal process should be as
descriptive as possible, although having even more detail in the proposals introduction could lead to
some confusion or lack of understanding. Not to mention if the document is too large then potential
authors could be scared off as the process suddenly looks a lot more complicated than it is. For those
reasons, this proposal does not consider integrating the template in the proposals introduction a good
idea.


## Security considerations

*Some proposals may have some security aspect to them that was addressed in the proposed solution. This
section is a great place to outline some of the security-sensitive components of your proposal, such as
why a particular approach was (or wasn't) taken. The example here is a bit of a stretch and unlikely to
actually be worthwhile of including in a proposal, but it is generally a good idea to list these kinds
of concerns where possible.*

By having a template available, people would know what the desired detail for a proposal is. This is not
considered a risk because it is important that people understand the proposal process from start to end.

## Unstable prefix

*If a proposal is implemented before it is included in the spec, then implementers must ensure that the
implementation is compatible with the final version that lands in the spec. This generally means that
experimental implementations should use `/unstable` endpoints, and use vendor prefixes where necessary.
For more information, see [MSC2324](https://github.com/matrix-org/matrix-doc/pull/2324). This section
should be used to document things such as what endpoints and names are being used while the feature is
in development, the name of the unstable feature flag to use to detect support for the feature, or what
migration steps are needed to switch to newer versions of the proposal.*

## Dependencies

This MSC builds on MSCxxxx, MSCyyyy and MSCzzzz (which at the time of writing have not yet been accepted
into the spec).
