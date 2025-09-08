# MSC4189: Allowing guests to access uploaded media

[MSC3916](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/3916-authentication-for-media.md)
introduced new endpoints which require clients to provide a valid access token in order to access
media. The MSC failed to specify [guest access](https://spec.matrix.org/v1.11/client-server-api/#guest-access)
requirements for the new endpoints.

This MSC specifies the missing guest access requirements on the new endpoints.

## Proposal

The following endpoints explicitly permit guest access, joining the
[list of other endpoints](https://spec.matrix.org/v1.11/client-server-api/#client-behaviour-13)
already in the specification:

* [`GET /_matrix/client/v1/media/download/{serverName}/{mediaId}`](https://spec.matrix.org/v1.11/client-server-api/#get_matrixclientv1mediadownloadservernamemediaid)
* [`GET /_matrix/client/v1/media/download/{serverName}/{mediaId}/{fileName}`](https://spec.matrix.org/v1.11/client-server-api/#get_matrixclientv1mediadownloadservernamemediaidfilename)
* [`GET /_matrix/client/v1/media/thumbnail/{serverName}/{mediaId}`](https://spec.matrix.org/v1.11/client-server-api/#get_matrixclientv1mediathumbnailservernamemediaid)

The rationale for the above endpoints is that being able to see events without the associated media
isn't very useful.

For clarity, the following endpoints are *not* added to the guest access list, as their prior (now
deprecated) versions are not already included. A future MSC may change this with sufficient rationale.
Note that guests cannot currently *upload* files, but can send messages/events.

* [`GET /_matrix/client/v1/media/config`](https://spec.matrix.org/v1.11/client-server-api/#get_matrixclientv1mediaconfig)
* [`GET /_matrix/client/v1/media/preview_url`](https://spec.matrix.org/v1.11/client-server-api/#get_matrixclientv1mediapreview_url)

## Potential issues

This MSC fixes an issue where guests cannot download images/files.

## Alternatives

None applicable.

## Security considerations

This MSC does not materially increase the threat profile for guests: guests could already download
media using the unauthenticated endpoints.

## Unstable prefix

Prefixed endpoints are excessive for this MSC. Implementations can enable guest access on the existing
endpoints safely, or continue to respond with "guest access forbidden" errors. No `/versions` flag
is specified for feature detection: clients with guest access tokens should expect failure until a
server advertises a specification version containing this MSC. Clients should continue trying to make
requests for the best user experience.

## Dependencies

This MSC has no dependencies.
