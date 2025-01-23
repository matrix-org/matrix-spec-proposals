# MSC4174: Web Push pusher kind

As stated in [MSC3013](https://github.com/matrix-org/matrix-spec-proposals/pull/3013), a first MSC about push notification encryption, that the present MSC is to replace:

Push notifications have the problem that they typically go through third-party push providers in order to be delivered,
e.g. FCM (Google) or APNs (Apple) and a push gateway (sygnal). In order to prevent these push providers and
push gateways from being able to read any sensitive information the `event_id_only` format was introduced, which only
pushes the `event_id` and `room_id` of an event down the push. After receiving the push message the client can hit the
`GET /_matrix/client/r0/rooms/{roomId}/event/{eventId}` to fetch the full event, and then create the notification based
on that.

Even the `event_id_only` leaks some metadata that can be avoided.

Today, web clients supporting push notifications (eg. hydrogen) needs to use a matrix to webpush gateway. This requires
going over the specifications, because they use `endpoint`, and `auth` in the `PusherData` (hydrogen [[1]], sygnal [[2]]),
while the specifications let understand that only `url` and `format` are allowed [[3]].
=> __PusherData already need to be updated__ to add `auth` and `endpoint`.

Web Push is a standard for (E2EE) push notifications, defined with RFC8030+RFC8291+RFC8292 [[4]][[5]][[6]]: many libraries
are already available and robuste: they are reviewed, and acknowledge by experts.

Having a webpush push kind would provide push notifications without gateway to
- Web app and desktop app
- Android apps using UnifiedPush (MSC2970 was open for this and won't be required anymore)
- Android apps using FCM (It is possible to push to FCM with webpush standard [[7]])
- Maybe other ? We have seen apple moving a lot into web push support [[8]]

[1]: https://github.com/element-hq/hydrogen-web/blob/9b68f30aad329c003ead70ff43f289e293efb8e0/src/platform/web/dom/NotificationService.js#L32
[2]: https://github.com/matrix-org/sygnal/blob/main/sygnal/webpushpushkin.py#L152
[3]: https://spec.matrix.org/v1.9/client-server-api/#_matrixclientv3pushers_pusherdata
[4]: https://www.rfc-editor.org/rfc/rfc8030
[5]: https://www.rfc-editor.org/rfc/rfc8291
[6]: https://www.rfc-editor.org/rfc/rfc8292
[7]: https://gist.github.com/mar-v-in/2a054e3a4c0a508656549fc7d0aaeb74#webpush
[8]: https://developer.apple.com/documentation/usernotifications/sending-web-push-notifications-in-web-apps-and-browsers

## Proposal

`PusherData` fields are now define as follow:
- `format`: Required if `kind` is `http` or `webpush`, not used if `kind` is `email`. The format to send
notifications in to Push Gateways. The details about what fields the homeserver should send to the push gateway
are defined in the Push Gateway Specification. Currently the only format available is ’event_id_only'.
- `url`: Required if `kind` is `http`, not used else. The URL to use to send notifications to. MUST be an
HTTPS URL with a path of /_matrix/push/v1/notify
- `endpoint`: Required if `kind` is `webpush`, not used else. The URL to send notification to, as defined as a
`push resource` by RFC8030. MUST be an HTTPS URL.
- `auth`: Required if `kind` is `webpush`, not used else. The authentication secret. This is 16 random bytes
encoded in base64 url.

The POST request to the endpoint dedicated to the creation, modification and deletin of pushers,
`POST /_matrix/client/v3/pushers/set` now supports a new `kind`: `webpush`.
- `kind`: Required: The `kind` of pusher to configure. `http` makes a pusher that sends HTTP pokes. `webpush` makes a
pusher that sends Web Push encrypted messages. `email` makes a pusher that emails the user with unread notifications.
`null` deletes the pusher.
- `pushkey`: Required: This is a unique identifier for this pusher. The value you should use for this is the routing
or destination address information for the notification, for example, the APNS token for APNS or the Registration ID
for GCM. If your notification client has no such concept, use any unique identifier. Max length, 512 bytes.
If the `kind` is "email", this is the email address to send notifications to.
If the `kind` is `webpush`, this is the user agent public key encoded in base64 url. The public key comes from a ECDH
keypair using the P-256 (prime256v1, cf. FIPS186) curve.

A VAPID (Voluntary Application Server Identification, cf RFC8292) is often needed to be able to register with a push
server.
It is proposed to add a `m.webpush` capability to the `/capabilities` endpoint with this format:
```
"m.webpush": {
	"enabled": true,
	"vapid": "BNbXV88MfMI0fSxB7cDngopoviZRTbxIS0qSS-O7BZCtG04khMOn-PP2ueb_X7Aeci42n02kJ0-JJJ0uQ4ELRTs"
}
```
It is also useful to decide if the client should register a pusher using `http` kind and and old style
Sygnal WebPush semantic. A client that supports this kind of pusher should use it if the server supports it too, and
not register another `http` pusher to avoid duplicate pushes.

## Potential issues

While implemnting, one have to be carreful with RFC8291: many libraries use the 4th draft of this spec. Checking the
Content-Encoding header is a good way to know if it the correct version. If the value is `aes128gcm`, then it uses
the right specifications, else (`aesgcm`), then it uses the draft version.

## Alternatives

`pushkey` could be a random ID, and we can add `p256dh` in the `PusherData`. But it would require client to store it,
while the public key already identify that pusher. And, client already use the PusherData that way.

`vapid` parameter could be made optional considering it is officially not a requirement, however it seems
existing big players push servers need it anyway to be able to subscribe, so it was decided to make it mandatory
to avoid issues with those.

## Security considerations

Security considerations are listed by RFC8030 [[9]], there are mainly resolved with RFC8291 (Encryption) and
RFC8292 (VAPID).

Like any other federation request, there is a risk of SSRF. This risk is limited since the post data isn't
arbitrary (the content is encrypted), and a potential malicious actor don't have access to the response.
Nevertheless, it is recommended to not post to private addresses, with the possibility with a setting to
whitelist a private IP. (Synapse already have ip_range_whitelist [[10]])
It is also recommended to not follow redirection, to avoid implementation issue where the destination is check
before sending the request but not for redirections.

Like any other federation request, there is a risk of DOS amplification. One malicious actor register many users
to a valid endpoint, then change the DNS record and target another server, then notify all these users. This
amplification is very limited since HTTPS is required and the TLS certificate of the target will be rejected. The
request won't reach any functionnality of the targeted application. The home server can reject pusher if the response
code is not one intended.

[9]: https://www.rfc-editor.org/rfc/rfc8030#section-8
[10]: https://matrix-org.github.io/synapse/latest/usage/configuration/config_documentation.html#ip_range_whitelist

## Unstable prefix

- Until this proposal is considered stable, implementations must use
`org.matrix.msc4174.webpush` instead of `m.webpush`.

## Dependencies

-

