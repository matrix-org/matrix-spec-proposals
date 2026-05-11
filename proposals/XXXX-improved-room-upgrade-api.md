# MSC0000: Improved Room Upgrade API

## Introduction

The current room upgrade API leaves almost all behavior as implementation detail and server controlled
with a total of 2 variables that are caller controlled. That being additional creators for v12 and later
in addition to what room version you desire.

This proposal proposes a new set of capabilities that indicates room upgrade behavior and a way to control
these behaviors.

`m.room_upgrade_capabilities` will contain a list of room upgrade related capabilities the homeserver posesses
both lists of what events will have their content migrated or what keys of what events will be migrated if
only partially migrated. But also what external attributes are moved like for example room directory listings
or local aliases.

This data is used to control the behavior of the new `POST /_matrix/client/v4/rooms/{roomId}/upgrade`
api endpoint.

This aims to enable clients to take full control over the room upgrade process while allowing the server
to help out in whatever ways the requesting client deems acceptable.

## Proposal

### `m.room_upgrade_capabilities` Schema

The new `m.room_upgrade_capabilities` capability schema is showed in this example below and later described.

```json
{
  "capabilities": {
    "m.room_upgrade_capabilities": {
      "migrated_events": [
        "m.room.name",
        "m.room.topic",
        "m.room.avatar",
        "m.room.join_rules",
        "m.room.history_visibility",
        "m.room.guest_access"
      ],
      "partially_migrated_events": {
        "m.room.power_levels": {
          "action": "include",
          "keys": [
            "users",
            "users_default",
            "events",
            "events_default",
            "state_default",
            "ban",
            "kick",
            "redact",
            "invite"
          ]
        },
        "m.room.create": {
          "action": "exclude",
          "keys": [
            "predecessor",
            "additional_creators"
          ]
        },
        "m.room.member": {
          "action": "include",
          "conditions": {
            "membership": "ban"
          },
          "keys": [
            "membership",
            "reason"
          ]
        }
      },
      "migrated_external_attributes": [
        "m.local_room_directory",
        "m.local_aliases"
      ]
    }
  }
}
```

#### Explanation of `m.room_upgrade_capabilities` Schema

* **`migrated_events`**: An array of event type strings. This clearly describes to the client which state events
  the server will seamlessly migrate to the new room, with full content preservation.
* **`partially_migrated_events`**: A key-value mapping where the key is the event type and the value is an
  object instructing how the properties are migrated. It contains:
  * **`action`**: Must be `"include"` or `"exclude"`. `"include"` means only the listed keys are migrated.
    `"exclude"` means all content properties migrate *except* the listed ones.
  * **`keys`**: An array of string keys inside the event's `content` to include or exclude.
  * **`conditions`**: (Optional) A map of key-value pairs that the event's content must match for this migration
    rule to apply. For example, `{"membership": "ban"}` restricts the rule so the server will only migrate
    `m.room.member` events representing user bans. Depending on the server's capabilities, multiple rule objects
    could theoretically be supported via an array if needed, but for simplicity a single condition block allows
    constraining the migration. (Needs further exploration)
* **`migrated_external_attributes`**: An array of string identifiers describing which external integrations or
  server-side metadata will be migrated during the upgrade (e.g., `local_room_directory` to update the room directory,
  `local_aliases` to move aliases to the new room).

The logic behind the shape of this schema is that it allows the server to accurately describe its behavior
during a room upgrade. So that the client can decide what behavior it would rather take on it self / disable.

The logic for the conditions attribute is just to have some way to express the special behavior that ban
copying has in a generic manner so any other cases like that are covered.

#### List of External Attributes

This MSC defines `m.local_room_directory` and `m.local_aliases` as external attributes initially leaving extending
this list to future proposals or vendored extensions.

`m.local_room_directory` means that the local room directory listing will be migrated automatically.
The server cant migrate remote directories at this time and if that ever becomes a capability it will
have its own capability.

`m.local_aliases` means that the local aliases for the room will be moved when the room is upgraded.
As the server cant migrate remote aliases at this time this capability is only talking about local aliases.
Same as with room directories if the server gains the ability to migrate remote aliases its a separate capability.

### `POST /_matrix/client/v4/rooms/{roomId}/upgrade`

The new version of the upgrade endpoint inherits the v3 endpoint behavior of having the `additional_creators`
and `new_version` keys in the request body.

This version also consumes the new `migration_schema` key that has the following schema.

```json
{
  "migration_schema": {
    "events": {
      "action": "exclude",
      "list": [
        "m.room.guest_access"
      ]
    },
    "external_attributes": {
      "action": "include",
      "list": [
        "m.room_directory"
      ]
    },
    "create_room_override": {
      "creation_content": {
        "m.federate": false
      },
      "initial_state": [
        {
          "type": "m.room.history_visibility",
          "content": {
            "history_visibility": "invited"
          }
        }
      ]
    }
  }
}
```

#### Explanation of `migration_schema`

