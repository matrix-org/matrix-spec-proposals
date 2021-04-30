# MSC3160: Attach timezone metadata to time information in messages

When communicating across timezones, you sometimes want to agree on a time with others, for example when to have a meeting. If somebody says, let's meet at 8pm, everybody else in the room has to think in what timezone the other person is, and work out the math in their head how that relates to their timezone, if different.

Luckily, computers are great at math, and so to facilitate this, clients could allow to represent a point in time with special markup in a message, adding the timezone of the sender. The clients of the other users in the room can then depending on their local timezone work out the math and render the point in time in the timezone of the user.

## Proposal

For events of type `m.room.message` with `msgtype` of `m.text` and `format` `org.matrix.custom.html` in the `content` field, the `formatted_body` field supports containing a `mx-time` element. Here is an example:

```json
{
    "type": "m.room.message",
    "content": {
        "msgtype": "m.text",
        "format": "org.matrix.custom.html",
        "formatted_body": "Shall we have a call at <mx-time timezone=\"-120\">9am</mx-time>?"
    }
}
```

The `timezone` attribute contains the local timezone offset in minutes from UTC.

### Possible user interface

Clients could either detect when the user writes something that looks like a timestamp and either automatically wrap it in a `<mx-time>`, or propose to do so. Alternatively, clients could have a time button in the composer formatting options that allows to add a time with a dialog, requiring less sophisticated time pattern detection while typing.

When rendering an `<mx-time>` element, clients could render it in a special way, and allow to interact with it to show the time in the timezone of the sender, or any other timezone.

## Potential issues

For web clients, Firefox always reports the local timezone to be UTC when resist fingerprinting is on. Web clients would therefore need to at least confirm the detected timezone with the user to ensure it does not get sent with a different timezone than the user is actually and create a whole level of confusion.

## Alternatives

HTML already supports a [`<time>` element](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/time), but it does not have an attribute to set timezone information. So instead of making an attribute up, I decided to go with a different tag.

## Security considerations

## Unstable prefix

Is a prefix needed for the tag name? If so, we can use `<org.matrix.msc3160.time>`.
