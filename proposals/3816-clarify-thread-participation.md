# MSC3816: Clarify Thread Participation

[MSC3440](https://github.com/matrix-org/matrix-doc/pull/3440) defines relations
for threads and includes a `current_user_participated` flag, which is not fully
defined:

> A flag set to `true` if the current logged in user has participated in the thread

Known implementations implement this as whether the currently logged in user has
sent an event with an `m.thread` relation targeting the event, but this does not
make sense if the requesting user was the original event in the thread.

Consider `A` as the root event in a thread from `@alice:example.com`, and `B`
as a threaded reply from `@bob:example.com`. The bundled aggregations for `A`
would include:

| Requester            | `current_user_participated` |
|----------------------|-----------------------------|
| `@alice:example.com` | `false`                     |
| `@bob:example.com`   | `true`                      |

If `@alice:example.com` sends reply `C`, this would change:

| Requester            | `current_user_participated` |
|----------------------|-----------------------------|
| `@alice:example.com` | `true`                      |
| `@bob:example.com`   | `true`                      |

The proposed clarification is that `@alice:example.com` should have always have
participated in the thread (e.g. both tables would be `true` in the example above).

## Proposal

The definition of the `current_user_participated` flag from
[MSC3440](https://github.com/matrix-org/matrix-doc/pull/3440) is updated to be:

> A boolean flag, which is set to `true` if the current logged in user has
> participated in the thread. The user has participated if:
>
> * They created the current event.
> * They created an event with a `m.thread` relation targeting the current event.

This better matches the intention of this flag, which is that a client is able to
visually separate threads which might be of interest.

## Potential issues

The current implementations will need to be updated to take into account the
sender of the current event when generating bundled aggregations. This should be
trivial since all of the needed information is directly available.

It is suggested to [the new `filter` parameters from MSC3440](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/3440-threading-via-relations.md#fetch-all-threads-in-a-room)
in order to list threads in a room that a user has participated in. There would
now be an inconsistency that threads where the current user sent the root event
but has not replied to the thread could not easily be fetched. A future MSC may
solve this problem.

## Alternatives

Do not clarify [MSC3440](https://github.com/matrix-org/matrix-spec-proposals/pull/3440)
and leave it up to implementations to define the behavior of the
`current_user_participated` flag.

## Security considerations

None

## Unstable prefix

None, the changes above shouldn't dramatically change behavior for clients.
