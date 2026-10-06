# MSC4425: Ephemeral media

Media is typically expected to be included in events and thus exist for a length of time approaching
"forever". In the meantime, use cases like [MSC4268](https://github.com/matrix-org/matrix-spec-proposals/pull/4268)
are coming up which use the media repo for non-event (temporary) data storage.

This proposal introduces a mechanism for a media uploader to indicate that their upload should be
considered ephemeral. An endpoint to delete media (making it truly ephemeral) is also introduced.

Future proposals like [MSC3911](https://github.com/matrix-org/matrix-spec-proposals/pull/3911) and
[MSC4322](https://github.com/matrix-org/matrix-spec-proposals/pull/4322) may introduce additional
mechanics for ensuring in-event media deletion/redaction.


## Proposal

On [`POST /_matrix/media/v1/create`](https://spec.matrix.org/v1.17/client-server-api/#post_matrixmediav1create)
and [`POST /_matrix/media/v3/upload`](https://spec.matrix.org/v1.17/client-server-api/#post_matrixmediav3upload),
a new `ephemeral` boolean query string parameter is added. `ephemeral` defaults to `false`.

When `ephemeral` is `true`, the uploader can later delete the media with a new endpoint:

```
DELETE /_matrix/client/v1/media/{origin}/{mediaId}
Authorization: ...

<empty request body>
```

This new endpoint requires authentication, can be rate limited, and returns the following:

* 200 OK + empty JSON object - The media was deleted or flagged as deleted on the server.
* 404 `M_NOT_FOUND` - The media was already deleted or was not found.
* 403 `M_FORBIDDEN` - The media was not uploaded by the user, was not found, or is not ephemeral.

The new endpoint is not available to guests because guests cannot upload media in the first place.

**Note**: Notifications to other servers/users are not sent when media is deleted. Read on for details
about cache expiration.

**Note**: Thumbnails for ephemeral media are also ephemeral themselves. They MUST be deleted at the
same time as the media object.

Over federation, ephemeral media is denoted in the media metadata during [download](https://spec.matrix.org/v1.17/server-server-api/#get_matrixfederationv1mediadownloadmediaid)
and [thumbnailing](https://spec.matrix.org/v1.17/server-server-api/#get_matrixfederationv1mediathumbnailmediaid),
like so:

```
Content-Type: multipart/mixed; boundary=gc0p4Jq0M2Yt08jU534c0p

--gc0p4Jq0M2Yt08jU534c0p
Content-Type: application/json

{"ephemeral":true}

--gc0p4Jq0M2Yt08jU534c0p
Content-Type: text/plain

Media content goes here
--gc0p4Jq0M2Yt08jU534c0p
```

Like the Client-Server API changes, `ephemeral` is optional and defaults to `false`. Values which aren't
booleans are considered `false` too.

When a server downloads ephemeral media (or its thumbnail) over federation, it MUST NOT cache that
response for longer than 1 day. This is to ensure two things:

1. Later, when the media is deleted, the remote server also implicitly deletes it.
2. Users cannot cause high bandwidth usage by cache-busting the media repo on upload.

Servers MAY be interested in applying harsher rate limits on ephemeral media than "regular" media to
further reduce resource consumption risks.


## Potential issues

The new delete endpoint is not technically idempotent - clients will need to expect a 200, 403, or
404 status code to confidently believe they have made the delete request.

Servers will likely need to track that they used the media ID even if the media has been deleted.
Otherwise, they might reuse the media ID and inappropriately grant access to the wrong user.

If ephemeral media is used in an event, that event might "break" for users later. This has larger
impact for media which is shared in multiple events, like custom emoji/stickers. Clients SHOULD NOT
use this proposal to upload media destined for an event.


## Alternatives

This proposal is complimentary to proposals which have more sophisticated deletion or redaction
mechanisms. For example, proposals which link media to the events they are sent within.


## Security considerations

If the cache value is too low, both remote and origin servers may experience abnormally high bandwidth
usage. Rate limits can help mitigate this.

If the cache value is too high, a later delete might get missed. Capping the server's value at 1 day
is a relatively arbitrary choice, but balances the likelihood of needing to make a second download
request with the ability for the media to disappear.

Clients might decide to flag all media, whether in events or otherwise, as ephemeral. If undesirable,
servers can impose stricter rate limits as they see fit.


## Unstable prefix

While this proposal is not considered stable, implementations should use `org.matrix.msc4425.ephemeral`
instead of `ephemeral` and `DELETE /_matrix/client/unstable/org.matrix.msc4425/{origin}/{mediaId}` in
place of the stable endpoint.


## Dependencies

This proposal has no direct dependencies.
