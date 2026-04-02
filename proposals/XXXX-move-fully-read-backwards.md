# MSC0000: Allow moving the fully read marker to older events

Today, many clients and servers assume that both read receipts and the fully read marker only ever
move forward monotonically, from older events to newer ones. However, currently the spec does not
actually explicitly state this requirement, which can lead to inconsistent server behavior, where some
implementations would allow clients to move the fully read marker backwards, while others would
silently drop the update and keep pointing to the newer event.

Both of these server-side treatments for read marker updates have their justification:

- When clients want to advance the fully read marker automatically while reading, it's reasonable to
  safeguard against race-conditions where the client may accidentally move the marker backwards
  without intending to do so. Since clients may be out-of-date without realizing, this check can be more easily
  achieved from the server, as already done in practice today in some server implementations such as synapse.
- Clients may wish to allow users to manually set the fully read marker. When a user explicitly states that
  the marker should be set to a specific message, moving the marker backwards is a valid use-case. In particular,
  some client may have automatically advanced the read marker further than the user actually read, such
  that the user may want to explicitly tell their client to move the unread line back to where they want to
  continue reading at a later time. In this scenario, race conditions based on outdated client data are
  less of a concern.

Accordingly, I propose that clients should be able to explicitly pick either behavior, and that
the specification should be clarified on a reasonable default behavior if no explicit preference is provided.
In particular I suggest that servers should by default check read markers and read receipts to only
move forward, while providing an optional flag when updating the fully read marker that allows clients to explicitly
move the marker backwards as well.


## Proposal

There are currently two endpoints that allow updating read markers:

- [`/_matrix/client/v3/rooms/{roomId}/receipt/{receiptType}/{eventId}`](https://spec.matrix.org/v1.18/client-server-api/#post_matrixclientv3roomsroomidreceiptreceipttypeeventid)
  allows clients to set either the read receipt or the read marker to a specific event, based on the provided
  `receiptType` in the query URL.
- [`/_matrix/client/v3/rooms/{roomId}/read_markers`](https://spec.matrix.org/v1.18/client-server-api/#post_matrixclientv3roomsroomidread_markers)
  allows clients to set the read marker and optionally read receipts in the same request, based on the provided
  request body.

By means of this proposal, we add a new optional boolean parameter `allow_backward` to the request body for both
endpoints.

If this flag is set to `false` or omitted, then servers should:
- Check that the provided event IDs are more recent than previously stored values for the respective receipt type.
- If it is more recent, continue to persist the new value, as done previously.
- If it matches the current state or points to an older event, silently drop the update (but still respond with code
  `200` to indicate the request was successfully handled, which matches currently observed server behavior).
- The logic to decide whether an event is more recent than another one is up to the implementation, but is expected to
  follow similar rules as other endpoints which imply a certain message order, such as the
  [`/messages`](https://spec.matrix.org/v1.18/client-server-api/#get_matrixclientv3roomsroomidmessages) endpoint.

If `allow_backward` is set to `true`, servers should also accept event IDs that move the fully read marker back in time.

When using the `/read_markers` endpoint, read receipts should still be checked for monotonicity even with
`allow_backward` enabled, such that only the fully read marker is allowed to move backwards. The goal of this
restriction is to keep this MSC lightweight while not having to worry about side-effects related to unread count
calculation and federation.

Similarly, requests to `/receipt` should only accept `true` for `allow_backward` when `receiptType` is set to
`m.fully_read`.
If a client calls this endpoint with `allow_backward` set to `true` for some other read receipt type than
the fully read marker, the server should return a `400` error response with `M_INVALID_PARAM` as `errcode`.

```
{
  "errcode": "M_INVALID_PARAM",
  "error": "allow_backward is only allowed to be true for m.fully_read."
}
```

### Examples

Example request body for `POST /_matrix/client/v3/rooms/{roomId}/read_markers`:

```
{
  "m.fully_read": "$somewhere:example.org",
  "m.read": "$elsewhere:example.org",
  "m.read.private": "$elsewhere:example.org",
  "allow_backward": true
}
```

Example request body for `POST /_matrix/client/v3/rooms/{roomId}/receipt/m.fully_read/{eventId}`:

```
{
  "allow_backward": true
}
```


## Potential issues

Maybe some clients assume that the fully read marker only ever moves forward.
However, usually `m.fully_read` is only used for rendering an unread line, so probably there shouldn't be too much
logic tied to it that would cause issues from breaking this assumption.


## Alternatives

### Allow controlling `m.fully_read` via normal account data endpoints

Currently the spec [prohibits](https://spec.matrix.org/v1.18/client-server-api/#put_matrixclientv3useruseridroomsroomidaccount_datatype)
servers from accepting `m.fully_read` account data set from
[`/account_data`](https://spec.matrix.org/v1.18/client-server-api/#put_matrixclientv3useruseridroomsroomidaccount_datatype).

If we dropped this part of the spec, clients could use this endpoint to have full control over the fully read marker.

However, since special handling for this account data field already exists, adding another codepath that allows
controlling the read markers could increase complexity in both client and server implementations,
and thus increase the chance for bugs.


### Always allow `m.fully_read` to move backwards

This approach can cause race conditions between clients in cases where we want to ensure monotonicity.  
In particular, clients may wish to advance the fully read marker automatically while the user scrolls,
but clients may not know that they have outdated information, which could lead to accidentally
moving the fully read marker backwards, causing poor UX as a result.


### Invent a new receipt or marker that allows moving backwards

One may argue that manually marking a message as fully read is a different concept than automatically advancing
the fully read markers and read receipts. This difference could justify adding yet another type of read receipt or
marker, possibly one that would also affect unread counts.  
However, the main goal of `m.fully_read` already covers the need for users to figure out what the last read message
is, and adding another type of receipt can become increasingly complex and confusing both for developers and users.


### Allow read receipts to be moved backwards as well

In contrast to `m.fully_read` which has rather limited scope (only lives in account data and commonly only affects
where to render the unread line in a room), read receipts are much more complex:

- There are private and public read receipts.
- There are threaded and un-threaded read receipts.
- Read receipts influence unread count calculation.
- Read receipts are federated.

So while it may also be desirable to allow read receipts to be moved backwards, e.g. in order to manually increment
unread counts, I consider this out of scope for this proposal. A future MSC may revisit this topic if necessary.


### MSC4033: Explicit ordering of events for receipts

[MSC4033](https://github.com/matrix-org/matrix-spec-proposals/blob/andybalaam/event-thread-and-order/proposals/4033-event-thread-and-order.md)
proposes an explicit specification of message order to use for read receipts, while intentionally not covering
`m.fully_read`.
As MSC0000 on the other hand does not further specify the actual order that servers should use, but
leaves the message order as an implementation detail to the server, both MSCs are complementary to each
other - if some variant of MSC4033 gets included into the spec, the same message order will likely be useful for
`m.fully_read` as well, for the case the client hasn't opted out of monotonic handling.


## Security considerations

None.

`m.fully_read` is stored in account data and only affects the user's own view on rooms.
Accordingly, allowing users to control the fully read marker more freely does not introduce any
new attack surface to other parties.


## Unstable prefix

Unstable implementations should use `com.beeper.allow_backward` in place of `allow_backward` in the request body.

Servers can promote support for this MSC in `/_matrix/client/versions` by setting the flag `com.beeper.msc0000`.
The feature flag should continue to be advertised after the MSC is accepted until the server advertises support for the stable spec release that includes this MSC.
