# MSC3816: Clarify Thread Participation

[MSC3440](https://github.com/matrix-org/matrix-doc/pull/3440) defines the `m.thread` relation
type, and the format of the serverside aggregation for them. The definition of the aggregation includes a
`current_user_participated` flag, which is not fully defined:

> A flag set to `true` if the current logged in user has participated in the thread

In particular, it is unclear whether sending the initial event (i.e., the event which is the
target of the `m.thread` relation) counts as participating in the thread.

Known implementations do *not* count the initial event in this way, and instead
implement this as: "has the current user sent an event with an `m.thread` relation
targeting the event", but this has found to give poor user experience in practice.

For example, consider `A` as the root event in a thread from `@alice:example.com`, and `B`
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
participated in the thread (i.e. both tables would be `true` in the example above).

## Proposal

The [definition of the `current_user_participated` flag](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/3440-threading-via-relations.md#event-format)
from the bundled aggregations for `m.thread` relations is updated:

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

MSC3440 proposes using [new `filter` parameters](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/3440-threading-via-relations.md#fetch-all-threads-in-a-room)
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
