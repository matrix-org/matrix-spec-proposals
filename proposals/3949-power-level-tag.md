### MSC3949 Power Level Tags

Currently permissions in a certain room are handle via `m.room.power_levels`. A power level is an
integer value, bigger the integer bigger the power. When we assign power level to a user we gave
them power represented as integer value. This integer value is abstract and does not tell what kind
of power it represent. Currently spec only suggest mapping abstract integer value to idea as: 0 - 49
to User, 50 - 99 to Moderator and 100 to Admin. This suggestion limits the wide range of power level
integers to only three idea's.

## Proposal

This MSC propose tags for power levels. A tag represent a configurable information that can be
tagged to any power level integer. This configurable information will give an idea of what a power
level is when presented to user in graphical user interface. This will enhance the experience of
managing permission as now power level can be able to represent the wide range of idea's. As power
level can be assigned to users, we can also display room member by associating idea of power in room
timeline and member list. This association will enhance the experience as tag will represent
responsibility's of members at glance.

### Tag Definition

A Tag have three properties: `name`, `color` and `icon` as described in table:

#### Tag
| Property | Type    | Description                                                                |
|----------|---------|----------------------------------------------------------------------------|
| name     | string  | Name of the tag. **Required**                                              |
| color    | string  | Color as `hex` value. For graphical emphasis and distinction between tags. |
| icon     | TagIcon | Graphical representation of tag.                                     |

#### TagIcon
| Property | Type      | Description                                                             |
|----------|-----------|-------------------------------------------------------------------------|
| key      | string    | This can be emoji similar to key in `m.reaction` or an `mxc` for image. |
| info     | ImageInfo | Standard `info` object for image if key is `mxc`.                       |


### Saving Tags

Tags can be saved by sending a state event of type `m.room.power_level_tags` with `state_key` as
empty string. The content will be a map of power level integer to Tag.

```json
{
  "type": "m.room.power_level_tags",
  "state_key": "",
  "content": {
    "100": {
      "name": "Admin",
      "color": "#000000",
      "icon": {
        "key": "mxc://admin_icon",
        "info": {
          "h": 152,
          "mimetype": "image/webp",
          "size": 30001,
          "w": 152
        }
      }
    },
    "50": {
      "name": "Moderator"
    },
    "38": {
      "name": "Bot",
      "icon": {
        "key": "🤖"
      }
    },
    "0": {
      "name": "Default"
    }
  }
}
```

### How it fit with existing system?

If a room does not have any `m.room.power_level_tags` event client can fallback to suggest 0-49 as
Default, 50-99 as Mod and 100 as Admin, alternatively client can create default content client side
by following the fallback strategy.

#### What if we have power level with undefined tag?

If a power level is not defined client can consider to display it with the lower defined power level
tag. If there is no lower defined tag, client can display it with the way of it's own choice.

### What else it fix?

This will also fix problem defined in [MSC3915: Owner power
level](https://github.com/matrix-org/matrix-spec-proposals/blob/matthew/owner-pl/proposals/3915-owner-power-level.md).

## Alternatives

None?

## Security considerations

None?

## Unstable prefix

Implementations SHOULD refer to `m.room.power_level_tags` as `in.cinny.room.power_level_tags`.

## Dependencies

None?
