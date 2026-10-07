# MSC4550: Explicit links

A sender may want a link to a Matrix user or room to appear as an ordinary hyperlink. Some clients instead give these
links a unique appearance which other links do not display, and may also replace the sender's link text with the user's
or room's current name. Even when a client preserves the text, the sender cannot ask it to use the same presentation
that an ordinary hyperlink would receive.

The [user and room mentions](https://spec.matrix.org/v1.19/client-server-api/#user-and-room-mentions) section
recommends including a Matrix URI in a mention's `formatted_body` and displaying mentions differently from ordinary
links. However, an `a` tag linking to a user or room does not say whether the sender intended that special presentation
or an ordinary hyperlink. Clients that display Matrix links differently from ordinary links cannot distinguish those
two intentions from the HTML alone. Other clients already display them as ordinary links.

Some clients also give event links special treatment, even though event links are not user or room mentions. For
example, when the link text is the URL itself, Element Web may replace it with "Message from Bob" or "Message in
#room".

This MSC adds an HTML attribute that marks a link for ordinary hyperlink presentation. It asks clients to preserve
the sender's link text and avoid special presentation they apply to Matrix links. The attribute does not change the
link target or control mention notifications.

## Proposal

This MSC adds `data-mx-link` to the attributes permitted on the `a` tag in [`m.room.message` formatted
bodies](https://spec.matrix.org/v1.19/client-server-api/#mroommessage-msgtypes).

A client SHOULD treat an `a` tag as a standard link if the `data-mx-link` attribute is present. If this
attribute has a value, that value is ignored. Some libraries may automatically add an empty value, i.e.
`data-mx-link=""`.

Clients SHOULD display such a link with the sender's link text. They SHOULD NOT apply formatting reserved for
mentions or other Matrix links, or replace the link text with a resolved user, room or event name. Clients MAY still
apply styling they use for all links, such as showing the linked site's icon.

Senders MAY add `data-mx-link` to any link to mark it as a standard link. This includes links to users, rooms and
events, in both `matrix.to` and `matrix:` form. It also applies if a client gives other kinds of links special
presentation. On a link the client already displays as a standard link, the attribute has no effect. Links without
the attribute display as they do today.

Without the attribute, a client may display this using its special formatting for links to users:

```html
<a href="https://matrix.to/#/@alice:example.org">Alice</a>
```

With the attribute, the same client displays this as an ordinary link with the text "DM me":

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
        "body": "Questions? DM me",
        "format": "org.matrix.custom.html",
        "formatted_body": "Questions? <a data-mx-link href=\"https://matrix.to/#/@alice:example.org\">DM me</a>",
        "m.mentions": {}
    }
}
```

### Relationship to `m.mentions`

The attribute only changes how clients display the link.
[`m.mentions`](https://spec.matrix.org/v1.19/client-server-api/#definition-mmentions) decides whether a message
mentions a user or room for notification purposes. Linking to a user does not automatically notify them. A message
can also notify a user without linking to them. Sending clients SHOULD NOT add a user to `m.mentions` just because
the message links to them with `data-mx-link`.

## Potential issues

Clients that don't support this MSC will ignore the attribute. Clients that normally give these links special
presentation will continue to do so, and may replace the sender's link text. This is the same behavior as today.

## Alternatives

### An attribute marking mentions instead of links

An attribute such as `data-mx-mention` could mark links that *should* receive mention formatting, with every other
link displayed as a standard link. Existing links intended as mentions don't carry that attribute, so clients that
adopted it would stop displaying those links with mention formatting in old messages. Marking standard links leaves
existing events unchanged.

## Security considerations

None.

## Unstable prefix

Until this MSC is accepted, implementations SHOULD use `data-org.matrix.msc4550.link` in place of
`data-mx-link`.

## Dependencies

None.
