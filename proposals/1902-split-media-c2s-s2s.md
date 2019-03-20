## Splitting the media repo into a client-side and server-side component

Currently Matrix relies on media being pulled from servers using the same set
of endpoints which clients use. This has so far meant that media repository
implementations cannot reliably enforce auth on given resources.

### Proposal

Servers shall use `/_matrix/media/v1` to access the media repository, adding
applicable headers for any federation request they would normally do. The media
repository must validate the request.

Clients shall use `/_matrix/client/{version}/media` to access the media repository,
providing an access token as it normally would. More detailed access control for
media is left as a task for [MSC701](https://github.com/matrix-org/matrix-doc/issues/701).
Currently, `{version}` may only be `r0` (or `unstable` for testing purposes).

Besides auth, the endpoints covered by the media repository are left otherwise
untouched. For example, the way to download a file from a server is still a request
to `GET /_matrix/media/{version}/download/remote.example.org/mediaid`. The similar
client endpoint would be `GET /_matrix/client/{version}/media/download/remote.example.org/mediaid`.

### Changes required by known implementations

**Clients**:
* Use the new endpoint, supplying required auth. Historically clients have used
  `/_matrix/media/` to download media unauthenticated, and media repository
  implementations should consider this before locking down the endpoint for servers
  only. Servers are encouraged to respect a reasonable transition period for clients
  to adopt the new spec, once landed.
* Potentially change how they download files. Currently many just stick the URL
  into an `<img src="..." />` (or equivalent) and hope for the best, however this
  opens up the user to risk if the access token were to be passed via the query
  string: users would more often be accidentally handing out their access token to
  people. Instead, clients should consider downloading media via other means and
  using blobs to populate img elements (or whatever their equivalent is for their
  chosen platform).
* Actually use the `r0` route if they aren't already. Some clients use the `v1`
  endpoints to show media to users, which is incorrect. Likewise, clients should
  not be using the `unstable` editions of these in released versions.

**Servers / Media repository implementations**:
* Mature server implementations currently require no changes here: they already
  make requests to the `v1` route and sign the request appropriately.
* Less mature implementations (such as the author's own media repository impl) will
  need to verify they make requests to the right place, and sign requests where
  appropriate.
* All implementations will need to verify the request is correctly signed for `v1`
  endpoints, and access token restrictions on the new `r0` endpoints.


### References

* [MSC701](https://github.com/matrix-org/matrix-doc/issues/701) - Access control and
  GDPR for the media repo.
* [matrix-doc#1341](https://github.com/matrix-org/matrix-doc/issues/1341) - Concerns
  with servers using the client-server endpoints to download media over federation.
