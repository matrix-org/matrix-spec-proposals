# MSC3230: User defined top level spaces ordering

Currently, Spaces as defined per [MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772) do not define an explicit order for top level spaces. Current implementations are ordering based on the lexicographic order of the roomIds.

As requested by a lot of users, it would be very convenient to be able to re-order top level spaces.

The ordering is per user and should be persisted and synced across the user's devices.

This MSC only concerns top level space ordering as subspace ordering is defined in the space as per m.space.child event.

## Proposal

The ordering information should be stored using room [`account_data`](https://matrix.org/docs/spec/client_server/latest#id125)

Order is saved by using a new room account data of type `m.space_order`

` PUT /_matrix/client/r0/user/{userId}/rooms/{roomId}/account_data/m.space.order`

````
{
    "type": "m.space_order",
    "content": {
        "order": "..."
    }
}
````

Where `order` is a string that will be compared using lexicographic order. Spaces with no order should appear last and be ordered using the roomID.

Order is defined as a `string` and not a `float` as in room tags, as recommanded because it was not very successful.



## Client recommendations:

After moving a space (e.g via DnD), client should limit the number of room account data update.
For example if the space is moved between two other spaces, just update the moved space order by appending a new character to the previous space order string

Re numbering (i.e change all spaces `m.space.order` account data) should be avoided as much as possible, as the updates might not be atomic for other clients and would makes spaces jump around.

## Potential issues

Spreading the order information across all spaces account data is making order changes not atomic.

Order string could grow infinitly and reach a hard limit, it might be needed to re-number when order string are too big.


## Future considerations

__Space Pinning__: The room `m.space_order` content could be extended by adding categories like `pinned`


__Space Folder__: In order to save vertical space, content could be extended to define folders and space with same folder could be represented as a single entry in the space pannel. On tap would expand the pannel.

## Alternatives

__Global Scope Account Data__

It's not clear whether this setting should be using global vs room scope.

Order could be stored in a global scope account as an array of roomID in the `org.matrix.mscXXX.space.order` type.
````
{
  "type": "org.matrix.mscXXX.space.order",
  "content": {
    "order": [
      "!GDoOXUnhorabeOhHur:matrix.org",
      "!ERioTVWSdvArJzumhm:foo.bar",
      "!AZozoWghOYSIAzerOIf:example.org",
      "!uZvykTONFkrkzGUFVE:mozilla.org",
      "!TfGEAMfGlIFILPqKYwQ:matrix.org",
      "!TaFfBCfZQRjDkrTvbDb:matrix.org"
    ]
  }
}
````

This alternative has been discarded as it won't scale, could reach event content size limit, and is less flexible as a way to define order compared to [0,1].

__Room Tags__


Order is stored using existing [Room Tagging](https://matrix.org/docs/spec/client_server/latest#room-tagging) mecanism.

> The tags on a room are received as single m.tag event in the account_data section of a room. The content of the m.tag event is a tags key whose value is an object mapping the name of each tag to another object.
> 
> The JSON object associated with each tag gives information about the tag, e.g how to order the rooms with a given tag.

````
{
    "content": {
        "tags": {
            "m.space": {
                "order": 0.9
            }
        }
    },
    "type": "m.tag"
}
````

As defined per `room tagging`ordering information is given under the order key as a number between 0 and 1. The numbers are compared such that 0 is displayed first. Therefore a room with an order of 0.2 would be displayed before a room with an order of 0.7. If a room has a tag without an order key then it should appear after the rooms with that tag that have an order key, fallbacking then to roomID lexical order.

This alternative has been discarded becaused perceived as confusing in regards of tags intentions.



## Potential issues

## Privacy considerations

## Unstable prefix

The following mapping will be used for identifiers in this MSC during development:


Proposed final identifier       | Purpose | Development identifier
------------------------------- | ------- | ----
`m.space_order` | event type | `org.matrix.msc3230.space_order`
