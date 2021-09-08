# MSC3386: Unified Join Rules

[MSC2403 Knock](https://github.com/matrix-org/matrix-doc/pull/2403) and [MSC3083 Restricting room membership based on membership in other rooms](https://github.com/matrix-org/matrix-doc/pull/3083) both update the join rules of a room to allow a new feature. The former defines `join_rule: knock` which allows anyone to knock to enter a room and the latter defines `join_rule: restricted` to restrict who can join a room based on a set of rules. Unfortunately these features can not be used together as a room can only have one `join_rule`.

This MSC aims to solve the proliferation of `join_rule`s and allow these features to interoperate.

As an added benefit this MSC is backwards-compatible. The `allow_knock` field can be added to an existing `join_rules: restricted` room and people can start knocking as it is supported by their servers and clients.

## Proposal

### `allow_knock`

`join_rule: restricted` will be updated with the `allow_knock` key. This functions identically to the `allow` key except that it controls who can knock, instead of controlling who can join. Please see [MSC3083 Restricting room membership based on membership in other rooms](https://github.com/matrix-org/matrix-doc/pull/3083) for how the rules are evaluated and [MSC2403 Knock](https://github.com/matrix-org/matrix-doc/pull/2403) for what it means to knock.

The `allow_knock` key may be absent in which case it is treated as if it was set to `[]` (the empty list). In this case no one is allowed to knock.

### `m.any`

The `m.any` allow type will be defined. This type allows any user to perform the relevant action. The may be used in both the `allow` and `allow_knock` fields.

### Example: Anyone can knock

This shows an example of a room where you can join if you are a member of `!users:example.org` otherwise you can only knock.

```json5
{
	"type": "m.room.join_rules"
	"state_key": ""
	"content": {
		"join_rule": "restricted"
		"allow": [{
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
		"join_rule": "restricted"
		"allow": [{
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

## Potential issues

### Useless allow_knock entires.

It is possible that entries in `allow_knock` are redundant because they are also included in `allow` so could simply join directly. While this is unsightly it is non-harmful and will not affect users or servers.

```json5
{
	"type": "m.room.join_rules"
	"state_key": ""
	"content": {
		"join_rule": "restricted"
		"allow": [{
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
		"join_rule": "restricted"
		"allow": [{
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
		"join_rule": "restricted"
		"allow": [{
			"type": "m.any"
		}, {
			// This is irrelevant because of the m.any rule.
			"type": "m.room_membership",
			"room_id": "!users:example.org"
		}]
	}
}
```

Clients may consider helping users to clean up unnecessary elements from the `allow` and `allow_knock` lists.

### Multiple ways to specify the same rules.

After this MSC is implemented it will be possible to specify all other (current) `join_rule` types in terms of `join_rule: restricted`.

This is considered a feature. Once this MSC is widely supported it is expected that rooms are created using `join_rule: restricted` preferentially for simplicity. The other types can be considered deprecated. In order to simplify the protocol a future room version may consider dropping support for anything but `restricted`.

The following is equivalent to `join_rule: public` (as far as join rules are concerned).

```json5
{
	"type": "m.room.join_rules"
	"state_key": ""
	"content": {
		"join_rule": "restricted"
		"allow": [{
			"type": "m.any"
		}]
	}
}
```

The following is equivalent to `join_rule: invite`.

```json5
{
	"type": "m.room.join_rules"
	"state_key": ""
	"content": {
		"join_rule": "restricted"
		"allow": []
	}
}
```

The following is equivalent to `join_rule: knock`.

```json5
{
	"type": "m.room.join_rules"
	"state_key": ""
	"content": {
		"join_rule": "restricted"
		"allow": []
		"allow_knock": [{
			"type": "m.any"
		}]
	}
}
```

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
