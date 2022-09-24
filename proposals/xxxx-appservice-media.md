# MSCxxxx: Appservice media

Appservices often need to bridge media, and do so by reuploading files to the homeserver. This
can cause a lot of storage usage. This MSC proposes a way for appservices to register media
(`mxc://`) namespaces.

## Proposal

This proposal adds a new key to the namespaces block of appservice registration. For example:

```yaml
namespaces:
  media:
    - exclusive: true
      regex: "foobar-.*"
```

Whenever the homeserver gets a request that matches the regex, it should make a http GET request
to `/_matrix/app/v1/media/{mediaId}`.

Example: using the example registration, fetching `mxc://server.tld/foobar-bazqux` should lead to a
request to `/_matrix/app/v1/media/foobar-bazqux`.

Appservices may set `Cache-Control` on their response. Homeservers should cache the response, though
they may remove cached remote media to save space.

## Potential issues

Media may not be able to load if the appservice is unable to reach wherever remote media is stored.

## Alternatives

*none*

## Security considerations

*none*

## Unstable prefix

`org.eu.celery.mscxxxx.media` should be used instead of `media`

## Dependencies

*none*
