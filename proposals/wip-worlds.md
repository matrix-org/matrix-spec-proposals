# MSC3815: Worlds

Worlds are 3D Matrix rooms currently being developed in the Third Room project. This spec defines additional state events that describe what 3D scene should be used for a room and what 3D avatar models should be used for each room member.

## Proposal

### `m.world` room type

Used to determine that the Matrix room should render a 3D scene in supporting clients.

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

Describes the 3D scene to use for a Matrix room as well as a thumbnail to use while the scene is loading or for other use in the client UI.

```json
{
  "type": "m.world",
  "content": {
    "scene_url": "mxc://example/scene.glb",
    "scene_preview_url": "mxc://example/thumbnail.jpeg"
  }
}
```

### `m.world.member` state event

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

TODO

## Dependencies

This MSC builds on MSC3401 (Group Calls) which is used for VoIP and game networking.
