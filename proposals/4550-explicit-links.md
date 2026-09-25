# MSC4550: Explicit links

The specification recommends that [user and room
mentions](https://spec.matrix.org/v1.19/client-server-api/#user-and-room-mentions) include a link to a Matrix URI
in a message's `formatted_body`, and says:

> Clients should display mentions differently from other elements.

In the HTML, a mention is just a link, so a client can't tell it apart from any other link to a user or room.
Every link to a user or room displays as a mention. If a sender writes
`Questions? [DM me](https://matrix.to/#/@alice:example.org)`, clients display it as a mention of Alice. A room
link like `[Join our support room](https://matrix.to/#/#support:example.org) for help` gets the same treatment.

Some clients display links to events differently too, even though the specification doesn't treat them as
mentions. Element Web shows a link to an event as "Message from Bob" or "Message in #room" when the link text is
the URL itself.

This MSC adds an HTML attribute that tells clients to display a link as a standard link, without the mention
formatting or any other special formatting that standard links don't get.

## Proposal

This MSC adds `data-mx-link` to the attributes permitted on the `a` tag in [`m.room.message` formatted
bodies](https://spec.matrix.org/v1.19/client-server-api/#mroommessage-msgtypes).

A client SHOULD treat an `a` tag as a standard link if the `data-mx-link` attribute is present. If this
attribute has a value, that value is ignored. Some libraries may automatically add an empty value, i.e.
`data-mx-link=""`.

Clients SHOULD display such a link with the sender's link text, and SHOULD NOT display it as a mention or give
it any other special formatting that standard links don't get. Clients MAY still apply styling
they use for all links, such as showing the linked site's icon.

Senders MAY add `data-mx-link` to any link to mark it as a standard link. It affects every link that clients
display differently from standard links, now or in the future. That commonly includes links to users, rooms and
events, in both `matrix.to` and `matrix:` form. On a link the client already displays as a standard link, the
attribute has no effect. Links without the attribute display as they do today.

A client still displays this link as a mention of Alice:

```html
<a href="https://matrix.to/#/@alice:example.org">Alice</a>
```

It displays this one as a standard link with the text "DM me":

```html
<a data-mx-link href="https://matrix.to/#/@alice:example.org">DM me</a>
```

And it displays this event link as the URL, with no special treatment:

```html
<a data-mx-link href="https://matrix.to/#/!abc:example.org/$def">https://matrix.to/#/!abc:example.org/$def</a>
```

A full event looks like this:

```json
{
    "type": "m.room.message",
    "content": {
        "msgtype": "m.text",
        "body": "Questions? [DM me](https://matrix.to/#/@alice:example.org)",
        "format": "org.matrix.custom.html",
        "formatted_body": "Questions? <a data-mx-link href=\"https://matrix.to/#/@alice:example.org\">DM me</a>",
        "m.mentions": {}
    }
}
```

### Relationship to `m.mentions`

The attribute only changes how clients display the link. [`m.mentions`](https://spec.matrix.org/v1.19/client-server-api/#definition-mmentions)
still decides whether a message mentions a user or room. Sending clients SHOULD NOT add a user to `m.mentions`
just because the message links to them with `data-mx-link`.

## Potential issues

Clients that don't support this MSC will ignore the attribute and keep displaying these links as mentions, so
the sender's intent is lost on those clients. This is no worse than today.

## Alternatives

### An attribute marking mentions instead of links

An attribute such as `data-mx-mention` could mark the links that *should* display as mentions, with every other
link displayed as a standard link. Existing mentions don't carry that attribute, so clients that adopted it would
stop displaying mentions in old messages. Marking standard links leaves existing events unchanged.

## Security considerations

None.

## Unstable prefix

Until this MSC is accepted, implementations SHOULD use `data-org.matrix.msc4550.link` in place of
`data-mx-link`.

## Dependencies

None.
