# MSC3386: Unified Join Rules

[MSC2403 Knock](https://github.com/matrix-org/matrix-doc/pull/2403) and [MSC3083 Restricting room membership based on membership in other rooms](https://github.com/matrix-org/matrix-doc/pull/3083) both update the join rules of a room to allow a new feature. The former defines `join_rule: knock` which allows anyone to knock to enter a room and the latter defines `join_rule: restricted` to restrict who can join a room based on a set of rules. Unfortunately these features can not be used together as a room can only have one `join_rule`.

This MSC aims to solve the proliferation of `join_rule`s and allow these features to interoperate.

## Proposal

In a future room version the meaning of the `m.room.join_rules` state event will be changed to the following.

### `join_rule`

The `join_rule` key is removed.

### `allow_join`

`allow` will be renamed to `allow_join`. Otherwise its meaning is unchanged.

The `allow_join` key may be absent in which case it is treated as if it was set to `[]` (the empty list). In this case no one is allowed to join without an invite.

### `allow_knock`

An `allow_knock` key will be allowed. This functions identically to the `allow_join` key except that it controls who can knock, instead of controlling who can join. Please see [MSC3083 Restricting room membership based on membership in other rooms](https://github.com/matrix-org/matrix-doc/pull/3083) for how the rules are evaluated and [MSC2403 Knock](https://github.com/matrix-org/matrix-doc/pull/2403) for what it means to knock.

The `allow_knock` key may be absent in which case it is treated as if it was set to `[]` (the empty list). In this case no one is allowed to knock.

### `m.any`

The `m.any` allow type will be defined. This type allows any user to perform the relevant action. The may be used in both the `allow_join` and `allow_knock` fields.

### Example: Anyone can knock

This shows an example of a room where you can join if you are a member of `!users:example.org` otherwise you can only knock.

```json5
{
	"type": "m.room.join_rules"
	"state_key": ""
	"content": {
		"allow_join": [{
			"type": "m.room_membership"
			"room_id": "!users:example.org"
		}]
		"allow_knock": [{
			"type": "m.any"
		}],
	},
}
```

### Example: Restricted knock

This shows an example of a room where anyone in the `!users:example.org` room (or space) can knock, but anyone in `!mods:example.org` can join directly.

```json5
{
	"type": "m.room.join_rules"
	"state_key": ""
	"content": {
		"allow_join": [{
			"type": "m.room_membership"
			"room_id": "!mods:example.org"
		}]
		"allow_knock": [{
			"type": "m.room_membership"
			"room_id": "!users:example.org"
		}]
	}
}
```

### Conversion

When upgrading a room the following rules can be used to generate a new `join_rules` that matches the previous `join_rules`.

#### `invite`

A `join_rules` state event with `join_rule: invite` can be replaced by the following `join_rules`.

```json5
{
	"type": "m.room.join_rules"
	"state_key": ""
	"content": {}
}
```

#### `public`

A `join_rules` state event with `join_rule: public` can be replaced by the following `join_rules`.

```json5
{
	"type": "m.room.join_rules"
	"state_key": ""
	"content": {
		"allow_join": [{
			"type": "m.any"
		}]
	}
}
```

#### `knock`

A `join_rules` state event with `join_rule: knock` can be replaced by the following `join_rules`.

```json5
{
	"type": "m.room.join_rules"
	"state_key": ""
	"content": {
		"allow_knock": [{
			"type": "m.any"
		}]
	}
}
```

#### `restricted`

A `join_rules` state event with `join_rule: restricted` can be replaced by an event with the following template. Substitute the previous elements from the `allow` attribute into the `allow_join` attribute.

```json5
{
	"type": "m.room.join_rules"
	"state_key": ""
	"content": {
		"allow_join": // Value from `allow` attribute of previous `join_rules`.
	}
}
```

For example the following `join_rules`...

```json5
{
	"type": "m.room.join_rules"
	"state_key": ""
	"content": {
		"join_rule": "restricted"
		"allow": [ {
			"type": "m.room_membership"
			"room_id": "!mods:example.org"
		}, {
			"type": "m.room_membership"
			"room_id": "!users:example.org"
		}]
	}
}
```

...becomes...

```json5
{
	"type": "m.room.join_rules"
	"state_key": ""
	"content": {
		"allow_join": [{
			"type": "m.room_membership"
			"room_id": "!mods:example.org"
		}, {
			"type": "m.room_membership"
			"room_id": "!users:example.org"
		}]
	}
}
```

## Potential issues

### Useless `allow_knock` entires.

It is possible that entries in `allow_knock` are redundant because they are also included in `allow_join` so could simply join directly. While this is unsightly it is non-harmful and will not affect users or servers.

```json5
{
	"type": "m.room.join_rules"
	"state_key": ""
	"content": {
		"allow_join": [{
			"type": "m.any"
		}]
		// This is irrelevant because anyone can directly join.
		"allow_knock": [{
			"type": "m.room_membership"
			"room_id": "!users:example.org"
		}]
	}
}
```

```json5
{
	"type": "m.room.join_rules"
	"state_key": ""
	"content": {
		"allow_join": [{
			"type": "m.room_membership",
			"room_id": "!users:example.org"
		}]
		// This is irrelevant because everyone in this room can join directly.
		"allow_knock": [{
			"type": "m.room_membership"
			"room_id": "!users:example.org"
		}]
	}
}
```

```json5
{
	"type": "m.room.join_rules"
	"state_key": ""
	"content": {
		"allow_join": [{
			"type": "m.any"
		}, {
			// This is irrelevant because of the m.any rule.
			"type": "m.room_membership",
			"room_id": "!users:example.org"
		}]
	}
}
```

Clients may consider helping users to clean up unnecessary elements from the `allow_join` and `allow_knock` lists.

## Alternatives

### Introduce a new mechanism for knock.

Knock is arguably not a join rule, it is a rule for who may request an invite. It could be moved to a separate mechanism to avoid the conflict with `join_rule: restricted`.

This MSC is a better alternative because:

- Knock does affect how people may join a room so it makes sense to handle it in the same location as other ways to join.
- Allowing `m.room_membership` restricted knocking is a useful feature that appears "for free" with this unification.

## Security considerations

Other than the general risk of adding complexity to `join_rules` there are no further security implications.

It is worth noting the [Security considerations of `m.room_membership`](./3083-restricted-rooms.md#security-considerations) as this MSC does not improve them and the same concerns apply (although with less consequences) to `allow_knock`.

## Unstable prefix

Until this specification is approved please the follow changes should be used for implementation:
- Use `ca.kevincox.allow_knock.v1` instead of the `allow_knock` attribute.
- use `ca.kevincox.any.v1` instead of `type: m.any`.
