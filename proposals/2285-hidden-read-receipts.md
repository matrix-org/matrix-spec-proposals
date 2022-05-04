# MSC2285: Hidden read receipts

Currently users must send read receipts in order to affect their notification
counts, which alerts other people that the user has read their message. For
primarily privacy reasons, it may be desirable to users to not advertise to
others that they've read a message.

## Proposal

This MSC proposes adding a new `receiptType` of `m.read.private`. This
`receiptType` is used when the user wants to affect their notification count but
doesn't want other users to see their read receipt.

To move the user's private read receipt to `$123` the client can make a POST
request such as this.

```HTTP
POST /_matrix/client/r0/rooms/!a:example.org/receipt/m.read.private/$123
{}
```

To also move the user's `m.fully_read` marker and `m.read` receipt the client
can make a POST request such as this.

```HTTP
POST /_matrix/client/r0/rooms/!a:example.org/read_markers
{
    "m.fully_read": "$123",
    "m.read": "$123",
    "m.read.private": "$123",
}
```

Both `m.read` and `m.read.private` clear notifications in the same way. If the
user sent two receipts into a room, the later one should be the one that decides
the notification count.

If the user has `m.read` and `m.read.private` receipts at the same event, the
`m.read` receipt takes precedence - an `m.read.private` receipt sent to an event
that already has `m.read`, shouldn't move the user's receipt up in the timeline
from the perspective of other users.

The `m.read` is now optional as sometimes we only want to send `m.read.private`.

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

|Release         |Development                      |
|----------------|---------------------------------|
|`m.read.private`|`org.matrix.msc2285.read.private`|

To detect server support, clients can either rely on the spec version (when
stable) or the presence of a `org.matrix.msc2285` flag in  `unstable_features`
on `/versions`. Clients are recommended to check for server support to ensure
they are not misleading the user about their read receipts not being visible to
other users.
