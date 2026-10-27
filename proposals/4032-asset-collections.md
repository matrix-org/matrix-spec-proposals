# MSC4032: Asset Collections

Asset Collections are intended to be a way to store one or more `mxc` files or URLs relating to a
particular room or user. Currently their primary use case is to store assets for 3D worlds
based on the [MSC3815](https://github.com/matrix-org/matrix-spec-proposals/pull/3815) proposal.

## Proposal

### Asset Types

These are the currently defined asset types:

- `m.image` - A 2D image in the PNG or JPEG format.
- `m.audio` - An audio file in the MP3 format.
- `m.video` - A video file in the MP4 format.
- `m.world.script` - A script file in the JavaScript or WebAssembly format.
- `m.world.model` - A 3D model in the glTF format.
- `m.world.avatar` - A 3D model in the glTF format that is intended to be used as an avatar.
- `m.world.scene` - A 3D model in the glTF format that is intended to be used as a scene.
- `m.world.object` - A 3D model in the glTF format that is intended to be used as an interactable object.
- `m.world.prefab` - A 3D prefab to be used in a scene.

### Base Asset data structure

```json
{
  "name": "Base Asset",
  "description": "Some asset",
  "categories": ["Category 1", "Category 2"],
  "url": "mxc://matrix.org/XXXX",
  "asset_type": "some_asset_type",
  "attribution": [
    {
      "title": "Sub Asset 1",
      "source_url": "https://example.com/sub-asset-1",
      "author_name": "Alice",
      "author_url": "https://example.com",
      "license": "CC0"
    },
    {
      "title": "Sub Asset 2",
      "source_url": "https://example.com/sub-asset-2",
      "author_name": "Bob",
      "author_url": "https://example.com",
      "license": "CC-BY-4.0"
    }
  ]
}
```

### Image Asset Data Structure

- `info` - Uses the [ImageInfo](https://spec.matrix.org/v1.6/client-server-api/#mimage) data structure.

```json
{
  // ...base asset
  "asset_type": "m.image",
  "info": {
    "w": 1920,
    "h": 1080,
    "mimetype": "image/png",
    "size": 123456,
    "thumbnail_info": {
      "w": 480,
      "h": 270,
      "mimetype": "image/png",
      "size": 12345
    },
    "thumbnail_url": "mxc://matrix.org/XXXX"
  }
}
```

### Audio Asset Data Structure

- `info` - Uses the [AudioInfo](https://spec.matrix.org/v1.6/client-server-api/#maudio) data structure.

```json
{
  // ...base asset
  "asset_type": "m.audio",
  "info": {
    "duration": 60,
    "mimetype": "audio/mpeg",
    "size": 123456
  }
}
```

### Video Asset Data Structure

- `info` - Uses the [VideoInfo](https://spec.matrix.org/v1.6/client-server-api/#mvideo) data structure.

```json
{
  // ...base asset
  "asset_type": "m.video",
  "video_info": {
    "duration": 60,
    "w": 1920,
    "h": 1080,
    "size": 123456,
    "mimetype": "video/mp4",
    "thumbnail_info": {
      "w": 480,
      "h": 270,
      "mimetype": "image/png",
      "size": 12345
    },
    "thumbnail_url": "mxc://matrix.org/XXXX"
  }
}
```

### Script Asset Data Structure

```json
{
  // ...base asset
  "asset_type": "m.world.script",
  "info": {
    "mimetype": "application/javascript",
    "size": 123456
  }
}
```

### Model Asset Data Structure

- `info` - Uses the ModelInfo data structure.
- `info.mimetype` - The mimetype of the model file.
- `info.size` - The size of the model file in bytes.
- `info.vertices` - The number of vertices in the model.
- `info.textures` - The number of textures in the model.
- `info.materials` - The number of materials in the model.
- `info.animations` - Whether the model contains animations.
- `info.audio` - Whether the model contains audio.
- `info.boundingBox` - The bounding box of the model.
- `info.boundingBox.min` - The minimum point of the bounding box.
- `info.boundingBox.max` - The maximum point of the bounding box.
- `info.thumbnail_info` - The thumbnail info of the model (uses the ThumbnailInfo data structure).
- `info.thumbnail_url` - The thumbnail URL of the model.

```json
{
  // ...base asset
  "asset_type": "m.world.model",
  "info": {
    "mimetype": "model/gltf-binary",
    "size": 123456,
    "vertices": 480,
    "textures": 1,
    "materials": 1,
    "animations": false,
    "audio": false,
    "boundingBox": {
      "min": [-1, -1, -1],
      "max": [1, 1, 1]
    },
    "thumbnail_info": {
      "w": 480,
      "h": 270,
      "mimetype": "image/png",
      "size": 12345
    },
    "thumbnail_url": "mxc://matrix.org/XXXX"
  }
}
```

### Avatar Asset Data Structure

- `info` - Uses the AvatarInfo data structure which extends from the ModelInfo data structure.
- `info.script_info` (optional) - The script info of the avatar (uses the ScriptInfo data structure).
- `info.script_info.mimetype` - The mimetype of the script file.
- `info.script_info.size` - The size of the script file in bytes.
- `info.script_url` (optional) - The script URL of the avatar.

```json
{
  // ...base asset
  "asset_type": "m.world.avatar",
  "mime_type": "model/gltf-binary",
  "info": {
    "mimetype": "model/gltf-binary",
    "size": 123456,
    "vertices": 480,
    "textures": 1,
    "materials": 1,
    "animations": false,
    "audio": false,
    "boundingBox": {
      "min": [-1, -1, -1],
      "max": [1, 1, 1]
    },
    "thumbnail_info": {
      "w": 480,
      "h": 270,
      "mimetype": "image/png",
      "size": 12345
    },
    "thumbnail_url": "mxc://matrix.org/XXXX",
    "script_info": {
      "mimetype": "application/javascript",
      "size": 123456
    },
    "script_url": "mxc://matrix.org/XXXX"
  }
}
```

### Scene Asset Data Structure

- `info` - Uses the SceneInfo data structure which extends from the ModelInfo data structure.
- `info.script_info` (optional) - The script info of the scene (uses the ScriptInfo data structure).

```json
{
  // ...base asset
  "asset_type": "m.world.scene",
  "info": {
    "mimetype": "model/gltf-binary",
    "size": 123456,
    "vertices": 480,
    "textures": 1,
    "materials": 1,
    "animations": false,
    "audio": false,
    "boundingBox": {
      "min": [-1, -1, -1],
      "max": [1, 1, 1]
    },
    "thumbnail_info": {
      "w": 480,
      "h": 270,
      "mimetype": "image/png",
      "size": 12345
    },
    "thumbnail_url": "mxc://matrix.org/XXXX",
    "script_info": {
      "mimetype": "application/javascript",
      "size": 123456
    },
    "script_url": "mxc://matrix.org/XXXX"
  }
}
```

### Object Asset Data Structure

- `info` - Uses the ObjectInfo data structure which extends from the ModelInfo data structure.

```json
{
  // ...base asset
  "asset_type": "m.world.object",
  "info": {
    "mimetype": "model/gltf-binary",
    "size": 123456,
    "vertices": 480,
    "textures": 1,
    "materials": 1,
    "animations": false,
    "audio": false,
    "boundingBox": {
      "min": [-1, -1, -1],
      "max": [1, 1, 1]
    },
    "thumbnail_info": {
      "w": 480,
      "h": 270,
      "mimetype": "image/png",
      "size": 12345
    },
    "thumbnail_url": "mxc://matrix.org/XXXX",
    "script_info": {
      "mimetype": "application/javascript",
      "size": 123456
    },
    "script_url": "mxc://matrix.org/XXXX"
  }
}
```

### Prefab Asset Data Structure

- `info` - Uses the PrefabInfo data structure.
- `info.thumbnail_info` - The thumbnail info of the prefab (uses the ThumbnailInfo data structure).
- `info.thumbnail_url` - The thumbnail URL of the prefab.

```json
{
  // ...base asset
  "asset_type": "m.world.prefab",
  "url": "prefab://prefab-name",
  "info": {
    "thumbnail_info": {
      "w": 480,
      "h": 270,
      "mimetype": "image/png",
      "size": 12345
    },
    "thumbnail_url": "mxc://matrix.org/XXXX"
  }
}
```

### Asset Collection data structure

```json
{
  "name": "My Assets",
  "description": "A collection of your uploaded assets",
  "icon_url": "/icons/my-assets.png",
  "categories": ["Models", "Images", "Audio"],
  "assets": [
    {
      "name": "Crate",
      "description": "A wooden crate.",
      "categories": ["Models"],
      "url": "mxc://matrix.org/XXXX",
      "asset_type": "m.world.model",
      "info": {
        "mimetype": "model/gltf-binary",
        "size": 123456,
        "vertices": 480,
        "textures": 1,
        "materials": 1,
        "animations": false,
        "audio": false,
        "boundingBox": {
          "min": [-1, -1, -1],
          "max": [1, 1, 1]
        },
        "thumbnail_info": {
          "w": 480,
          "h": 270,
          "mimetype": "image/png",
          "size": 12345
        },
        "thumbnail_url": "mxc://matrix.org/XXXX"
      },
      "attribution": [
        {
          "title": "Wood Material",
          "source_url": "https://example.com/wood-material",
          "author_name": "Alice",
          "author_url": "https://example.com",
          "license": "CC0"
        },
        {
          "title": "Crate Base Mesh",
          "source_url": "https://example.com/crate",
          "author_name": "Bob",
          "author_url": "https://example.com",
          "license": "CC-BY-4.0"
        }
      ]
    }
  ]
}
```

### Collection list data structure

```json
{
  "collections": [
    {
      "url": "mxc://matrix.org/XXXX",
    },
    {
      "state_key": "repository_room_key",
      "room_id": "!XXXX:matrix.org"
    }
  ]
}
```

### `m.asset_collections.my_collections` account data event

This account data event is used to store a user's personal collections.

```json
{
  "collections": [
    {
      "url": "mxc://matrix.org/XXXX",
    },
    {
      "state_key": "repository_room_key",
      "room_id": "!XXXX:matrix.org"
    }
  ]
}
```

### `m.asset_collections.user_uploads` account data event

This account data event is used to store a collection of the user's uploaded assets.

```json
{
  "name": "My Assets",
  "description": "A collection of your uploaded assets",
  "icon_url": "/icons/my-assets.png",
  "categories": ["Models", "Images", "Audio"],
  "assets": [
    {
      "name": "Crate",
      "description": "A wooden crate.",
      "categories": ["Models"],
      "url": "mxc://matrix.org/XXXX",
      "asset_type": "m.world.model",
      "info": {
        "mimetype": "model/gltf-binary",
        "size": 123456,
        "vertices": 480,
        "textures": 1,
        "materials": 1,
        "animations": false,
        "audio": false,
        "boundingBox": {
          "min": [-1, -1, -1],
          "max": [1, 1, 1]
        },
        "thumbnail_info": {
          "w": 480,
          "h": 270,
          "mimetype": "image/png",
          "size": 12345
        },
        "thumbnail_url": "mxc://matrix.org/XXXX"
      },
      "attribution": [
        {
          "title": "Wood Material",
          "source_url": "https://example.com/wood-material",
          "author_name": "Alice",
          "author_url": "https://example.com",
          "license": "CC0"
        },
        {
          "title": "Crate Base Mesh",
          "source_url": "https://example.com/crate",
          "author_name": "Bob",
          "author_url": "https://example.com",
          "license": "CC-BY-4.0"
        }
      ]
    }
  ]
}
```

### `m.asset_collections.room_uploads` room state event

This room state event is used to store the collection metadata for room uploads.

```json
{
  "type": "m.asset_collections.room_uploads",
  "content": {
    "name": "Room Uploads",
    "description": "A collection of assets uploaded to this room",
    "icon_url": "/icons/room-assets.png",
    "categories": ["Models", "Images", "Audio"]
  }
}
```

### `m.asset_collections.room_uploads.item` room state event

This room state event is used to store the data for an uploaded asset. The key should be the original mxc
media ID of the asset.

** TODO: Should we use a different key? **

```json
{
  "type": "m.asset_collections.room_uploads.item",
  "state_key": "mxc-id",
  "content": {
    "name": "Crate",
    "description": "A wooden crate.",
    "categories": ["Models"],
    "url": "mxc://matrix.org/XXXX",
    "asset_type": "m.world.model",
    "info": {
      "mimetype": "model/gltf-binary",
      "size": 123456,
      "vertices": 480,
      "textures": 1,
      "materials": 1,
      "animations": false,
      "audio": false,
      "boundingBox": {
        "min": [-1, -1, -1],
        "max": [1, 1, 1]
      },
      "thumbnail_info": {
        "w": 480,
        "h": 270,
        "mimetype": "image/png",
        "size": 12345
      },
      "thumbnail_url": "mxc://matrix.org/XXXX"
    },
    "attribution": [
      {
        "title": "Wood Material",
        "source_url": "https://example.com/wood-material",
        "author_name": "Alice",
        "author_url": "https://example.com",
        "license": "CC0"
      },
      {
        "title": "Crate Base Mesh",
        "source_url": "https://example.com/crate",
        "author_name": "Bob",
        "author_url": "https://example.com",
        "license": "CC-BY-4.0"
      }
    ]
  }
}
```

### `m.asset_collections.world_collections.item` room state event

This room state event is used to store the data for a collection in the world. The key should be
the mxc media ID of the collection.

```json
{
  "type": "m.asset_collections.room_uploads.item",
  "state_key": "mxc-id",
  "content": {
    "url": "mxc://matrix.org/XXXX"
  }
}
```

### `m.repository_room.collection` room message event

A collection can be submitted by the user using `m.repository_room.collection` message event. Other then
`attribution` and `description` all properties specified below are required to describe a collection.

`version` this property should be incremented when a new version of the collection is submitted.

`name` this is the name of the collection.

`description` (optional) this is a short description of the collection.

`url` this is the URL of the 3D collection to use for the room. Currently only .glb files are supported.
For supported glTF extensions see the
[Third Room glTF extensions](https://thirdroom.io/docs/gltf/).

`thumbnail_url` this is the URL of the thumbnail image to use for the collection.

`thumbnail_info` this is an object containing information about the thumbnail image to use for the collection. This should use the `ThumbnailInfo` type.

`attribution` (optional) this is an array of attributions for the collection.

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
  "type": "m.repository_room.collection",
  "content": {
    "collection": {
      "version": 1,
      "name": "Kenney's Nature Kit",
      "description": "A collection of nature assets.",
      "url": "mxc:abc",
      "thumbnail_info": {
        "w": 480,
        "h": 270,
        "mimetype": "image/png",
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
    }
  }
}
```

### `m.repository_room.featured_collection` room state event

Admin can feature a collection by sending `m.repository_room.featured_collection` state event with
`state_key` set to the `event_id` of original collection message event. Original message `"collection"`
properties can be copied to this event. An additional `order` key is same as specified in spec to
[order space
children](https://spec.matrix.org/v1.5/client-server-api/#ordering-of-children-within-a-space) and
is used to order the featured collection.

```json
{
  "type": "m.repository_room.featured_collection",
  "state_key": "collection_message_event_id",
  "content": {
    "collection": {
      "url": "mxc:abc",
      "thumbnail_info": {
        "w": 480,
        "h": 270,
        "mimetype": "image/png",
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

## Potential issues

TODO

## Alternatives

TODO

## Security considerations

TODO

## Unstable prefix

* `org.matrix.msc4032.world.script` - Script asset type
* `org.matrix.msc4032.world.model` - Model asset type
* `org.matrix.msc4032.world.avatar` - Avatar asset type
* `org.matrix.msc4032.world.scene` - Scene asset type
* `org.matrix.msc4032.world.object` - Object asset type
* `org.matrix.msc4032.world.prefab` - Prefab asset type
* `org.matrix.msc4032.asset_collections.my_collections` - User's collections
* `org.matrix.msc4032.asset_collections.user_uploads` - User's uploads collection
* `org.matrix.msc4032.asset_collections.room_uploads` - Room's uploads collection
* `org.matrix.msc4032.asset_collections.room_uploads.item` - Room upload
* `org.matrix.msc4032.asset_collections.world_collections.item` - World collections
* `org.matrix.msc4032.repository_room.collection` - Repository room collection
* `org.matrix.msc4032.repository_room.featured_collection` - Repository room featured collection

## Dependencies

TODO
