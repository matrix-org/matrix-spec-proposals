# MSC4177: Upload Location Hints

This MSC proposes extensions to the media APIs that allow servers and clients to provide each other
location hints for uploaded media.

Often Matrix homeservers serve users in many geographical locations. For media that is uploaded and
downloaded via a CDN (see: [MSC3860](https://github.com/matrix-org/matrix-spec-proposals/pull/3860),
[MSC3870](https://github.com/matrix-org/matrix-spec-proposals/pull/3870)) it is advantageous to use
a location as close to the user as possible. This MSC allows servers to advertise available media
storage locations and for clients to request media is uploaded to one of these locations.

All the changes are optional, ultimately the server retains control of where media gets put.

## Proposal

Firstly, to provide available locations to clients, the [`/_matrix/client/v1/media/config`](https://spec.matrix.org/v1.11/client-server-api/#get_matrixclientv1mediaconfig)
endpoint is extended with a new response field:

```json
{
  "m.upload.locations": ["EU", "NA"],
  ...
}
```

The `m.upload.locations` field is a list of strings. Interpretation of the strings is up to clients
and servers and undefined in the spec. (Note: does this make sense?)

When clients wish to upload media, they can then include one of the location hints from the config
in upload or create media requests using the `location` query parameter, for example:

- `POST /_matrix/media/v1/upload?location=EU`
- `POST /_matrix/media/v1/create?location=EU`

When clients request a location the server MAY use that location hint to upload the media to a
bucket matching that location. Clients must not expect this to be guaranteed and ultimately the
server decides.

## Potential issues

How do clients/servers interpret location hints? Is it sensible to leave this undefined/open. We 
could provide explicit options, or a baseline of options, "it is recommended location hints use
geographical ISO codes" for example.

## Alternatives

Server could use request IP to achieve this without any hints, though inaccurate and invalid when
a user is abroad. This is reasonable fallback behaviour for a server when clients do not provide
any location hint.

## Security considerations

None? Reveals bucket locations (to logged in users), but servers are aware of this and there's
no security issue (I think).

## Unstable prefix

`com.beeper.m.upload.locations`

## Dependencies

Though not a hard dependency uploads will only get speed benefits from this MSC once [MSC3870](https://github.com/matrix-org/matrix-spec-proposals/pull/3870)
is merged (otherwise uploads still route through the users homeserver location).
