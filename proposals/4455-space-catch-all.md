# MSC4455: Space catch-all

This MSC introduces a new state event for `m.space` rooms that allows spaces to instruct clients to
include "space orphans" (rooms not part of any space that the user knows of).

## Proposal

Personal spaces are a great way to organize your own inbox. Accordingly, you may want to have a set
of spaces that you use for day-to-day communication, ignoring a majority of other chats you may have
joined. However, sometimes you may get invited to a new chat and not immediately remember
to put it into your day-to-day spaces. A catch-all space property would allow you to upgrade
your space to include any room that you haven't categorized into an appropriate space yet, and thus
ensure you don't miss out. In this scenario, you would then remove rooms from the catch-all
space by ensuring they are assigned to another space, e.g. a "verbose" space.

Accordingly, space rooms can include a `m.space.catch_all` state event to instruct clients to perform
such catch-all functionality. For the time being, server implementations are not required to apply
matching logic on the space endpoints; in particular the
[`/hierarchy`](https://spec.matrix.org/v1.18/client-server-api/#get_matrixclientv1roomsroomidhierarchy)
endpoint should keep focusing on only `m.space.child` relations to keep implementation simple.

The `m.space.catch_all` holds the following boolean flags:
- `include_orphans` (required): If `true`, clients should include any rooms that are not children of any
  space that the user is joined to when rendering this space, optionally subject to filters controlled
  by the other flags.
- `filter_is_dm` (optional): If `true`, only orphan rooms that are direct chats are considered. If `false`
  only orphan rooms that are *not* direct chats are considered. If omitted, both kinds of chats are
  considered. Whether a room is considered a direct chat depends solely on
  [`m.direct`](https://spec.matrix.org/v1.18/client-server-api/#mdirect) tracking, as long as this account
  data field is considered the canonical source for direct chats.

Clients should only consider `m.space.catch_all` state events using an empty state key.

Future MSCs may add additional filters on which orphans to include.


## Potential issues

In case of shared spaces, this can cause spaces to be shown differently for different users.
Clients may wish to only allow configuring this setting to private spaces, or render a
visual indication for whether a room is an explicit child of a space (directly or indirectly),
or pulled in via catch-all.


## Alternatives

Historically I would have a script running on my server that assigns space orphans to a dedicated space.
This approach made it work automatically with any client that supports spaces, but on the other hand it
requires (in this case hard-coded) server-side complexity.

Proper server support may also be added using the same or similar state events, to reduce client
implementation requirements. This may be beneficial for clients that do not wish to keep track of a
complete list of spaces and space children on their own.


## Security considerations

Since this MSC only relates to what rooms clients render under which space filter, the attack surface is
rather limited. The main concern would be public spaces causing unexpected filter behavior as outlined in
potential issues.

## Unstable prefix

Unstable implementations should use `de.spiritcroc.space.catch_all` instead of `m.space.catch_all`
for the state event type.

## Dependencies

None.
