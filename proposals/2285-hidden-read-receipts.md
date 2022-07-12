# MSC2285: Private read receipts

Currently users must send read receipts in order to affect their notification
counts, which alerts other people that the user has read their message. For
primarily privacy reasons, it may be desirable to users to not advertise to
others that they've read a message.

## Proposal

This MSC proposes adding a new `receiptType` (see [the receipts
spec](https://spec.matrix.org/v1.3/client-server-api/#receipts)) of
`m.read.private`. This `receiptType` is used when the user wants to affect their
notification count but doesn't want other users to see their read receipt.

To move the user's private read receipt to `$123` the client can make a POST
request to the [`/receipt`
endpoint](https://spec.matrix.org/v1.3/client-server-api/#post_matrixclientv3roomsroomidreceiptreceipttypeeventid).
For example:

```HTTP
POST /_matrix/client/v3/rooms/!a:example.org/receipt/m.read.private/$123
{}
```

The MSC also proposes adding `m.fully_read` as a possible `receiptType` for
`/receipt` to make this endpoint consistent with `/read_markers`. (we have two
endpoints that do essentially the same thing, so it would make sense for them to
be consistent)

Alternatively, the client can move the user's `m.fully_read` marker and/or
`m.read` receipt at the same time as `m.read.private` by making a POST request
to the [`/read_markers`
endpoint](https://spec.matrix.org/v1.3/client-server-api/#post_matrixclientv3roomsroomidread_markers).
For example:

```HTTP
POST /_matrix/client/r0/rooms/!a:example.org/read_markers
{
    "m.fully_read": "$123",
    "m.read": "$123",
    "m.read.private": "$123"
}
```

Both `m.read` and `m.read.private` clear notifications in the same way. If the
user sent two receipts into a room, the later one should be the one that decides
the notification count.

If the user has `m.read` and `m.read.private` receipts at the same event, the
`m.read` receipt takes precedence - an `m.read.private` receipt sent to an event
that already has `m.read`, shouldn't move the user's receipt up in the timeline
from the perspective of other users.

The `m.read` property is now optional for the [`/read_markers`
endpoint](https://spec.matrix.org/v1.3/client-server-api/#post_matrixclientv3roomsroomidread_markers)
as sometimes we only want to send `m.read.private`.

Servers MUST NOT send receipts of `receiptType` `m.read.private` to any other
user than the sender. Servers also MUST NOT send receipts of `receiptType`
`m.read.private` to any server over federation.

## Security considerations

Servers could act as if `m.read.private` is the same as `m.read` so the user
must already trust the homeserver to a degree however, and the methods of
notifying the user to the problem are difficult to implement. Users can always
run their own homeservers to ensure it behaves correctly.

## Potential issues

Clients which support read receipts would end up rendering the user's receipt as
jumping down when they send a message. This is no different from how IRC and
similarly bridged users are perceived today.

## Alternatives

It has been suggested to use account data to control this on a per-account
basis. While this might have some benefits, it is much less flexible and would
lead to us inventing a way to store per-account settings in account data which
should be handled in a separate MSC.

Previous iterations of this MSC additionally suggested that having an `m.hidden`
flag on existing read receipts could work, however this feels like assigning too
much responsibility to an existing structure.

## Unstable prefix

While this MSC is not considered stable, implementations should use
`org.matrix.msc2285` as a namespace.

|Stable (post-FCP)|Unstable                         |
|-----------------|---------------------------------|
|`m.read.private` |`org.matrix.msc2285.read.private`|

## Detecting server support

Clients are required to check for server support to ensure they are not sending
read receipts which are not clearing notifications.

If a client has this feature enabled, in the case of the server not supporting
the MSC, the client should either keep sending private read receipts with the
knowledge that notifications will not be clearing or it should warn the user and
start sending public read receipts.

**Once this MSC gets merged and once it becomes a part of a spec version,
clients should update their implementations as fast as possible to accommodate
the fact that the way of detecting server support will change.**

### While the MSC is unstable

During this period, to detect server support clients should check for the
presence of the `org.matrix.msc2285` flag in `unstable_features` on `/versions`.
Clients are also required to use the unstable prefixes (see [unstable
prefix](#unstable-prefix)) during this time.

### Once the MSC is merged but not in a spec version

Once this MSC is merged, but is not yet part of the spec, clients should rely on
the presence of the `org.matrix.msc2285.stable` flag in `unstable_features` to
determine server support. If the flag is present, clients are required to use
stable prefixes (see [unstable prefix](#unstable-prefix)).

### Once the MSC is in a spec version

Once this MSC becomes a part of a spec version, clients should rely on the
presence of the spec version, that supports the MSC, in `versions` on
`/versions`, to determine support. Servers will also drop the
`org.matrix.msc2285.stable` flag once the MSC is part of a spec version.
