# MSC3948: Repository Room for Thirdroom

This spec defines state events that can be used to store and distribute 3D assets (such as scenes
and avatar), [World](https://github.com/matrix-org/matrix-spec-proposals/pull/3815) and normal
matrix rooms.

## Proposal

### `m.repository_room` room type

Repository room can be distinguished by the `"type": "m.repository_room"` key value pair
present in `m.room.create` state event content.

```json
{
  "type": "m.room.create",
  "content": {
    "type": "m.repository_room",
    "creator": "@example:example.org",
    "m.federate": true,
  }
}
```

### Submitting scene with `m.repository_room.scene` message event

A scene can be submitted by the user using `m.repository_room.scene` message event. Other then
`attribution` and `description` all properties specified below are required to describe a scene.

`version` this property should be incremented when a new version of the scene is submitted.

`name` this is the name of the scene.

`description` (optional) this is a short description of the scene.

`url` this is the URL of the 3D scene to use for the room. Currently only .glb files are supported.
For supported glTF extensions see the
[Third Room glTF extensions](https://thirdroom.io/docs/gltf/).

`script_url` (optional) is the URL to a JavaScript or WebAssembly file that will be executed in the
3D scene. This can be used to add interactivity to the scene. See the [WebSceneGraph
documentation](https://thirdroom.io/docs/guides/websg/) for more information on scripts.

`thumbnail_url` this is the URL of the thumbnail image to use for the room.

`thumbnail_info` this is an object containing information about the thumbnail image using the
ThumbnailInfo data type.

`attribution` (optional) this is an array of attributions for the scene.

`attribution.title` (optional) this is the title of the attributed sub-asset. This should be the
original title of the source material.

`attribution.source_url` (optional) this is the URL of the source material. This could be a link to
the original asset, a page describing the asset, or some other url describing where the asset is
from.

`attribution.author_name` This is the name of the author (individual or organization) of the source
material.

`attribution.author_url` (optional) this is the URL of the author's website.

`attribution.license` (optional) this is the license of the source material. This should be a valid
[SPDX license identifier](https://spdx.org/licenses/).

```json
{
  "type": "m.repository_room.scene",
  "content": {
    "scene": {
      "version": 1,
      "name": "Forest Scene",
      "description": "A low poly forest scene.",
      "url": "mxc:abc",
      "thumbnail_info": {
        "w": 1920,
        "h": 1080,
        "mimetype": "image/jpeg",
        "size": 12345
      },
      "thumbnail_url": "mxc://matrix.org/XXXX",
      "attribution": [
        {
          "title": "Kenney's Nature Kit",
          "source_url": "https://kenney.nl/assets/nature-kit",
          "author_name": "Kenney",
          "author_url": "https://kenney.nl",
          "license": "CC0"
        }
      ]
    },
  },
}
```

### Featuring scene with `m.repository_room.featured_scene` state event

Admin can feature a scene by sending `m.repository_room.featured_scene` state event with
`state_key` set to the `event_id` of original scene message event. Original message `"scene"`
properties can be copied to this event. An additional `order` key is same as specified in spec to
[order space
children](https://spec.matrix.org/v1.5/client-server-api/#ordering-of-children-within-a-space) and
is used to order the featured scene.

```json
{
  "type": "m.repository_room.featured_scene",
  "state_key": "scene_message_event_id",
  "content": {
    "scene": {
      "url": "mxc:abc",
      "thumbnail_info": {
        "w": 1920,
        "h": 1080,
        "mimetype": "image/jpeg",
        "size": 12345
      },
      "thumbnail_url": "mxc://matrix.org/XXXX",
      ...
    },
    "order": ""
  },
}
```

A scene can be Unfeatured by removing content from this state event.

### Creating a [World](https://github.com/matrix-org/matrix-spec-proposals/pull/3815) with featured scene

A user can create a 3D [World](https://github.com/matrix-org/matrix-spec-proposals/pull/3815) with
featured scenes by using the content from featured scene event. Additionally `"scene_from"` property
with `"state_key"` of featured scene event and `"room_id"` of `repository_room` is added so client
can check and prompt an admin for future featured scene updates.

```json
{
  "type": "m.world",
  "state_key": "",
  "content": {
    "scene_url": "",
    "thumbnail_info": {
      "w": 1920,
      "h": 1080,
      "mimetype": "image/jpeg",
      "size": 12345
    },
    "thumbnail_url": "mxc://matrix.org/XXXX",
    "scene": {
      "url": "mxc:abc",
      "thumbnail_info": {
        "w": 1920,
        "h": 1080,
        "mimetype": "image/jpeg",
        "size": 12345
      },
      "thumbnail_url": "mxc://matrix.org/XXXX",
      ...
    },
    "scene_from": {
      "state_key": "featured_scene_state_key",
      "room_id": "repository_room_id"
    }
  }
}
```

### Featuring world with `m.repository_room.featured_world` state event

A public [World](https://github.com/matrix-org/matrix-spec-proposals/pull/3815) can be featured by
sending `m.repository_room.featured_world` state event with `"state_key"` as `room_id` of the
World. `"content"` of this event is same as
[`m.space.child`](https://spec.matrix.org/v1.5/client-server-api/#mspacechild). Client can use
[MSC3266: Room summary API](https://github.com/matrix-org/matrix-spec-proposals/pull/3266) to
display world to user.

```json
{
  "type": "m.repository_room.featured_world",
  "state_key": "world_id",
  "content": {
    "suggested": false,
    "via": [],
    "order": ""
  }
}
```

### Featuring room with  `m.repository_room.featured_room` state event

This state event is same as `m.repository_room.featured_world` but for featuring normal matrix
chat room.

```json
{
  "type": "m.repository_room.featured_room",
  "state_key": "room_id",
  "content": {
    "suggested": false,
    "via": [],
    "order": ""
  }
}
```

## Issues

* A featured World/room can not be joined if room owner made them invite only. Client should not
  display such rooms by looking at the `join_rule` return by [MSC3266: Room summary
  API](https://github.com/matrix-org/matrix-spec-proposals/pull/3266)

## Unstable prefix
* `org.matrix.msc3948.repository_room` - Repository room type
* `org.matrix.msc3948.repository_room.scene` - Scene message event type
* `org.matrix.msc3948.repository_room.featured_scene` - Featured scene state event type
* `org.matrix.msc3948.repository_room.featured_world` - Featured world state event type
* `org.matrix.msc3948.repository_room.featured_room` - Featured room state event type

## Dependencies

* [MSC3815: 3D Worlds](https://github.com/matrix-org/matrix-spec-proposals/pull/3815)
* [MSC3266: Room summary API](https://github.com/matrix-org/matrix-spec-proposals/pull/3266)
