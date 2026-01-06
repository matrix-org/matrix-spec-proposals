# MSC4174: Web push

This MSC supersedes and replaces [MSC3013](https://github.com/matrix-org/matrix-spec-proposals/pull/3013), which introduced push notification encryption first.

Push notifications typically go through third-party push providers in order to be delivered: 1) a push gateway (sygnal) and
2) e.g. FCM (Google) or APNs (Apple). In order to prevent these push providers and
push gateways from being able to read any sensitive information, the `event_id_only` format was introduced, where the push content only contains the `event_id` and `room_id` of an event. After receiving the push message the client uses
`GET /_matrix/client/r0/rooms/{roomId}/event/{eventId}` to fetch the full event itself, and creates the notification based
on that.

Leaking the room and event id to third parties is problematic and can be avoided.

Today, web clients supporting push notifications (eg. hydrogen) needs to use a matrix to webpush gateway. This requires
going over the specifications, because they use `endpoint`, and `auth` in the `PusherData` ([hydrogen](https://github.com/element-hq/hydrogen-web/blob/9b68f30aad329c003ead70ff43f289e293efb8e0/src/platform/web/dom/NotificationService.js#L32), [sygnal](https://github.com/matrix-org/sygnal/blob/main/sygnal/webpushpushkin.py#L152)),
while [the current specifications let understand that only `url` and `format` are allowed](https://spec.matrix.org/v1.9/client-server-api/#_matrixclientv3pushers_pusherdata).
The specifications already need to be adapted to follow what the web clients do.

Web Push is a standard for (E2EE) push notifications, defined with [RFC8030](https://www.rfc-editor.org/rfc/rfc8030)+[RFC8291](https://www.rfc-editor.org/rfc/rfc8291)+[RFC8292](https://www.rfc-editor.org/rfc/rfc8292): many libraries
are already available and robust: they are reviewed, and acknowledge by experts.

Extending the push kind to [`POST /_matrix/client/v3/pushers/set`](https://spec.matrix.org/v1.16/client-server-api/#post_matrixclientv3pushersset) to a `*webpush*` would provide encrypted push notifications without the need for an external gateway to
- Web app and desktop app
- Android apps using [UnifiedPush](https://codeberg.org/UnifiedPush/specifications/src/branch/main/specifications/android.md#resources). This MSC would make [MSC2970](https://github.com/matrix-org/matrix-spec-proposals/pull/2970) redundant.
- Android apps using FCM ([It is possible to push to FCM with webpush standard](https://unifiedpush.org/news/20250131_push_for_decentralized/))
- Maybe other ? We have seen [apple moving a lot into web push support](https://developer.apple.com/documentation/usernotifications/sending-web-push-notifications-in-web-apps-and-browsers)

## Proposal

The MSC introduces a new push kind: webpush.

`PusherData` is extended as as follow:
- `format`: is updated to be required if `kind` is `http` or `webpush`
- `url`: is updated to be required if `kind` is `http`, not used otherwise (to clarify this isn't used with webpush).
- `endpoint`: is introduced, required if `kind` is `webpush`, not used otherwise. The URL to send the notification to, as defined as a
`push resource` by RFC8030. MUST be an HTTPS URL.
- `auth`: is introduced, required if `kind` is `webpush`, not used else. The authentication secret as specified by RFC8291. This is 16 random bytes
encoded in base64 url.

The POST request to the endpoint dedicated to the creation, modification and deletion of pushers,
`POST /_matrix/client/v3/pushers/set` now supports a new `kind`: `webpush`.
- `kind`: is updated to introduce `webpush` which makes a
pusher that sends Web Push encrypted messages.
- `pushkey`: is updated, if the `kind` is `webpush`, this is the user agent public key in the uncompressed form ([SEC 1](https://www.secg.org/sec1-v2.pdf), section 2.3.3, replicated from X9.62), encoded in base64 url. The public key comes from a ECDH
keypair using the P-256 (prime256v1, cf. FIPS186) curve.

If the request creates a new pusher or modify the `pushkey`, the `PusherData.endpoint`, or the `PusherData.auth`, then
the server respond with a 201, "The pusher is set but needs to be activated". The Server send a push notification to the
endpoint, encrypted with `pushKey` and `PusherData.auth`, authenticated with the VAPID key with a message containing
the `app_id` and a `ack_token`, a UUIDv4 token in the hyphen form, valid for 5 minutes:

```
{
	"app_id": "im.vector.app.android",
	"ack_token": "6fc76b70-5fad-4eb7-93ea-a1af7a03258b"
}
```

A new endpoint is introduced, dedicated to pusher validation:
- POST `/_matrix/client/v3/pushers/ack`
- Rate limited: No, Requires authentication: Yes
- The request contains the `app_id` and `ack_token` parameters, received with the push notification.
- The response, with status code 200, contains the `app_id` and `status`, which can be one of the following values:
    - "unknown_app_id" if no pusher with this app_id exists
		- "expired" if this token for this app_id is expired
		- "unknown_token" if a pusher with this app_id exists, but the token is not known. An expired token may send this status too
		- "ok" if the pusher has been activated

The Pusher Data get a new optional field, `activated`, a boolean which is false until the pusher is activated with the request to
`/_matrix/client/v3/pushers/ack`.

A VAPID (Voluntary Application Server Identification, cf RFC8292) is often needed to be able to register with a push
server.
It is proposed to add a `m.webpush` capability to the `/capabilities` endpoint with this format:

The VAPID public key is in the uncompressed form, base64url encoded.

```
"m.webpush": {
	"enabled": true,
	"vapid": "BNbXV88MfMI0fSxB7cDngopoviZRTbxIS0qSS-O7BZCtG04khMOn-PP2ueb_X7Aeci42n02kJ0-JJJ0uQ4ELRTs"
}
```

It is also useful to decide if the client should register a pusher using `http` kind and and old style
Sygnal WebPush semantic. A client that supports this kind of pusher should use it if the server supports it too, and
not register another `http` pusher to avoid duplicate pushes.

## Overview with webpush

```
                                                +-------------------+
                  Matrix HTTP                   |                   |
             Notification Protocol              |   Device Vendor   |
                                                |                   |
           +-------------------+                | +---------------+ |
           |                   |                | |               | |
           | Matrix homeserver +--> Web Push +----> Push Server   | |
           |                   |                | |               | |
           +-^-----------------+                | +----+----------+ |
             |                                  |      |            |
    Matrix   |                                  |      |            |
 Client/Server API  +                           |      |            |
             |      |                           +-------------------+
             |   +--+-+                                |
             |   |    <--------------------------------+
             +---+    |
                 |    |          Provider Push Protocol
                 +----+

         Mobile Device or Client
```

## Potential issues

Many libraries only implement [I-D.ietf-webpush-encryption-04](https://datatracker.ietf.org/doc/html/draft-ietf-webpush-encryption-04) from October 2016, rather than the final version of [RFC8291](https://datatracker.ietf.org/doc/html/rfc8291) from November 2017. Thus, some care needs to be taken during implementation. Checking the
Content-Encoding header is a good way to check for the correct version. If the value is `aes128gcm`, then it uses
the right specifications, in case of  `aesgcm` it uses the draft version.

## Alternatives

`pushkey` could be a random ID, and we can add `p256dh` in the `PusherData`. But it would require client to store it,
while the public key already identify that pusher. And, client already use the PusherData that way.

`vapid` parameter could be made optional considering it is officially not a requirement, however it seems
existing big players push servers need it anyway to be able to subscribe, so it was decided to make it mandatory
to avoid issues with those.

## Security considerations

Security considerations are listed by [RFC8030](https://www.rfc-editor.org/rfc/rfc8030#section-8), there are mainly resolved with [RFC8291](https://datatracker.ietf.org/doc/html/rfc8291) (Encryption) and
[RFC8292](https://datatracker.ietf.org/doc/html/rfc8292) (VAPID).

Like any other federation request, there is a risk of SSRF. This risk is limited since the post data isn't
arbitrary (the content is encrypted), and a potential malicious actor don't have access to the response.
Nevertheless, it is recommended to not post to private addresses, with the possibility with a setting to
whitelist a private IP. (Synapse already implements [`ip_range_whitelist`](https://matrix-org.github.io/synapse/latest/usage/configuration/config_documentation.html#ip_range_whitelist))
It is also recommended to not follow redirection, to avoid implementation issue where the destination is checked
before sending the request but not for redirection.

Like any other federation request, there is a risk of DOS amplification. One malicious actor register many users
to a valid endpoint, then change the DNS record and target another server, then notify all these users. This
amplification is very limited since HTTPS is required and the TLS certificate of the target will be rejected. The
request won't reach any functionality of the targeted application. The home server can reject pusher if the response
code is not one intended.

## Unstable prefix

- Until this proposal is considered stable, implementations must use
`org.matrix.msc4174.webpush` instead of `m.webpush`.

## Dependencies

-
