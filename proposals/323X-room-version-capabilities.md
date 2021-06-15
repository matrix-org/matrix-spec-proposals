# MSCXXXX: Room version capabilities

Room version updates can bring new functionalities, for example v7 is introducing `knocking`.

There is a delay before a room version became the default version (when supported by enough home servers).
And when creating rooms clients should not ask for a specific version (or else they will stick to this
specific version unless they are updated).

So currently clients can't know before creating the room if a feature they need will be supported by the created room.

The goal of this MSC is to give the client a way to have more informations on the supported features of room
versions available on a given server, to give more feedbacks to users during room creation as well as
in the room settings section.

## Proposal

The __m.room_versions capability__  [`/_matrix/client/r0/capabilities`]([https://matrix.org/docs/spec/client_server/r0.6.1#m-room-versions-capability])
enpoint could be decorated to provide more information on room version capabilities.

Actual capabilities response:
````
{
  "capabilities": {
    "m.room_versions": {
      "default": "6",
      "available": {
        "1": "stable",
        "2": "stable",
        "3": "stable",
        "4": "stable",
        "5": "stable",
        "6": "stable",,
        "org.matrix.msc2176": "unstable",
        "org.matrix.msc3083": "unstable"
      }
    },
    "m.change_password": {...}
  }
}
````

Proposed modification

````
{
  "capabilities": {
    "m.room_versions": {
      "default": "6",
      "available": {
        "1": "stable",
        "...,
        "6": "stable",
        "7": "stable",
        "8": "stable",
        "9": "stable"
      },
      "room_capabilities": {
          "msc2403" : {
              "best": "7",
              "support" : ["7"]
          },
          "msc3083" : {
              "best": "9",
              "support" : ["8", "9"]
          }
      }
    }
  }
}
````

A new object is added under `room_capabilities`, each key is the name of a capability.
This object provides the list of room version supporting this capability as well as the preferred version to use.


As part of this MSC, two capabilities are defined:
- msc2403 a.k.a knocking join rule support
- msc3083 a.k.a restricted join rule support 

## Client recommendations:

When presenting room settings, clients should use capabilities in order to display the correct UI. 

For example if the room support knocking, the client should add this option in the join rule chooser
(and if not only show `Invite Only` and `Public` for example).

When creating a room, client could check if the needed feature is supported by the server before creating.

If the feature is not supported, the client could inform the user that this type of room can't be created
as well as an information message explaining how to contact the homeserver admin.

If the feature is supported by the default room version, then just continue as usual.

If the feature is supported but by a stable room version that is not the default one, the client should
then request to use the preferred version (`best`) that supports the feature, in the create room call:

````
POST /_matrix/client/r0/createRoom HTTP/1.1
Content-Type: application/json

{
  "preset": "....",
  "name": "....",
  "topic": "....",
  "creation_content": { ... }
  "room_version": "8"
}
````

If multiple capabilities are needed, then the client should peek on of the common stable version
in `support`even if not defined as `best`

It is not recommanded to use an unstable room version even if it's the only one supporting a given feature.
It should be reserved for development.


## Potential issues


## Alternatives

````
 "room_capabilities": {
          "7" : ["msc2403"],
          "8" :  ["msc2403", "msc3083"]
      }
````

A new field is added under `room_capabilities`, and for each available room version a list of `string`
capabilities is provided.
The room versions are ordered, if a capabilities is supported by several unstable room version, the latest is the prefered one.

## Security considerations


## Unstable prefix

The following mapping will be used for identifiers in this MSC during development:


Proposed final identifier       | Purpose | Development identifier
------------------------------- | ------- | ----
`room_capabilities` | event type | `org.matrix.mscXXX.room_capabilities`
