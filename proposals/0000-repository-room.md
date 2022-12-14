# MSC0000: Repository Room

This spec defines state events that can be used to store and distribute 3D assets (such as scenes and avatar), [World](https://github.com/matrix-org/matrix-spec-proposals/pull/3815) and normal matrix rooms.

## Proposal

### `msc0000.repository_room` room type

Repository room can be distinguished by the `"type": "msc0000.repository_room"` key value pair present in `m.room.create` state event content.

```json
{
  "type": "m.room.create",
  "content": {
    "type": "msc0000.repository_room",
    "creator": "@example:example.org",
    "m.federate": true,
  }
}
```

### Submitting scene with `msc0000.repository_room.scene` message event

A scene can be submitted by the user using `msc0000.repository_room.scene` message event. Other then `author_url` & `source_url` all properties specified below are required to describe a scene.

```json
{
  "type": "tr.repository_room.scene",
  "content": {
    "scene": {
      "url": "mxc:abc",
      "preview_url": "mxc:abc",
      "name": "",
      "description": "",
      "author_name": "",
      "license": "",
      "version": 1,
      "author_url": "",
      "source_url": "",
    },
  },
}
```

### Featuring scene with `msc0000.repository_room.featured_scene` state event

Admin can feature a scene by sending `msc0000.repository_room.featured_scene` state event with `state_key` set to the `event_id` of original scene message event. Original message `"scene"` properties can be copied to this event. An additional `order` key is same as specified in spec to [order space children](https://spec.matrix.org/v1.5/client-server-api/#ordering-of-children-within-a-space) and is used to order the featured scene.

```json
{
  "type": "tr.repository_room.featured_scene",
  "state_key": "scene_message_event_id",
  "content": {
    "scene": {
      "url": "mxc:abc",
      "preview_url": "mxc:abc",
      ...
    },
    "order": ""
  },
}
```

A scene can be Unfeatured by removing content from this state event.

### Creating a [World](https://github.com/matrix-org/matrix-spec-proposals/pull/3815) with featured scene

A user can create a 3D [World](https://github.com/matrix-org/matrix-spec-proposals/pull/3815) with featured scenes by using the content from featured scene event. Additionally `"scene_from"` property with `"state_key"` of featured scene event and `"room_id"` of `repository_room` is added so client can check and prompt an admin for future featured scene updates.

```json
{
  "type": "m.world",
  "state_key": "",
  "content": {
    "scene_url": "",
    "scene_preview_url": "",
    "scene": {
      "url": "mxc:abc",
      "preview_url": "mxc:abc",
      ...
    },
    "scene_from": {
      "state_key": "featured_scene_state_key",
      "room_id": "repository_room_id"
    }
  }
}
```

### Featuring world with `msc0000.repository_room.featured_world` state event

A [World](https://github.com/matrix-org/matrix-spec-proposals/pull/3815) can be featured by sending `msc0000.repository_room.featured_world` state event with `"state_key"` as `room_id` of the World. `"content"` of this event is same as [`m.space.child`](https://spec.matrix.org/v1.5/client-server-api/#mspacechild). Client can use [MSC3266: Room summary API](https://github.com/matrix-org/matrix-spec-proposals/pull/3266) to display world to user.

```json
{
  "type": "tr.repository_room.featured_world",
  "state_key": "world_id",
  "content": {
    "suggested": false,
    "via": [],
    "order": ""
  }
}
```

### Featuring room with  `msc0000.repository_room.featured_room` state event

This state event is same as `msc0000.repository_room.featured_world` but for featuring normal matrix chat room.

```json
{
  "type": "tr.repository_room.featured_room",
  "state_key": "room_id",
  "content": {
    "suggested": false,
    "via": [],
    "order": ""
  }
}
```
