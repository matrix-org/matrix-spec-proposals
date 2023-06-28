# MSCXXXX: Asset Collections

Asset Collections are intended to be a way to store one or more `mxc` files or URLs relating to a
particular room or user. Currently their primary use case is to store assets for 3D worlds
based on the [MSC3815](https://github.com/matrix-org/matrix-spec-proposals/pull/3815) proposal.

## Proposal

### Asset Types

These are the currently defined asset types:

- `image` - A 2D image in the PNG or JPEG format.
- `audio` - An audio file in the MP3 format.
- `video` - A video file in the MP4 format.
- `script` - A script file in the JavaScript or WebAssembly format.
- `model` - A 3D model in the glTF format.
- `avatar` - A 3D model in the glTF format that is intended to be used as an avatar.
- `scene` - A 3D model in the glTF format that is intended to be used as a scene.
- `object` - A 3D model in the glTF format that is intended to be used as an interactable object.

### Base Asset data structure

```json
{
  "name": "Base Asset",
  "description": "Some asset",
  "categories": ["Category 1", "Category 2"],
  "preview_url": "mxc://matrix.org/XXXX",
  "url": "mxc://matrix.org/XXXX",
  "mime_type": "image/png",
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

```json
{
  // ...base asset
  "asset_type": "image",
  "mime_type": "image/png",
  "image_info": {
    "width": 1920,
    "height": 1080
  }
}
```

### Audio Asset Data Structure

```json
{
  // ...base asset
  "asset_type": "audio",
  "mime_type": "audio/mpeg",
  "audio_info": {
    "duration": 60
  }
}
```

### Video Asset Data Structure

```json
{
  // ...base asset
  "asset_type": "video",
  "mime_type": "video/mp4",
  "video_info": {
    "duration": 60,
    "width": 1920,
    "height": 1080
  }
}
```

### Script Asset Data Structure

```json
{
  // ...base asset
  "asset_type": "script",
  "mime_type": "application/javascript"
}
```

### Model Asset Data Structure

```json
{
  // ...base asset
  "asset_type": "model",
  "mime_type": "model/gltf-binary",
  "model_info": {
    "triangles": 480,
    "materials": 1,
    "animations": false,
    "boundingBox": {
      "min": [-1, -1, -1],
      "max": [1, 1, 1]
    }
  }
}
```

### Avatar Asset Data Structure

```json
{
  // ...base asset
  "asset_type": "avatar",
  "mime_type": "model/gltf-binary",
  "avatar_info": {
    "script_url": "mxc://matrix.org/XXXX",
    "triangles": 480,
    "materials": 1,
    "boundingBox": {
      "min": [-1, -1, -1],
      "max": [1, 1, 1]
    }
  }
}
```

### Scene Asset Data Structure

```json
{
  // ...base asset
  "asset_type": "scene",
  "mime_type": "model/gltf-binary",
  "scene_info": {
    "script_url": "mxc://matrix.org/XXXX",
    "triangles": 480,
    "materials": 1,
    "boundingBox": {
      "min": [-1, -1, -1],
      "max": [1, 1, 1]
    }
  }
}
```

### Object Asset Data Structure

```json
{
  // ...base asset
  "asset_type": "object",
  "mime_type": "model/gltf-binary",
  "object_info": {
    "script_url": "mxc://matrix.org/XXXX",
    "triangles": 480,
    "materials": 1,
    "boundingBox": {
      "min": [-1, -1, -1],
      "max": [1, 1, 1]
    }
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
      "preview_url": "mxc://matrix.org/XXXX",
      "url": "mxc://matrix.org/XXXX",
      "asset_type": "model",
      "model_info": {
        "triangles": 480,
        "materials": 1,
        "animations": false,
        "boundingBox": {
          "min": [-1, -1, -1],
          "max": [1, 1, 1]
        }
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
      "preview_url": "mxc://matrix.org/XXXX",
      "url": "mxc://matrix.org/XXXX",
      "asset_type": "model",
      "model_info": {
        "triangles": 480,
        "materials": 1,
        "animations": false,
        "boundingBox": {
          "min": [-1, -1, -1],
          "max": [1, 1, 1]
        }
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
    {
      "name": "Crate",
      "description": "A wooden crate.",
      "categories": ["Models"],
      "preview_url": "mxc://matrix.org/XXXX",
      "url": "mxc://matrix.org/XXXX",
      "asset_type": "model",
      "model_info": {
        "triangles": 480,
        "materials": 1,
        "animations": false,
        "boundingBox": {
          "min": [-1, -1, -1],
          "max": [1, 1, 1]
        }
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

`preview_url` this is the URL of the preview image to use for the room. This should be a
high resolution, compressed, 16:9 aspect ratio image that is representative of the collection.

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
      "preview_url": "mxc:abc",
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
      "preview_url": "mxc:abc",
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

TODO

## Dependencies

TODO
