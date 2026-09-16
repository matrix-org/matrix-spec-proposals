# MSC4544: Rich Presences in Matrix

# Abstract

This MSC proposes a mechanism for Matrix users to share rich presence data (such as currently playing games, listening to music, or other activities) over a new `m.rpc` profile field. This MSC defines a local transport protocol for Matrix clients to receive presence data from supported apps (examples: games, media players, etc) and a data model for structured presence entries.

# Proposal
## Data transport

Matrix clients supporting rich presences SHOULD listen for WebSocket connections using one of the following:

- **Unix domain socket** at `/tmp/.[client_name]_[opaque_id]/presence.sock`
- **HTTP** at `ws://localhost:{port}/presence`

The minimal available port from the range `44190`–`45190` SHOULD be selected.

The `[opaque_id]` component in the Unix socket path MUST NOT be directly traceable to the user's Matrix ID. Implementations SHOULD use a salted hash (e.g., HMAC-SHA256) of the Matrix user ID. A truncated hash is acceptable.

Compatible apps send rich presence data to the running Matrix client's WebSocket server using the message format described below.

### Message format

Each WebSocket message is a JSON object. Two message types are defined.

#### Add presence

```json
{
	"type": "add_presence",
	"data": {
		"id": "ed6f7005-77db-4fc0-8644-9ac18120cd40",
		"type": "m.rpc.activity",
		"name": "Super Tux Kart",
		"state": "Playing",
		"details": "Character: Tux",
		"expiry": 1789566446997
	},
	"app_id": {
		"id": "0fbaf247-2e0c-4bae-be93-5f40aa71e604",
		"name": "Super Tux Kart"
	}
}
```

- `data`. A **PresenceDataObject**.
- `app_id`. An **AppIdentifierObject**.

#### Remove presence

```json
{
	"type": "remove_presence",
	"data": {
		"id": "ed6f7005-77db-4fc0-8644-9ac18120cd40"
	},
	"app_id": {
		"id": "0fbaf247-2e0c-4bae-be93-5f40aa71e604",
		"name": "Super Tux Kart"
	}
}
```

- `data`. An object containing only the `id` field of the presence to remove.
- `app_id`. **AppIdentifierObject** that originally added the presence.

### AppIdentifierObject

Contains the following fields:

- **`id`**. A locally generated application identifier, preferably unique per installation (e.g., UUID v4).
- **`name`**. A human-readable application name.

Clients MUST provide a user-facing interface to manage which apps are allowed to broadcast presences. This interface SHOULD allow:

- Viewing all apps that have requested presence access.
- Allowing or denying presences per app.
- Setting a default policy (allow or deny). The default MUST be **deny**.

### ButtonDataObject

Contains the following fields:

- **`label`**. Visible button label.
- **`url`**. Link that should be opened upon clicking the button. May contain the `{openid_data}` placeholder when `request_openid` is `true`.
- **`request_openid`**. Optional boolean, defaults to `false`. If `true`, the client MUST request an OpenID token from the user's homeserver (using `/_matrix/client/v3/user/{userId}/openid/request_token`) and replace `{openid_data}` in `url` with the URL-encoded JSON representation of the OpenID response before navigation.

A presence entry MAY contain up to 3 buttons.

#### User confirmation

Clients MUST prompt the user before navigating to any button `url`. The prompt MUST display the fully-resolved URL so the user can inspect the destination before proceeding.

For buttons with `request_openid: true`, the prompt MUST additionally disclose that an OpenID request will be performed and warn about the associated risks: IP address disclosure, browser/metadata leakage, and correlation to the user's Matrix account.

Clients MUST NOT persist the user's confirmation per app, per session, or per button. The prompt MUST be shown on every click.

Example with OpenID:

```json
{
	"label": "Join game",
	"url": "https://game.example.com/join?matrix={openid_data}",
	"request_openid": true
}
```

### PresenceDataObject

Contains the following fields:

- **`id`**. An opaque identifier (e.g., UUID v4) used to reference this presence entry for later removal.
- **`type`**. Presence type. One of:
  - `m.rpc.activity` for games, applications, or general activities.
  - `m.rpc.music` for music playback.
- **`expiry`**. Unix timestamp (milliseconds) after which this presence entry is considered stale. Clients MUST stop displaying the entry after expiry. Senders SHOULD remove expired entries before updating. Viewing clients MUST filter out expired entries regardless of whether the server's stored copy or federated cache still contains them.
- **`buttons`**. Optional array of **ButtonDataObject**s. Maximum 3.

#### Type: `m.rpc.activity`

- **`name`**. Activity name (e.g., game name).
- **`state`**. Current state (e.g., "Playing singleplayer"). Optional.
- **`details`**. Additional details (e.g., "Chapter 3"). Optional.
- **`since`**. Unix timestamp (milliseconds) of when the activity started. Optional. If present, clients SHOULD display elapsed time.
- **`until`**. Unix timestamp (milliseconds) of when the current activity will end or change (e.g., when a match ends). Optional. If present, clients SHOULD display time remaining. If both `since` and `until` are present, clients SHOULD render a progress bar.
- **`large_icon_url`**. Optional MXC URL of a large icon. Implementations SHOULD reuse previously uploaded icons rather than re-uploading on every update.
- **`small_icon_url`**. Optional MXC URL of a small icon (e.g., a status indicator). Requires `large_icon_url` to be present.
- **`large_icon_tooltip`**. Tooltip text for the large icon.
- **`small_icon_tooltip`**. Tooltip text for the small icon.

