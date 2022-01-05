---
type: module
---

### Room Tagging

Users can add tags to rooms. Tags are namespaced strings used to label
rooms. A room may have multiple tags. Tags are only visible to the user
that set them but are shared across all their devices.

#### Events

The tags on a room are received as single `m.tag` event in the
`account_data` section of a room. The content of the `m.tag` event is a
`tags` key whose value is an object mapping the name of each tag to
another object.

The JSON object associated with each tag gives information about the
tag, e.g how to order the rooms with a given tag.

Ordering information is given under the `order` key as a number between
0 and 1. The numbers are compared such that 0 is displayed first.
Therefore a room with an `order` of `0.2` would be displayed before a
room with an `order` of `0.7`. If a room has a tag without an `order`
key then it should appear after the rooms with that tag that have an
`order` key.

The name of a tag MUST NOT exceed 255 bytes.

The tag namespace is defined as follows:

-   The namespace `m.*` is reserved for tags defined in the Matrix
    specification. Clients must ignore any tags in this namespace they
    don't understand.
-   The namespace `u.*` is reserved for user-defined tags. The portion
    of the string after the `u.` is defined to be the display name of
    this tag. No other semantics should be inferred from tags in this
    namespace.
-   A client or app willing to use special tags for advanced
    functionality should namespace them similarly to state keys:
    `tld.name.*`
-   Any tag in the `tld.name.*` form but not matching the namespace of
    the current client should be ignored
-   Any tag not matching the above rules should be interpreted as a user
    tag from the `u.*` namespace, as if the name had already had `u.`
    stripped from the start (ie. the name of the tag is used as the
    display name directly). These non-namespaced tags are supported for
    historical reasons. New tags should use one of the defined
    namespaces above.

Several special names are listed in the specification: The following
tags are defined in the `m.*` namespace:

-   `m.favourite`: The user's favourite rooms. These should be shown
    with higher precedence than other rooms.
-   `m.lowpriority`: These should be shown with lower precedence than
    others.
-   `m.server_notice`: Used to identify [Server Notice
    Rooms](#server-notices).

{{% event event="m.tag" %}}

#### Client Behaviour

{{% http-api spec="client-server" api="tags" %}}