* **`events`**: An object controlling which state events to migrate from the server's supported capabilities.
  * **`action`**: Must be `"include"` or `"exclude"`. `"include"` instructs the server to only migrate the event
    types specified in `list`. `"exclude"` instructs the server to migrate all supported event types *except* those
    in `list`.
  * **`list`**: An array of event type strings to apply the action against.
* **`external_attributes`**: Controls the migration of external server-side metadata, using the identical `action`
  and `list` structure as `events`. (e.g., using `include` with `m.room_directory` to only keep the directory
  listing but drop local aliases).
* **`create_room_override`**: An object whose schema directly aligns with the request body of the standard
  `POST /_matrix/client/v3/createRoom` API. During the upgrade process, the server will merge these parameters
  into the setup of the new room, with values from here strictly taking precedence over the server's default or
  derived migration logic. The create room schema in this API does exclude the ability to set the room id
  of the predecessor room. This is because this is controlled via the invokation of the API it self.
  `additional_creators` is also ignored as its controlled via the root level request body key.
  The room version parameter is also ignored as its also controlled via the root level request body key.

The logic for this schema is actually relatively simple. Using the capabilities the server gives the client
we have enough information to tell the server to please not touch a specific area. Simpler clients will probably
exclusively deal in excluded events but more advanced clients can expose all this raw complexity via GUI and
deliver this choice to the end user.

As for the purpose of the `create_room_override`. That exists to give all the power and flexibility of a manual
room upgrade to this process. This MSC is intended to in spirit deprecate the need for manual room upgrades.

It should be noted that its fully intentional that attributes like encryption are not protected under this schema.
This is because upgrading a room to disable E2EE is a fully supported usecase for this proposal as its a
common irreversible mistake beginners make.

Room types are also not rendered immune as this proposal is intended to account for situations like upgrading
a policy list. If upgrading a policy list to have a room type like is proposed by MSC3784 then you need to
have the abilit to set your own room type. This capability is provided via the `create_room_override`

### Ratelimited / Authenticated

The capabilities response will inherit these attributes from the capabilities endpoint.

The new `POST /_matrix/client/v4/rooms/{roomID}/upgrade` endpoint is rate limited and authenticated.

Any other stance than rate limited and authenticated would not be defensible as a default. Unlimited room creation
is not recomended especially as your allowed to issue invites via this endpoint due to creation content.
And invites may also be spawned via this endpoint for servers that migrate private rooms that way.

## Potential issues

This proposal does propose some decently complex mechanisms to be introduced for handling room upgrades
and that can be a problem for homeservers and clients alike. This complexity is argued for in this MSC
as a necessary evil. The current API behavior is not compatible with serious work has been argued plenty
in the ecosystem.

There is also the very serious issue of that clients who use include migration schemas and not exclusions
can fall out of date with critical new events. Like policy servers. This is
addressed by the fact that its only advanced clients that are recomended to run inclusion migrations. These
clients are expected to know the consequences of their actions or to give this complexity straight
to the user.

Some clients may find that the current all or nothing for a given state event nature of the migration schema
is too coarse. It was deemed to be a acceptable tradeoff to make the API ergonomics better.

## Alternatives

The primary alternative considered would be to split this out into a dedicated endpoint instead of versioning
the upgrade endpoint but that was dismissed as not needed. This behavior fits into the intent for upgrade.

There is also the alternative of skipping the complexity via telling the server to disable all this behavior.
This solution was rejected because most users of /upgrade have a short list of problems with the endpoint,
that when addresed makes the endpoint totally usable and actually useful.

It was considered to make a separate endpoint that can be described as a bare room creation endpoint that disables
all server fancyness in setting up rooms except joining after creation but thats not an alternative.
That is a separate feature that happens to help out room upgrades. That idea can be explored by another
proposal in more detail.

## Security considerations

The new capabilities data shouldnt be sensetive but servers are free to lock away the data behind authenticated
status as the capabilities endpoint allows authentication. And the new upgrade endpoint also requires auth
and does instruct you to rate limit it.

And the primary security risk i see for this endpoint is actually in the logic around the create event stuff.
That can be a bit of a pita to parse. But since this proposal doesnt introduce any concept like that the server
runs a migration script we reduce the attack surface there. The fact that the migration schema
is designed as simple as it is has security perks. Simple boleans have much less attack surface after all.

No further security considerations have been identified at this time.

## Unstable prefix

`POST /_matrix/client/v4/rooms/{roomID}/upgrade` turns into `POST /_matrix/client/unstable/rooms/{roomID}/support.feline.mscXXXX.v1.upgrade`

And `m.room_upgrade_capabilities` in the capabilities response becomes `support.feline.mscXXXX.v1.room_upgrade_capabilities`

And the following external attribute maps become.

`m.local_room_directory` -> `support.feline.mscXXXX.v1.local_room_directory`
`m.local_aliases` -> `support.feline.mscXXXX.v1.local_aliases`

## Dependencies

This MSC does not have any dependencies not part of the latest spec release.
