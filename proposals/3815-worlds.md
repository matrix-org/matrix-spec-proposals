# MSC3815: Worlds

Worlds are 3D Matrix rooms currently being developed in the [Third Room
project](https://thirdroom.io). This spec defines a new room type, additional state events, and
account state keys used to describe 3D worlds, avatars, profiles, and members of 3D worlds.

## Proposal

### `m.world` room type

This is a new room type used to determine that the Matrix room should render a 3D scene in
supporting clients.

Clients which support rendering 3D worlds should then use the `m.world` state event to determine
what 3D scene to render for the room.

Clients which do not support rendering 3D worlds can still interact with members of the room as a
normal Matrix room.

```json
{
  "type": "m.room.create",
  "content": {
    "type": "m.world",
    "creator": "@example:example.org",
    "m.federate": true,
    "room_version": "9"
  }
}
```

### `m.world` state event

Describes the 3D scene to use for a Matrix room.

`scene_name` (optional) is the name of the scene. This is separate from the room name and should be
displayed with the other details describing the scene. When provided, this property overrides the
`base_scene.name` property. Either a `scene_name` or `base_scene.name` must be provided.

`scene_url` (optional) is the URL of the 3D scene to use for the room. Currently only .glb files are
supported. For supported glTF extensions see the [Third Room glTF extensions
documentation](https://thirdroom.io/docs/gltf/). When provided, this property overrides the
`base_scene.url` property. Either a `scene_url` or `base_scene.url` must be provided.

`scene_description` (optional) is a short description of the scene. When provided, this property
overrides the `base_scene.description` property.

`thumbnail_url` (optional) is the URL to an image to use while loading the scene. This should be a
large 16:9 image that is representative of the scene or your room. When provided, this property
overrides the `base_scene.info.thumbnail_url` property. Either a `thumbnail_url` or
`base_scene.info.thumbnail_url` must be provided.

`thumbnail_info` (optional) is an object that describes the thumbnail image. This uses the
`ThumbnailInfo` data structure.

`script_url` (optional) is the URL to a JavaScript or WebAssembly file that will be executed in the
3D scene. This can be used to add interactivity to the scene. See the [WebSceneGraph
documentation](https://thirdroom.io/docs/guides/websg/) for more information on scripts. When
provided, this property overrides the `base_scene.script_url` property.

`attribution` (optional) this is an array of additional attribution details that should be displayed
to the user. If `base_scene.attribution` is defined then this array will be appended to the base
scene's attributions. This is useful when you have added additional content to the base scene. The
attribution data structure is described in detail in
[MSC4032](https://github.com/matrix-org/matrix-spec-proposals/pull/4032).

`base_scene` is an asset object that describes the scene that the `scene_url` is based on. This is
used to provide info and attribution for the current scene. The properties of scene asset objects
are described in detail in [MSC3948](https://github.com/matrix-org/matrix-spec-proposals/pull/3948).

`base_scene_from` is an object that describes where the `base_scene` came from and is used to update
the `base_scene` if it has changes. `state_key` and `room_id` are used to find the asset in the
associated Repository Room which is described in detail in
[MSC3948](https://github.com/matrix-org/matrix-spec-proposals/pull/3948). When the world's version
is less than the version in the Repository Room and the current user has permission to update the
world, they will be prompted to update the world to the latest version. If they have made changes to
the world or script then they will be warned that their changes will be lost if they update.

```json
{
  "type": "m.world",
  "content": {
    "scene_name": "My Forest Scene",
    "scene_description": "My remixed low poly forest scene",
    "scene_url": "mxc://example/scene.glb",
    "thumbnail_info": {
      "w": 480,
      "h": 270,
      "mimetype": "image/png",
      "size": 12345
    },
    "thumbnail_url": "mxc://matrix.org/XXXX",
    "script_url": "mxc://example/script.js",
    "attribution": [
      {
        "title": "Terrain Model",
        "source_url": "https://example.com/terrain.glb",
        "author_name": "Alice",
        "author_url": "https://example.com",
        "license": "CC-BY 4.0"
      }
    ],
    "base_scene": {
      "version": 1,
      "name": "Forest",
      "description": "A low poly forest scene",
      "url": "mxc:abc",
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
      },
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
    "base_scene_from": {
      "state_key": "featured_scene_state_key",
      "room_id": "repository_room_id"
    }
  }
}
```

### `m.world.avatars` state event

The `m.world.avatars` state event is used to define the avatars that are available to users in the
world. If this state event is not present than any custom avatars may be used in the world.

`allow_custom_avatars` (optional) is a boolean that determines if users can use custom avatars in
the room. If this is `true` then users can use any avatar they want. If this is `false` then users
can only use avatars that are defined in the `avatars` array. If this is not defined then it
defaults to `true`.

`avatars` (optional) is an array of avatar assets that should be displayed to the user when they
enter the world for the first time. Once they have selected an avatar they can set the avatar in the
`m.world.member` event. If `allow_custom_avatars` is `false` then this array must be defined. If
`allow_custom_avatars` is `true` then this array is optional.

```json
{
  "type": "m.world.avatars",
  "content": {
    "allow_custom_avatars": false,
    "avatars": [
      {
        "name": "Y Bot",
        "description": "A friendly robot",
        "url": "mxc://matrix.org/XXXX",
        "asset_type": "m.world.avatar",
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
        },
        "attribution": [
          {
            "title": "Y Bot",
            "source_url": "https://www.mixamo.com",
            "author_name": "Mixamo",
            "author_url": "https://www.mixamo.com",
          }
        ]
      }
    ]
  }
}
```

### `m.world.profile` account data

The `m.world.profile` account data event is used to store the user's default home world and avatar
as well as any other world-specific account data.

When a user first signs into a client that supports rendering 3D worlds, the client should fetch the
`m.world.profile` account data event for the user's account. If it doesn't exist it should be
created with a default `home_world_id` and `avatar_url`.

`home_world_id` is a room id/alias that the user has set as their default home world. This is the
world that the user will be placed in when they first sign in to a client that supports rendering 3D
worlds.

`avatar_url` is the URL to the user's avatar. This is used to display the user's avatar in the 3D
world.

```json
{
  "home_world_id": "!XXXX:matrix.org",
  "default_avatar_url": "mxc://example/avatar.glb",
}
```

### `m.world.member` state event

The `m.world.member` state event is used to store world-specific information about a user. This is
similar to the `m.room.member` state event but is specific to a world. Currently the only
information that is stored is the user's avatar. The `avatar_url` is copied from the user's
`m.world.profile` account data when they join a world, they also can set a custom avatar for the
world.

```json
{
  "type": "m.world.member",
  "state_key": "@alice:matrix.org",
  "content": {
    "avatar_url": "mxc://example/avatar.glb"
  }
}
```

## Potential issues

TODO

## Alternatives

TODO

## Security considerations

TODO

## Unstable prefix

`org.matrix.msc3815.world` `org.matrix.msc3815.world.avatars` `org.matrix.msc3815.world.profile`
`org.matrix.msc3815.world.member`

## Dependencies

This MSC builds on [MSC3401](https://github.com/matrix-org/matrix-doc/pull/3401) (Group Calls) which
is used for VoIP and game networking.

The data structures defined in the `m.world` and `m.world.avatars` event types are based on the data
structures defined in [MSC4032](https://github.com/matrix-org/matrix-spec-proposals/pull/4032).
