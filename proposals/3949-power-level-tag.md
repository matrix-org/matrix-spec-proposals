### MSC3949 Power Level Tags

Currently permissions in a certain room are handle via `m.room.power_levels`. A power level is an integer value, bigger the integer bigger the power. When we assign power level to a user we gave them power represented as integer value. This integer value is abstract and does not tell what kind of power it represent. Currently spec only suggest mapping abstract integer value to idea as: 0 - 49 to User, 50 - 99 to Moderator - 100 to Admin. This suggestion limits the wide range of power level integers to only three idea's.

This MSC propose tags for power levels. A tag represent a configurable information that can be tagged to any power level integer. This configurable information will give an idea of what a power level is when presented to user in graphical user interface. This will enhance the experience of managing permission as now power level can be able to represent the wide range of idea's. As power level can be assigned to users, we can also display room member by associating idea of power in room timeline and member list. This association will enhance the experience as tag will represent responsibility's of members at glance.

## Proposal

### What is Tag?
A Tag have three properties: `"name"`, `"color"` and `"icon"`.
```json
{
  "name": "Admin",
  "color": {
    "on_light": "#023020",
    "on_dark": "#90EE90"
  },
  "icon": {
    "url": "mxc:abc",
    "info": {
      "h": 152,
      "mimetype": "image/webp",
      "size": 30001,
      "w": 152
    }
  }
}
```
* `"name"` For what a tag represent. **Required**.
* `"color"` Color of tag. To create graphical emphasis and distinction between tags. (*Optional*)
  - `"on_light"` Tag color for lighter background.
  - `"on_dark"` Tag color for darker background.
* `"icon"` To display graphical representation of tags name. (*Optional*)

### Attaching Tag to Power Level
Tag can be attached to a power level by send a state event with key as `m.room.power_level_tag` and state key as value of power level.
```json
{
  "type": "m.room.power_level_tag",
  "state_key": "100",
  "content": {
    "name": "Admin",
    "color": {
      "on_light": "#023020",
      "on_dark": "#90EE90"
    },
    "icon": {
      "url": "mxc://admin_icon",
      "info": {
        "h": 152,
        "mimetype": "image/webp",
        "size": 30001,
        "w": 152
      }
    }
  }
}
```

### Deleting a Tag
A tag can be deleted by clearing all content from it's state event.

### How it fit with existing system?
If a room does not have any `m.room.power_level_tag` events client can fallback to suggest 0-49 as Default, 50-99 as Mod and 100 as Admin or alternatively create tag automatically as Default for 0, Mod for 50 and 100 for Admin.

#### What if we have power level with undefined tag?
If a power level is not defined client can consider to display it with the lower defined power level tag. If there is no lower defined tag, client can consider displaying tag defined with `m.room.power_level_tag` state event + state key as `"state_key": ""`, if no such event find client can display it power level itself or with the way of it's own choice.

### What else it fix?
This will also fix problem defined in [MSC3915: Owner power level](https://github.com/matrix-org/matrix-spec-proposals/blob/matthew/owner-pl/proposals/3915-owner-power-level.md).

## Alternatives

None?

## Security considerations

None?

## Unstable prefix

TODO

## Dependencies

None?
