# MSC4396: Inline linked media

**This proposal is a work in progress and may change dramatically.**

Linking media to events is desirable to allow users to have their media deleted when their events
are no longer accessible and to ensure that only those with visibility on an event can download the
media for it.

Like [MSC3911](https://github.com/matrix-org/matrix-spec-proposals/pull/3911), this proposal builds
on the [authentication requirements](https://spec.matrix.org/v1.17/client-server-api/#content-repository:~:text=%5BChanged%20in%20v1.11%5D%20The,later%20version%20of%20the%20specification)
added to the download endpoints in Matrix 1.11 by requiring that users also be *authorized* to access
the media.

The general concept of MSC3911 is preserved by this proposal: media *must* be linked to an event. The
difference is how that linking happens. In MSC3911, media is "attached" to an event at send-time after
being uploaded. In this proposal, media is uploaded at send-time and attached in the same operation.

Combining the operations ensures there's a guaranteed link between media and event, but does also
mean that media must be available to be combined in the operation. This also may lead to client
compatibility issues because the sender will not be able to populate the `url` on an event itself.

**Note**: Backwards compatibility is explored later in this proposal, but it's not perfect. More
review and thought needs to happen here.

The fact that an event contains media does not necessarily mean that event needs to be linked to
that media, however. For example, in the case of an [MSC4027-style](https://github.com/matrix-org/matrix-spec-proposals/pull/4027)
reaction, the reaction event is copying media that was already uploaded (and ideally, linked) to an
event elsewhere. If that reaction event were to be redacted, the underlying media would not be affected,
so it is not required to be linked to the event. If the event containing the original media were to
be redacted however, most (if not all) reactions which used that media ID would stop working.

## Adjacent use cases

There are some use cases which are addressed by this MSC, but not big enough to be drivers for this
specific design:

* Combining the media upload and event sending allows safety tooling to more efficiently scan the
  media. Currently, a safety tool will need to extract the media ID out of the event, download it,
  scan it, then take relevant action. With the combined operation, the safety tool can skip the
  extraction and download steps, improving response time.

**TODO**: More?

## Proposal

[`POST /_matrix/media/v3/upload`](https://spec.matrix.org/v1.17/client-server-api/#post_matrixmediav3upload)
and [`POST /_matrix/media/v1/create`](https://spec.matrix.org/v1.17/client-server-api/#post_matrixmediav1create)
are **deprecated** with no direct replacement. [`PUT /_matrix/media/v3/upload/:serverName/:mediaId`](https://spec.matrix.org/v1.17/client-server-api/#put_matrixmediav3uploadservernamemediaid)
is deprecated and moved to `PUT /_matrix/client/v1/media/upload/:serverName/:mediaId` with no other
changes to its schema. This completes the transition started in [MSC3916](https://github.com/matrix-org/matrix-spec-proposals/pull/3916).

The following endpoints receive an endpoint version bump (`v3` -> `v4` in most cases) to support a
new request format, described below.

* [`PUT /_matrix/client/v3/rooms/:roomId/send/:type/:txnId`](https://spec.matrix.org/v1.17/client-server-api/#put_matrixclientv3roomsroomidsendeventtypetxnid)
* [`PUT /_matrix/client/v3/rooms/:roomId/state/:type/(:stateKey)`](https://spec.matrix.org/v1.17/client-server-api/#put_matrixclientv3roomsroomidstateeventtypestatekey)
* [`PUT /_matrix/client/v3/sendToDevice/:type/:txnId`](https://spec.matrix.org/v1.17/client-server-api/#put_matrixclientv3sendtodeviceeventtypetxnid)
* [`PUT /_matrix/client/v3/profile/:userId/:keyName`](https://spec.matrix.org/v1.17/client-server-api/#put_matrixclientv3profileuseridkeyname)

**TODO**: More?

In addition to supporting their already-specified schemas, these endpoints now support an additional
(and optional) `multipart/mixed` body. This is the same approach as the Federation API's
[media download response body](https://spec.matrix.org/v1.17/server-server-api/#get_matrixfederationv1mediadownloadmediaid).

The first part is *always* the JSON request body (as defined by the endpoint's normal schema). There
MAY be zero or more parts denoting different media objects to assign to the event. Servers SHOULD
limit how many media objects can be assigned to an event, and MUST NOT limit the caller to less than
5 objects. This is to support media with thumbnails in rooms.

An example request might be:

```
PUT /_matrix/client/v3/rooms/!x/send/m.room.message/1
Authorization: Bearer TOKEN
Content-Type: multipart/mixed; boundary=a1b2c3

--a1b2c3
Content-Type: application/json

{
  "msgtype": "m.image",
  "body": "image.png",
  "url_index": 0,
  "info": {
    "h": 1600,
    "w": 1600,
    "size": 206895,
    "mimetype": "image/png",
    "thumbnail_url_index": 1
    "thumbnail_info": {
      "h": 32,
      "w": 32,
      "size": 4950,
      "mimetype": "image/png"
    }
  }
}

--a1b2c3
Content-Type: image/png

[png data]

--a1b2c3
Content-Type: image/png
X-Matrix-Request-Async-File: true

--a1b2c3
```

There are a few notable details in this example:

1. `url` and `thumbnail_url` are replaced by `[thumbnail_]url_index`. This is the index of the media
   URI in the `m.media` list (described later in this proposal).
2. `X-Matrix-Request-Async-File` is a header on the third part. By setting this to `true`, the caller
   is saying that it doesn't yet have the media and would like to use the (newly defined)
   `PUT /_matrix/client/v1/media/upload/:serverName/:mediaId` endpoint instead. The caller discovers
   the media ID to upload to via the endpoint's response.

   The async media has the same time-to-upload and similar restrictions from the now-deprecated
   `/create` endpoint.

For this example, the response may be:

```jsonc
{
  "event_id": "$x",
  "media_uris": [
    "mxc://example.org/one", // the first media part
    "mxc://example.org/two"  // the second media part (which is an async upload)
  ],
  "unused_expires_at": 1647257217083 // for the async media parts
}
```

Internally, the server mutates the resulting event's `content` to include an
[MSC1767-style](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/1767-extensible-events.md)
`m.media` mixin.

**Note**: The server *always* overwrites `m.media`, even if there's no media to assign to the event.
If the `m.media` array is empty, the field SHOULD be deleted from the `content` instead.

`m.media` is an array of linked (or assigned, or attached, or $synonym) media URIs, like so:

```jsonc
{
  // other event fields omitted for brevity
  "type": "m.room.message",
  "content": {
    "msgtype": "m.image",
    "body": "image.png",
    "url_index": 0,
    "info": {
      "thumbnail_url_index": 1
      // and etc
    },
    "m.media": [
      "mxc://example.org/one",
      "mxc://example.org/two"
    ]
  }
}
```

If the client does *not* need to link media to the event, they can use the normal `url` field instead.
This will result in an event with no (or empty) `m.media` array, making that media immune to removal
through this event.

### Media removal

Later, when an event with `m.media` becomes redacted (or effectively redacted via GDPR or similar),
the media IDs in that array also become redacted/removed. It's left as an implementation detail whether
to immediately delete the underlying file on the server, but the effect MUST be that attempts to
download the media fail with a `410 Gone` HTTP status code and `M_GONE` error code.

**Note**: `410 M_GONE` is new to the following endpoints:

* [`GET /_matrix/client/v1/media/download/:serverName/:mediaId`](https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv1mediadownloadservernamemediaid)
* [`GET /_matrix/client/v1/media/download/:serverName/:mediaId/:fileName`](https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv1mediadownloadservernamemediaidfilename)
* [`GET /_matrix/client/v1/media/thumbnail/:serverName/:mediaId`](https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv1mediathumbnailservernamemediaid)
* [`GET /_matrix/federation/v1/media/download/:mediaId`](https://spec.matrix.org/v1.17/server-server-api/#get_matrixfederationv1mediadownloadmediaid)
* [`GET /_matrix/federation/v1/media/thumbnail/:mediaId`](https://spec.matrix.org/v1.17/server-server-api/#get_matrixfederationv1mediathumbnailmediaid)
* Deprecated variants of the above (if still in the spec when this MSC lands).

Servers MAY also respond with a generic `404 M_NOT_FOUND` to hide the previous existence of media.

Servers MAY allow server admins (or similar concept) to download redacted media for investigative or
safety purposes.

Clients SHOULD purge local caches of media upon redaction where possible.

### Authorized downloads

A user MUST NOT be able to download media from events they do not have visibility of. This affects:

* [`GET /_matrix/client/v1/media/download/:serverName/:mediaId`](https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv1mediadownloadservernamemediaid)
* [`GET /_matrix/client/v1/media/download/:serverName/:mediaId/:fileName`](https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv1mediadownloadservernamemediaidfilename)
* [`GET /_matrix/client/v1/media/thumbnail/:serverName/:mediaId`](https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv1mediathumbnailservernamemediaid)
* Deprecated variants of the above (if still in the spec when this MSC lands).

Users receive an `403 M_FORBIDDEN` error when downloading media associated with an event they cannot
see.

A user can "see" an event if the event is in a [`world_readable`](https://spec.matrix.org/v1.17/client-server-api/#room-history-visibility)
room or the history visibility otherwise permits them to see the event.

The visibility constraints are carried over federation using the currently-empty JSON object part
on the download endpoints below:

* [`GET /_matrix/federation/v1/media/download/:mediaId`](https://spec.matrix.org/v1.17/server-server-api/#get_matrixfederationv1mediadownloadmediaid)
* [`GET /_matrix/federation/v1/media/thumbnail/:mediaId`](https://spec.matrix.org/v1.17/server-server-api/#get_matrixfederationv1mediathumbnailmediaid)

Example:

```
Content-Type: multipart/mixed; boundary=gc0p4Jq0M2Yt08jU534c0p

--gc0p4Jq0M2Yt08jU534c0p
Content-Type: application/json

{"visibility":"$x"}

--gc0p4Jq0M2Yt08jU534c0p
Content-Type: text/plain

This media is plain text. Maybe somebody used it as a paste bin.

--gc0p4Jq0M2Yt08jU534c0p
```

If the event belongs to a `world_readable` room at the time it was sent, `visibility` is the string
`world_readable` instead of an event ID. The default for `visibility` when not present is `world_readable`.

The calling server is responsible for ensuring the original requesting user has appropriate access
to the event listed (when `visibility != world_readable`). This may involve the server
[fetching the event](https://spec.matrix.org/v1.17/server-server-api/#get_matrixfederationv1eventeventid)
over federation to better understand the context.

If the calling server doesn't have any users which would be able to see the event, the federation
download instead fails with `403 M_FORBIDDEN`.

### Encryption

In encrypted rooms, media is first encrypted before being referenced in an event. This capability is
retained, though the `m.media` mixin will be on the unencrypted outer portion of the event. To reduce
(though not eliminate) metadata risk of observers guessing at which of the URIs is the original and
which is a thumbnail, the event contents use `(thumbnail_)url_index` fields which reference a specific
URI in the array. There is no requirement or expectation that the first URI is the original file, so
clients can randomize the order of their uploaded media. They can also reuse media multiple times in
the same event by using the same index, though this is not expected to be common.

Encrypted media is otherwise sent and encrypted per normal.

### Custom emoji

For the purposes of this proposal, "(custom) emoji" encompasses inline emoji via
[mxc-`src`'d `img` tags](https://spec.matrix.org/v1.17/client-server-api/#mroommessage-msgtypes),
[MSC4027-style reactions](https://github.com/matrix-org/matrix-spec-proposals/pull/4027),
and [stickers](https://spec.matrix.org/v1.17/client-server-api/#sticker-messages).

With the current [MSC2545-led](https://github.com/matrix-org/matrix-spec-proposals/pull/2545) direction,
emoji is compiled into "packs" which may be reused by other users. In this setup, media uploads would
be linked to the events in the packs rather than when those emoji are used.

When a pack event is redacted, the associated emoji would stop working wherever it was used.

If clients are sending media without a pack, they would upload the media alongside the event content
like the above `m.image` example. This does not scale very well, so packs are recommended.

### Profiles

Profile changes often result in `m.room.member` events being sent. This proposal changes the
[`PUT /_matrix/client/v3/profile/:userId/:keyName`](https://spec.matrix.org/v1.17/client-server-api/#put_matrixclientv3profileuseridkeyname)
endpoint to support the new `m.media` mixin, but requires special handling because the data is not
in a traditional event shape. When `keyName` is `avatar_url`, the multipart request body schema still
applies, though the JSON object part will always be an empty object. The first (and hopefully, only)
media part will become the user's avatar, populating both the `avatar_url` and `m.media` fields on
the resulting `m.room.member` event.

Servers SHOULD use a distinct media URI for each room they update. This may involve internally referencing
the media or linking to it to avoid excessive data use.

Servers SHOULD maintain `m.media` when updating other parts of the user's profile. This is important
when first joining a room as well to ensure the user's avatar is appropriately handled.

**TODO**: Consider invites.

### Other use cases for arbitrary uploads

This proposal intentionally limits a user's ability to upload content outside of an event. In cases
where media needs to be shared by (authenticated) URL, users can create a `world_readable` room,
upload it, then share a link to the resulting media.

Servers MAY also synthesize (un)restricted media as needed. There is no requirement that the event ID
referenced in `visibility` actually have an `m.media` array referencing the media ID. Servers can use
this to internally create `world_readable` or visible-to-some-users media. Such cases include icons
on a website, creating their own server-managed emoji packs, populating a user's profile, etc.

### Backwards compatibility

**TODO**: This works, but it's a bit ugly. Consider alternatives.

Removing `url` from events would be an invasive breaking change to client behaviour currently. To support
clients transitioning to a new system, the media parts MAY have an `X-Matrix-Media-URI` header to
designate that the content should be pulled from that media ID instead. The server MUST only accept
header values which they created themselves. A media ID MUST NOT be used more than once (doing so
results in a `400 M_INVALID_PARAM` error).

If the media doesn't exist or has expired, the server similarly returns an `400 M_INVALID_PARAM`
error. `400 M_INVALID_PARAM` is further returned if more than one `X-Matrix-Media-URI` headers are
present on a single part.

The server populates `m.media` using the `X-Matrix-Media-URI` header on each part. The client otherwise
sends the event normally, using `url` and (preferably) `url_index` concurrently.

### WIP NOTES

**TODO**: Incorporate into the MSC properly.

* to-device is supported for [MSC4268](https://github.com/matrix-org/matrix-spec-proposals/pull/4268)
  use cases. It's unclear what the precise endpoint shape would be for this (hopefully similar to
  what's already above).
* more examples of how all of this works, including sequence diagrams

## Potential issues

**TODO**

## Alternatives

**TODO**

## Security considerations

**TODO**

## Unstable prefix

**TODO**. It's not really suggested to implement this thing so early in the design process.

## Dependencies

This proposal has no direct dependencies.