#### Type: `m.rpc.music`

- **`track`**. Track name.
- **`artist`**. Optional artist name.
- **`album`**. Optional album name.
- **`player_name`**. Optional player name (e.g., "YouTube Music").
- **`cover_url`**. Optional MXC URL of album or track cover art. Implementations SHOULD reuse previously uploaded URLs.
- **`progress`**. Optional object containing:
  - **`since`**. Unix timestamp (milliseconds) of when this track started playing.
  - **`until`**. Unix timestamp (milliseconds) of when this track will end playing.

  Either both fields MUST be present, or the `progress` object MUST be absent entirely. Clients SHOULD render a progress bar with optional elapsed/remaining time indicators.

## Data federation

The `m.rpc` profile field is federated via the arbitrary profile field mechanism defined in [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133).

## Data content

The `m.rpc` profile field contains an array of **PresenceDataObject**s. A maximum of 4 entries SHOULD be stored at once.

### Profile field updates

#### PUT

Sets the full set of active presences for the user.

```
PUT /_matrix/client/v3/profile/{userId}/m.rpc
Authorization: Bearer {accessToken}
Content-Type: application/json

{
	"m.rpc": [
		{
			"id": "56ac2b4a-8ba3-46de-88d1-66886af12a3a",
			"type": "m.rpc.activity",
			"expiry": 1789570579430,
			"name": "Minecraft",
			"state": "Playing on a server",
			"details": "Overworld",
			"since": 1789570159430,
			"large_icon_url": "mxc://example.com/56ac2b4a-8ba3-46de-88d1-66886af12a3a"
		}
	]
}
```

The request body is the complete array of currently active presence entries. Any prior value of `m.rpc` is entirely replaced.

Clients SHOULD remove entries whose `expiry` timestamp has passed before sending a PUT. Clients SHOULD serialize writes, a new PUT MUST NOT be issued until the previous PUT has resolved to avoid out-of-order updates from locally queued presence changes.

#### DELETE

Removes the `m.rpc` field entirely.

```
DELETE /_matrix/client/v3/profile/{userId}/m.rpc
```

Clients MUST send a DELETE (rather than PUT with an empty array) when no active presences remain after expiry filtering.

#### Merge strategy

Clients receive presence updates from local apps via the WebSocket transport, queue them, merge into the current local state, and then write the full array via PUT. Clients SHOULD hold subsequent writes until the previous PUT resolves to avoid race conditions.

### Examples

#### Games

```json
{
	"m.rpc": [
		{
			"id": "56ac2b4a-8ba3-46de-88d1-66886af12a3a",
			"type": "m.rpc.activity",
			"expiry": 1789570579430,
			"name": "Minecraft",
			"state": "Playing on a server",
			"details": "Overworld",
			"since": 1789570159430,
			"large_icon_url": "mxc://example.com/56ac2b4a-8ba3-46de-88d1-66886af12a3a"
		}
	]
}
```

#### Media

```json
{
	"m.rpc": [
		{
			"id": "2020f5b6-a12d-4d39-832b-35ba35b13fc7",
			"type": "m.rpc.music",
			"track": "Hated by Life",
			"artist": "Iori Kanzaki",
			"player_name": "YouTube Music",
			"cover_url": "mxc://example.com/2020f5b6-a12d-4d39-832b-35ba35b13fc7",
			"progress": {
				"since": 1789572366500,
				"until": 1789572634500
			},
			"buttons": [
				{
					"label": "YT Music",
					"url": "https://music.youtube.com/watch?v=N2A2VZTl9X0"
				}
			]
		}
	]
}
```
## Potential implementations

- A game mod to send rich presence data (e.g., for Minecraft).
- A mobile app to show currently playing song (like [Extera RPC](https://source.extera.xyz/Extera/RichPresenceAndroid)).
- A script for mirroring "Now playing" data from Last.fm or similar services.

## Security considerations

Users may not wish to share their activity information. This feature SHOULD be turned off by default. Clients MAY notify users about support for this feature upon first launch.

Clients MUST prompt before navigating to any button URL. For buttons with `request_openid: true`, the prompt MUST additionally warn about the risks of OpenID requests.

The opaque identifier used in the Unix socket path MUST NOT be directly traceable to the user's Matrix ID. A salted hash (e.g., HMAC-SHA256) of the Matrix user ID SHOULD be used instead.
## Alternatives
- [MSC4320](https://github.com/matrix-org/matrix-spec-proposals/pull/4320): an alternative approach to rich presence in Matrix.
## Unstable prefix
While this MSC is considered unstable, `m.rpc.` SHOULD be replaced with `xyz.extera.MSC4544.` in all field names and type identifiers.
