# MSC3359: Delayed Push

Mobile applications usually have to rely on a proprietary push provider for delivering
messages to the phone they run on. These providers don't allow self-hosting, and
aren't exactly known to respect the privacy of their users.

[MSC3013](https://github.com/matrix-org/matrix-doc/pull/3013) (encrypted push)
lays the groundwork for reducing the amount of information that the push provider
sees, by hiding the room and event IDs from the push providers. While that is
already a good step towards preventing profiling on the push provider side, they
can still build social graphs based on timing analysis.

To further reduce the ability of profiling that the push providers continue to have,
we propose that clients can configure a randomized delay when setting up the push
provider, which is automatically added to pushes. This will not completely prevent
profiling, but with enough traffic it will at least make it quite a bit harder and
less accurate.

## Proposal

A new pusher data field, `random_delay`, is introduced for pushers of kind `http`.
This field is not to be added to the actual push payload being sent to push gateways.
It is an integer and denotes the maximum random delay of each push frame being
pushed out, in milliseconds. A value of `0` or absence of the field disables this
delay. As such, setting a pusher with a random delay of 1500 milliseconds would
look as following:
```
POST /_matrix/client/r0/pushers/set HTTP/1.1
Content-Type: application/json

{
  "lang": "en",
  "kind": "http",
  "app_display_name": "Mat Rix",
  "device_display_name": "iPhone 9",
  "profile_tag": "xxyyzz",
  "app_id": "com.example.app.ios",
  "pushkey": "APA91bHPRgkF3JUikC4ENAHEeMrd41Zxv3hVZjC9KtT8OvPVGJ-hQMRKRrZuJAEcl7B338qju59zJMjw2DELjzEvxwYv7hH5Ynpc1ODQ0aT4U4OFEeco8ohsN5PjL1iC2dNtk2BAokeMCg2ZXKqpc8FXKmhX94kIxQ",
  "data": {
    "url": "https://push-gateway.location.here/_matrix/push/v1/notify",
    "format": "event_id_only",
    "random_delay": 1500
  },
  "append": false
}
```

Before sending out a push notification to the provided http endpoint the server
must then create a random integer between 0 and the provided `random_delay`, and
delay the push message by that many milliseconds.

### What this MSC does and does not address

This MSC addresses central push providers (FCM, APNS, etc.) being able to do large-scale
time analysis attempting to figure out who is talking to whom.

This MSC, however, does *not* address if a central push provider wants to figure
out if two specific people are actually talking to each other. These analysis are
significantly more computational heavy, though, as you have to target specific users.

### Recommended values of random_delay

While higher random delays tend to worsen user experience, they do decrease profiling
possibilities. So, we want to pick an as high random delay as needed but as little
delay as possible. Additionally, the random delay needed depends on the minimum
frequency of all push messages a given pusher emits to FCM/APNS, and thus is typically
different for each app. If your push gateway pushes out messages with a frequency of
![`$f_{push}$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{f_{push}}),
then the jitter ![`$t_{jitter}$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{t_{jitter}})
you set should be at least
![`$t_{jitter} = \frac{1}{f_{push} * a}$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{t_{jitter}%20=%20\frac{1}{f_{push}%20*%20a}})
where
![`$a = \frac{2 - \sqrt{2}}{2}$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{a%20=%20\frac{2%20-%20\sqrt{2}}{2}}).
See Appendix A for how this value was determined.

Example values:

| ![`$f_push Hz$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{f_{push}%20[Hz]}) | ![`$t_{jitter} s$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{t_{jitter}%20[s]}) |
|-------------|---------------------|
| 0.25        | 13.656854249492383  |
| 0.5         | 6.828427124746192   |
| 1           | 3.414213562373096   |
| 10          | 0.3414213562373095  |
| 100         | 0.03414213562373096 |

Please note that you should never pick a smaller value of ![`$t_{jitter}$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{t_{jitter}})
than the calculated ones, larger ones are fine, though.

## Potential issues

As push messages get randomly delayed before being pushed out to the end user, it
could reduce the user experience. Since push notifications typically do not have
to be extremely instant, but something like an up-to 15 seconds delay is usually
fine, it should not impact the user experience too much. Additionally, as the
app grows, the delay can be smaller and smaller.

## Security considerations

Because this MSC does not change which information is pushed out, but only when,
there are no new security implications.

## Unstable prefix

This feature is to be advertised as an experimental feature in the `GET /_matrix/client/versions`
response, with the key `com.famedly.msc3359` set to `true`. So, the response could
look then as following:

```json
{
    "versions": ["r0.6.0"],
    "unstable_features": {
        "com.famedly.msc3359": true
    }
}
```
