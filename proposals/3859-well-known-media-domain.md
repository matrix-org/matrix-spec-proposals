# MSC3859: .well-known Media Domain

Currently Matrix clients and servers discover homeservers and identify servers via the `.well-known/matrix/client` and 
`.well-known/matrix/server` endpoints. This is currently limited to the homeserver and for clients the identity server.
This MSC proposes adding an additional field that can be used to specify a media server that can optionally be used 
for `/_matrix/media/*` endpoints.

The reasoning behind this change is to support hosting media behind a CDN designed and optimised specifically for 
serving media. Since media transfers and endpoints are very different to the other JSON based endpoints a separate 
domain offers maximum flexibility for server owners.


## Proposals

### Extend the client .well-known

Add a new optional field, `m.media_server` that can specify a separate URL to be used for media requests. Clients can 
then optionally use this field for all media endpoints, including both download and upload.

```json
{
  "m.homeserver": {
    "base_url": "https://matrix.example.com"
  },
  "m.media_server": {
    "base_url": "https://matrix-media.example.com"
  }
}
```

To ensure backwards compatibility the homeserver base URL must also be able to serve the same media requests (via a 
proxy or some other backend system).

### Extend the server .well-known

This is the same as above but for the server endpoint:

```json
{
  "m.server": "matrix.example.com:443",
  "m.media_server": "matrix-media.example.com:443"
}
```

As above, the non-media endpoint must also serve media requests.


## Alternatives

### Redirects

For the download path, the homeserver could send a redirect response to a CDN backed domain. This is proposed in 
MSC3860.

For the upload path this is not possible under HTTP.


## Security Considerations

Server admins may have to manage two distinct domains/installs increasing management & attack vector.


## Unstable Prefix

While not released in the Matrix spec implementations should use field `com.beeper.msc3859.m.media_server` in place of 
`m.media_server` in the well known responses:

```json
# Client
{
  "com.beeper.msc3859.m.media_server": {
    "base_url": "https://matrix-media.example.com"
  }
}
# Server
{
  "com.beeper.msc3859.m.media_server": "matrix-media.example.com:443"
}
```