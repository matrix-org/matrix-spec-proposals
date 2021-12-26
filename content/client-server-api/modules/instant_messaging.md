---
type: module
weight: 10
---

### Instant Messaging

This module adds support for sending human-readable messages to a room.
It also adds support for associating human-readable information with the
room itself such as a room name and topic.

#### Events

Event definitions can be found in the (events spec)[/events/].

#### Recommendations when sending messages

In the event of send failure, clients SHOULD retry requests using an
exponential-backoff algorithm for a certain amount of time T. It is
recommended that T is no longer than 5 minutes. After this time, the
client should stop retrying and mark the message as "unsent". Users
should be able to manually resend unsent messages.

Users may type several messages at once and send them all in quick
succession. Clients SHOULD preserve the order in which they were sent by
the user. This means that clients should wait for the response to the
previous request before sending the next request. This can lead to
head-of-line blocking. In order to reduce the impact of head-of-line
blocking, clients should use a queue per room rather than a global
queue, as ordering is only relevant within a single room rather than
between rooms.

#### Local echo

Messages SHOULD appear immediately in the message view when a user
presses the "send" button. This should occur even if the message is
still sending. This is referred to as "local echo". Clients SHOULD
implement "local echo" of messages. Clients MAY display messages in a
different format to indicate that the server has not processed the
message. This format should be removed when the server responds.

Clients need to be able to match the message they are sending with the
same message which they receive from the event stream. The echo of the
same message from the event stream is referred to as "remote echo". Both
echoes need to be identified as the same message in order to prevent
duplicate messages being displayed. Ideally this pairing would occur
transparently to the user: the UI would not flicker as it transitions
from local to remote. Flickering can be reduced through clients making
use of the transaction ID they used to send a particular event. The
transaction ID used will be included in the event's `unsigned` data as
`transaction_id` when it arrives through the event stream.

Clients unable to make use of the transaction ID are likely to
experience flickering when the remote echo arrives on the event stream
*before* the request to send the message completes. In that case the
event arrives before the client has obtained an event ID, making it
impossible to identify it as a remote echo. This results in the client
displaying the message twice for some time (depending on the server
responsiveness) before the original request to send the message
completes. Once it completes, the client can take remedial actions to
remove the duplicate event by looking for duplicate event IDs.

#### Calculating the display name for a user

Clients may wish to show the human-readable display name of a room
member as part of a membership list, or when they send a message.
However, different members may have conflicting display names. Display
names MUST be disambiguated before showing them to the user, in order to
prevent spoofing of other users.

To ensure this is done consistently across clients, clients SHOULD use
the following algorithm to calculate a disambiguated display name for a
given user:

1.  Inspect the `m.room.member` state event for the relevant user id.
2.  If the `m.room.member` state event has no `displayname` field, or if
    that field has a `null` value, use the raw user id as the display
    name. Otherwise:
3.  If the `m.room.member` event has a `displayname` which is unique
    among members of the room with `membership: join` or
    `membership: invite`, use the given `displayname` as the
    user-visible display name. Otherwise:
4.  The `m.room.member` event has a non-unique `displayname`. This
    should be disambiguated using the user id, for example "display name
    (@id:homeserver.org)".

Developers should take note of the following when implementing the above
algorithm:

-   The user-visible display name of one member can be affected by
    changes in the state of another member. For example, if
    `@user1:matrix.org` is present in a room, with `displayname: Alice`,
    then when `@user2:example.com` joins the room, also with
    `displayname: Alice`, *both* users must be given disambiguated
    display names. Similarly, when one of the users then changes their
    display name, there is no longer a clash, and *both* users can be
    given their chosen display name. Clients should be alert to this
    possibility and ensure that all affected users are correctly
    renamed.
-   The display name of a room may also be affected by changes in the
    membership list. This is due to the room name sometimes being based
    on user display names (see [Calculating the display name for a
    room](#calculating-the-display-name-for-a-room)).
-   If the entire membership list is searched for clashing display
    names, this leads to an O(N^2) implementation for building the list
    of room members. This will be very inefficient for rooms with large
    numbers of members. It is recommended that client implementations
    maintain a hash table mapping from `displayname` to a list of room
    members using that name. Such a table can then be used for efficient
    calculation of whether disambiguation is needed.

#### Displaying membership information with messages

Clients may wish to show the display name and avatar URL of the room
member who sent a message. This can be achieved by inspecting the
`m.room.member` state event for that user ID (see [Calculating the
display name for a user](#calculating-the-display-name-for-a-user)).

When a user paginates the message history, clients may wish to show the
**historical** display name and avatar URL for a room member. This is
possible because older `m.room.member` events are returned when
paginating. This can be implemented efficiently by keeping two sets of
room state: old and current. As new events arrive and/or the user
paginates back in time, these two sets of state diverge from each other.
New events update the current state and paginated events update the old
state. When paginated events are processed sequentially, the old state
represents the state of the room *at the time the event was sent*. This
can then be used to set the historical display name and avatar URL.

#### Calculating the display name for a room

Clients may wish to show a human-readable name for a room. There are a
number of possibilities for choosing a useful name. To ensure that rooms
are named consistently across clients, clients SHOULD use the following
algorithm to choose a name:

1.  If the room has an [m.room.name](#m.room.name) state event with a non-empty
    `name` field, use the name given by that field.
2.  If the room has an [m.room.canonical\_alias](#m.room.canonical_alias) state event with a
    valid `alias` field, use the alias given by that field as the name.
    Note that clients should avoid using `alt_aliases` when calculating
    the room name.
3.  If none of the above conditions are met, a name should be composed
    based on the members of the room. Clients should consider
    [m.room.member](#m.room.member) events for users other than the logged-in user, as
    defined below.
    1.  If the number of `m.heroes` for the room are greater or equal to
        `m.joined_member_count + m.invited_member_count - 1`, then use
        the membership events for the heroes to calculate display names
        for the users ([disambiguating them if
        required](#calculating-the-display-name-for-a-user)) and
        concatenating them. For example, the client may choose to show
        "Alice, Bob, and Charlie (@charlie:example.org)" as the room
        name. The client may optionally limit the number of users it
        uses to generate a room name.
    2.  If there are fewer heroes than
        `m.joined_member_count + m.invited_member_count - 1`, and
        `m.joined_member_count + m.invited_member_count` is greater than
        1, the client should use the heroes to calculate display names
        for the users ([disambiguating them if
        required](#calculating-the-display-name-for-a-user)) and
        concatenating them alongside a count of the remaining users. For
        example, "Alice, Bob, and 1234 others".
    3.  If `m.joined_member_count + m.invited_member_count` is less than
        or equal to 1 (indicating the member is alone), the client
        should use the rules above to indicate that the room was empty.
        For example, "Empty Room (was Alice)", "Empty Room (was Alice
        and 1234 others)", or "Empty Room" if there are no heroes.

Clients SHOULD internationalise the room name to the user's language
when using the `m.heroes` to calculate the name. Clients SHOULD use
minimum 5 heroes to calculate room names where possible, but may use
more or less to fit better with their user experience.

#### Security considerations

Messages sent using this module are not encrypted, although end to end
encryption is in development (see [E2E module](#end-to-end-encryption)).

Clients should sanitise **all displayed keys** for unsafe HTML to
prevent Cross-Site Scripting (XSS) attacks. This includes room names and
topics.
