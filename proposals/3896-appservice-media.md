# MSC3896: Appservice media

Appservices often need to bridge media, and do so by reuploading files to the homeserver. This
can cause a lot of storage usage. This MSC proposes a way for appservices to register media
(`mxc://`) namespaces.

## Proposal

This proposal adds a new key (`media`) to the namespaces block of appservice registration.

Whenever the homeserver gets a request for a media ID that matches the regex and the requested
`server_name` of the media is it's own, it should make a HTTP GET request to
`/_matrix/app/v1/media/{mediaId}`.

This request has no body nor query parameters. Servers MAY be redirected via HTTP 307/308 responses,
which they should follow to obtain the content. `Content-Disposition` and `Content-Type` headers
SHOULD be set in the response, so that the server is made aware of the file name and content type
of the media, although this is not always possible with the remote platform the appservice is
fetching the media from.

For example:

```yaml
namespaces:
  media:
    - exclusive: true
      regex: "foobar-.*"
```

In this case, fetching `mxc://server.tld/foobar-bazqux` leads to a request to
`/_matrix/app/v1/media/foobar-bazqux`.

Appservices may set `Cache-Control` on their response. Homeservers should cache the response, though
they may remove cached remote media to save space.

## Potential issues

Media may not be able to load if the appservice is unable to reach wherever remote media is stored.

## Alternatives

*none*

## Security considerations

*none*

## Unstable prefix

While this MSC is not considered stable, implementations should use
`/_matrix/app/unstable/org.eu.celery.msc3896/media/{mediaId}` instead of `/_matrix/app/v1/media/{mediaId}`
to request media from the appservice, and `org.eu.celery.msc3896.media` instead of `media` in the
appservice registration file.

## Dependencies

*none*
