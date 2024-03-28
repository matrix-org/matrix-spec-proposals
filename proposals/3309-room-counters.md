# MSC3309: Room Counters

Rooms are often are used for a specific topic, e.g. for a particular team within
an organization, which often have useful resources or state external to the
room. Currently, the normal way of tracking that in a room is to add links to
the topic, which works well for a lot of use cases. However, there are times
when you want to track more dynamic state in the room, e.g. number of open pull
requests on an associated repository. Updating the topic each time has a number
of drawbacks, such as changes being shown in the timeline, and it being hard for
users to pick out the information from the topic at a glance.

This MSC proposes adding simple counters that are designed to be frequently
updated and rendered near, but separately from, the room topic.


## Proposal

The simple counters are implemented via adding a new state event type:
`m.room.counter`, which includes the text to render and optional extra metadata.
The `state_key` of the event is set to an arbitrary value, allowing multiple
counters to be used in the room.

The fields for the content are:

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `title` | `false` | string | The text to render when displaying the counter. If empty the counter should be hidden entirely. |
| `link` | `false` | string | A link to direct the user to when the counter is clicked |
| `value` | `false` | integer | A numeric value associated with the counter. If omitted then no value should be rendered |
| `severity` | `false` | enum | One of `notice`, `normal`, `warning` or `alert`. Defaults to `normal` |

By omitting a `value` the "counter" can be used to render a piece of
information, such as the current API status from a status page, etc.

The optional `severity` field is used to indicate the status of the associated
resource, and clients should render counters differently depending on
`severity`. For example, a counter used to track the number of open critical
alerts in a monitoring system may use `normal` if there are zero critical alerts
and `alert` when there is at least one critical alert, clients could render the
counter in a normal font and colour for the former case and in a bold red font
in the latter case.

A guide for how clients should render the different severity levels is, assuming
a client with a light background and black font:

| Level | Style | Colour | Comment |
|-------|-------|--------|---------|
| `notice` | normal | grey | A notice should be rendered *less* obtrusively than elements around it, e.g. the topic. |
| `normal` | normal | black | Should be rendered with default style |
| `warning` | bold | amber | Noticeably more eye catching than the `normal` style, but not obtrusively so. |
| `alert` | bold | red | The styling should demand the attention of users in the room. |


## Potential issues

The proposal is primarily aimed at rendering counters that may need attention,
such as monitoring alerts or items in a review queue. As such the styling
options are fairly limited, but adds enough scope for different clients to
choose radically different styles.

It is also left up to the clients to decide on how to order multiple counters,
potentially leading to confusion.

## Alternatives

Instead of having a separate `value` field it could be pulled into the `title`
field, simplifying the event format. Having the `value` separate allows the
value to be more easily tracked over time.

## Security considerations

None.

## Unstable prefix

The counter event as described is currently being used with a type of `re.jki.counter`.
