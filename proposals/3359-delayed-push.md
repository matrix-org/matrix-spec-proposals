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
we propose that clients can configure a randomized delay, called jitter, when setting
up the push provider, which is automatically added to pushes. This will not completely
prevent profiling, but with enough traffic it will at least make it quite a bit
harder and less accurate.

## Proposal

A new pusher data field, `jitter`, is introduced for pushers of kind `http`.
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
    "jitter": 1500
  },
  "append": false
}
```

Before sending out a push notification to the provided http endpoint the server
must then create a random integer between 0 and the provided `jitter`, and
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

As push messages get a jitter before being pushed out to the end user, it could
reduce the user experience. Since push notifications typically do not have to be
extremely instant, but something like an up-to 15 seconds delay is usually fine,
it should not impact the user experience too much. Additionally, as the app grows,
the delay can be smaller and smaller.

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

## Appendix A

Two people, Alice and Bob, are talking with each other, both using the same push
provider, and both randomly delaying their messages with
![`$t_{jitter}$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{t_{jitter}}).
Let the delay of a specific push notification of Alice be
![`$d_{A}$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{d_{A}})
and of Bob be
![`$d_{B}$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{d_{B}})
where ![`$d_x \in [0, t_{jitter}]$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{d_x%20\in%20[0,%20t_{jitter}]}).

This means that the resulting delay between the push messages of Alice and Bobs
is ![`$\delta = \lvert d_A - d_B \rvert$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{\delta%20=%20\lvert%20d_A%20-%20d_B%20\rvert}).

We want the average ![`$\delta$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{\delta})
to be greater or equal than
![`$\T_{push} = \frac{1}{f_{push}}$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{\T_{push}%20=%20\frac{1}{f_{push}}}),
the time between two push notifications that the push gateway sees.

For this we define
![`$P(t) = t_{jitter} - t$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{P%28t%29%20%3D%20t_%7Bjitter%7D%20-%20t}),
which is an un-normalised probability distribution, giving the probability that two push messages at
![`$t$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{t}) originated from
the same event. This is derived from the definition of ![`$\delta$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{\delta}).

This means that a time between two pushes at the push gateway of ![`$T_{push}$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{T_{push}})
defined as
![`$\int_0^{T_{push}} P(t) dt = \int_{T_{push}}^{t_{jitter}} P(t) dt$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{%5Cint_0%5E%7BT_%7Bpush%7D%7D%20P%28t%29%20dt%20%3D%20%5Cint_%7BT_%7Bpush%7D%7D%5E%7Bt_%7Bjitter%7D%7D%20P%28t%29%20dt})
is the threshold where it becomes statistically impossible for a jitter of
![`$t_{jitter}$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{t_{jitter}})
to correlated two push messages with one another.

Solving this equation gives
![`$T_{push, 1} = \sqrt{2} t_{jitter}$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{T_%7Bpush%2C%201%7D%20%3D%20%5Csqrt%7B2%7D%20t_%7Bjitter%7D})
and ![`$t_{push, 2} = \frac{2 - \sqrt{2}}{2} t_{jitter}$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{t_%7Bpush%2C%202%7D%20%3D%20%5Cfrac%7B2%20-%20%5Csqrt%7B2%7D%7D%7B2%7D%20t_%7Bjitter%7D}).
As ![`$T_{push, 1} > t_{jitter}$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{T_%7Bpush%2C%201%7D%20%3E%20t_%7Bjitter%7D})
does not make sense in our case, we can eliminate
![`$T_{push, 1}$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{T_%7Bpush%2C%201%7D}),
leaving us with ![`$T_{push, 2}$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{T_%7Bpush%2C%202%7D}).

Now we define ![`$a$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{a})
as ![`$\frac{T_{push}}{a} = t_{jitter}$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{%5Cfrac%7BT_%7Bpush%7D%7D%7Ba%7D%20%3D%20t_%7Bjitter%7D}),
giving ![`$a = \frac{2 - \sqrt{2}}{2}$`](https://render.githubusercontent.com/render/math?math=\bgcolor{white}{a%20%3D%20%5Cfrac%7B2%20-%20%5Csqrt%7B2%7D%7D%7B2%7D}).
