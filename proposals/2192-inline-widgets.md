# MSC2192: Inline widgets

Widgets are embedded applications that usually reside within the context of a room or
account to add useful functionality, such as a collaborative whiteboard, stickers,
dashboards, and conferencing. Currently, this feature doesn't extend into the timeline
itself for rich embeds of content, like videos and other sharable content.

This MSC proposes "inline widgets" as a mechanism for sharing embeddable content within
a room, primarily intended to cover video (YouTube, etc) embeds but able to cover a
wide range of use cases.

To achieve this, we use [MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767) to
define a new event type and suitable "content blocks" for supporting widgets and embeds
within a room.

For reference, the original Widget API is defined as [MSC1236](https://github.com/matrix-org/matrix-doc/issues/1236).

## Proposal

Using [MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767)'s system, we define
an `m.embed` event type with suitable content blocks to cover a web-based embedded
application in the timeline.

An example is:

```json5
{
  "type": "m.embed",
  "content": {
    "m.text": [
       // Format of the fallback is not defined, but should have enough information for a text-only
       // client to do something with the widget.
       {"body": "https://www.youtube.com/watch?v=Vn-NZvMcujc"}
    ],
    "m.widget": {
      "url": "https://www.youtube.com/embed/Vn-NZvMcujc",
      "waitForIframeLoad": true,
      "type": "
    }
  }
}
```

With consideration for extensible events, the following content blocks are defined:

* `m.widget` - The same fields as a widget event in room state, minus `creatorUserId`
  and `id`. Instead, implementations should use the `sender` as the creator and `event_id`
  as widget ID.

Together with content blocks from other proposals, an `m.embed` is described as:

* **Required** - An `m.text` block to act as a fallback for clients which can't process
  inline widgets.
* **Required** - An `m.widget` block to describe the widget itself. Clients use this to show
  the widget.

The above describes the minimum requirements for sending an `m.embed` event. Senders can add
additional blocks, however as per the extensible events system, receivers which understand
inline widget events should not honour them.

If a client does not support rendering inline widgets, the client would instead typically
represent the event as a plain text message.

When rendering the inline widget's iframe, all the normal widget options apply, including
availability of the Widget API. Further, templating on the URL is also supported, and
widgets should still *not* rely on `$matrix_user_id` being trusted.

Clients SHOULD limit the maximum height and width of inline widgets to prevent
large portions of the timeline being inaccessible to users. Scrollbars are encouraged
for long/large content.

## Potential issues

Previous drafts of this proposal supported an extended set of Matrix HTML to offer forms to users
which could then be used to render polls and similar functionality without the integration
asking the question requiring a web server. The complexity with that approach was that
it relied on HTML, which some clients cannot or will not support. The approach additionally
opened up the client to several XSS and similar security vulnerabilities due to the complex
nature of untrusted user-provided HTML being rendered in the client.

## Security considerations

Allowing arbitrary embeds opens up a spam vector for auto-playing videos, scare content,
and similar spam. Clients should do their best to avoid these kinds of attacks, such as
by blocking the widget from loading until the user accepts the widget or otherwise has
trust in the sender (where "trust" is left as an implementation detail).

## Unstable prefix

While this MSC is not considered stable, implementations should use `org.matrix.msc2192.`
in place of `m.`. For example, `m.widget` becomes `org.matrix.msc2192.widget`

## Alternative solutions

There are some possible alternatives:

#### Extended Matrix HTML for inline widgets

As alluded to earlier in this proposal, inline HTML could be used instead of the
`widget_url` field. In the interest of preserving the historical record more cleanly,
the entire previous draft is included here.

An inline HTML widget would take the following form, noting the use of `widget_html`
instead of `widget_url` to define the widget:
```json
{
    "type": "m.room.message",
    "content": {
        "msgtype": "m.widget",
        "body": "Poll: What is your favourite food?",
        "widget_html": "<button data-mx-action='sendText' data-mx-value='Ice Cream'>Ice Cream</button><button data-mx-action='sendText' data-mx-value='Pizza'>Pizza</button>",
        "waitForIframeLoad": true,
        "type": "m.custom",
        "name": "Poll",
        "data": {
            "title": "Favourite Food"
        }
    }
}
```

Events should only contain a `widget_url` or a `widget_html`, however when both are
specified clients should prefer to use the `widget_url`.

Inline HTML widgets inherit all behaviour of inline widgets above.

The HTML supported by `widget_html` is the same HTML set supported by Matrix
already (see paramgraphs under [m.room.message types](https://matrix.org/docs/spec/client_server/r0.5.0#m-room-message-msgtypes))
with a few additions:
* `button` is allowed with the `data-mx-action`,`data-mx-value`, and `name` attributes.
* `select` is allowed with the `name` attribute.
* `option` (under `select`) is allowed with the `value` and `selected` attributes.
* `input` is allowed with types `radio`, `checkbox`, `text`, and `password`. Inputs
  can additionally have `placeholder`, `value`, `checked`, and `name` as attributes.
* `form` is allowed with the `data-mx-event-type` attribute.
* `label` is allowed.

The attributes have special meanings:
* `data-mx-action` can be one of `m.send_text`, `m.send_notice`, or `m.send_hidden`.
  Because the attribute is only applicable to buttons, when the button is clicked
  the action occurs through the Widget postMessage API:
  * `m.send_text`: Sends the `data-mx-value` as an `m.text` room message.
  * `m.send_notice`: Sends the `data-mx-value` as an `m.notice` room message.
  * `m.send_hidden`: Sends the `data-mx-value` as an `m.room.hidden` event in the
    `body` field of the `content`.

  When buttons do not have this field, they should be assumed to be submit buttons
  for the parent `form`, if present.
* `data-mx-event-type` is the type of event to send when the form is submitted. The
  event's content will be a mapping of all the `name` attributes for form elements
  (`select` and `input`) in the form, with the added `m.form_name` for the `form`'s
  `name` and `m.button_name` for the `button`'s `name` which was clicked. For example,
  the following HTML:
  ```html
  <form data-mx-event-type="org.example.poll_response" name="favourite_food">
      <select name="preset">
          <option value="Ice Cream" selected>Ice Cream</option>
          <option value="Pizza">Pizza</option>
      </select>
      <input type="text" placeholder="Other" name="other">
      <label>
        <input type="checkbox" name="certified" value="yes" checked>
        I certify this is my favourite food.
      </label>

      <p>
        Second favourite food:
        <label><input type="radio" name="second_favourite" value="Ice Cream" checked> Ice Cream</label>
        <label><input type="radio" name="second_favourite" value="Pizza"> Pizza</label>
        <label><input type="radio" name="second_favourite" value="Chips"> Chips</label>
      </p>
      <button name="submit">Submit</button>
  </form>
  ```
  would produce the following event when the submit button was pressed:
  ```json
  {
      "type": "org.example.poll_response",
      "content": {
          "m.form_name": "favourite_food",
          "m.button_name": "submit",
          "preset": "Ice Cream",
          "other": "Doughnuts",
          "certified": "yes",
          "second_favourite": "Ice Cream"
      }
  }
  ```

  If no form `name` is specified, `m.form_name` is not included. Likewise for the
  button pressed. `m.form_name` and `m.button_name` SHOULD be added last to avoid
  forms overwriting the values (although doing so wouldn't cause problems anyways).

  For radio buttons, checkboxes, and selects: if no option is selected then the
  value is not included in the event. Empty textboxes are included as empty strings.

  Note that no validation is permitted by the HTML: the use of `widget_html` is
  not meant to be fully-featured. More advanced use cases are expected to be
  handled by `widget_url` instead, as it is not under the same limitations.

When handling `widget_html`, clients SHOULD wrap the HTML in their own local
wrapper. For example, a client may embed an iframe with a URL of
`/widget_html.html?html=...` for sandboxing.

In order to allow the widget to send custom/non-standardized events, a new postMessage
API needs to be considered. In MSC1236 there is a `fromWidget` action for `send_event`,
however in practice this action was never implemented. Instead, the action was
implemented as the event type to send (`fromWidget` action of `m.sticker`, for example).
This proposal re-introduces `send_event` with an altered payload to better suit custom
events:
```json
{
    "api": "fromWidget",
    "action": "send_event",
    "widgetId": "ID_GOES_HERE",
    "event_type": "org.example.poll_response",
    "event_content": {...}
}
```

This proposal does not support sending state events through this action. To negotiate
sending of the event type, the widget would request the event type prefixed with the
string `"m.send."` as the capability. For example, the widget would request the
`m.send.org.example.poll_response` capability in the above examples.
