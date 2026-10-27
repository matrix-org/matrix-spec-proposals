# MSC4320: Rich Presence

# Context
Discord, a popular instant messenger, has a feature where alongside normal presence (ie online/away/busy/offline, status messages) there can be current activities. For example, music shows album art, song name, artist and current song progress, games show the map and such, etc.
# Proposal 
### Data transport
JSON data will be sent over a websocket running on `http://localhost:{TBD}/rpc`. This will be easiest for native clients, web clients will require something running on the host. Clients will send data to the server via a `PUT` to `/_matrix/client/v3/profile/{userId}/m.rpc` with content explained in "data content". Servers should preform basic validation on `m.rpc` to ensure only the needed fields are included. After an activity is closed or a song is paused/stopped, a`DELETE` should be sent to `_matrix/client/v3/profile/{userId}/m.rpc`. Note that skipping a track should not delete the RPC, as long as there's music playing. In that event, the `m.rpc` field should just be updated.
### Data federation
`m.rpc` data will be federated over a `GET` to `/_matrix/client/v3/profile/{userId}/m.rpc`, as per [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133). 
### Data content
All rich presence needs a `type` (can be `"m.rpc.media"` or `"m.rpc.activity"`) within `m.rpc`. Each type has different requirements. `m.rpc.media` is for media and `m.rpc.activity` is for general activities (usually games).
Required fields if `type` is `m.rpc.media`:
- `artist` containing the artist.
- `album` containing the album.
- `track` containing the track name.

Required fields if `type` is `m.rpc.activity`:
- `name` containing the activity name.

Optional fields if `type` is `m.rpc.media`:
- `progress` containing `length` with the length of the track in seconds.
	- `time_complete` is needed for clients to show the media progress. It should only be updated in the event of the timestamp not being able to be guessed by a client.
	- Both of these are highly recommended to be added.
- `cover_art` containing a MXC with the album art. Clients should hash the album art and re-use the MXC for album art matching that hash to avoid duplicating uploads.
- `player` containing the media player.
- `streaming_link` containing a link to the song on streaming services (i.e. Spotify, YouTube). Clients should warn the user before opening the link.

Optional fields if `type` is `m.rpc.activity`:
- `image` containing an MXC to show as an activity image. Clients should hash the image and re-use the MXC for album art matching that hash to avoid duplicating uploads.
- `details` containing details (i.e. current map, location, etc).
If `m.rpc` is not present within a profile, clients can assume that the user either chose not to send RPC or doesn't have anything sending RPC right now.
#### Examples
Media:
```json
{
	"avatar_url": "…", "displayname": "…",
	"m.rpc": {
	    "type": "m.rpc.media",
	    "progress"{
		"length": 204,
		"complete": 102,
	    },
	    "artist": "ari melody",
	    "album": "free2play",
	    "track": "FTL (Faster Than Light)",
	    "cover_art": "mxc://ip-logger.com/YS5tqBewwZ4HFF3hU9KT8OskREUmlPfM",
	    "player": "Spotify",
	    "streaming_link": "https://open.spotify.com/track/1zJWGrUJ7dy7wQuMSVbvCn"
	}
}
```
Games:
```json
{
	"avatar_url": "…", "displayname": "…",
	"m.rpc": {
		"type": "m.rpc.activity",
		"name": "SuperTuxKart",
		"details": "Playing Oliver's Math Class as Xenia on Intermediate"
	}
}
```
### Potential implementations
- Something using [arRPC](https://arrpc.openasar.dev/) to pretend to be Discord to get info.
- A script mirroring the "now playing" feature on [last.fm](https://last.fm/) or [ListenBrainz](https://listenbrainz.org).
- A Visual Studio Code extension showing the open project, file, etc. Maybe even errors in the code!
# Security considerations
This introduces a privacy risk, as not all users want to broadcast the current song or activity they're doing. Therefore, this feature must not be enabled by default on clients that support this MSC. Clients supporting this feature may notify the user in a non-intrusive way.
# Alternatives
None considered.
# Potential issues
Web clients need to run something on the host, decreasing portability. This can't really be solved.
# Unstable prefix
While in development, clients implementing this MSC should use `com.ip-logger.msc4320.rpc(.*)` instead of `m.rpc(.*)`.
